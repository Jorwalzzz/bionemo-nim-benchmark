"""
FastAPI route handlers and dependency injection for Machine-Bound Localhost Owner Access Mode.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from bionemo_benchmark.infra.owner_security import (
    OWNER_COOKIE_NAME,
    OwnerPolicy,
    owner_security_manager,
)

logger = logging.getLogger("OwnerRoutes")
router: APIRouter = APIRouter(prefix="/api/owner", tags=["Owner Access"])


class OwnerLoginRequest(BaseModel):
    owner_id: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


def get_trial_policy(request: Request) -> OwnerPolicy:
    """
    FastAPI dependency resolving the active owner authorization policy.
    Checks loopback origin, hardware MachineGuid fingerprint, and HMAC session cookie.
    """
    client_host = request.client.host if request.client else None
    cookie_value = request.cookies.get(OWNER_COOKIE_NAME)
    return owner_security_manager.evaluate_request_policy(client_host, cookie_value)


@router.get("/status")
def get_owner_status(
    request: Request,
    policy: OwnerPolicy = Depends(get_trial_policy),
) -> Response:
    """
    Reports the owner authentication status.
    Fails closed with 403 Forbidden if called from any non-loopback host.
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

    return JSONResponse(
        content={
            "configured": policy.configured,
            "authenticated": policy.is_owner,
            "owner_id": policy.owner_id,
            "unlimited_trials": policy.unlimited_trials,
            "machine_locked": policy.machine_locked,
        }
    )


@router.post("/login")
def owner_login(payload: OwnerLoginRequest, request: Request) -> Response:
    """
    Authenticates the workstation owner using scrypt password verification and hardware binding.
    Sets an HttpOnly, SameSite=Strict HMAC session cookie on success.
    """
    client_host = request.client.host if request.client else None
    status_code, body, cookie_val = owner_security_manager.authenticate_owner(
        client_host=client_host,
        owner_id=payload.owner_id,
        password=payload.password,
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
    client_host = request.client.host if request.client else None
    if not owner_security_manager.is_loopback(client_host):
        return JSONResponse(
            status_code=403,
            content={
                "error": "LOOPBACK_REQUIRED",
                "message": "Owner Access Mode is restricted to localhost callers.",
            },
        )

    resp = JSONResponse(content={"success": True, "message": "Owner session cleared."})
    resp.delete_cookie(key=OWNER_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return resp
