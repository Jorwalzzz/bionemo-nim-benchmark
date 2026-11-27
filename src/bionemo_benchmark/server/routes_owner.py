"""
FastAPI route handlers and dependency injection for Machine-Bound Localhost Owner Access Mode.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from bionemo_benchmark.infra.owner_security import (
    OWNER_COOKIE_NAME,
    OWNER_TOKEN_HEADER,
    OwnerPolicy,
    owner_security_manager,
)
from bionemo_benchmark.server.serializers import verify_request_origin

logger = logging.getLogger("OwnerRoutes")
router: APIRouter = APIRouter(prefix="/api/owner", tags=["Owner Access"])


class OwnerLoginRequest(BaseModel):
    owner_id: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)
    boot_token: str | None = Field(default=None, max_length=256)


def get_trial_policy(request: Request) -> OwnerPolicy:
    """
    FastAPI dependency resolving the active owner authorization policy.
    Checks direct loopback origin, absence of forwarding headers, hardware MachineGuid
    fingerprint, per-boot cryptographic token binding, and HMAC session cookie.
    """
    client_host = request.client.host if request.client else None
    cookie_value = request.cookies.get(OWNER_COOKIE_NAME)
    return owner_security_manager.evaluate_request_policy(
        client_host, cookie_value, headers=request.headers
    )


@router.get("/status")
def get_owner_status(
    request: Request,
    policy: OwnerPolicy = Depends(get_trial_policy),
) -> Response:
    """
    Reports the owner authentication status.
    Fails closed with 403 Forbidden if called from non-loopback or proxied headers.
    """
    client_host = request.client.host if request.client else None
    if not owner_security_manager.is_loopback(client_host):
        return JSONResponse(
            status_code=403,
            content={
                "error": "LOOPBACK_REQUIRED",
                "message": "Owner Access Mode is restricted to localhost callers.",
            },
        )
    if owner_security_manager.has_forwarding_headers(request.headers):
        return JSONResponse(
            status_code=403,
            content={
                "error": "FORWARDED_OWNER_REJECTED",
                "message": "Owner Access Mode rejects proxied or forwarded requests.",
            },
        )

    return JSONResponse(
        content={
            "configured": policy.configured,
            "authenticated": policy.is_owner,
            "owner_id": policy.owner_id,
            "unlimited_trials": policy.unlimited_trials,
            "machine_locked": policy.machine_locked,
            "boot_token_required": True,
        }
    )


@router.post("/login")
def owner_login(payload: OwnerLoginRequest, request: Request) -> Response:
    """
    Authenticates workstation owner using direct loopback socket verification, absence of
    forwarding headers, per-boot cryptographic token, hardware binding, and scrypt.
    """
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin owner authentication blocked.",
            },
        )

    client_host = request.client.host if request.client else None
    boot_token = request.headers.get(OWNER_TOKEN_HEADER) or payload.boot_token
    status_code, body, cookie_val = owner_security_manager.authenticate_owner(
        client_host=client_host,
        owner_id=payload.owner_id,
        password=payload.password,
        headers=request.headers,
        provided_boot_token=boot_token,
    )

    resp = JSONResponse(status_code=status_code, content=body)
    if status_code == 200 and cookie_val:
        resp.set_cookie(
            key=OWNER_COOKIE_NAME,
            value=cookie_val,
            httponly=True,
            samesite="strict",
            path="/",
            max_age=86400,
            secure=request.url.scheme == "https",
        )
    return resp


@router.post("/logout")
def owner_logout(request: Request) -> Response:
    """Terminates the active owner session by clearing the HttpOnly cookie."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin owner logout blocked.",
            },
        )
    client_host = request.client.host if request.client else None
    if not owner_security_manager.is_loopback(client_host):
        return JSONResponse(
            status_code=403,
            content={
                "error": "LOOPBACK_REQUIRED",
                "message": "Owner Access Mode is restricted to localhost callers.",
            },
        )
    if owner_security_manager.has_forwarding_headers(request.headers):
        return JSONResponse(
            status_code=403,
            content={
                "error": "FORWARDED_OWNER_REJECTED",
                "message": "Owner Access Mode rejects proxied or forwarded requests.",
            },
        )

    resp = JSONResponse(content={"success": True, "message": "Owner session cleared."})
    resp.delete_cookie(key=OWNER_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return resp
