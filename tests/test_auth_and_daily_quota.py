"""
Unit tests for AuthManager and Synchronized 3:00 PM IST Quota Engine.
"""

import os
import tempfile

import pytest

from bionemo_benchmark.infra.auth_manager import AuthManager


@pytest.fixture
def auth_mgr():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = os.path.join(tmpdir, "test_auth.json")
        feedback = os.path.join(tmpdir, "test_feedback.json")
        mgr = AuthManager(ledger_path=ledger, feedback_path=feedback, daily_limit=5, iterations=1000)
        yield mgr


class TestAuthManager:
    def test_default_evaluator_account_exists(self, auth_mgr):
        """Default evaluator account is auto-provisioned."""
        ok, res, msg = auth_mgr.authenticate_user("evaluator@bionemo.org", "DemoResearcher2026!")
        assert ok is True
        assert res["email"] == "evaluator@bionemo.org"
        assert res["quota"]["daily_limit"] == 5
        assert res["quota"]["runs_remaining"] == 5

    def test_user_registration_and_login(self, auth_mgr):
        """Standard researcher registration and login flow."""
        ok, user, msg = auth_mgr.register_user(
            email="dr.curie@radium.org",
            password="StrongPassword123!",
            full_name="Marie Curie",
            organization="Sorbonne",
        )
        assert ok is True
        assert user["email"] == "dr.curie@radium.org"
        assert user["full_name"] == "Marie Curie"
        assert "token" in user

        # Verify token works
        user_id = auth_mgr.verify_token(user["token"])
        assert user_id == user["user_id"]

        # Authenticate via login
        login_ok, login_data, _ = auth_mgr.authenticate_user(
            "dr.curie@radium.org", "StrongPassword123!"
        )
        assert login_ok is True
        assert login_data["user_id"] == user["user_id"]

    def test_duplicate_email_rejected(self, auth_mgr):
        """Cannot register with the same email twice."""
        auth_mgr.register_user("scientist@lab.edu", "Password123!")
        ok, _, msg = auth_mgr.register_user("scientist@lab.edu", "DifferentPassword123!")
        assert ok is False
        assert "already exists" in msg.lower()

    def test_invalid_password_rejected(self, auth_mgr):
        """Passwords under 6 characters are rejected."""
        ok, _, msg = auth_mgr.register_user("valid@email.com", "123")
        assert ok is False
        assert "at least 6 characters" in msg

    def test_invalid_email_format_rejected(self, auth_mgr):
        """Malformed email strings are rejected."""
        ok, _, msg = auth_mgr.register_user("not-an-email", "Password123!")
        assert ok is False
        assert "invalid email" in msg.lower()

    def test_5_runs_quota_consumption(self, auth_mgr):
        """User can execute exactly 5 runs; the 6th run is denied."""
        ok, user, _ = auth_mgr.register_user("tester@bionemo.org", "TestPass123!")
        uid = user["user_id"]

        # Consume 5 runs
        for run_idx in range(1, 6):
            decision = auth_mgr.consume_run(uid)
            assert decision.allowed is True
            assert decision.reservation_id
            assert decision.quota_info["runs_used"] == run_idx
            assert decision.quota_info["runs_remaining"] == 5 - run_idx

        # 6th run must be denied
        decision = auth_mgr.consume_run(uid)
        assert decision.allowed is False
        assert decision.reservation_id is None
        assert decision.quota_info["runs_remaining"] == 0
        assert "Daily free quota reached" in decision.message
        assert "3:00 PM IST" in decision.message

    def test_synchronized_3pm_ist_rollover(self, auth_mgr):
        """
        Advancing timestamp past 3:00 PM IST (09:30 UTC) automatically
        resets the quota back to 5 runs without data loss.
        """
        ok, user, _ = auth_mgr.register_user("rollover@bionemo.org", "TestPass123!")
        uid = user["user_id"]

        # Base timestamp: 2026-11-01 14:00:00 IST (08:30:00 UTC) -> 1 hour before reset
        t_before = 1793521800  # Exactly before 15:00 IST
        
        # Exhaust quota before reset
        for _ in range(5):
            decision = auth_mgr.consume_run(uid, timestamp=t_before)
            assert decision.allowed is True

        # Check exhausted
        q_exhausted = auth_mgr.get_user_quota(uid, timestamp=t_before)
        assert q_exhausted["allowed"] is False
        assert q_exhausted["runs_remaining"] == 0

        # Advance timestamp past 15:00:00 IST (add 3600 * 2 = 2 hours)
        t_after = t_before + 7200  # Now 16:00:00 IST
        q_refreshed = auth_mgr.get_user_quota(uid, timestamp=t_after)
        assert q_refreshed["allowed"] is True
        assert q_refreshed["runs_remaining"] == 5
        assert q_refreshed["runs_used"] == 0

        # Can consume run in new cycle
        d_new = auth_mgr.consume_run(uid, timestamp=t_after)
        assert d_new.allowed is True
        assert d_new.quota_info["runs_used"] == 1
        assert d_new.quota_info["runs_remaining"] == 4


