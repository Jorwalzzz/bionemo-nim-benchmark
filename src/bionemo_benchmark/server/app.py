"""
FastAPI application setup, security middleware, static routing, and server lifecycle.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import threading
import uuid
import webbrowser
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders

from bionemo_benchmark.infra.owner_security import (
    get_owner_boot_token_path,
    owner_security_manager,
)
from bionemo_benchmark.infra.security_sentinel import SecretScrubber
from bionemo_benchmark.server.routes_auth import router as auth_router
from bionemo_benchmark.server.routes_campaign import router as campaign_router
from bionemo_benchmark.server.routes_owner import router as owner_router
from bionemo_benchmark.server.routes_structure import router as structure_router
from bionemo_benchmark.server.serializers import (
    ASSETS_DIR,
    BASE_DIR,
    CSS_DIR,
    DATA_DIR,
    JS_DIR,
    MAX_PAYLOAD_SIZE,
    RESULTS_DIR,
    ROOT_ASSETS_DIR,
    VENDOR_DIR,
    client_ip,
    in_flight_limiter,
    logger,
)

# Load environment configuration
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Default local executions to full unlimited workstation mode
if "PORT" not in os.environ and not os.environ.get("DISABLE_TRIAL_LIMIT"):
    os.environ["DISABLE_TRIAL_LIMIT"] = "true"

app: FastAPI = FastAPI(title="Agentic BioNeMo Cockpit API", version="2.2.0")

# Explicit CORS policy restricting origins to local workstations and verified production domains
ALLOWED_CORS_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8088",
    "http://localhost:8088",
    "https://jorwalzzz.github.io",
]

SECURITY_RESPONSE_HEADERS: tuple[tuple[str, str], ...] = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("X-XSS-Protection", "1; mode=block"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Permissions-Policy", "geolocation=(), camera=(), microphone=(), payment=()"),
    (
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://3Dmol.org https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://health.api.nvidia.com https://integrate.api.nvidia.com https://files.rcsb.org https://raw.githubusercontent.com;",
    ),
)


async def _send_asgi_json(
    send: Any,
    status_code: int,
    payload: dict[str, Any],
    extra_headers: dict[str, str] | None = None,
) -> None:
    """Emit a pure-ASGI JSON response without invoking BaseHTTPMiddleware buffering."""
    body = json.dumps(payload).encode("utf-8")
    raw_headers: list[tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]
    for k, v in SECURITY_RESPONSE_HEADERS:
        raw_headers.append((k.lower().encode("ascii"), v.encode("ascii")))
    if extra_headers:
        for k, v in extra_headers.items():
            raw_headers.append((k.lower().encode("ascii"), v.encode("ascii")))
    await send({"type": "http.response.start", "status": status_code, "headers": raw_headers})
    await send({"type": "http.response.body", "body": body, "more_body": False})


class PayloadLimitASGIMiddleware:
    """Pure ASGI body size enforcement covering Content-Length and Transfer-Encoding: chunked."""

    def __init__(self, app_asgi: Any, max_bytes: int = MAX_PAYLOAD_SIZE) -> None:
        self.app = app_asgi
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or scope.get("method", "GET") in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return

        for raw_name, raw_val in scope.get("headers", []):
            if raw_name.lower() == b"content-length":
                try:
                    declared_len = int(raw_val.decode("ascii").strip())
                except ValueError:
                    await _send_asgi_json(
                        send,
                        400,
                        {"error": "INVALID_CONTENT_LENGTH", "message": "Malformed Content-Length header."},
                    )
                    return
                if declared_len > self.max_bytes:
                    await _send_asgi_json(
                        send,
                        413,
                        {
                            "error": "PAYLOAD_TOO_LARGE",
                            "message": f"Request payload exceeds {self.max_bytes // 1024}KB limit.",
                        },
                    )
                    return

        chunks: list[bytes] = []
        total_bytes = 0
        more_body = True
        while more_body:
            message = await receive()
            msg_type = message.get("type")
            if msg_type == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if chunk:
                total_bytes += len(chunk)
                if total_bytes > self.max_bytes:
                    await _send_asgi_json(
                        send,
                        413,
                        {
                            "error": "PAYLOAD_TOO_LARGE",
                            "message": f"Request payload exceeds {self.max_bytes // 1024}KB limit.",
                        },
                    )
                    return
                chunks.append(chunk)
            more_body = bool(message.get("more_body", False))

        buffered = b"".join(chunks)
        delivered = False

        async def replay_receive() -> dict[str, Any]:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": buffered, "more_body": False}
            return await receive()

        await self.app(scope, replay_receive, send)


class SecurityHeadersAndRateLimitASGIMiddleware:
    """Pure ASGI rate limiter and security header injector preserving unbuffered SSE streams."""

    def __init__(self, app_asgi: Any) -> None:
        self.app = app_asgi

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        req = Request(scope)
        ip = client_ip(req)
        path = scope.get("path", "")
        cost = 2.0 if any(p in path for p in ("/api/run", "/api/stream", "/api/redock")) else 0.5
        allowed, retry_after = in_flight_limiter.allow_request(ip, cost=cost)
        if not allowed:
            await _send_asgi_json(
                send,
                429,
                {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests from IP {ip}. Please retry after {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                extra_headers={"Retry-After": str(int(retry_after) + 1)},
            )
            return

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                headers = MutableHeaders(scope=message)
                for k, v in SECURITY_RESPONSE_HEADERS:
                    headers[k] = v
                if "server" in headers:
                    del headers["server"]
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(PayloadLimitASGIMiddleware, max_bytes=MAX_PAYLOAD_SIZE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersAndRateLimitASGIMiddleware)


@app.exception_handler(ValueError)
async def value_error_security_handler(request: Request, exc: ValueError):
    """Handles validation and biosecurity screening violations with client-friendly 400 responses."""
    err_msg = SecretScrubber.scrub(str(exc))
    return JSONResponse(
        status_code=400, content={"error": "VALIDATION_FAILED", "message": err_msg}
    )


@app.exception_handler(Exception)
async def global_security_exception_handler(request: Request, exc: Exception):
    """Global exception handler to mask internal traces and scrub secrets from logs."""
    error_id = f"sec_{uuid.uuid4().hex[:10]}"
    safe_exc_msg = SecretScrubber.scrub(str(exc))
    logger.error(
        "Internal processing error [%s] on %s %s: %s",
        error_id,
        request.method,
        request.url.path,
        safe_exc_msg,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "A secure processing exception occurred. Incident logged.",
            "incident_id": error_id,
        },
    )


# -------------------------------------------------------------------------
# Static File System Mounts
# -------------------------------------------------------------------------

os.makedirs(RESULTS_DIR, exist_ok=True)
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

if os.path.exists(ROOT_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ROOT_ASSETS_DIR), name="assets")
elif os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

if os.path.exists(DATA_DIR):
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

if os.path.exists(CSS_DIR):
    app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")

if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")

if os.path.exists(VENDOR_DIR):
    app.mount("/vendor", StaticFiles(directory=VENDOR_DIR), name="vendor")


# -------------------------------------------------------------------------
# Include Route Handlers
# -------------------------------------------------------------------------

app.include_router(owner_router)
app.include_router(auth_router)
app.include_router(campaign_router)
app.include_router(structure_router)


# -------------------------------------------------------------------------
# CLI & Process Lifecycle
# -------------------------------------------------------------------------


def _free_port(host: str, port: int, tries: int = 20) -> int:
    """Return `port` if bindable, else the next free port (local runs only)."""
    for p in range(port, port + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, p)) != 0:
                return p
    return port


def main(argv: list[str] | None = None) -> None:
    """Entry point for the BioNeMo Cockpit server."""
    import uvicorn

    cloud = "PORT" in os.environ
    ap = argparse.ArgumentParser(prog="jorwal-nim", description="JORWAL NIM cockpit")
    ap.add_argument("--host", default="127.0.0.1", help="Host interface to bind (defaults to 127.0.0.1)")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    ap.add_argument("--open", action="store_true", help="open the browser once ready")
    args = ap.parse_args(argv)

    port = args.port if cloud else _free_port("127.0.0.1", args.port)
    owner_security_manager.get_boot_token()
    boot_path = get_owner_boot_token_path()
    if args.open:
        threading.Timer(
            1.5, webbrowser.open, [f"http://localhost:{port}/cockpit.html"]
        ).start()
    print(f"BioNeMo Discovery Cockpit: http://localhost:{port}/cockpit.html  (Ctrl+C to stop)")
    print(f"Owner Boot Token File (0600): {boot_path}")
    uvicorn.run(app, host=args.host, port=port, reload=False)


if __name__ == "__main__":
    main()
