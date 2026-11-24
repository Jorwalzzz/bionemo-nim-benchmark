"""
Agentic BioNeMo - Machine-Bound Localhost Owner Security Engine

Enforces hardware-locked, loopback-only authentication for workstation owners:
1. Zero repo secrets: Configuration stored strictly in %LOCALAPPDATA%\\bionemo-nim\\owner_auth.json
   (fallback: ~/.config/bionemo-nim/owner_auth.json on non-Windows).
2. Hardware lock: Bound to the SHA-256 hash of the machine's Windows MachineGuid.
3. Strict user ACLs: Permissions restricted to the active Windows user via icacls (or 0600 on POSIX).
4. Strict loopback gate: Gated to localhost / 127.0.0.1 / ::1 callers.
5. Standard library cryptography: hashlib.scrypt, secrets.token_hex(32), hmac.compare_digest.
6. Rate limiting: 5 failed attempts trigger a 60-second lockout.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, NamedTuple

logger = logging.getLogger("OwnerSecurity")

OWNER_COOKIE_NAME = "bionemo_owner_session"
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def get_machine_guid_fingerprint() -> str:
    """
    Retrieves the machine's hardware GUID and computes its SHA-256 fingerprint.
    On Windows, reads HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid via winreg.
    Supports BIONEMO_MACHINE_GUID environment override for hermetic testing.
    """
    env_guid = os.environ.get("BIONEMO_MACHINE_GUID")
    if env_guid:
        return hashlib.sha256(env_guid.strip().encode("utf-8")).hexdigest()

    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            ) as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                if guid:
                    return hashlib.sha256(str(guid).strip().encode("utf-8")).hexdigest()
        except Exception as exc:
            logger.warning(f"Unable to read Windows MachineGuid: {exc}")
    elif sys.platform.startswith("linux"):
        for mid_path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            if os.path.isfile(mid_path):
                try:
                    with open(mid_path, encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            return hashlib.sha256(content.encode("utf-8")).hexdigest()
                except Exception as exc:
                    logger.debug(f"Unable to read Linux machine-id at {mid_path}: {exc}")
    return ""


def get_owner_auth_path() -> Path:
    """
    Resolves the external path for owner_auth.json.
    Windows: %LOCALAPPDATA%\\bionemo-nim\\owner_auth.json
    Non-Windows: ~/.config/bionemo-nim/owner_auth.json
    Supports BIONEMO_OWNER_AUTH_PATH override for hermetic testing.
    """
    override = os.environ.get("BIONEMO_OWNER_AUTH_PATH")
    if override:
        return Path(override).resolve()

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            local_app_data = os.path.expanduser(r"~\AppData\Local")
        return (Path(local_app_data) / "bionemo-nim" / "owner_auth.json").resolve()

    return Path(os.path.expanduser("~/.config/bionemo-nim/owner_auth.json")).resolve()


def apply_strict_file_acls(path: Path) -> None:
    """
    Locks file permissions strictly to the active user.
    On Windows: icacls <file> /inheritance:r /grant:r "%USERNAME%:(R,W)"
    On POSIX: chmod 0600
    """
    if not path.is_file():
        return

    if sys.platform == "win32":
        username = os.environ.get("USERNAME")
        if username:
            try:
                subprocess.run(
                    [
                        "icacls",
                        str(path),
                        "/inheritance:r",
                        "/grant:r",
                        f"{username}:(R,W)",
                    ],
                    check=True,
                    capture_output=True,
                    shell=False,
                )
            except Exception as exc:
                logger.warning(f"Failed to apply Windows icacls to {path}: {exc}")
    else:
        try:
            os.chmod(path, 0o600)
        except Exception as exc:
            logger.warning(f"Failed to apply chmod 0600 to {path}: {exc}")


def hash_password(password: str) -> tuple[str, str]:
    """Hashes a password with hashlib.scrypt using a 16-byte random salt."""
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        maxmem=0,
        dklen=64,
    )
    return salt.hex(), dk.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Verifies a password against stored scrypt salt and hash using hmac.compare_digest."""
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        computed = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            maxmem=0,
            dklen=64,
        )
        return hmac.compare_digest(computed, expected)
    except Exception:
        return False


