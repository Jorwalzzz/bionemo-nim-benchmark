"""
Serializers, client extraction, security helpers, and shared state for BioNeMo Cockpit.
"""

from __future__ import annotations

import logging
import math
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import Request, Response

from bionemo_benchmark.infra.auth_manager import AuthManager
from bionemo_benchmark.infra.security_sentinel import (
    BiosecurityScreener,
    TokenBucketRateLimiter,
)
from bionemo_benchmark.infra.trial_limiter import TrialLimiter, extract_client_ip

# ... keep path helpers intact; only replace client_ip & verify_request_origin cleanly below


def find_repo_root() -> str:
    """Locate the project repository root directory."""
    for p in Path(__file__).resolve().parents:
        if (p / "pyproject.toml").exists() and (p / "index.html").exists():
            return str(p)
    return str(Path(__file__).resolve().parents[3])


BASE_DIR: str = find_repo_root()
SRC_DIR: str = os.path.join(BASE_DIR, "src")
RESULTS_DIR: str = os.path.join(BASE_DIR, "results")
ROOT_ASSETS_DIR: str = os.path.join(BASE_DIR, "assets")
ASSETS_DIR: str = os.path.join(RESULTS_DIR, "assets")
DATA_DIR: str = os.path.join(BASE_DIR, "data")
CSS_DIR: str = os.path.join(BASE_DIR, "css")
JS_DIR: str = os.path.join(BASE_DIR, "js")
VENDOR_DIR: str = os.path.join(BASE_DIR, "vendor")
INSTALLERS_DIR: str = os.path.join(BASE_DIR, "scripts", "installers")
HTML_PATH: str = os.path.join(BASE_DIR, "cockpit.html")
LANDING_PATH: str = os.path.join(BASE_DIR, "index.html")

ALLOWED_ROOT_ASSETS: frozenset[str] = frozenset(
    {
        "app.min.css",
        "cockpit.css",
        "cockpit.js",
        "theme.css",
        "input.css",
        "favicon.ico",
    }
)

MAX_PAYLOAD_SIZE: int = 128 * 1024  # 128 KB max request body size
ADMIN_RESET_KEY: str | None = os.environ.get("ADMIN_RESET_KEY")
TRUSTED_PROXIES: frozenset[str] = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})

logger: logging.Logger = logging.getLogger("CockpitSecurity")

# In-flight Token Bucket Rate Limiter (Max burst 40 requests, refilling at 1 req/sec)
in_flight_limiter: TokenBucketRateLimiter = TokenBucketRateLimiter(
    capacity=40, refill_rate_per_sec=1.0
)

COOKIE_NAME: str = "bionemo_trial_session"
trial_limiter: TrialLimiter = TrialLimiter()
AUTH_COOKIE_NAME: str = "bionemo_auth_token"
auth_manager: AuthManager = AuthManager()


def client_ip(request: Request) -> str:
    """Rightmost untrusted-hop client IP extraction bounded by TRUSTED_PROXY_CIDRS."""
    peer_ip = request.client.host if request.client else "127.0.0.1"
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    return extract_client_ip(peer_ip, xff)


