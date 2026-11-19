"""
Authentication, session management, quota tracking, and feedback API routes.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from bionemo_benchmark.infra.auth_manager import validate_email_address
from bionemo_benchmark.server.serializers import (
    AUTH_COOKIE_NAME,
    COOKIE_NAME,
    auth_manager,
    client_ip,
    get_authenticated_user,
    get_client_identifiers,
    sanitize_target_query,
    trial_limiter,
    verify_request_origin,
    with_auth_cookie,
    with_cookie,
)

router: APIRouter = APIRouter()


def gate_run(request: Request, target: str) -> tuple[Response | None, tuple[str, str | None, dict[str, Any]] | None]:
    """Origin check, sanitize, and consume a trial run. Returns (error_response, ctx)."""
    if not verify_request_origin(request):
        return (
            JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF_ORIGIN_REJECTED",
                    "message": "Cross-origin execution blocked for security.",
                },
            ),
            None,
        )
    target = sanitize_target_query(target)
    # In production/trial mode, require authenticated researcher account and 3:00 PM IST quota
    if os.environ.get("DISABLE_TRIAL_LIMIT", "").lower() not in ("true", "1", "yes"):
        user = get_authenticated_user(request)
        if not user:
            return (
                JSONResponse(
                    status_code=401,
                    content={
                        "error": "AUTHENTICATION_REQUIRED",
                        "message": "Free trial discovery requires a researcher account. Please sign in or register (5 free runs every 24 hours, resets at 3:00 PM IST).",
                        "requires_auth": True,
                    },
                ),
                None,
            )
        allowed, quota_info = auth_manager.consume_run(user["id"])
        if not allowed:
            return (
                JSONResponse(
                    status_code=429,
                    content={
                        "error": "DAILY_QUOTA_EXCEEDED",
                        "message": "Daily trial quota of 5 runs reached. Quota refreshes automatically at 3:00 PM IST (09:30 UTC).",
                        "quota": quota_info,
                    },
                ),
                None,
            )
        return None, (target, None, quota_info)

    session_id, token, fp_hash, ip, ua = get_client_identifiers(request)
    allowed, info = trial_limiter.consume_trial_run(
        session_id=session_id,
        fp_hash=fp_hash,
        ip_str=ip,
        target_name=target,
        user_agent=ua,
    )
    if not allowed:
        code = 429 if info.get("error") == "GLOBAL_DAILY_LIMIT_REACHED" else 403
        return with_cookie(JSONResponse(status_code=code, content=info), token), None
    return None, (target, token, info)


@router.get("/api/trial-status")
def get_trial_status(request: Request) -> Response:
    """Check remaining trial runs for caller across session, fingerprint, IP, and global daily ceiling."""
    session_id, signed_token, fp_hash, cip, _ = get_client_identifiers(request)
    usage = trial_limiter.check_usage(session_id, fp_hash, cip)

    resp = JSONResponse(usage)
    is_secure = (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto") == "https"
        or os.environ.get("SECURE_COOKIES", "").lower() in ("true", "1", "yes")
    )
    resp.set_cookie(
        key=COOKIE_NAME,
        value=signed_token,
        max_age=86400 * 365,
        httponly=True,
        samesite="lax",
        secure=is_secure,
    )
    resp.delete_cookie(key="creator_mode")
    return resp


@router.api_route("/api/reset-trial", methods=["GET", "POST"])
def reset_trial(request: Request) -> Response:
    """
    Administrative Quota Reset Endpoint:
    Strictly protected by ADMIN_RESET_KEY to prevent unauthorized quota resets.
    """
    admin_key = os.environ.get("ADMIN_RESET_KEY", "").strip()
    provided_key = (
        request.headers.get("X-Admin-Key", "").strip()
        or request.query_params.get("key", "").strip()
    )
    if not admin_key or not secrets.compare_digest(provided_key, admin_key):
        return JSONResponse(
            status_code=403,
            content={
                "error": "UNAUTHORIZED_ADMIN_KEY",
                "message": "Access denied. Valid administrator key required to reset quota.",
            },
        )

    session_id, signed_token, fp_hash, cip, _ = get_client_identifiers(request)
    trial_limiter.reset_caller(session_id, fp_hash, cip)
    resp = JSONResponse(
        {
            "success": True,
            "message": "Trial quota has been reset by administrator.",
            "trial_status": {
                "allowed": True,
                "runs_used": 0,
                "runs_remaining": trial_limiter.max_runs,
                "max_runs": trial_limiter.max_runs,
                "is_locked": False,
            },
        }
    )
    is_secure = (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto") == "https"
        or os.environ.get("SECURE_COOKIES", "").lower() in ("true", "1", "yes")
    )
    resp.set_cookie(
        key=COOKIE_NAME,
        value=signed_token,
        max_age=86400 * 365,
        httponly=True,
        samesite="lax",
        secure=is_secure,
    )
    resp.delete_cookie(key="creator_mode")
    return resp


@router.post("/api/auth/validate-email")
async def api_validate_email(request: Request) -> dict[str, Any]:
    """Validates email format, domain existence checks, typo suggestions, and disposable address detection."""
    try:
        body = await request.json()
        raw_email = str(body.get("email", "")).strip()
    except Exception:
        raw_email = ""
    is_valid, msg, typo, classification = validate_email_address(raw_email)
    return {
        "valid": is_valid,
        "message": msg,
        "suggestion": typo,
        "classification": classification,
    }


@router.post("/api/auth/register")
async def api_register(request: Request) -> Response:
    """Registers a new researcher account."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={"error": "CSRF_ORIGIN_REJECTED", "message": "Cross-origin request rejected."},
        )
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "INVALID_JSON", "message": "Malformed JSON payload."},
        )

    email = str(body.get("email", "")).strip()
    password = str(body.get("password", "")).strip()
    full_name = str(body.get("full_name", "")).strip()
    organization = str(body.get("organization", "")).strip()

    success, user_dict, err_msg = auth_manager.register_user(
        email=email,
        password=password,
        full_name=full_name,
        organization=organization,
    )
    if not success:
        return JSONResponse(
            status_code=400,
            content={"error": "REGISTRATION_FAILED", "message": err_msg},
        )

    token = auth_manager.create_token(user_dict["id"])
    quota = auth_manager.get_user_quota(user_dict["id"])
    resp = JSONResponse(
        {
            "success": True,
            "message": "Account created successfully.",
            "token": token,
            "user": user_dict,
            "quota": quota,
        }
    )
    return with_auth_cookie(resp, token, request)


