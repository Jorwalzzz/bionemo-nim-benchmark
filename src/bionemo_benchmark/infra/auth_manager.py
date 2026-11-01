"""
Agentic BioNeMo - Researcher Authentication, Synchronized Daily Quotas & Feedback Engine.

Provides:
1. PBKDF2-HMAC-SHA256 salted password hashing.
2. Tamper-proof HMAC-SHA256 session bearer tokens.
3. Synchronized 24-hour daily quota engine anchored strictly to 3:00 PM IST (09:30:00 UTC).
4. Authenticated researcher feedback ingestion with input sanitization.
5. Persistent thread-safe atomic storage for user accounts and feedback records.
"""

import base64
import datetime
import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

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

# Configuration invariants
FREE_TRIAL_DAILY_RUNS = int(os.environ.get("FREE_TRIAL_DAILY_RUNS", "5"))
RESET_OFFSET_SECONDS = 9 * 3600 + 30 * 60  # 34,200 seconds (09:30 UTC = 15:00 IST)
PASSWORD_SALT_BYTES = 32
DEFAULT_PBKDF2_ITERATIONS = int(os.environ.get("PBKDF2_ITERATIONS", "100_000"))
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _get_or_create_auth_secret() -> bytes:
    """Retrieve or initialize persistent HMAC secret key for auth tokens."""
    if os.environ.get("AUTH_SECRET_KEY"):
        return os.environ["AUTH_SECRET_KEY"].encode("utf-8")
    secret_file = os.path.join(DATA_DIR, ".auth_secret")
    if os.path.exists(secret_file):
        try:
            with open(secret_file, "rb") as f:
                key = f.read().strip()
                if len(key) >= 32:
                    return key
        except Exception:
            pass
    key = secrets.token_bytes(32)
    try:
        with open(secret_file, "wb") as f:
            f.write(key)
    except Exception:
        pass
    return key


