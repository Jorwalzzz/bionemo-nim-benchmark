"""
Stage 1B Security, Proxy IP Extraction, CSRF, ASGI Chunked Limits, SSE Streaming,
SSRF DNS/Redirect Hardening, MCP Sync & XSS Prevention Regression Suite.
"""

from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.infra.security_sentinel import SafeSanitizer
from bionemo_benchmark.infra.trial_limiter import extract_client_ip
from bionemo_benchmark.server.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestTrustedProxyIPExtraction:
    """Verify rightmost untrusted-hop X-Forwarded-For extraction."""

    def test_extract_client_ip_ignores_spoofed_leftmost_hop(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.0.0.0/8,172.16.0.0/12")
        # Spoofed leftmost 1.2.3.4 must be ignored; rightmost outside proxy CIDRs is 203.0.113.9
        resolved = extract_client_ip("10.1.2.3", "1.2.3.4, 203.0.113.9, 172.16.5.4")
        assert resolved == "203.0.113.9"

    def test_untrusted_peer_ignores_forwarded_headers(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
        resolved = extract_client_ip("198.51.100.77", "8.8.8.8, 127.0.0.1")
        assert resolved == "198.51.100.77"


class TestStrictAntiCSRF:
    """Verify Sec-Fetch-Site, explicit CSRF header/JSON requirement, and exact origin matching."""

    def test_blocks_sec_fetch_site_cross_site_even_from_loopback(self):
        client = TestClient(app, client=("127.0.0.1", 55555))
        resp = client.post(
            "/api/target/fetch",
            headers={
                "Origin": "http://localhost:8000",
                "Sec-Fetch-Site": "cross-site",
                "X-BioNeMo-CSRF": "1",
            },
            json={"target": "KRAS G12D"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"] == "CSRF_ORIGIN_REJECTED"

    def test_blocks_bodyless_post_without_csrf_header_even_on_loopback(self):
        client = TestClient(app, client=("127.0.0.1", 55555))
        resp = client.post("/api/run?target=KRAS+G12D&candidates=2")
        assert resp.status_code == 403
        assert resp.json()["error"] == "CSRF_ORIGIN_REJECTED"

    def test_blocks_wildcard_hf_space_and_github_subdomains(self):
        client = TestClient(app, client=("127.0.0.1", 55555))
        for origin in ("https://random-user.hf.space", "https://attacker.github.io"):
            resp = client.post(
                "/api/target/fetch",
                headers={"Origin": origin},
                json={"target": "KRAS"},
            )
            assert resp.status_code == 403
            assert resp.json()["error"] == "CSRF_ORIGIN_REJECTED"


class TestPureASGIStreamingAndChunkedCap:
    """Verify chunked body size cap (no Content-Length) and unbuffered incremental SSE."""

    def test_chunked_streaming_payload_over_128kb_rejected_with_413(self):
        async def _run():
            async def chunked_body():
                for _ in range(5):
                    yield b"x" * 40000  # 200 KB total without Content-Length

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
                return await ac.post(
                    "/api/redock",
                    content=chunked_body(),
                    headers={"Content-Type": "application/json", "X-BioNeMo-CSRF": "1"},
                )

        resp = asyncio.run(_run())
        assert resp.status_code == 413
        assert resp.json()["error"] == "PAYLOAD_TOO_LARGE"

    def test_sse_stream_delivers_events_incrementally_and_refunds_on_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        async def _stream_ok():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
                events: list[str] = []
                async with ac.stream(
                    "POST",
                    "/api/stream",
                    json={"target": "KRAS G12D", "candidates": 2},
                    headers={"X-BioNeMo-CSRF": "1"},
                ) as resp:
                    assert resp.status_code == 200
                    assert "text/event-stream" in resp.headers.get("content-type", "")
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            payload = json.loads(line[6:])
                            events.append(payload.get("event", ""))
                            if payload.get("event") == "campaign_complete":
                                break
                return events

        seen_events = asyncio.run(_stream_ok())
        assert seen_events[0] == "stream_ready"
        assert "campaign_complete" in seen_events

        # Also verify upstream failure mid-SSE refunds quota slot cleanly
        import bionemo_benchmark.server.routes_campaign as routes_campaign_mod

        monkeypatch.setenv("DISABLE_TRIAL_LIMIT", "false")
        sync_client = TestClient(app)
        reg = sync_client.post(
            "/api/auth/register",
            json={"email": "sse_refund@stanford.edu", "password": "StrongPassword123!"},
        )
        assert reg.status_code == 200
        tok = reg.json()["token"]

        class BrokenStreamOrch:
            def run_discovery_campaign(self, **kwargs):
                raise RuntimeError("Simulated NIM SSE timeout")

        with monkeypatch.context() as ctx:
            ctx.setattr(routes_campaign_mod, "make_orchestrator", lambda **kw: BrokenStreamOrch())

            async def _stream_fail():
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
                    async with ac.stream(
                        "POST",
                        "/api/stream",
                        json={"target": "KRAS G12D", "candidates": 2},
                        headers={"Authorization": f"Bearer {tok}", "X-BioNeMo-CSRF": "1"},
                    ) as resp:
                        assert resp.status_code == 200
                        return [json.loads(ln[6:]).get("event") async for ln in resp.aiter_lines() if ln.startswith("data: ")]

            fail_events = asyncio.run(_stream_fail())
            assert "campaign_error" in fail_events

        me_res = sync_client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
        assert me_res.status_code == 200
        assert me_res.json()["quota"]["runs_remaining"] == 5


class TestSSRFHardeningAndRedirects:
    """Verify DNS IP checks, metadata blocks, NIM_ALLOW_PRIVATE_HOSTS toggle, and allow_redirects=False."""

    def test_dns_rebinding_private_ip_blocked_by_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("NIM_ALLOWED_HOSTS", "custom-nim.internal")
        monkeypatch.delenv("NIM_ALLOW_PRIVATE_HOSTS", raising=False)
        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda host, port, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.20.30.40", 443))],
        )
        with pytest.raises(ValueError, match="non-public IP"):
            SafeSanitizer.validate_outbound_url("https://custom-nim.internal/v1/infer")

        monkeypatch.setenv("NIM_ALLOW_PRIVATE_HOSTS", "true")
        assert (
            SafeSanitizer.validate_outbound_url("https://custom-nim.internal/v1/infer")
            == "https://custom-nim.internal/v1/infer"
        )

    def test_cloud_metadata_unconditionally_blocked_even_with_private_flag(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("NIM_ALLOWED_HOSTS", "169.254.169.254,fd00:ec2::254,meta-rebind.internal")
        monkeypatch.setenv("NIM_ALLOW_PRIVATE_HOSTS", "true")

        with pytest.raises(ValueError, match="metadata"):
            SafeSanitizer.validate_outbound_url("https://169.254.169.254/latest/meta-data/")

        with pytest.raises(ValueError, match="metadata"):
            SafeSanitizer.validate_outbound_url("https://[fd00:ec2::254]/latest/meta-data/")

        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda host, port, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 443))],
        )
        with pytest.raises(ValueError, match="metadata"):
            SafeSanitizer.validate_outbound_url("https://meta-rebind.internal/")

    def test_safe_http_request_disables_redirects(self, monkeypatch: pytest.MonkeyPatch):
        captured: dict[str, object] = {}

        def fake_request(**kwargs):
            captured.update(kwargs)
            resp = MagicMock()
            resp.status_code = 200
            return resp

        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda host, port, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
        )
        monkeypatch.setattr("bionemo_benchmark.infra.security_sentinel.requests.request", fake_request)
        SafeSanitizer.safe_http_request("GET", "https://files.rcsb.org/download/7RPZ.pdb")
        assert captured["allow_redirects"] is False
        assert captured["verify"] is True


class TestMCPAndDOMXSSRegression:
    """Verify .antigravity/mcp.json matches exported tools and DOM XSS sink is eliminated."""

    def test_mcp_json_matches_exported_server_tools(self):
        pytest.importorskip("mcp")
        import bionemo_benchmark.mcp.server as mcp_srv

        mcp_cfg = json.loads((REPO_ROOT / ".antigravity" / "mcp.json").read_text(encoding="utf-8"))
        configured_tools = set(mcp_cfg["mcpServers"]["bionemo-local"]["enabledTools"])
        exported_tools = {
            name for name in dir(mcp_srv) if name.startswith("bionemo_") and callable(getattr(mcp_srv, name))
        }
        assert configured_tools == exported_tools

    def test_frontend_email_validator_has_no_quote_regex_or_inline_onclick(self):
        api_js = (REPO_ROOT / "js" / "cockpit" / "api.js").read_text(encoding="utf-8")
        assert "onclick=\"fixEmailTypo" not in api_js
        assert "fixBtn.addEventListener('click'" in api_js
        regex_line = next(line for line in api_js.splitlines() if "const EMAIL_STRICT_REGEX" in line)
        assert "'*" not in regex_line