def test_api_auth_and_feedback_flow():
    """Verify end-to-end FastAPI routes for auth and feedback."""
    from starlette.testclient import TestClient

    from serve_cockpit import app

    client = TestClient(app)

    # 1. Check unauthenticated me
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is False
    assert "quota" in data
    assert "seconds_remaining" in data["quota"]

    # 2. Unauthenticated feedback submission rejected
    unauth_fb = client.post(
        "/api/feedback",
        json={"rating": 5, "comments": "Great discovery run!", "target_name": "KRAS G12D"},
    )
    assert unauth_fb.status_code == 401

    # 3. Demo evaluator login
    login_resp = client.post("/api/auth/demo-login", headers={"X-BioNeMo-CSRF": "1"})
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["success"] is True
    assert "token" in login_data
    token = login_data["token"]
    assert login_data["user"]["email"] == "evaluator@bionemo.org"

    headers = {"Authorization": f"Bearer {token}"}

    # 4. Authenticated me
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["email"] == "evaluator@bionemo.org"
    assert me_data["quota"]["runs_remaining"] <= 5

    # 5. Authenticated feedback submission succeeds
    auth_fb = client.post(
        "/api/feedback",
        headers=headers,
        json={"rating": 5, "category": "Lead Candidates", "comments": "Excellent docking poses.", "target_name": "KRAS G12D"},
    )
    assert auth_fb.status_code == 200
    assert auth_fb.json()["success"] is True

    # 6. Retrieve feedback history
    fb_list = client.get("/api/feedback", headers=headers)
    assert fb_list.status_code == 200
    items = fb_list.json()["feedback"]
    assert len(items) >= 1
    assert any(item["comments"] == "Excellent docking poses." for item in items)

    # 7. Logout clears session
    logout_resp = client.post("/api/auth/logout", headers={"X-BioNeMo-CSRF": "1"})
    assert logout_resp.status_code == 200


def test_email_validation_rules():
    """Verify detailed email validation, domain checks, typo suggestions, and disposable rejection."""
    from bionemo_benchmark.infra.auth_manager import validate_email_address

    # 1. Valid academic & institutional
    ok, msg, typo, kind = validate_email_address("dr.alex@stanford.edu")
    assert ok is True
    assert kind == "academic"

    ok, msg, typo, kind = validate_email_address("prof@cam.ac.uk")
    assert ok is True
    assert kind == "academic"

    # 2. Valid standard
    ok, msg, typo, kind = validate_email_address("researcher@company.com")
    assert ok is True
    assert kind == "standard"

    # 3. Disposable throwaway domains rejected
    ok, msg, typo, kind = validate_email_address("bot@mailinator.com")
    assert ok is False
    assert kind == "disposable"
    assert "disposable" in msg.lower() or "temporary" in msg.lower()

    ok, msg, typo, kind = validate_email_address("tester@10minutemail.com")
    assert ok is False
    assert kind == "disposable"

    # 4. Common typos detected with suggestions
    ok, msg, typo, kind = validate_email_address("researcher@gamil.com")
    assert ok is False
    assert kind == "typo"
    assert typo == "researcher@gmail.com"
    assert "gmail.com" in msg

    ok, msg, typo, kind = validate_email_address("user@yaho.com")
    assert ok is False
    assert kind == "typo"
    assert typo == "user@yahoo.com"

    # 5. Malformed formats rejected
    for bad in ["not-an-email", "@nodomain.com", "user@", "user@domain", "user@domain.c", "user@@domain.com"]:
        ok, msg, _, kind = validate_email_address(bad)
        assert ok is False
        assert kind == "invalid"


