"""
Agentic BioNeMo - Enterprise Anti-Bypass Trial Rate Limiter & Fingerprinting Engine

Provides:
1. Run limits per device / session / IP / /24 subnet backed by SQLite WAL.
2. Global Daily Circuit Breaker across anonymous trial runs.
3. Rightmost untrusted-hop IP extraction bounded strictly by TRUSTED_PROXY_CIDRS.
4. Cryptographically signed HMAC-SHA256 HttpOnly session cookies (>=32-byte key fail-closed).
5. High-entropy client fingerprint hashing and bot User-Agent shield.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("TrialLimiter")

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

LEDGER_PATH = os.environ.get(
    "TRIAL_LEDGER_PATH", os.path.join(DATA_DIR, "trial_ledger.json")
)
SECRET_KEY_PATH = os.path.join(DATA_DIR, ".trial_secret")
MIN_SECRET_BYTES = 32
MAX_TRIAL_RUNS = int(os.environ.get("MAX_TRIAL_RUNS", "2"))
MAX_SUBNET_RUNS = int(os.environ.get("MAX_SUBNET_RUNS", "4"))
MAX_GLOBAL_DAILY_RUNS = int(os.environ.get("MAX_GLOBAL_DAILY_RUNS", "25"))

MAX_TARGET_CHARS = int(os.environ.get("MAX_TARGET_CHARS", "1500"))
MAX_POCKET_RESIDUES = int(os.environ.get("MAX_POCKET_RESIDUES", "30"))

BLOCKED_USER_AGENTS = (
    "curl",
    "python-requests",
    "aiohttp",
    "wget",
    "httpie",
    "postmanruntime",
    "scrapy",
    "go-http-client",
    "apache-httpclient",
)


def parse_trusted_proxy_cidrs() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse explicit comma-separated CIDRs from TRUSTED_PROXY_CIDRS env variable."""
    raw = os.environ.get("TRUSTED_PROXY_CIDRS", "").strip()
    if not raw:
        return []
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for entry in raw.split(","):
        token = entry.strip()
        if not token:
            continue
        try:
            networks.append(ipaddress.ip_network(token, strict=False))
        except ValueError:
            logger.warning("Ignoring invalid CIDR entry in TRUSTED_PROXY_CIDRS: %s", token)
    return networks


def _ip_in_networks(
    ip_str: str, networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]
) -> bool:
    if not networks:
        return False
    try:
        addr = ipaddress.ip_address(ip_str.strip())
    except ValueError:
        return False
    return any(addr in net for net in networks)


def extract_client_ip(peer_ip: str | None, forwarded_for: str | None = None) -> str:
    """
    Extract client IP safely: use peer socket host directly unless it matches an explicit
    TRUSTED_PROXY_CIDRS entry, in which case walk X-Forwarded-For right-to-left and pick
    the rightmost valid hop outside TRUSTED_PROXY_CIDRS (never trusting leftmost spoofed hops).
    """
    clean_peer = (peer_ip or "127.0.0.1").strip() or "127.0.0.1"
    trusted = parse_trusted_proxy_cidrs()
    if not trusted or not _ip_in_networks(clean_peer, trusted) or not forwarded_for:
        return clean_peer

    hops = [h.strip() for h in forwarded_for.split(",") if h.strip()]
    for hop in reversed(hops):
        try:
            addr = ipaddress.ip_address(hop)
        except ValueError:
            return clean_peer
        if not any(addr in net for net in trusted):
            return str(addr)
    return clean_peer


def _get_or_create_secret_key(data_dir: str | None = None) -> bytes:
    """
    Retrieve or initialize persistent HMAC secret key for trial tokens.
    Fails closed if TRIAL_SECRET_KEY or persisted secret has fewer than 32 bytes.
    """
    env_key = os.environ.get("TRIAL_SECRET_KEY")
    if env_key is not None:
        raw = env_key.encode("utf-8")
        if len(raw) < MIN_SECRET_BYTES:
            raise RuntimeError(
                f"TRIAL_SECRET_KEY must contain at least {MIN_SECRET_BYTES} bytes of entropy."
            )
        return raw

    target_file = os.path.join(data_dir, ".trial_secret") if data_dir else SECRET_KEY_PATH
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    if os.path.exists(target_file):
        with open(target_file, "rb") as f:
            key = f.read()
        if len(key) < MIN_SECRET_BYTES:
            raise RuntimeError(
                f"Persisted trial secret at {target_file} has insufficient entropy (< {MIN_SECRET_BYTES} bytes)."
            )
        return key

    key = secrets.token_bytes(MIN_SECRET_BYTES)
    tmp_path = f"{target_file}.tmp.{os.getpid()}"
    with open(tmp_path, "wb") as f:
        f.write(key)
    os.replace(tmp_path, target_file)
    if os.name != "nt":
        try:
            os.chmod(target_file, 0o600)
        except OSError:
            pass
    return key


