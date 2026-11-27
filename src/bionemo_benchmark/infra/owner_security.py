"""
Agentic BioNeMo - Machine-Bound Localhost Owner Security Engine

Enforces hardware-locked, three-factor loopback authentication for workstation owners:
1. Raw socket peer IP strictly on loopback (127.0.0.1 / ::1 / localhost / testclient).
2. Zero proxy forwarding headers (X-Forwarded-For, Forwarded, X-Real-IP, CF-Connecting-IP).
3. Constant-time verified per-boot cryptographic owner token (secrets.token_urlsafe(32)),
   persisted with 0600 permissions outside repo or injected via BIONEMO_OWNER_BOOT_TOKEN.
4. MachineGuid SHA-256 hardware fingerprint lock and hashlib.scrypt credentials.
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
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

logger = logging.getLogger("OwnerSecurity")

OWNER_COOKIE_NAME = "bionemo_owner_session"
OWNER_TOKEN_HEADER = "X-Owner-Token"
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}
FORWARDING_HEADERS = frozenset(
    {
        "x-forwarded-for",
        "forwarded",
        "x-real-ip",
        "cf-connecting-ip",
    }
)


def get_machine_guid_fingerprint() -> str:
    """
    Retrieve the machine's hardware GUID and compute its SHA-256 fingerprint.
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
            logger.warning("Unable to read Windows MachineGuid: %s", exc)
    elif sys.platform.startswith("linux"):
        for mid_path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            if os.path.isfile(mid_path):
                try:
                    with open(mid_path, encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            return hashlib.sha256(content.encode("utf-8")).hexdigest()
                except Exception as exc:
                    logger.debug("Unable to read Linux machine-id at %s: %s", mid_path, exc)
    return ""


def get_owner_auth_path() -> Path:
    """Resolve external path for owner_auth.json."""
    override = os.environ.get("BIONEMO_OWNER_AUTH_PATH")
    if override:
        return Path(override).resolve()

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
        return (Path(local_app_data) / "bionemo-nim" / "owner_auth.json").resolve()

    return Path(os.path.expanduser("~/.config/bionemo-nim/owner_auth.json")).resolve()


def get_owner_boot_token_path() -> Path:
    """Resolve external path for the per-boot owner cryptographic token file."""
    override = os.environ.get("BIONEMO_OWNER_BOOT_TOKEN_PATH")
    if override:
        return Path(override).resolve()
    return get_owner_auth_path().parent / "owner_boot_token"


def apply_strict_file_acls(path: Path) -> None:
    """Lock file permissions strictly to the active user (chmod 0600 on POSIX, icacls on Windows)."""
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
                logger.warning("Failed to apply Windows icacls to %s: %s", path, exc)
    else:
        try:
            os.chmod(path, 0o600)
        except Exception as exc:
            logger.warning("Failed to apply chmod 0600 to %s: %s", path, exc)


def hash_password(password: str) -> tuple[str, str]:
    """Hash a password with hashlib.scrypt using a 16-byte random salt."""
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
    """Verify a password against stored scrypt salt and hash using hmac.compare_digest."""
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


def _boot_token_digest(boot_token: str) -> str:
    return hashlib.sha256(boot_token.encode("utf-8")).hexdigest()[:24]


def sign_session_token(
    owner_id: str,
    signing_key_hex: str,
    ttl_seconds: int = 86400,
    boot_token: str | None = None,
) -> str:
    """Sign an owner session token bound to owner_id and optional per-boot token digest."""
    exp = int(time.time()) + ttl_seconds
    payload_dict: dict[str, Any] = {
        "owner_id": owner_id,
        "exp": exp,
        "role": "owner",
        "unlimited_trials": True,
    }
    if boot_token:
        payload_dict["boot"] = _boot_token_digest(boot_token)
    raw_payload = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(raw_payload).decode("ascii").rstrip("=")
    key_bytes = bytes.fromhex(signing_key_hex)
    sig = hmac.new(key_bytes, payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_session_token(
    token: str, signing_key_hex: str, expected_boot_token: str | None = None
) -> tuple[bool, str | None]:
    """Verify HMAC signature, expiration, and current-boot binding of an owner session token."""
    try:
        if not token or "." not in token:
            return False, None
        payload_b64, sig = token.split(".", 1)
        key_bytes = bytes.fromhex(signing_key_hex)
        expected_sig = hmac.new(
            key_bytes, payload_b64.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False, None

        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        raw_payload = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        data = json.loads(raw_payload)

        if data.get("exp", 0) < time.time():
            return False, None
        if expected_boot_token:
            token_boot = str(data.get("boot", ""))
            expected_boot = _boot_token_digest(expected_boot_token)
            if not token_boot or not hmac.compare_digest(token_boot, expected_boot):
                return False, None
        return True, data.get("owner_id")
    except Exception:
        return False, None


class OwnerRateLimiter:
    """In-memory rate limiter enforcing a 60-second lockout after 5 consecutive failures."""

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
    """Coordinate loopback, zero-forwarding, per-boot token, and hardware validation."""

    def __init__(self) -> None:
        self.rate_limiter = OwnerRateLimiter()
        self._boot_lock = threading.Lock()
        self._boot_token = self._generate_and_persist_boot_token()

    def _generate_and_persist_boot_token(self) -> str:
        token = secrets.token_urlsafe(32)
        env_override = os.environ.get("BIONEMO_OWNER_BOOT_TOKEN", "").strip()
        if env_override and len(env_override) >= 32:
            token = env_override
        try:
            token_path = get_owner_boot_token_path()
            token_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = token_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(token)
            tmp_path.replace(token_path)
            if os.name != "nt":
                os.chmod(token_path, 0o600)
            else:
                apply_strict_file_acls(token_path)
        except Exception as exc:
            logger.debug("Could not persist owner boot token to disk: %s", exc)
        return token

    def get_boot_token(self) -> str:
        """Return active per-boot owner token (honoring non-empty >=32 char env override)."""
        env_override = os.environ.get("BIONEMO_OWNER_BOOT_TOKEN", "").strip()
        if env_override and len(env_override) >= 32:
            return env_override
        return self._boot_token

    def rotate_boot_token(self) -> str:
        """Rotate per-boot owner token (invalidates all prior owner cookies immediately)."""
        with self._boot_lock:
            self._boot_token = self._generate_and_persist_boot_token()
            return self._boot_token

    def verify_boot_token(self, provided_token: str | None) -> bool:
        """Verify provided per-boot token using constant-time hmac.compare_digest."""
        if not provided_token or not isinstance(provided_token, str):
            return False
        expected = self.get_boot_token()
        return hmac.compare_digest(provided_token.strip(), expected)

    @staticmethod
    def is_loopback(client_host: str | None) -> bool:
        if not client_host:
            return False
        return client_host in LOOPBACK_HOSTS

    @staticmethod
    def has_forwarding_headers(headers: Mapping[str, str] | None) -> bool:
        """Detect any proxy forwarding header indicating non-direct socket origin."""
        if not headers:
            return False
        return any(k.lower() in FORWARDING_HEADERS and str(v).strip() for k, v in headers.items())

    def is_direct_loopback(
        self, client_host: str | None, headers: Mapping[str, str] | None = None
    ) -> bool:
        """Require raw socket loopback AND complete absence of forwarding headers."""
        return self.is_loopback(client_host) and not self.has_forwarding_headers(headers)

    def load_owner_config(self) -> tuple[dict[str, Any] | None, bool]:
        """
        Load owner_auth.json and validate MachineGuid fingerprint.
        Returns (config_dict, is_machine_match). Fails closed on missing or mismatched state.
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
            logger.warning("Failed to load or verify owner configuration from %s: %s", path, exc)
            return None, False

    def authenticate_owner(
        self,
        client_host: str | None,
        owner_id: str,
        password: str,
        headers: Mapping[str, str] | None = None,
        provided_boot_token: str | None = None,
    ) -> tuple[int, dict[str, Any], str | None]:
        """
        Authenticate workstation owner requiring:
        (a) direct loopback socket IP,
        (b) zero proxy forwarding headers,
        (c) valid per-boot cryptographic token verified in constant time, and
        (d) hardware-locked scrypt credential verification.
        """
        if not self.is_loopback(client_host):
            return (
                403,
                {
                    "error": "LOOPBACK_REQUIRED",
                    "message": "Owner Access Mode is strictly localhost only.",
                },
                None,
            )

        if self.has_forwarding_headers(headers):
            return (
                403,
                {
                    "error": "FORWARDED_OWNER_REJECTED",
                    "message": "Owner Access Mode rejects proxied or forwarded requests.",
                },
                None,
            )

        rate_key = f"{client_host}:{owner_id}"
        is_locked, remaining_sec = self.rate_limiter.is_locked(rate_key)
        if is_locked:
            return (
                429,
                {
                    "error": "OWNER_LOCKOUT",
                    "message": f"Too many failed login attempts. Locked out for {remaining_sec} seconds.",
                    "retry_after": remaining_sec,
                },
                None,
            )

        if not self.verify_boot_token(provided_boot_token):
            locked, lockout_sec = self.rate_limiter.record_failure(rate_key)
            if locked:
                return (
                    429,
                    {
                        "error": "OWNER_LOCKOUT",
                        "message": f"Too many failed attempts. Locked out for {lockout_sec} seconds.",
                        "retry_after": lockout_sec,
                    },
                    None,
                )
            return (
                403,
                {
                    "error": "OWNER_TOKEN_REQUIRED",
                    "message": "Valid per-boot cryptographic owner token required.",
                },
                None,
            )

        config, machine_match = self.load_owner_config()
        if not config or not machine_match:
            return (
                403,
                {
                    "error": "OWNER_CONFIG_INVALID",
                    "message": "Owner authentication record missing or hardware MachineGuid mismatch.",
                },
                None,
            )

        expected_owner_id = config.get("owner_id", "")
        salt_hex = config.get("salt_hex", "")
        hash_hex = config.get("scrypt_hash_hex", "")
        signing_key_hex = config.get("signing_key_hex", "")

        id_match = hmac.compare_digest(owner_id.strip(), expected_owner_id.strip())
        pwd_match = verify_password(password, salt_hex, hash_hex)

        if not id_match or not pwd_match:
            locked, lockout_sec = self.rate_limiter.record_failure(rate_key)
            if locked:
                return (
                    429,
                    {
                        "error": "OWNER_LOCKOUT",
                        "message": f"Too many failed attempts. Locked out for {lockout_sec} seconds.",
                        "retry_after": lockout_sec,
                    },
                    None,
                )
            return (
                401,
                {"error": "INVALID_CREDENTIALS", "message": "Invalid Owner ID or password."},
                None,
            )

        self.rate_limiter.record_success(rate_key)
        cookie = sign_session_token(
            expected_owner_id, signing_key_hex, boot_token=self.get_boot_token()
        )
        return (
            200,
            {
                "success": True,
                "role": "owner",
                "owner_id": expected_owner_id,
                "unlimited_trials": True,
                "message": "Owner authentication successful. Unlimited trials activated.",
            },
            cookie,
        )

    def evaluate_request_policy(
        self,
        client_host: str | None,
        cookie_value: str | None,
        headers: Mapping[str, str] | None = None,
    ) -> OwnerPolicy:
        """
        Evaluate active owner privileges. Fails closed on non-loopback sockets,
        forwarding headers, missing config, mismatched hardware, or stale-boot cookies.
        """
        if not self.is_direct_loopback(client_host, headers):
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
        valid, owner_id = verify_session_token(
            cookie_value, signing_key_hex, expected_boot_token=self.get_boot_token()
        )
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