def test_api_validate_email_endpoint():
    """Verify POST /api/auth/validate-email returns real-time feedback."""
    from starlette.testclient import TestClient

    from serve_cockpit import app

    client = TestClient(app)

    # Valid academic
    r1 = client.post("/api/auth/validate-email", json={"email": "dr.smith@harvard.edu"})
    assert r1.status_code == 200
    assert r1.json()["valid"] is True
    assert r1.json()["classification"] == "academic"

    # Typo suggestion
    r2 = client.post("/api/auth/validate-email", json={"email": "test@gmai.com"})
    assert r2.status_code == 200
    assert r2.json()["valid"] is False
    assert r2.json()["suggestion"] == "test@gmail.com"

    # Disposable rejected
    r3 = client.post("/api/auth/validate-email", json={"email": "throwaway@tempmail.com"})
    assert r3.status_code == 200
    assert r3.json()["valid"] is False
    assert r3.json()["classification"] == "disposable"


def test_registration_rejects_disposable_and_typo_emails(auth_mgr):
    """Registration fails closed on disposable or typo domain addresses."""
    # Disposable
    ok, _, msg = auth_mgr.register_user("bot@mailinator.com", "Password123!")
    assert ok is False
    assert "disposable" in msg.lower() or "temporary" in msg.lower()

    # Typo
    ok, _, msg = auth_mgr.register_user("user@hotmial.com", "Password123!")
    assert ok is False
    assert "typo" in msg.lower() or "hotmail.com" in msg.lower()


def test_token_revocation(auth_mgr):
    """Session token can be actively revoked and rejected on subsequent verification."""
    ok, user, _ = auth_mgr.register_user("revoketest@bionemo.org", "Pass12345!")
    assert ok is True
    token = user["token"]

    # Valid before revocation
    assert auth_mgr.verify_token(token) == user["user_id"]

    # Revoke
    revoked = auth_mgr.revoke_token(token)
    assert revoked is True

    # Now invalid
    assert auth_mgr.verify_token(token) is None


def test_brute_force_account_lockout(auth_mgr):
    """Account is temporarily locked after 5 consecutive failed login attempts."""
    email = "lockout_target@bionemo.org"
    auth_mgr.register_user(email, "SecretPassword123!")

    # 4 failed attempts - not yet locked
    for _ in range(4):
        ok, _, msg = auth_mgr.authenticate_user(email, "WrongPassword!")
        assert ok is False
        assert "temporarily locked" not in msg

    # 5th failed attempt triggers lockout
    ok, _, msg = auth_mgr.authenticate_user(email, "WrongPassword!")
    assert ok is False

    # 6th attempt (even with correct password) is blocked by lockout
    ok, _, msg = auth_mgr.authenticate_user(email, "SecretPassword123!")
    assert ok is False
    assert "temporarily locked" in msg.lower()


def test_gmail_canonicalization_and_scrypt_and_token_version(tmp_path):
    """Verify Gmail alias canonicalization, scrypt hashing, and token_version session revocation."""
    mgr = AuthManager(
        ledger_path=str(tmp_path / "auth.db"),
        feedback_path=str(tmp_path / "fb.db"),
        daily_limit=5,
    )
    ok, u1, _ = mgr.register_user("a.lice+work@googlemail.com", "StrongPass999!")
    assert ok is True
    assert u1["hash_algo"] == "scrypt"

    # Canonical Gmail duplicate must be rejected (prevents free-tier alias farming)
    ok2, _, msg2 = mgr.register_user("alice+spam@gmail.com", "StrongPass999!")
    assert ok2 is False
    assert "already exists" in msg2.lower()

    token1 = u1["token"]
    assert mgr.verify_token(token1) == u1["user_id"]

    # Password change bumps token_version, invalidating existing tokens immediately
    assert mgr.change_password(u1["user_id"], "NewStrongPass888!") is True
    assert mgr.verify_token(token1) is None

    ok_login, login_res, _ = mgr.authenticate_user("a.lice+work@googlemail.com", "NewStrongPass888!")
    assert ok_login is True
    token2 = login_res["token"]
    assert mgr.verify_token(token2) == u1["user_id"]

    # Role change also bumps token_version
    assert mgr.update_role(u1["user_id"], "reviewer") is True
    assert mgr.verify_token(token2) is None


