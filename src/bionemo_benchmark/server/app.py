"""
FastAPI application setup, security middleware, static routing, and server lifecycle.
"""

from __future__ import annotations

import argparse
import os
import socket
import threading
import uuid
import webbrowser

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

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
    "https://jorwalzzz.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Security Headers & Hardening Middleware
# -------------------------------------------------------------------------


@app.middleware("http")
async def enterprise_security_headers_middleware(request: Request, call_next):
    """Enforces enterprise defense-in-depth HTTP security headers, rate limits, and payload size limits."""
    # 1. In-flight rate limit check per client IP
    ip = client_ip(request)
    cost = (
        2.0
        if any(
            p in request.url.path for p in ("/api/run", "/api/stream", "/api/redock")
        )
        else 0.5
    )
    allowed, retry_after = in_flight_limiter.allow_request(ip, cost=cost)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many requests from IP {ip}. Please retry after {retry_after} seconds.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    # 2. Payload size ceiling
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
        return JSONResponse(
            status_code=413,
            content={
                "error": "PAYLOAD_TOO_LARGE",
                "message": "Request payload exceeds 128KB limit.",
            },
        )

    response: Response = await call_next(request)

    # 3. Enterprise Hardened Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "geolocation=(), camera=(), microphone=(), payment=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://3Dmol.org https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://health.api.nvidia.com https://integrate.api.nvidia.com https://files.rcsb.org https://raw.githubusercontent.com;"
    )
    if "server" in response.headers:
        del response.headers["server"]
    return response


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
    if args.open:
        threading.Timer(
            1.5, webbrowser.open, [f"http://localhost:{port}/cockpit.html"]
        ).start()
    print(f"BioNeMo Discovery Cockpit: http://localhost:{port}/cockpit.html  (Ctrl+C to stop)")
    uvicorn.run(app, host=args.host, port=port, reload=False)


if __name__ == "__main__":
    main()