@router.post("/api/auth/login")
async def api_login(request: Request) -> Response:
    """Authenticates researcher and issues session token."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={"error": "CSRF_ORIGIN_REJECTED", "message": "Cross-origin request rejected."},
        )
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "INVALID_JSON", "message": "Malformed JSON payload."},
        )

    email = str(body.get("email", "")).strip()
    password = str(body.get("password", "")).strip()

    success, auth_data, err_msg = auth_manager.authenticate_user(email, password)
    if not success:
        return JSONResponse(
            status_code=401,
            content={"error": "AUTH_FAILED", "message": err_msg or "Invalid credentials."},
        )

    resp = JSONResponse(
        {
            "success": True,
            "token": auth_data["token"],
            "user": auth_data["user"],
            "quota": auth_data["quota"],
        }
    )
    return with_auth_cookie(resp, auth_data["token"], request)


@router.post("/api/auth/demo-login")
def api_demo_login(request: Request) -> Response:
    """1-Click Evaluator Account Login."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={"error": "CSRF_ORIGIN_REJECTED", "message": "Cross-origin request rejected."},
        )
    success, auth_data, err_msg = auth_manager.authenticate_user(
        "evaluator@bionemo.org", "DemoResearcher2026!"
    )
    if not success:
        return JSONResponse(
            status_code=500,
            content={"error": "DEMO_ACCOUNT_ERROR", "message": err_msg or "Demo account unavailable."},
        )

    resp = JSONResponse(
        {
            "success": True,
            "demo": True,
            "token": auth_data["token"],
            "user": auth_data["user"],
            "quota": auth_data["quota"],
        }
    )
    return with_auth_cookie(resp, auth_data["token"], request)


@router.post("/api/auth/logout")
def api_logout(request: Request) -> Response:
    """Logs out researcher session, invalidates HMAC token on server-side blocklist, and clears auth cookie."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={"error": "CSRF_ORIGIN_REJECTED", "message": "Cross-origin request rejected."},
        )

    token = None
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)

    if token:
        auth_manager.revoke_token(token)

    resp = JSONResponse({"success": True, "message": "Logged out successfully."})
    resp.delete_cookie(AUTH_COOKIE_NAME)
    return resp


@router.get("/api/auth/me")
def api_get_current_user(request: Request) -> dict[str, Any]:
    """Fetches currently authenticated user and synchronized 3:00 PM IST quota."""
    user = get_authenticated_user(request)
    if user:
        quota = auth_manager.get_user_quota(user["id"])
        return {"authenticated": True, "user": user, "quota": quota}
    return {
        "authenticated": False,
        "quota": auth_manager.get_cycle_info(),
    }


@router.post("/api/feedback")
async def api_submit_feedback(request: Request) -> Response:
    """Submits authenticated researcher feedback."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={"error": "CSRF_ORIGIN_REJECTED", "message": "Cross-origin request rejected."},
        )
    user = get_authenticated_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={
                "error": "AUTHENTICATION_REQUIRED",
                "message": "You must be signed in to submit scientific feedback.",
            },
        )
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "INVALID_JSON", "message": "Malformed JSON payload."},
        )

    try:
        rating = int(body.get("rating", 5))
    except (ValueError, TypeError):
        rating = 5

    category = str(body.get("category", "General Evaluation"))
    comments = str(body.get("comments", "")).strip()
    target_name = str(body.get("target_name", "KRAS G12D")).strip()

    if not comments:
        return JSONResponse(
            status_code=400,
            content={"error": "EMPTY_COMMENTS", "message": "Feedback comments cannot be empty."},
        )

    success, fb_entry, err_msg = auth_manager.submit_feedback(
        user_id=user["id"],
        category=category,
        rating=rating,
        comments=comments,
        target_complex=target_name,
        client_ip=client_ip(request),
    )
    if not success:
        return JSONResponse(
            status_code=400,
            content={"error": "FEEDBACK_FAILED", "message": err_msg},
        )
    return JSONResponse(
        {
            "success": True,
            "message": "Thank you! Your feedback has been recorded.",
            "feedback_id": fb_entry["id"],
            "feedback": fb_entry,
        }
    )


@router.get("/api/feedback")
def api_get_feedback(request: Request) -> Response:
    """Retrieves feedback history for authenticated researcher."""
    user = get_authenticated_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "AUTHENTICATION_REQUIRED", "message": "Sign in required to view feedback history."},
        )
    items = auth_manager.get_feedback_for_user(user["id"])
    return JSONResponse({"feedback": items})
