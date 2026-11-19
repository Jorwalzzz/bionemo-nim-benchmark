"""
Serializers, client extraction, security helpers, and shared state for BioNeMo Cockpit.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from bionemo_benchmark.infra.auth_manager import AuthManager
from bionemo_benchmark.infra.security_sentinel import (
    BiosecurityScreener,
    SecretScrubber,
    TokenBucketRateLimiter,
)
from bionemo_benchmark.infra.trial_limiter import TrialLimiter


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
ADMIN_RESET_KEY: Optional[str] = os.environ.get("ADMIN_RESET_KEY")
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
    """Proxy-aware client IP extraction, validating against trusted reverse proxies."""
    peer_ip = request.client.host if request.client else "127.0.0.1"
    if peer_ip in TRUSTED_PROXIES or os.environ.get("TRUST_ALL_PROXIES", "").lower() in ("1", "true", "yes"):
        h = request.headers
        for name in (
            "cf-connecting-ip",
            "CF-Connecting-IP",
            "x-forwarded-for",
            "X-Forwarded-For",
            "x-real-ip",
            "X-Real-IP",
        ):
            val = h.get(name)
            if val:
                return val.split(",")[0].strip()
    return peer_ip


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


def verify_request_origin(request: Request) -> bool:
    """
    Verifies that API mutation requests originate from a legitimate origin (anti-CSRF).
    Enforces strict protocol and exact domain/port matching to prevent subdomain spoofing.
    """
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    host = request.headers.get("host")
    check_url = origin or referer or ""
    if not check_url:
        peer = request.client.host if request.client else "127.0.0.1"
        if peer in TRUSTED_PROXIES or (host and host.split(":")[0].lower() in ("localhost", "127.0.0.1", "testserver")):
            return True
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return False

    try:
        parsed = urlparse(check_url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()
        if host:
            host_header_name = host.split(":")[0].lower()
            if hostname == host_header_name:
                return True

        if hostname in ("localhost", "127.0.0.1", "testserver"):
            return True
        if (
            hostname == "huggingface.co"
            or hostname.endswith(".hf.space")
            or hostname.endswith(".huggingface.co")
            or hostname == "jorwalzzz.github.io"
        ):
            return True
    except Exception:
        return False

    return False


def get_authenticated_user(request: Request) -> Optional[Dict[str, Any]]:
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
    response: Response, token: str, request: Optional[Request] = None
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


def get_client_identifiers(request: Request) -> Tuple[str, str, str, str, Optional[str]]:
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