class AuthManager:
    """Thread-safe researcher authentication, synchronized 3:00 PM IST quota & feedback manager."""

    def __init__(
        self,
        ledger_path: str = AUTH_LEDGER_PATH,
        feedback_path: str = FEEDBACK_LEDGER_PATH,
        daily_limit: int = FREE_TRIAL_DAILY_RUNS,
        iterations: int = DEFAULT_PBKDF2_ITERATIONS,
    ):
        self.ledger_path = ledger_path
        self.feedback_path = feedback_path
        self.daily_limit = daily_limit
        self.iterations = iterations
        self._secret = _get_or_create_auth_secret()
        # Use RLock to prevent self-deadlocks on nested helper calls
        self._lock = threading.RLock()
        self._ledger: Dict[str, Any] = self._load_ledger()
        self._init_default_evaluator()

    def _load_ledger(self) -> Dict[str, Any]:
        """Atomically load user auth ledger from disk."""
        default_ledger: Dict[str, Any] = {
            "version": 1,
            "users": {},  # user_id -> user_dict
            "emails": {},  # email_lower -> user_id
            "usage": {},  # "user_id:cycle_key" -> count
            "sessions": {},  # token -> {user_id, expires_at}
        }
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "users" in data:
                        return data
            except Exception as e:
                print(f"[AuthManager] Warning: could not load auth ledger: {e}")
        return default_ledger

    def _save_ledger(self) -> None:
        """Atomically persist ledger to disk using temp file replacement."""
        dir_name = os.path.dirname(self.ledger_path)
        os.makedirs(dir_name, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                "w", dir=dir_name, delete=False, encoding="utf-8"
            ) as tf:
                json.dump(self._ledger, tf, indent=2)
                temp_name = tf.name
            os.replace(temp_name, self.ledger_path)
        except Exception as e:
            print(f"[AuthManager] Error writing auth ledger: {e}")

    def _init_default_evaluator(self) -> None:
        """Provision the default 1-click evaluator account if not already present."""
        evaluator_email = "evaluator@bionemo.org"
        with self._lock:
            if evaluator_email.lower() not in self._ledger.get("emails", {}):
                salt = secrets.token_hex(PASSWORD_SALT_BYTES)
                pwd_hash = self._hash_password("DemoResearcher2026!", salt)
                user_id = "evaluator-demo-001"
                now = int(time.time())
                user_data = {
                    "user_id": user_id,
                    "email": evaluator_email,
                    "full_name": "Academic Peer Evaluator",
                    "organization": "BioNeMo Review Committee",
                    "salt": salt,
                    "password_hash": pwd_hash,
                    "created_at": now,
                    "tier": "free_trial",
                    "is_active": True,
                }
                self._ledger["users"][user_id] = user_data
                self._ledger["emails"][evaluator_email.lower()] = user_id
                self._save_ledger()

    # ─────────────────────────────────────────────────────────────
    # Cryptographic Password & Token Helpers
    # ─────────────────────────────────────────────────────────────

    def _hash_password(self, password: str, salt_hex: str) -> str:
        """Derive salted key using PBKDF2-HMAC-SHA256."""
        salt_bytes = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_bytes,
            self.iterations,
        )
        return key.hex()

    def _create_token(self, user_id: str, max_age_seconds: int = 86400 * 30) -> str:
        """Create a signed session token: base64(user_id:created:expires).hmac_sig"""
        created = int(time.time())
        expires = created + max_age_seconds
        payload_raw = f"{user_id}:{created}:{expires}"
        payload_b64 = base64.urlsafe_b64encode(payload_raw.encode("utf-8")).decode("ascii")
        sig = hmac.new(
            self._secret, payload_b64.encode("ascii"), hashlib.sha256
        ).hexdigest()
        return f"{payload_b64}.{sig}"

    def verify_token(self, token: Optional[str]) -> Optional[str]:
        """Verify token HMAC signature and expiration; returns user_id if valid."""
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
            user_id, created_str, expires_str = payload_raw.split(":")
            expires = int(expires_str)
            if time.time() > expires:
                return None
            return user_id
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────
    # Synchronized 3:00 PM IST (09:30 UTC) Cycle Calculation
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_cycle_info(timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate current 24-hour cycle anchored to 3:00:00 PM IST (09:30:00 UTC).
        All users worldwide refresh in sync at this exact moment.
        """
        t = timestamp if timestamp is not None else time.time()
        cycle_idx = int((t - RESET_OFFSET_SECONDS) // 86400)
        next_reset_epoch = (cycle_idx + 1) * 86400 + RESET_OFFSET_SECONDS
        seconds_remaining = max(0, int(next_reset_epoch - t))

        cycle_dt = datetime.datetime.fromtimestamp(
            cycle_idx * 86400 + RESET_OFFSET_SECONDS, datetime.timezone.utc
        )
        cycle_key = cycle_dt.strftime("%Y-%m-%d_1500IST")

        # Format IST display time
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
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Register a new researcher account."""
        email_clean = email.strip()
        if not EMAIL_REGEX.match(email_clean):
            return False, None, "Invalid email address format."
        if not password or len(password) < 6:
            return False, None, "Password must be at least 6 characters."

        email_key = email_clean.lower()
        with self._lock:
            if email_key in self._ledger.get("emails", {}):
                return False, None, "An account with this email already exists."

            user_id = f"user-{secrets.token_hex(8)}"
            salt = secrets.token_hex(PASSWORD_SALT_BYTES)
            pwd_hash = self._hash_password(password, salt)
            now = int(time.time())

            user_record = {
                "user_id": user_id,
                "email": email_clean,
                "full_name": full_name.strip() or "Researcher",
                "organization": organization.strip() or "Independent Academic",
                "salt": salt,
                "password_hash": pwd_hash,
                "created_at": now,
                "tier": "free_trial",
                "is_active": True,
            }
            self._ledger["users"][user_id] = user_record
            self._ledger["emails"][email_key] = user_id
            self._save_ledger()

            token = self._create_token(user_id)
            quota = self.get_user_quota(user_id)
            u_info = {
                "id": user_id,
                "user_id": user_id,
                "email": email_clean,
                "full_name": user_record["full_name"],
                "organization": user_record["organization"],
            }
            return True, {
                **u_info,
                "user": u_info,
                "token": token,
                "quota": quota,
            }, "Account created successfully."

    def authenticate_user(
        self, email: str, password: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Authenticate user credentials and return session token + quota info."""
        email_key = email.strip().lower()
        with self._lock:
            user_id = self._ledger.get("emails", {}).get(email_key)
            if not user_id or user_id not in self._ledger.get("users", {}):
                return False, None, "Invalid email or password."

            user = self._ledger["users"][user_id]
            expected_hash = self._hash_password(password, user["salt"])
            if not hmac.compare_digest(user["password_hash"], expected_hash):
                return False, None, "Invalid email or password."

            token = self._create_token(user_id)
            quota = self.get_user_quota(user_id)
            u_info = {
                "id": user_id,
                "user_id": user_id,
                "email": user["email"],
                "full_name": user["full_name"],
                "organization": user["organization"],
            }
            return True, {
                **u_info,
                "user": u_info,
                "token": token,
                "quota": quota,
            }, "Authentication successful."

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by user_id."""
        with self._lock:
            user = self._ledger.get("users", {}).get(user_id)
            if not user:
                return None
            return {
                "id": user["user_id"],
                "user_id": user["user_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "organization": user["organization"],
                "tier": user.get("tier", "free_trial"),
                "created_at": user["created_at"],
            }

    # ─────────────────────────────────────────────────────────────
    # Synchronized 5-Run Quota Verification & Consumption
    # ─────────────────────────────────────────────────────────────

    def get_user_quota(
        self, user_id: str, timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Return remaining runs and countdown to 3:00 PM IST for given user."""
        cycle_info = self.get_cycle_info(timestamp)
        cycle_key = cycle_info["cycle_key"]
        usage_key = f"{user_id}:{cycle_key}"

        with self._lock:
            runs_used = self._ledger.get("usage", {}).get(usage_key, 0)

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
            "cycle_key": cycle_key,
        }

    def consume_run(
        self, user_id: str, timestamp: Optional[float] = None
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Atomically verify availability and consume 1 discovery screening run."""
        cycle_info = self.get_cycle_info(timestamp)
        cycle_key = cycle_info["cycle_key"]
        usage_key = f"{user_id}:{cycle_key}"

        with self._lock:
            if "usage" not in self._ledger:
                self._ledger["usage"] = {}
            current_runs = self._ledger["usage"].get(usage_key, 0)
            if current_runs >= self.daily_limit:
                quota = self.get_user_quota(user_id, timestamp)
                return (
                    False,
                    quota,
                    f"Daily free quota reached ({self.daily_limit}/{self.daily_limit} runs used). All quotas reset at 3:00 PM IST in {cycle_info['countdown']}.",
                )

            self._ledger["usage"][usage_key] = current_runs + 1
            self._save_ledger()

        quota = self.get_user_quota(user_id, timestamp)
        return True, quota, "Trial run authorized."

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
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Validate, sanitize, and record feedback submitted by an authenticated researcher."""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False, {}, "User profile not found."

        valid_categories = {
            "Scientific Accuracy",
            "Model Latency",
            "Bug Report",
            "Feature Request",
            "General",
        }
        category_clean = category.strip()
        if category_clean not in valid_categories:
            category_clean = "General"

        rating_clean = max(1, min(5, int(rating))) if rating else 5
        comments_clean = (comments or "").strip()
        if not comments_clean:
            return False, {}, "Feedback comments cannot be empty."

        # Truncate comments to prevent storage bloat
        if len(comments_clean) > 2000:
            comments_clean = comments_clean[:2000]

        feedback_id = f"fb-{secrets.token_hex(6)}"
        entry = {
            "id": feedback_id,
            "feedback_id": feedback_id,
            "timestamp": int(time.time()),
            "user_id": user_id,
            "email": profile["email"],
            "full_name": profile["full_name"],
            "organization": profile["organization"],
            "category": category_clean,
            "rating": rating_clean,
            "comments": comments_clean,
            "target_complex": target_complex.strip() or "General",
            "client_ip": client_ip,
        }

        with self._lock:
            submissions: List[Dict[str, Any]] = []
            if os.path.exists(self.feedback_path):
                try:
                    with open(self.feedback_path, "r", encoding="utf-8") as f:
                        submissions = json.load(f)
                        if not isinstance(submissions, list):
                            submissions = []
                except Exception:
                    submissions = []

            submissions.append(entry)
            dir_name = os.path.dirname(self.feedback_path)
            os.makedirs(dir_name, exist_ok=True)
            try:
                with tempfile.NamedTemporaryFile(
                    "w", dir=dir_name, delete=False, encoding="utf-8"
                ) as tf:
                    json.dump(submissions, tf, indent=2)
                    temp_name = tf.name
                os.replace(temp_name, self.feedback_path)
            except Exception as e:
                print(f"[AuthManager] Error saving feedback: {e}")
                return False, {}, f"Failed to record feedback: {e}"

        return True, entry, "Thank you! Your feedback has been recorded."

    def get_feedback_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve feedback history for a given researcher."""
        with self._lock:
            if not os.path.exists(self.feedback_path):
                return []
            try:
                with open(self.feedback_path, "r", encoding="utf-8") as f:
                    all_fb = json.load(f)
                    if isinstance(all_fb, list):
                        return [fb for fb in all_fb if fb.get("user_id") == user_id]
            except Exception:
                return []
            return []