def sanitize_target_query(query: str) -> str:
    """Sanitizes incoming biological target query against command injection, XSS, and dual-use toxin keywords."""
    if not query:
        return "KRAS G12D"
    raw_str = str(query)[:1500]
    cleaned = re.sub(r"<[^>]*?>", "", raw_str)
    cleaned = re.sub(r"[;&|`$><\\/\n\r]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    candidate = cleaned[:1500] if cleaned else "KRAS G12D"

    is_safe, reason = BiosecurityScreener.screen_target(candidate)
    if not is_safe:
        logger.warning(
            "Biosecurity restriction triggered on target query '%s': %s",
            candidate,
            reason,
        )
        raise ValueError(reason or "BIOSECURITY_RESTRICTION: Target disallowed.")

    return candidate


_EXACT_ALLOWED_HTTPS_HOSTS: frozenset[str] = frozenset(
    {
        "jorwalzzz.github.io",
        "huggingface.co",
        "jorwalzzz-bionemo-nim-benchmark.hf.space",
    }
)


def _normalize_origin_tuple(raw_url: str) -> tuple[str, str, int | None] | None:
    """Parse an Origin or Referer URL into canonical (scheme, host, port)."""
    try:
        parsed = urlparse(raw_url.strip())
    except ValueError:
        return None
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").rstrip(".").lower()
    if scheme not in ("http", "https") or not host:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    default_port = 443 if scheme == "https" else 80
    effective_port = port if port and port != default_port else None
    return scheme, host, effective_port


def _is_origin_allowlisted(raw_url: str) -> bool:
    """Check parsed origin strictly against exact allowlisted origins (zero wildcards)."""
    norm = _normalize_origin_tuple(raw_url)
    if norm is None:
        return False
    scheme, hostname, port = norm

    # Permit configured exact origins from environment
    for entry in os.environ.get("BIONEMO_ALLOWED_ORIGINS", "").split(","):
        if entry.strip():
            allowed_norm = _normalize_origin_tuple(entry)
            if allowed_norm is not None and norm == allowed_norm:
                return True

    # Permit local workstation loopback origins on any port
    if hostname in ("localhost", "127.0.0.1", "testserver"):
        return True

    # Permit exact verified HTTPS deployment origins on standard HTTPS port only
    if scheme == "https" and port is None and hostname in _EXACT_ALLOWED_HTTPS_HOSTS:
        return True

    return False


def verify_request_origin(request: Request) -> bool:
    """
    Enforces strict anti-CSRF checks on mutating endpoints without Host/proxy bypasses:
    1. Rejects Sec-Fetch-Site: cross-site headers unconditionally.
    2. Requires Content-Type: application/json OR X-BioNeMo-CSRF: 1 on mutating verbs.
    3. Validates Origin/Referer strictly against an exact origin allowlist when supplied.
    """
    method = (request.method or "GET").upper()
    if method in ("GET", "HEAD", "OPTIONS"):
        return True

    sec_fetch_site = (request.headers.get("sec-fetch-site") or "").strip().lower()
    if sec_fetch_site == "cross-site":
        return False

    raw_ct = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    csrf_hdr = (request.headers.get("x-bionemo-csrf") or "").strip()
    if raw_ct != "application/json" and csrf_hdr != "1":
        return False

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    check_url = origin or referer or ""
    if check_url:
        return _is_origin_allowlisted(check_url)

    return True


def get_authenticated_user(request: Request) -> dict[str, Any] | None:
    """Extracts and verifies JWT/HMAC token from Authorization header or cookie."""
    token = None
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None
    user_id = auth_manager.verify_token(token)
    if not user_id:
        return None
    return auth_manager.get_user_profile(user_id)


def with_auth_cookie(
    response: Response, token: str, request: Request | None = None
) -> Response:
    """Sets secure HTTP-only authentication session cookie."""
    is_secure = False
    if request:
        is_secure = (
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto") == "https"
        )
    if os.environ.get("SECURE_COOKIES", "").lower() in ("true", "1", "yes"):
        is_secure = True
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=86400 * 30,
        httponly=True,
        samesite="lax",
        secure=is_secure,
    )
    return response


def get_client_identifiers(request: Request) -> tuple[str, str, str, str, str | None]:
    """Extract or issue tamper-proof session token, proxy-aware client IP, and composite fingerprint."""
    cookie_token = request.cookies.get(COOKIE_NAME)
    session_id = trial_limiter.verify_and_extract_session(cookie_token)
    if not session_id:
        signed_token = trial_limiter.create_signed_session_token()
        session_id = trial_limiter.verify_and_extract_session(signed_token)
    else:
        signed_token = cookie_token

    ip = client_ip(request)

    client_fp = request.headers.get("X-Client-Fingerprint") or request.query_params.get("fp")
    user_agent = request.headers.get("User-Agent")
    accept_lang = request.headers.get("Accept-Language")
    fp_hash = trial_limiter.compute_composite_fingerprint(client_fp, user_agent, accept_lang)

    return session_id, signed_token, fp_hash, ip, user_agent


def with_cookie(resp: Response, token: str) -> Response:
    """Attach trial session cookie to response."""
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=86400 * 365,
        httponly=True,
        samesite="lax",
    )
    return resp


def sanitize_json_numbers(obj: Any) -> Any:
    """Recursively converts NaN/Inf floats into None for strict RFC-8259 JSON."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: sanitize_json_numbers(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_json_numbers(v) for v in obj]
    return obj

