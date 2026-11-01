"""
Unit tests for AuthManager and Synchronized 3:00 PM IST Quota Engine.
"""

import os
import tempfile
import time
import pytest
from bionemo_benchmark.infra.auth_manager import AuthManager, RESET_OFFSET_SECONDS


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
            allowed, quota, msg = auth_mgr.consume_run(uid)
            assert allowed is True
            assert quota["runs_used"] == run_idx
            assert quota["runs_remaining"] == 5 - run_idx

        # 6th run must be denied
        allowed, quota, msg = auth_mgr.consume_run(uid)
        assert allowed is False
        assert quota["runs_remaining"] == 0
        assert "Daily free quota reached" in msg
        assert "3:00 PM IST" in msg

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
            allowed, _, _ = auth_mgr.consume_run(uid, timestamp=t_before)
            assert allowed is True

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
        allowed, q_new, _ = auth_mgr.consume_run(uid, timestamp=t_after)
        assert allowed is True
        assert q_new["runs_used"] == 1
        assert q_new["runs_remaining"] == 4


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
    login_resp = client.post("/api/auth/demo-login")
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
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