def test_fail_closed_short_auth_secret(tmp_path, monkeypatch):
    """AuthManager refuses to start if AUTH_SECRET_KEY has fewer than 32 bytes."""
    monkeypatch.setenv("AUTH_SECRET_KEY", "too-short-secret")
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        AuthManager(
            ledger_path=str(tmp_path / "auth_short.db"),
            feedback_path=str(tmp_path / "fb_short.db"),
        )


def test_parallel_consume_run_race_safety(tmp_path):
    """Concurrent consume_run calls under SQLite WAL cannot exceed daily quota."""
    import concurrent.futures

    mgr = AuthManager(
        ledger_path=str(tmp_path / "race.db"),
        feedback_path=str(tmp_path / "fb.db"),
        daily_limit=5,
    )
    ok, u, _ = mgr.register_user("racer@stanford.edu", "RacePass123!")
    assert ok is True
    uid = u["user_id"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        decisions = list(pool.map(lambda _: mgr.consume_run(uid), range(12)))

    allowed_count = sum(1 for d in decisions if d.allowed)
    denied_count = sum(1 for d in decisions if not d.allowed)
    assert allowed_count == 5
    assert denied_count == 7


def test_api_quota_enforcement_and_refund_on_upstream_5xx(monkeypatch):
    """With DISABLE_TRIAL_LIMIT=false, /api/run enforces quota and refunds slots on upstream failures."""
    from starlette.testclient import TestClient

    import bionemo_benchmark.server.routes_campaign as routes_campaign_mod
    from serve_cockpit import app

    monkeypatch.setenv("DISABLE_TRIAL_LIMIT", "false")
    client = TestClient(app, raise_server_exceptions=False)

    # Unauthenticated run blocked
    unauth = client.post(
        "/api/run?target=KRAS+G12D&candidates=2",
        headers={"X-BioNeMo-CSRF": "1"},
    )
    assert unauth.status_code == 401

    reg = client.post(
        "/api/auth/register",
        json={"email": "quota_tester@mit.edu", "password": "StrongPassword123!"},
    )
    assert reg.status_code == 200
    token = reg.json()["token"]
    hdrs = {"Authorization": f"Bearer {token}", "X-BioNeMo-CSRF": "1"}

    # Simulate upstream 5xx / runtime error inside orchestrator -> reservation MUST refund cleanly
    class FailingOrchestrator:
        mock = False
        api_key = "nvapi-test"

        def run_discovery_campaign(self, **kwargs):
            raise RuntimeError("Upstream NIM 503 Service Unavailable")

    with monkeypatch.context() as ctx:
        ctx.setattr(routes_campaign_mod, "make_orchestrator", lambda **kw: FailingOrchestrator())
        failed = client.post("/api/run?target=KRAS+G12D&candidates=2", headers=hdrs)
        assert failed.status_code == 500

    # Verify quota was refunded (still 5 runs remaining)
    me_after_fail = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after_fail.status_code == 200
    assert me_after_fail.json()["quota"]["runs_remaining"] == 5

    # Consume all 5 valid runs -> 6th returns 429
    for idx in range(5):
        ok_run = client.post("/api/run?target=KRAS+G12D&candidates=2", headers=hdrs)
        assert ok_run.status_code == 200, f"Run {idx + 1} failed: {ok_run.text}"

    blocked = client.post("/api/run?target=KRAS+G12D&candidates=2", headers=hdrs)
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "DAILY_QUOTA_EXCEEDED"