def _resolve_sqlite_path(ledger_path: str) -> Path:
    p = Path(ledger_path)
    if p.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        return p
    return p.with_suffix(".db")


class TrialLimiter:
    """Thread-safe trial rate limiter backed by SQLite WAL with global circuit breaker."""

    def __init__(
        self,
        ledger_path: str = LEDGER_PATH,
        max_runs: int = MAX_TRIAL_RUNS,
        max_subnet_runs: int = MAX_SUBNET_RUNS,
        max_global_daily_runs: int = MAX_GLOBAL_DAILY_RUNS,
    ):
        self.ledger_path = ledger_path
        self.db_path = _resolve_sqlite_path(ledger_path)
        self.max_runs = max_runs
        self.max_subnet_runs = max_subnet_runs
        self.max_global_daily_runs = max_global_daily_runs
        secret_dir = str(self.db_path.parent) if ledger_path != LEDGER_PATH else None
        self._secret_key = _get_or_create_secret_key(secret_dir)
        self._lock = threading.Lock()
        self._init_db()
        self._migrate_legacy_json()

    def _connect(self) -> sqlite3.Connection:
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
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS daily_usage (
                        day_key TEXT PRIMARY KEY,
                        runs_used INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trial_sessions (
                        session_id TEXT PRIMARY KEY,
                        runs INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        last_used TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trial_fingerprints (
                        fp_hash TEXT PRIMARY KEY,
                        runs INTEGER NOT NULL DEFAULT 0,
                        first_seen TEXT NOT NULL,
                        last_seen TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trial_ips (
                        ip_str TEXT PRIMARY KEY,
                        runs INTEGER NOT NULL DEFAULT 0,
                        first_seen TEXT NOT NULL,
                        last_seen TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trial_subnets (
                        subnet TEXT PRIMARY KEY,
                        runs INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trial_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        ip TEXT NOT NULL,
                        fp TEXT NOT NULL,
                        target TEXT NOT NULL,
                        run_number INTEGER NOT NULL
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
        """One-time optional migration from legacy trial_ledger.json when SQLite tables are empty."""
        if (
            not self.ledger_path
            or self.ledger_path.endswith((".db", ".sqlite", ".sqlite3"))
            or not os.path.exists(self.ledger_path)
        ):
            return
        with self._lock:
            conn = self._connect()
            try:
                sess_count = conn.execute("SELECT COUNT(*) FROM trial_sessions").fetchone()[0]
                daily_count = conn.execute("SELECT COUNT(*) FROM daily_usage").fetchone()[0]
                if sess_count > 0 or daily_count > 0:
                    return
                with open(self.ledger_path, encoding="utf-8") as f:
                    legacy = json.load(f)
                if not isinstance(legacy, dict) or "sessions" not in legacy:
                    return
                now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                conn.execute("BEGIN IMMEDIATE")
                for day_key, count in legacy.get("daily_usage", {}).items():
                    conn.execute(
                        "INSERT OR IGNORE INTO daily_usage (day_key, runs_used) VALUES (?, ?)",
                        (day_key, int(count)),
                    )
                for sid, rec in legacy.get("sessions", {}).items():
                    conn.execute(
                        "INSERT OR IGNORE INTO trial_sessions (session_id, runs, created_at, last_used) VALUES (?, ?, ?, ?)",
                        (
                            sid,
                            int(rec.get("runs", 0)),
                            rec.get("created_at", now_ts),
                            rec.get("last_used", now_ts),
                        ),
                    )
                for fp, rec in legacy.get("fingerprints", {}).items():
                    conn.execute(
                        "INSERT OR IGNORE INTO trial_fingerprints (fp_hash, runs, first_seen, last_seen) VALUES (?, ?, ?, ?)",
                        (
                            fp,
                            int(rec.get("runs", 0)),
                            rec.get("first_seen", now_ts),
                            rec.get("last_seen", now_ts),
                        ),
                    )
                for ip_key, rec in legacy.get("ips", {}).items():
                    conn.execute(
                        "INSERT OR IGNORE INTO trial_ips (ip_str, runs, first_seen, last_seen) VALUES (?, ?, ?, ?)",
                        (
                            ip_key,
                            int(rec.get("runs", 0)),
                            rec.get("first_seen", now_ts),
                            rec.get("last_seen", now_ts),
                        ),
                    )
                for subnet_key, count in legacy.get("subnets", {}).items():
                    conn.execute(
                        "INSERT OR IGNORE INTO trial_subnets (subnet, runs) VALUES (?, ?)",
                        (subnet_key, int(count)),
                    )
                conn.execute("COMMIT")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                logger.warning("Legacy trial ledger JSON migration skipped: %s", exc)
            finally:
                conn.close()

    # ─────────────────────────────────────────────────────────────
    # Bot Shield & Token Handling
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def is_bot_user_agent(user_agent: str | None) -> bool:
        """Check if incoming request is from an automated scraping tool."""
        if not user_agent:
            return False
        ua_lower = user_agent.lower().strip()
        return any(bot in ua_lower for bot in BLOCKED_USER_AGENTS)

    def create_signed_session_token(self, session_id: str | None = None) -> str:
        """Generate a tamper-proof session token: <session_id>:<timestamp>:<hmac_signature>."""
        if not session_id:
            session_id = secrets.token_hex(16)
        ts = str(int(time.time()))
        payload = f"{session_id}:{ts}"
        sig = hmac.new(
            self._secret_key, payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return f"{payload}:{sig}"

    def verify_and_extract_session(
        self, token_str: str | None, max_age_seconds: int = 86400 * 30
    ) -> str | None:
        """Validate HMAC signature and expiration of incoming session token."""
        if not token_str or not isinstance(token_str, str):
            return None
        parts = token_str.strip().split(":")
        if len(parts) != 3:
            return None
        session_id, ts_str, sig = parts
        try:
            ts = int(ts_str)
            now = int(time.time())
            if ts > now + 300 or (now - ts) > max_age_seconds:
                return None
        except (ValueError, TypeError):
            return None

        payload = f"{session_id}:{ts_str}"
        expected_sig = hmac.new(
            self._secret_key, payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return session_id
        return None

    # ─────────────────────────────────────────────────────────────
    # IP & Subnet Normalization
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def normalize_ip(ip_str: str) -> tuple[str, str]:
        """Normalize IPv4/IPv6 address and compute /24 or /48 subnet key."""
        ip_str = ip_str.strip()
        if ip_str in ("127.0.0.1", "::1", "localhost", "testclient"):
            return "127.0.0.1", "127.0.0.1/32"
        try:
            obj = ipaddress.ip_address(ip_str)
            if obj.version == 4:
                net = ipaddress.ip_network(f"{ip_str}/24", strict=False)
                return str(obj), str(net)
            net = ipaddress.ip_network(f"{ip_str}/48", strict=False)
            return str(obj), str(net)
        except ValueError:
            return ip_str, ip_str

    @staticmethod
    def compute_composite_fingerprint(
        client_fp: str | None,
        user_agent: str | None,
        accept_lang: str | None = None,
    ) -> str:
        """Compute SHA-256 fingerprint from client hardware attributes."""
        raw = f"{client_fp or 'unknown_fp'}|{user_agent or 'unknown_ua'}|{accept_lang or 'unknown_lang'}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    # ─────────────────────────────────────────────────────────────
    # Trial Limit Evaluation & Atomic Consumption
    # ─────────────────────────────────────────────────────────────

    def check_usage(
        self, session_id: str | None, fp_hash: str, ip_str: str
    ) -> dict[str, Any]:
        """Check current trial usage without consuming."""
        if os.environ.get("DISABLE_TRIAL_LIMIT", "").lower() in ("true", "1", "yes"):
            return {
                "allowed": True,
                "runs_used": 0,
                "runs_remaining": 9999,
                "max_runs": 9999,
                "session_runs": 0,
                "fp_runs": 0,
                "ip_runs": 0,
                "is_locked": False,
                "circuit_breaker_active": False,
                "reason": "Full Local App: Trial Limiter Disabled",
            }

        today = time.strftime("%Y-%m-%d", time.gmtime())
        norm_ip, subnet = self.normalize_ip(ip_str)
        is_local = norm_ip == "127.0.0.1"

        with self._lock:
            conn = self._connect()
            try:
                d_row = conn.execute(
                    "SELECT runs_used FROM daily_usage WHERE day_key = ?", (today,)
                ).fetchone()
                daily_count = int(d_row["runs_used"]) if d_row else 0
                if daily_count >= self.max_global_daily_runs:
                    return {
                        "allowed": False,
                        "runs_used": self.max_runs,
                        "runs_remaining": 0,
                        "max_runs": self.max_runs,
                        "is_locked": True,
                        "circuit_breaker_active": True,
                        "reason": "Global daily demo quota reached. Please use the Local 1-Click Installer.",
                    }

                session_runs = 0
                if session_id:
                    s_row = conn.execute(
                        "SELECT runs FROM trial_sessions WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                    session_runs = int(s_row["runs"]) if s_row else 0

                fp_runs = 0
                if fp_hash:
                    f_row = conn.execute(
                        "SELECT runs FROM trial_fingerprints WHERE fp_hash = ?",
                        (fp_hash,),
                    ).fetchone()
                    fp_runs = int(f_row["runs"]) if f_row else 0

                ip_runs = 0
                subnet_runs = 0
                if not is_local:
                    i_row = conn.execute(
                        "SELECT runs FROM trial_ips WHERE ip_str = ?", (norm_ip,)
                    ).fetchone()
                    ip_runs = int(i_row["runs"]) if i_row else 0
                    sub_row = conn.execute(
                        "SELECT runs FROM trial_subnets WHERE subnet = ?", (subnet,)
                    ).fetchone()
                    subnet_runs = int(sub_row["runs"]) if sub_row else 0
            finally:
                conn.close()

        runs_used = max(session_runs, fp_runs, ip_runs)
        runs_remaining = max(0, self.max_runs - runs_used)
        allowed = runs_used < self.max_runs

        if not is_local and subnet_runs >= self.max_subnet_runs:
            allowed = False
            reason = f"Subnet trial quota exceeded ({subnet_runs}/{self.max_subnet_runs})"
        elif not allowed:
            reason = f"Free trial limit reached ({runs_used}/{self.max_runs} runs used)"
        else:
            reason = "Trial run available"

        return {
            "allowed": allowed,
            "runs_used": runs_used,
            "runs_remaining": runs_remaining,
            "max_runs": self.max_runs,
            "session_runs": session_runs,
            "fp_runs": fp_runs,
            "ip_runs": ip_runs,
            "is_locked": not allowed,
            "circuit_breaker_active": False,
            "reason": reason,
        }

    def consume_trial_run(
        self,
        session_id: str,
        fp_hash: str,
        ip_str: str,
        target_name: str = "Unknown",
        user_agent: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Atomically verify availability and consume 1 trial run in SQLite WAL."""
        if os.environ.get("DISABLE_TRIAL_LIMIT", "").lower() in ("true", "1", "yes"):
            return True, {
                "allowed": True,
                "runs_used": 0,
                "runs_remaining": 9999,
                "max_runs": 9999,
                "is_locked": False,
                "message": "Full Local App: Unlimited Discovery Mode",
            }

        if self.is_bot_user_agent(user_agent):
            return False, {
                "allowed": False,
                "error": "BOT_REQUEST_FORBIDDEN",
                "message": "Automated scripts are blocked on the trial demo to protect API credits. Launch the Local App for script access.",
            }

        if target_name and len(target_name.strip()) > MAX_TARGET_CHARS:
            return False, {
                "allowed": False,
                "error": "INPUT_TOKEN_LIMIT_EXCEEDED",
                "message": f"Input query exceeds trial token budget ({len(target_name)} > {MAX_TARGET_CHARS} chars). Truncate to active domain.",
            }

        today = time.strftime("%Y-%m-%d", time.gmtime())
        now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        norm_ip, subnet = self.normalize_ip(ip_str)
        is_local = norm_ip == "127.0.0.1"

        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                d_row = conn.execute(
                    "SELECT runs_used FROM daily_usage WHERE day_key = ?", (today,)
                ).fetchone()
                daily_count = int(d_row["runs_used"]) if d_row else 0
                if daily_count >= self.max_global_daily_runs:
                    conn.execute("ROLLBACK")
                    return False, {
                        "allowed": False,
                        "runs_used": self.max_runs,
                        "runs_remaining": 0,
                        "max_runs": self.max_runs,
                        "is_locked": True,
                        "error": "GLOBAL_DAILY_LIMIT_REACHED",
                        "message": "Today's global discovery quota has been reached to protect server & API credits. Launch the Local App for unlimited execution.",
                    }

                s_row = conn.execute(
                    "SELECT runs FROM trial_sessions WHERE session_id = ?", (session_id,)
                ).fetchone()
                session_runs = int(s_row["runs"]) if s_row else 0

                f_row = conn.execute(
                    "SELECT runs FROM trial_fingerprints WHERE fp_hash = ?", (fp_hash,)
                ).fetchone()
                fp_runs = int(f_row["runs"]) if f_row else 0

                ip_runs = 0
                subnet_runs = 0
                if not is_local:
                    i_row = conn.execute(
                        "SELECT runs FROM trial_ips WHERE ip_str = ?", (norm_ip,)
                    ).fetchone()
                    ip_runs = int(i_row["runs"]) if i_row else 0
                    sub_row = conn.execute(
                        "SELECT runs FROM trial_subnets WHERE subnet = ?", (subnet,)
                    ).fetchone()
                    subnet_runs = int(sub_row["runs"]) if sub_row else 0

                current_runs = max(session_runs, fp_runs, ip_runs)
                if current_runs >= self.max_runs:
                    conn.execute("ROLLBACK")
                    return False, {
                        "allowed": False,
                        "runs_used": current_runs,
                        "runs_remaining": 0,
                        "max_runs": self.max_runs,
                        "is_locked": True,
                        "error": "TRIAL_LIMIT_EXCEEDED",
                        "message": f"Free trial limit reached ({current_runs}/{self.max_runs} run used). Launch the Full Local App for unlimited campaigns.",
                    }

                if not is_local and subnet_runs >= self.max_subnet_runs:
                    conn.execute("ROLLBACK")
                    return False, {
                        "allowed": False,
                        "runs_used": current_runs,
                        "runs_remaining": 0,
                        "max_runs": self.max_runs,
                        "is_locked": True,
                        "error": "SUBNET_QUOTA_EXCEEDED",
                        "message": "Subnet trial quota exceeded. Launch the Full Local App for unlimited access.",
                    }

                new_run_count = current_runs + 1
                conn.execute(
                    """
                    INSERT INTO daily_usage (day_key, runs_used) VALUES (?, ?)
                    ON CONFLICT(day_key) DO UPDATE SET runs_used = excluded.runs_used
                    """,
                    (today, daily_count + 1),
                )
                conn.execute(
                    """
                    INSERT INTO trial_sessions (session_id, runs, created_at, last_used)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET runs = excluded.runs, last_used = excluded.last_used
                    """,
                    (session_id, new_run_count, now_ts, now_ts),
                )
                conn.execute(
                    """
                    INSERT INTO trial_fingerprints (fp_hash, runs, first_seen, last_seen)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(fp_hash) DO UPDATE SET runs = excluded.runs, last_seen = excluded.last_seen
                    """,
                    (fp_hash, new_run_count, now_ts, now_ts),
                )
                if not is_local:
                    conn.execute(
                        """
                        INSERT INTO trial_ips (ip_str, runs, first_seen, last_seen)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(ip_str) DO UPDATE SET runs = excluded.runs, last_seen = excluded.last_seen
                        """,
                        (norm_ip, new_run_count, now_ts, now_ts),
                    )
                    conn.execute(
                        """
                        INSERT INTO trial_subnets (subnet, runs) VALUES (?, ?)
                        ON CONFLICT(subnet) DO UPDATE SET runs = trial_subnets.runs + 1
                        """,
                        (subnet, 1),
                    )
                conn.execute(
                    """
                    INSERT INTO trial_history (timestamp, session_id, ip, fp, target, run_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (now_ts, session_id, norm_ip, fp_hash, target_name, new_run_count),
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

        runs_rem = max(0, self.max_runs - new_run_count)
        is_locked = runs_rem == 0
        return True, {
            "allowed": True,
            "runs_used": new_run_count,
            "runs_remaining": runs_rem,
            "max_runs": self.max_runs,
            "is_locked": is_locked,
            "message": f"Demo trial run {new_run_count} of {self.max_runs} completed. {runs_rem} free trial run(s) remaining.",
        }

    def reset_caller(self, session_id: str, fp_hash: str, ip_str: str) -> None:
        """Reset usage for a specific caller."""
        norm_ip, subnet = self.normalize_ip(ip_str)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM trial_ips WHERE ip_str IN (?, ?)", (norm_ip, ip_str))
                conn.execute("DELETE FROM trial_sessions WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM trial_fingerprints WHERE fp_hash = ?", (fp_hash,))
                conn.execute("DELETE FROM trial_subnets WHERE subnet = ?", (subnet,))
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()

    def reset_for_tests(self) -> None:
        """Clear trial database tables cleanly for tests."""
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                for table in (
                    "daily_usage",
                    "trial_sessions",
                    "trial_fingerprints",
                    "trial_ips",
                    "trial_subnets",
                    "trial_history",
                ):
                    conn.execute(f"DELETE FROM {table}")  # nosec B608
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                conn.close()