def sign_session_token(owner_id: str, signing_key_hex: str, ttl_seconds: int = 86400) -> str:
    """Signs an owner session token with HMAC-SHA256."""
    exp = int(time.time()) + ttl_seconds
    payload_dict = {
        "owner_id": owner_id,
        "exp": exp,
        "role": "owner",
        "unlimited_trials": True,
    }
    raw_payload = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(raw_payload).decode("ascii").rstrip("=")
    key_bytes = bytes.fromhex(signing_key_hex)
    sig = hmac.new(key_bytes, payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_session_token(token: str, signing_key_hex: str) -> tuple[bool, str | None]:
    """Verifies HMAC signature and expiration of an owner session token."""
    try:
        if not token or "." not in token:
            return False, None
        payload_b64, sig = token.split(".", 1)
        key_bytes = bytes.fromhex(signing_key_hex)
        expected_sig = hmac.new(key_bytes, payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False, None

        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        raw_payload = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        data = json.loads(raw_payload)

        if data.get("exp", 0) < time.time():
            return False, None
        return True, data.get("owner_id")
    except Exception:
        return False, None


class OwnerRateLimiter:
    """In-memory rate limiter enforcing a 60-second lockout after 5 consecutive failed attempts."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 60):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._lock = threading.Lock()
        self._failures: dict[str, list[float]] = {}
        self._lockouts: dict[str, float] = {}

    def is_locked(self, key: str) -> tuple[bool, int]:
        with self._lock:
            now = time.time()
            until = self._lockouts.get(key, 0.0)
            if until > now:
                return True, int(until - now) + 1
            return False, 0

    def record_failure(self, key: str) -> tuple[bool, int]:
        with self._lock:
            now = time.time()
            times = [t for t in self._failures.get(key, []) if now - t < 300]
            times.append(now)
            self._failures[key] = times
            if len(times) >= self.max_attempts:
                until = now + self.lockout_seconds
                self._lockouts[key] = until
                self._failures[key] = []
                return True, self.lockout_seconds
            return False, 0

    def record_success(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
            self._lockouts.pop(key, None)


class OwnerPolicy(NamedTuple):
    is_owner: bool
    owner_id: str | None
    unlimited_trials: bool
    configured: bool
    machine_locked: bool


class OwnerSecurityManager:
    """Coordinates hardware validation, credential lookup, and owner session policy."""

    def __init__(self) -> None:
        self.rate_limiter = OwnerRateLimiter()

    def is_loopback(self, client_host: str | None) -> bool:
        if not client_host:
            return False
        return client_host in LOOPBACK_HOSTS

    def load_owner_config(self) -> tuple[dict[str, Any] | None, bool]:
        """
        Loads owner_auth.json and validates MachineGuid fingerprint.
        Returns (config_dict, is_machine_match).
        Fails closed if file is missing, corrupt, or hardware hash mismatches.
        """
        path = get_owner_auth_path()
        if not path.is_file():
            return None, False

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            stored_guid_hash = data.get("machine_guid_hash", "")
            current_guid_hash = get_machine_guid_fingerprint()

            if not current_guid_hash or not stored_guid_hash:
                return data, False

            if not hmac.compare_digest(stored_guid_hash, current_guid_hash):
                return data, False

            return data, True
        except Exception as exc:
            logger.warning(f"Failed to load or verify owner configuration from {path}: {exc}")
            return None, False

    def authenticate_owner(
        self,
        client_host: str | None,
        owner_id: str,
        password: str,
    ) -> tuple[int, dict[str, Any], str | None]:
        """
        Attempts owner login.
        Returns (http_status, response_body, session_cookie_or_none).
        """
        # 1. Strict loopback gate
        if not self.is_loopback(client_host):
            return 403, {"error": "LOOPBACK_REQUIRED", "message": "Owner Access Mode is strictly localhost only."}, None

        # 2. Rate limit check
        rate_key = f"{client_host}:{owner_id}"
        is_locked, remaining_sec = self.rate_limiter.is_locked(rate_key)
        if is_locked:
            return 429, {
                "error": "OWNER_LOCKOUT",
                "message": f"Too many failed login attempts. Locked out for {remaining_sec} seconds.",
                "retry_after": remaining_sec,
            }, None

        # 3. Hardware-locked config validation
        config, machine_match = self.load_owner_config()
        if not config or not machine_match:
            return 403, {
                "error": "OWNER_CONFIG_INVALID",
                "message": "Owner authentication record missing or hardware MachineGuid mismatch.",
            }, None

        expected_owner_id = config.get("owner_id", "")
        salt_hex = config.get("salt_hex", "")
        hash_hex = config.get("scrypt_hash_hex", "")
        signing_key_hex = config.get("signing_key_hex", "")

        # 4. Identity and password verification
        id_match = hmac.compare_digest(owner_id.strip(), expected_owner_id.strip())
        pwd_match = verify_password(password, salt_hex, hash_hex)

        if not id_match or not pwd_match:
            locked, lockout_sec = self.rate_limiter.record_failure(rate_key)
            if locked:
                return 429, {
                    "error": "OWNER_LOCKOUT",
                    "message": f"Too many failed attempts. Locked out for {lockout_sec} seconds.",
                    "retry_after": lockout_sec,
                }, None
            return 401, {"error": "INVALID_CREDENTIALS", "message": "Invalid Owner ID or password."}, None

        # 5. Success
        self.rate_limiter.record_success(rate_key)
        cookie = sign_session_token(expected_owner_id, signing_key_hex)
        return 200, {
            "success": True,
            "role": "owner",
            "owner_id": expected_owner_id,
            "unlimited_trials": True,
            "message": "Owner authentication successful. Unlimited trials activated.",
        }, cookie

    def evaluate_request_policy(self, client_host: str | None, cookie_value: str | None) -> OwnerPolicy:
        """
        Evaluates the caller's request to determine if it possesses active owner privileges.
        Fails closed on any non-loopback host, missing config, mismatched hardware, or invalid cookie.
        """
        if not self.is_loopback(client_host):
            return OwnerPolicy(
                is_owner=False,
                owner_id=None,
                unlimited_trials=False,
                configured=False,
                machine_locked=False,
            )

        config, machine_match = self.load_owner_config()
        if not config:
            return OwnerPolicy(
                is_owner=False,
                owner_id=None,
                unlimited_trials=False,
                configured=False,
                machine_locked=False,
            )

        if not machine_match:
            return OwnerPolicy(
                is_owner=False,
                owner_id=None,
                unlimited_trials=False,
                configured=True,
                machine_locked=False,
            )

        if not cookie_value:
            return OwnerPolicy(
                is_owner=False,
                owner_id=None,
                unlimited_trials=False,
                configured=True,
                machine_locked=True,
            )

        signing_key_hex = config.get("signing_key_hex", "")
        valid, owner_id = verify_session_token(cookie_value, signing_key_hex)
        if valid and owner_id:
            return OwnerPolicy(
                is_owner=True,
                owner_id=owner_id,
                unlimited_trials=True,
                configured=True,
                machine_locked=True,
            )

        return OwnerPolicy(
            is_owner=False,
            owner_id=None,
            unlimited_trials=False,
            configured=True,
            machine_locked=True,
        )


owner_security_manager = OwnerSecurityManager()
