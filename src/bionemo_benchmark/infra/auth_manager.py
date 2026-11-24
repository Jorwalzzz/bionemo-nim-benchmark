"""
Agentic BioNeMo - Researcher Authentication, Synchronized Daily Quotas & Feedback Engine.

Provides:
1. Per-user salted hashlib.scrypt password hashing and constant-time digest checks.
2. Tamper-proof HMAC-SHA256 session bearer tokens with per-user token_version revocation.
3. Synchronized 24-hour daily quota engine anchored strictly to 3:00 PM IST (09:30:00 UTC)
   with two-phase SQLite WAL reservation and compensating refund on upstream errors.
4. Canonical email normalization (including Gmail dot/+tag aliasing for quota fairness).
5. Persistent SQLite WAL storage with optional one-time migration from legacy JSON ledgers.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("AuthManager")

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

AUTH_LEDGER_PATH = os.environ.get(
    "AUTH_LEDGER_PATH", os.path.join(DATA_DIR, "users_auth.json")
)
FEEDBACK_LEDGER_PATH = os.environ.get(
    "FEEDBACK_LEDGER_PATH", os.path.join(DATA_DIR, "feedback_submissions.json")
)

FREE_TRIAL_DAILY_RUNS = int(os.environ.get("FREE_TRIAL_DAILY_RUNS", "5"))
RESET_OFFSET_SECONDS = 9 * 3600 + 30 * 60  # 34,200 seconds (09:30 UTC = 15:00 IST)
PASSWORD_SALT_BYTES = 16
SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64
MIN_AUTH_SECRET_BYTES = 32
DEFAULT_PBKDF2_ITERATIONS = int(os.environ.get("PBKDF2_ITERATIONS", "100_000"))

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "yopmail.com",
    "throwawaymail.com",
    "trashmail.com",
    "sharklasers.com",
    "getnada.com",
    "temp-mail.org",
    "dispostable.com",
    "fakeinbox.com",
    "mailnesia.com",
    "maildrop.cc",
    "mohmal.com",
    "generator.email",
    "inboxkitten.com",
    "burnermail.io",
}

COMMON_DOMAIN_TYPOS = {
    "gamil.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "yaho.com": "yahoo.com",
    "yahooo.com": "yahoo.com",
    "hotmial.com": "hotmail.com",
    "hotmaill.com": "hotmail.com",
    "outlok.com": "outlook.com",
    "outloo.com": "outlook.com",
    "protonmai.com": "protonmail.com",
    "protonmial.com": "protonmail.com",
}

# Disallow unsafe quote characters in local-part while permitting standard email tokens.
EMAIL_STRICT_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&*+/=?^_{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

VALID_FEEDBACK_CATEGORIES = frozenset(
    {
        "Lead Candidates",
        "ESMFold Structure",
        "ADMET & Druggability",
        "Retrosynthesis",
        "UI & Performance",
        "General Evaluation",
        "Scientific Accuracy",
        "Model Latency",
        "Bug Report",
        "Feature Request",
        "General",
    }
)


@dataclass(frozen=True)
class QuotaDecision:
    """Immutable decision object returned by atomic quota reservation operations."""

    allowed: bool
    quota_info: dict[str, Any]
    message: str
    reservation_id: str | None = None


def normalize_email(email: str) -> str:
    """Return lowercased trimmed email string."""
    return (email or "").strip().lower()


def canonicalize_email(email: str) -> str:
    """Canonicalize email identity (collapsing Gmail/Googlemail dot and +tag aliases)."""
    clean = normalize_email(email)
    if "@" not in clean:
        return clean
    local, domain = clean.split("@", 1)
    if domain in {"gmail.com", "googlemail.com"}:
        domain = "gmail.com"
        local = local.split("+", 1)[0].replace(".", "")
    return f"{local}@{domain}"


def validate_email_address(email: str) -> tuple[bool, str, str | None, str]:
    """
    Validate email format, domain extension checks, typo suggestions, and disposable domains.
    Returns (is_valid, message, typo_suggestion, classification).
    """
    if not email or not isinstance(email, str):
        return False, "Invalid email address format: Email cannot be empty.", None, "invalid"

    clean = email.strip()
    if len(clean) > 254:
        return False, "Invalid email address format: Exceeds 254 character maximum.", None, "invalid"

    if "@" not in clean:
        return False, "Invalid email address format: Missing '@' symbol.", None, "invalid"

    parts = clean.split("@")
    if len(parts) != 2:
        return False, "Invalid email address format: Contains multiple '@' symbols.", None, "invalid"

    local_part, domain_part = parts
    if not local_part:
        return False, "Invalid email address format: Missing recipient name before '@'.", None, "invalid"

    if not domain_part:
        return False, "Invalid email address format: Missing domain after '@'.", None, "invalid"

    if "." not in domain_part:
        return (
            False,
            f"Invalid email address format: Domain '@{domain_part}' missing extension (.com, .edu, .org).",
            None,
            "invalid",
        )

    tld = domain_part.split(".")[-1].lower()
    if len(tld) < 2 or not tld.isalpha():
        return (
            False,
            f"Invalid email address format: Extension '.{tld}' must be at least 2 letters.",
            None,
            "invalid",
        )

    if not EMAIL_STRICT_REGEX.match(clean):
        return False, "Invalid email address format.", None, "invalid"

    domain_lower = domain_part.lower()
    if domain_lower in DISPOSABLE_EMAIL_DOMAINS:
        return (
            False,
            f"Disposable temporary email domain '@{domain_lower}' is not permitted. Please use an institutional, academic, or primary email address.",
            None,
            "disposable",
        )

    if domain_lower in COMMON_DOMAIN_TYPOS:
        suggested = COMMON_DOMAIN_TYPOS[domain_lower]
        return (
            False,
            f"Possible typo in '@{domain_lower}'. Did you mean '@{suggested}'?",
            f"{local_part}@{suggested}",
            "typo",
        )

    is_academic = any(
        domain_lower.endswith(suf)
        for suf in (".edu", ".ac.uk", ".edu.cn", ".ac.in", ".res.in", ".org")
    )
    classification = "academic" if is_academic else "standard"
    return True, "Valid email address.", None, classification


def _apply_restricted_permissions(path: str | Path) -> None:
    """Restrict secret file permissions cleanly where supported by host OS."""
    target = str(path)
    if os.name != "nt":
        try:
            os.chmod(target, 0o600)
        except OSError as exc:
            logger.warning("Could not enforce 0600 permissions on %s: %s", target, exc)


def _get_or_create_auth_secret(data_dir: str | None = None) -> bytes:
    """
    Retrieve or initialize persistent HMAC secret key for auth tokens.
    Fails closed if AUTH_SECRET_KEY or persisted secret has fewer than 32 bytes.
    """
    env_val = os.environ.get("AUTH_SECRET_KEY")
    if env_val is not None:
        raw = env_val.encode("utf-8")
        if len(raw) < MIN_AUTH_SECRET_BYTES:
            raise RuntimeError(
                f"AUTH_SECRET_KEY must contain at least {MIN_AUTH_SECRET_BYTES} bytes of entropy."
            )
        return raw

    target_dir = data_dir or DATA_DIR
    os.makedirs(target_dir, exist_ok=True)
    secret_file = os.path.join(target_dir, ".auth_secret")
    if os.path.exists(secret_file):
        with open(secret_file, "rb") as f:
            key = f.read()
        # Accept either raw 32+ bytes or 64+ ASCII hex representation
        if len(key) < MIN_AUTH_SECRET_BYTES:
            raise RuntimeError(
                f"Persisted auth secret at {secret_file} has insufficient entropy (< {MIN_AUTH_SECRET_BYTES} bytes)."
            )
        return key

    key = secrets.token_bytes(MIN_AUTH_SECRET_BYTES)
    tmp_path = f"{secret_file}.tmp.{os.getpid()}"
    with open(tmp_path, "wb") as f:
        f.write(key)
    os.replace(tmp_path, secret_file)
    _apply_restricted_permissions(secret_file)
    return key


def _resolve_sqlite_path(ledger_path: str) -> Path:
    """Map JSON or DB ledger path cleanly onto a SQLite database file path."""
    p = Path(ledger_path)
    if p.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        return p
    return p.with_suffix(".db")


class AuthManager:
    """Thread-safe SQLite WAL authentication, quota reservation, and feedback manager."""

    def __init__(
        self,
        ledger_path: str = AUTH_LEDGER_PATH,
        feedback_path: str = FEEDBACK_LEDGER_PATH,
        daily_limit: int = FREE_TRIAL_DAILY_RUNS,
        iterations: int = DEFAULT_PBKDF2_ITERATIONS,
    ):
        self.ledger_path = ledger_path
        self.feedback_path = feedback_path
        self.db_path = _resolve_sqlite_path(ledger_path)
        self.daily_limit = daily_limit
        self.iterations = iterations
        secret_dir = str(self.db_path.parent) if ledger_path != AUTH_LEDGER_PATH else DATA_DIR
        self._secret = _get_or_create_auth_secret(secret_dir)
        self._lock = threading.RLock()
        self._failed_logins: dict[str, dict[str, Any]] = {}
        self._init_db()
        self._migrate_legacy_json()
        self._init_default_evaluator()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection configured for strict WAL concurrency and safe cleanup."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        canonical_email TEXT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        organization TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        hash_algo TEXT NOT NULL DEFAULT 'scrypt',
                        role TEXT NOT NULL DEFAULT 'researcher',
                        tier TEXT NOT NULL DEFAULT 'free_trial',
                        is_active INTEGER NOT NULL DEFAULT 1,
                        token_version INTEGER NOT NULL DEFAULT 1,
                        created_at INTEGER NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quota_usage (
                        canonical_key TEXT NOT NULL,
                        cycle_key TEXT NOT NULL,
                        runs_used INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (canonical_key, cycle_key)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quota_reservations (
                        reservation_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        canonical_key TEXT NOT NULL,
                        cycle_key TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at INTEGER NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS revoked_tokens (
                        sig TEXT PRIMARY KEY,
                        expires_at INTEGER NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feedback_submissions (
                        feedback_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        email TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        organization TEXT NOT NULL,
                        category TEXT NOT NULL,
                        rating INTEGER NOT NULL,
                        comments TEXT NOT NULL,
                        target_complex TEXT NOT NULL,
                        client_ip TEXT NOT NULL,
                        timestamp INTEGER NOT NULL
                    )
                    """
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            finally:
                conn.close()

    def _migrate_legacy_json(self) -> None:
        """One-time optional migration from legacy JSON user/feedback files if tables are empty."""
        with self._lock:
            conn = self._connect()
            try:
                user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                if (
                    user_count == 0
                    and self.ledger_path
                    and not self.ledger_path.endswith((".db", ".sqlite", ".sqlite3"))
                    and os.path.exists(self.ledger_path)
                ):
                    try:
                        with open(self.ledger_path, encoding="utf-8") as f:
                            legacy = json.load(f)
                        if isinstance(legacy, dict) and "users" in legacy:
                            conn.execute("BEGIN IMMEDIATE")
                            id_to_canonical: dict[str, str] = {}
                            for uid, u in legacy.get("users", {}).items():
                                email_norm = normalize_email(u.get("email", ""))
                                canon = canonicalize_email(email_norm)
                                if not email_norm or canon in id_to_canonical.values():
                                    continue
                                id_to_canonical[uid] = canon
                                p_hash = str(u.get("password_hash", ""))
                                algo = "scrypt" if len(p_hash) == SCRYPT_DKLEN * 2 else "pbkdf2_sha256"
                                conn.execute(
                                    """
                                    INSERT OR IGNORE INTO users (
                                        user_id, email, canonical_email, full_name, organization,
                                        salt, password_hash, hash_algo, role, tier, is_active,
                                        token_version, created_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        uid,
                                        email_norm,
                                        canon,
                                        u.get("full_name", "Researcher"),
                                        u.get("organization", "Independent Academic"),
                                        u.get("salt", ""),
                                        p_hash,
                                        algo,
                                        u.get("role", "researcher"),
                                        u.get("tier", "free_trial"),
                                        1 if u.get("is_active", True) else 0,
                                        int(u.get("token_version", 1)),
                                        int(u.get("created_at", int(time.time()))),
                                    ),
                                )
                            for usage_key, count in legacy.get("usage", {}).items():
                                if ":" in usage_key:
                                    uid, cycle_key = usage_key.split(":", 1)
                                    canon = id_to_canonical.get(uid, uid)
                                    conn.execute(
                                        """
                                        INSERT INTO quota_usage (canonical_key, cycle_key, runs_used)
                                        VALUES (?, ?, ?)
                                        ON CONFLICT(canonical_key, cycle_key)
                                        DO UPDATE SET runs_used = MAX(runs_used, excluded.runs_used)
                                        """,
                                        (canon, cycle_key, int(count)),
                                    )
                            for sig, exp in legacy.get("revoked_tokens", {}).items():
                                conn.execute(
                                    "INSERT OR IGNORE INTO revoked_tokens (sig, expires_at) VALUES (?, ?)",
                                    (sig, int(exp)),
                                )
                            conn.execute("COMMIT")
                    except Exception as exc:
                        try:
                            conn.execute("ROLLBACK")
                        except sqlite3.Error:
                            pass
                        logger.warning("Legacy auth JSON migration skipped: %s", exc)

                fb_count = conn.execute("SELECT COUNT(*) FROM feedback_submissions").fetchone()[0]
                if (
                    fb_count == 0
                    and self.feedback_path
                    and not self.feedback_path.endswith((".db", ".sqlite", ".sqlite3"))
                    and os.path.exists(self.feedback_path)
                ):
                    try:
                        with open(self.feedback_path, encoding="utf-8") as f:
                            fb_items = json.load(f)
                        if isinstance(fb_items, list):
                            conn.execute("BEGIN IMMEDIATE")
                            for item in fb_items:
                                if not isinstance(item, dict) or not item.get("feedback_id"):
                                    continue
                                conn.execute(
                                    """
                                    INSERT OR IGNORE INTO feedback_submissions (
                                        feedback_id, user_id, email, full_name, organization,
                                        category, rating, comments, target_complex, client_ip, timestamp
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        item["feedback_id"],
                                        item.get("user_id", ""),
                                        item.get("email", ""),
                                        item.get("full_name", "Researcher"),
                                        item.get("organization", "Independent"),
                                        item.get("category", "General"),
                                        int(item.get("rating", 5)),
                                        item.get("comments", ""),
                                        item.get("target_complex", "General"),
                                        item.get("client_ip", "Unknown"),
                                        int(item.get("timestamp", int(time.time()))),
                                    ),
                                )
                            conn.execute("COMMIT")
                    except Exception as exc:
                        try:
                            conn.execute("ROLLBACK")
                        except sqlite3.Error:
                            pass
                        logger.warning("Legacy feedback JSON migration skipped: %s", exc)
            finally:
                conn.close()

    def _init_default_evaluator(self) -> None:
        """Provision the default 1-click evaluator account if not already present."""
        evaluator_email = "evaluator@bionemo.org"
        canon = canonicalize_email(evaluator_email)
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT user_id FROM users WHERE canonical_email = ? OR email = ?",
                    (canon, evaluator_email),
                ).fetchone()
                if row is not None:
                    return
                salt = secrets.token_hex(PASSWORD_SALT_BYTES)
                pwd_hash = self._hash_password("DemoResearcher2026!", salt)
                now = int(time.time())
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """
                    INSERT OR IGNORE INTO users (
                        user_id, email, canonical_email, full_name, organization,
                        salt, password_hash, hash_algo, role, tier, is_active,
                        token_version, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "evaluator-demo-001",
                        evaluator_email,
                        canon,
                        "Academic Peer Evaluator",
                        "BioNeMo Review Committee",
                        salt,
                        pwd_hash,
                        "scrypt",
                        "evaluator",
                        "free_trial",
                        1,
                        1,
                        now,
                    ),
                )
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    # ─────────────────────────────────────────────────────────────
    # Cryptographic Password & Token Helpers
    # ─────────────────────────────────────────────────────────────

    def _hash_password(self, password: str, salt_hex: str) -> str:
        """Derive salted key using memory-hard hashlib.scrypt."""
        salt_bytes = bytes.fromhex(salt_hex)
        key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt_bytes,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            maxmem=0,
            dklen=SCRYPT_DKLEN,
        )
        return key.hex()

    def _verify_password_hash(
        self, password: str, salt_hex: str, stored_hash: str, algo: str
    ) -> bool:
        """Verify stored password hash in constant time."""
        try:
            salt_bytes = bytes.fromhex(salt_hex)
            if algo == "pbkdf2_sha256":
                computed = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt_bytes,
                    self.iterations,
                ).hex()
            else:
                computed = hashlib.scrypt(
                    password.encode("utf-8"),
                    salt=salt_bytes,
                    n=SCRYPT_N,
                    r=SCRYPT_R,
                    p=SCRYPT_P,
                    maxmem=0,
                    dklen=SCRYPT_DKLEN,
                ).hex()
            return hmac.compare_digest(computed, stored_hash)
        except Exception:
            return False

    def _create_token(
        self, user_id: str, token_version: int = 1, max_age_seconds: int = 86400 * 30
    ) -> str:
        """Create signed bearer token binding user_id, expiry, and token_version."""
        created = int(time.time())
        expires = created + max_age_seconds
        payload_raw = f"{user_id}:{created}:{expires}:{token_version}"
        payload_b64 = base64.urlsafe_b64encode(payload_raw.encode("utf-8")).decode("ascii")
        sig = hmac.new(
            self._secret, payload_b64.encode("ascii"), hashlib.sha256
        ).hexdigest()
        return f"{payload_b64}.{sig}"

    def create_token(self, user_id: str, max_age_seconds: int = 86400 * 30) -> str:
        """Create a signed session token stamped with the user's current token_version."""
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT token_version FROM users WHERE user_id = ? AND is_active = 1",
                    (user_id,),
                ).fetchone()
                version = int(row["token_version"]) if row else 1
            finally:
                conn.close()
        return self._create_token(user_id, token_version=version, max_age_seconds=max_age_seconds)

    def revoke_token(self, token: str | None) -> bool:
        """Revoke an active token by recording its signature and incrementing token_version."""
        if not token or not isinstance(token, str) or "." not in token:
            return False
        parts = token.strip().split(".")
        if len(parts) != 2:
            return False
        payload_b64, sig = parts
        expected_sig = hmac.new(
            self._secret, payload_b64.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False

        user_id: str | None = None
        expires = int(time.time()) + 86400 * 30
        try:
            payload_raw = base64.urlsafe_b64decode(payload_b64.encode("ascii")).decode("utf-8")
            segments = payload_raw.split(":")
            user_id = segments[0]
            if len(segments) >= 3:
                expires = int(segments[2])
        except Exception:
            pass

        with self._lock:
            conn = self._connect()
            try:
                now = int(time.time())
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM revoked_tokens WHERE expires_at <= ?", (now,))
                conn.execute(
                    "INSERT OR REPLACE INTO revoked_tokens (sig, expires_at) VALUES (?, ?)",
                    (sig, expires),
                )
                if user_id:
                    conn.execute(
                        "UPDATE users SET token_version = token_version + 1 WHERE user_id = ?",
                        (user_id,),
                    )
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()
        return True

    def revoke_user_sessions(self, user_id: str) -> int:
        """Increment token_version for user_id so all existing tokens fail immediately."""
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    "UPDATE users SET token_version = token_version + 1 WHERE user_id = ?",
                    (user_id,),
                )
                row = conn.execute(
                    "SELECT token_version FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                conn.execute("COMMIT")
                return int(row["token_version"]) if row else 0
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    def change_password(self, user_id: str, new_password: str) -> bool:
        """Update password using scrypt and increment token_version to revoke old sessions."""
        if not new_password or len(new_password) < 6:
            return False
        salt = secrets.token_hex(PASSWORD_SALT_BYTES)
        pwd_hash = self._hash_password(new_password, salt)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                cur = conn.execute(
                    """
                    UPDATE users
                    SET salt = ?, password_hash = ?, hash_algo = 'scrypt',
                        token_version = token_version + 1
                    WHERE user_id = ?
                    """,
                    (salt, pwd_hash, user_id),
                )
                conn.execute("COMMIT")
                return cur.rowcount > 0
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    def update_role(self, user_id: str, new_role: str) -> bool:
        """Update user role and increment token_version so prior claims expire immediately."""
        clean_role = (new_role or "researcher").strip().lower()
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                cur = conn.execute(
                    """
                    UPDATE users
                    SET role = ?, token_version = token_version + 1
                    WHERE user_id = ?
                    """,
                    (clean_role, user_id),
                )
                conn.execute("COMMIT")
                return cur.rowcount > 0
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    def verify_token(self, token: str | None) -> str | None:
        """Verify HMAC signature, revocation list, expiration, and per-user token_version."""
        if not token or not isinstance(token, str) or "." not in token:
            return None
        parts = token.strip().split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(
            self._secret, payload_b64.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        try:
            payload_raw = base64.urlsafe_b64decode(payload_b64.encode("ascii")).decode("utf-8")
            segments = payload_raw.split(":")
            if len(segments) != 4:
                return None
            user_id, _, expires_str, ver_str = segments
            expires = int(expires_str)
            token_ver = int(ver_str)
            if time.time() > expires:
                return None
        except Exception:
            return None

        with self._lock:
            conn = self._connect()
            try:
                revoked = conn.execute(
                    "SELECT 1 FROM revoked_tokens WHERE sig = ?", (sig,)
                ).fetchone()
                if revoked is not None:
                    return None
                row = conn.execute(
                    "SELECT token_version, is_active FROM users WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
                if row is None or int(row["is_active"]) != 1:
                    return None
                if int(row["token_version"]) != token_ver:
                    return None
                return user_id
            finally:
                conn.close()

    # ─────────────────────────────────────────────────────────────
    # Synchronized 3:00 PM IST (09:30 UTC) Cycle Calculation
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_cycle_info(timestamp: float | None = None) -> dict[str, Any]:
        """
        Calculate current 24-hour cycle anchored to 3:00:00 PM IST (09:30:00 UTC).
        All users worldwide refresh in sync at this exact moment.
        """
        t = timestamp if timestamp is not None else time.time()
        cycle_idx = int((t - RESET_OFFSET_SECONDS) // 86400)
        next_reset_epoch = (cycle_idx + 1) * 86400 + RESET_OFFSET_SECONDS
        seconds_remaining = max(0, int(next_reset_epoch - t))

        cycle_dt = datetime.datetime.fromtimestamp(
            cycle_idx * 86400 + RESET_OFFSET_SECONDS, datetime.UTC
        )
        cycle_key = cycle_dt.strftime("%Y-%m-%d_1500IST")

        ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        next_reset_ist = datetime.datetime.fromtimestamp(next_reset_epoch, ist_tz)
        formatted_ist = next_reset_ist.strftime("%Y-%m-%d %I:%M:%S %p IST")

        h = seconds_remaining // 3600
        m = (seconds_remaining % 3600) // 60
        s = seconds_remaining % 60
        countdown_str = f"{h:02d}:{m:02d}:{s:02d}"

        return {
            "cycle_key": cycle_key,
            "next_reset_epoch": next_reset_epoch,
            "seconds_remaining": seconds_remaining,
            "countdown": countdown_str,
            "next_reset_ist": formatted_ist,
            "reset_target": "3:00 PM IST",
        }

    # ─────────────────────────────────────────────────────────────
    # User Registration & Authentication
    # ─────────────────────────────────────────────────────────────

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str = "Researcher",
        organization: str = "Independent Academic",
    ) -> tuple[bool, dict[str, Any] | None, str]:
        """Register a new researcher account using normalized and canonicalized email checks."""
        email_clean = normalize_email(email)
        is_valid, msg, _, _ = validate_email_address(email_clean)
        if not is_valid:
            return False, None, msg
        if not password or len(password) < 6:
            return False, None, "Password must be at least 6 characters."

        canon = canonicalize_email(email_clean)
        user_id = f"user-{secrets.token_hex(8)}"
        salt = secrets.token_hex(PASSWORD_SALT_BYTES)
        pwd_hash = self._hash_password(password, salt)
        now = int(time.time())
        clean_name = full_name.strip() or "Researcher"
        clean_org = organization.strip() or "Independent Academic"

        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                existing = conn.execute(
                    "SELECT user_id FROM users WHERE email = ? OR canonical_email = ?",
                    (email_clean, canon),
                ).fetchone()
                if existing is not None:
                    conn.execute("ROLLBACK")
                    return False, None, "An account with this email already exists."

                conn.execute(
                    """
                    INSERT INTO users (
                        user_id, email, canonical_email, full_name, organization,
                        salt, password_hash, hash_algo, role, tier, is_active,
                        token_version, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        email_clean,
                        canon,
                        clean_name,
                        clean_org,
                        salt,
                        pwd_hash,
                        "scrypt",
                        "researcher",
                        "free_trial",
                        1,
                        1,
                        now,
                    ),
                )
                conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                return False, None, "An account with this email already exists."
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

        token = self._create_token(user_id, token_version=1)
        quota = self.get_user_quota(user_id)
        u_info = {
            "id": user_id,
            "user_id": user_id,
            "email": email_clean,
            "full_name": clean_name,
            "organization": clean_org,
            "role": "researcher",
            "hash_algo": "scrypt",
        }
        return (
            True,
            {
                **u_info,
                "user": u_info,
                "token": token,
                "quota": quota,
            },
            "Account created successfully.",
        )

    def authenticate_user(
        self, email: str, password: str
    ) -> tuple[bool, dict[str, Any] | None, str]:
        """Authenticate researcher credentials with constant-time checks and lockout defense."""
        email_key = normalize_email(email)
        canon = canonicalize_email(email_key)
        now = int(time.time())

        with self._lock:
            failure_record = self._failed_logins.get(canon)
            if failure_record:
                consecutive = failure_record.get("count", 0)
                last_failed = failure_record.get("last_attempt", 0)
                if consecutive >= 5:
                    if now - last_failed < 300:
                        retry_after = int(300 - (now - last_failed))
                        return (
                            False,
                            None,
                            f"Account temporarily locked due to too many failed login attempts. Retry in {retry_after}s.",
                        )
                    self._failed_logins.pop(canon, None)

            conn = self._connect()
            try:
                user = conn.execute(
                    """
                    SELECT user_id, email, canonical_email, full_name, organization,
                           salt, password_hash, hash_algo, role, is_active, token_version
                    FROM users WHERE email = ? OR canonical_email = ?
                    """,
                    (email_key, canon),
                ).fetchone()
            finally:
                conn.close()

            if user is None or int(user["is_active"]) != 1:
                # Equalize scrypt work against user enumeration timing side-channels
                self._verify_password_hash(password, "00" * PASSWORD_SALT_BYTES, "00" * SCRYPT_DKLEN, "scrypt")
                self._record_failed_login(canon, now)
                return False, None, "Invalid email or password."

            if not self._verify_password_hash(
                password, user["salt"], user["password_hash"], user["hash_algo"]
            ):
                self._record_failed_login(canon, now)
                return False, None, "Invalid email or password."

            # Transparently upgrade legacy PBKDF2 hash to scrypt on login
            if user["hash_algo"] != "scrypt":
                new_salt = secrets.token_hex(PASSWORD_SALT_BYTES)
                new_hash = self._hash_password(password, new_salt)
                conn = self._connect()
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute(
                        "UPDATE users SET salt = ?, password_hash = ?, hash_algo = 'scrypt' WHERE user_id = ?",
                        (new_salt, new_hash, user["user_id"]),
                    )
                    conn.execute("COMMIT")
                finally:
                    conn.close()

            self._failed_logins.pop(canon, None)

        token = self._create_token(
            user["user_id"], token_version=int(user["token_version"])
        )
        quota = self.get_user_quota(user["user_id"])
        u_info = {
            "id": user["user_id"],
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "organization": user["organization"],
            "role": user["role"],
        }
        return (
            True,
            {
                **u_info,
                "user": u_info,
                "token": token,
                "quota": quota,
            },
            "Authentication successful.",
        )

    def _record_failed_login(self, canonical_key: str, now: int) -> None:
        """Record a failed login attempt for account lockout tracking."""
        rec = self._failed_logins.setdefault(canonical_key, {"count": 0, "last_attempt": now})
        rec["count"] += 1
        rec["last_attempt"] = now

    def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve user profile by user_id."""
        with self._lock:
            conn = self._connect()
            try:
                user = conn.execute(
                    """
                    SELECT user_id, email, full_name, organization, role, tier, created_at
                    FROM users WHERE user_id = ? AND is_active = 1
                    """,
                    (user_id,),
                ).fetchone()
            finally:
                conn.close()
        if user is None:
            return None
        return {
            "id": user["user_id"],
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "organization": user["organization"],
            "role": user["role"],
            "tier": user["tier"],
            "created_at": user["created_at"],
        }

    # ─────────────────────────────────────────────────────────────
    # Two-Phase Synchronized Quota Reservation & Refund Engine
    # ─────────────────────────────────────────────────────────────

    def _canonical_quota_key(self, conn: sqlite3.Connection, user_id: str) -> str:
        row = conn.execute(
            "SELECT canonical_email FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return str(row["canonical_email"]) if row else user_id

    def _build_quota_dict(
        self, runs_used: int, cycle_info: dict[str, Any]
    ) -> dict[str, Any]:
        runs_remaining = max(0, self.daily_limit - runs_used)
        return {
            "allowed": runs_used < self.daily_limit,
            "runs_used": runs_used,
            "runs_remaining": runs_remaining,
            "daily_limit": self.daily_limit,
            "seconds_remaining": cycle_info["seconds_remaining"],
            "countdown": cycle_info["countdown"],
            "next_reset_ist": cycle_info["next_reset_ist"],
            "reset_target": "3:00 PM IST",
            "cycle_key": cycle_info["cycle_key"],
        }

    def get_user_quota(
        self, user_id: str, timestamp: float | None = None
    ) -> dict[str, Any]:
        """Return remaining runs and countdown to 3:00 PM IST for given user."""
        cycle_info = self.get_cycle_info(timestamp)
        cycle_key = cycle_info["cycle_key"]
        with self._lock:
            conn = self._connect()
            try:
                canon_key = self._canonical_quota_key(conn, user_id)
                row = conn.execute(
                    "SELECT runs_used FROM quota_usage WHERE canonical_key = ? AND cycle_key = ?",
                    (canon_key, cycle_key),
                ).fetchone()
                runs_used = int(row["runs_used"]) if row else 0
            finally:
                conn.close()
        return self._build_quota_dict(runs_used, cycle_info)

    def consume_run(
        self, user_id: str, timestamp: float | None = None
    ) -> QuotaDecision:
        """
        Atomically reserve 1 discovery run using SQLite BEGIN IMMEDIATE.
        Returns QuotaDecision(allowed, quota_info, message, reservation_id).
        """
        cycle_info = self.get_cycle_info(timestamp)
        cycle_key = cycle_info["cycle_key"]
        reservation_id = f"res-{secrets.token_hex(12)}"
        now = int(time.time())

        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                canon_key = self._canonical_quota_key(conn, user_id)
                row = conn.execute(
                    "SELECT runs_used FROM quota_usage WHERE canonical_key = ? AND cycle_key = ?",
                    (canon_key, cycle_key),
                ).fetchone()
                current_runs = int(row["runs_used"]) if row else 0

                if current_runs >= self.daily_limit:
                    conn.execute("ROLLBACK")
                    return QuotaDecision(
                        allowed=False,
                        quota_info=self._build_quota_dict(current_runs, cycle_info),
                        message=(
                            f"Daily free quota reached ({self.daily_limit}/{self.daily_limit} runs used). "
                            f"All quotas reset at 3:00 PM IST in {cycle_info['countdown']}."
                        ),
                        reservation_id=None,
                    )

                new_runs = current_runs + 1
                conn.execute(
                    """
                    INSERT INTO quota_usage (canonical_key, cycle_key, runs_used)
                    VALUES (?, ?, ?)
                    ON CONFLICT(canonical_key, cycle_key)
                    DO UPDATE SET runs_used = excluded.runs_used
                    """,
                    (canon_key, cycle_key, new_runs),
                )
                conn.execute(
                    """
                    INSERT INTO quota_reservations (
                        reservation_id, user_id, canonical_key, cycle_key, status, created_at
                    ) VALUES (?, ?, ?, ?, 'RESERVED', ?)
                    """,
                    (reservation_id, user_id, canon_key, cycle_key, now),
                )
                conn.execute("COMMIT")
                return QuotaDecision(
                    allowed=True,
                    quota_info=self._build_quota_dict(new_runs, cycle_info),
                    message="Trial run authorized.",
                    reservation_id=reservation_id,
                )
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    def refund_run(self, reservation_id: str | None) -> bool:
        """
        Compensating transaction restoring 1 quota run when an upstream NIM fails/times out.
        Strictly idempotent per reservation_id.
        """
        if not reservation_id:
            return False
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT canonical_key, cycle_key, status FROM quota_reservations WHERE reservation_id = ?",
                    (reservation_id,),
                ).fetchone()
                if row is None or row["status"] != "RESERVED":
                    conn.execute("ROLLBACK")
                    return False

                conn.execute(
                    "UPDATE quota_reservations SET status = 'REFUNDED' WHERE reservation_id = ?",
                    (reservation_id,),
                )
                conn.execute(
                    """
                    UPDATE quota_usage
                    SET runs_used = MAX(0, runs_used - 1)
                    WHERE canonical_key = ? AND cycle_key = ?
                    """,
                    (row["canonical_key"], row["cycle_key"]),
                )
                conn.execute("COMMIT")
                return True
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    def commit_run(self, reservation_id: str | None) -> bool:
        """Finalize a reserved run after upstream completion (idempotent)."""
        if not reservation_id:
            return False
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                cur = conn.execute(
                    """
                    UPDATE quota_reservations
                    SET status = 'COMMITTED'
                    WHERE reservation_id = ? AND status = 'RESERVED'
                    """,
                    (reservation_id,),
                )
                conn.execute("COMMIT")
                return cur.rowcount > 0
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    # ─────────────────────────────────────────────────────────────
    # Authenticated Researcher Feedback System
    # ─────────────────────────────────────────────────────────────

    def submit_feedback(
        self,
        user_id: str,
        category: str,
        rating: int,
        comments: str,
        target_complex: str = "General",
        client_ip: str = "Unknown",
    ) -> tuple[bool, dict[str, Any], str]:
        """Validate, sanitize, and persist authenticated researcher feedback in SQLite WAL."""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False, {}, "User profile not found."

        category_clean = (category or "").strip()
        if category_clean not in VALID_FEEDBACK_CATEGORIES:
            category_clean = "General"

        rating_clean = max(1, min(5, int(rating))) if rating else 5
        comments_clean = (comments or "").strip()
        if not comments_clean:
            return False, {}, "Feedback comments cannot be empty."

        if len(comments_clean) > 2000:
            comments_clean = comments_clean[:2000]

        feedback_id = f"fb-{secrets.token_hex(6)}"
        now = int(time.time())
        clean_target = (target_complex or "").strip() or "General"
        entry = {
            "id": feedback_id,
            "feedback_id": feedback_id,
            "timestamp": now,
            "user_id": user_id,
            "email": profile["email"],
            "full_name": profile["full_name"],
            "organization": profile["organization"],
            "category": category_clean,
            "rating": rating_clean,
            "comments": comments_clean,
            "target_complex": clean_target,
            "client_ip": client_ip,
        }

        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """
                    INSERT INTO feedback_submissions (
                        feedback_id, user_id, email, full_name, organization,
                        category, rating, comments, target_complex, client_ip, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback_id,
                        user_id,
                        profile["email"],
                        profile["full_name"],
                        profile["organization"],
                        category_clean,
                        rating_clean,
                        comments_clean,
                        clean_target,
                        client_ip,
                        now,
                    ),
                )
                conn.execute("COMMIT")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                return False, {}, f"Failed to record feedback: {exc}"
            finally:
                conn.close()

        return True, entry, "Thank you! Your feedback has been recorded."

    def get_feedback_for_user(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieve feedback history for a given researcher."""
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT feedback_id, user_id, email, full_name, organization,
                           category, rating, comments, target_complex, client_ip, timestamp
                    FROM feedback_submissions
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    """,
                    (user_id,),
                ).fetchall()
            finally:
                conn.close()

        return [
            {
                "id": row["feedback_id"],
                "feedback_id": row["feedback_id"],
                "timestamp": row["timestamp"],
                "user_id": row["user_id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "organization": row["organization"],
                "category": row["category"],
                "rating": row["rating"],
                "comments": row["comments"],
                "target_complex": row["target_complex"],
                "client_ip": row["client_ip"],
            }
            for row in rows
        ]
