"""
Unit tests for Authenticated Feedback Submissions and Ingestion.
"""

import os
import tempfile
import pytest
os.environ["PBKDF2_ITERATIONS"] = "1000"
import bionemo_benchmark.infra.auth_manager as am
am.PBKDF2_ITERATIONS = 1000
from bionemo_benchmark.infra.auth_manager import AuthManager


@pytest.fixture
def auth_mgr():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = os.path.join(tmpdir, "test_auth.json")
        feedback = os.path.join(tmpdir, "test_feedback.json")
        mgr = AuthManager(ledger_path=ledger, feedback_path=feedback, daily_limit=5)
        yield mgr


class TestFeedbackSubmissions:
    def test_authenticated_feedback_success(self, auth_mgr):
        """Authenticated researcher can submit valid feedback."""
        ok, user, _ = auth_mgr.register_user("dr.chen@biomed.edu", "ChemPass2026!", full_name="Dr. Chen")
        uid = user["user_id"]

        ok, entry, msg = auth_mgr.submit_feedback(
            user_id=uid,
            category="Scientific Accuracy",
            rating=5,
            comments="KRAS G12D docked pose closely matches crystal structure 8AZV pocket geometry.",
            target_complex="KRAS G12D",
            client_ip="192.168.1.50",
        )
        assert ok is True
        assert entry["user_id"] == uid
        assert entry["email"] == "dr.chen@biomed.edu"
        assert entry["rating"] == 5
        assert entry["category"] == "Scientific Accuracy"
        assert "recorded" in msg.lower()

        # Check retrieval
        history = auth_mgr.get_feedback_for_user(uid)
        assert len(history) == 1
        assert history[0]["feedback_id"] == entry["feedback_id"]

    def test_unauthenticated_user_cannot_submit(self, auth_mgr):
        """Non-existent or unauthenticated user ID cannot submit feedback."""
        ok, _, msg = auth_mgr.submit_feedback(
            user_id="non-existent-user-id",
            category="General",
            rating=4,
            comments="Great platform!",
        )
        assert ok is False
        assert "not found" in msg.lower()

    def test_empty_comments_rejected(self, auth_mgr):
        """Feedback with whitespace or empty comments is rejected."""
        ok, user, _ = auth_mgr.register_user("reviewer@nih.gov", "Secret1234!")
        uid = user["user_id"]

        ok, _, msg = auth_mgr.submit_feedback(
            user_id=uid,
            category="Bug Report",
            rating=1,
            comments="   ",
        )
        assert ok is False
        assert "cannot be empty" in msg.lower()

    def test_invalid_category_defaults_to_general(self, auth_mgr):
        """Unrecognized category safely falls back to 'General'."""
        ok, user, _ = auth_mgr.register_user("researcher@pharma.com", "Secret1234!")
        uid = user["user_id"]

        ok, entry, _ = auth_mgr.submit_feedback(
            user_id=uid,
            category="RandomCategoryNotAllowed",
            rating=4,
            comments="The latency is sub-second on H100 NIM.",
        )
        assert ok is True
        assert entry["category"] == "General"

    def test_rating_clamped_between_1_and_5(self, auth_mgr):
        """Ratings below 1 or above 5 are safely clamped."""
        ok, user, _ = auth_mgr.register_user("eval@mit.edu", "Secret1234!")
        uid = user["user_id"]

        ok, entry_high, _ = auth_mgr.submit_feedback(
            user_id=uid, category="General", rating=10, comments="Superb"
        )
        assert entry_high["rating"] == 5

        ok, entry_low, _ = auth_mgr.submit_feedback(
            user_id=uid, category="General", rating=-2, comments="Sub-par"
        )
        assert entry_low["rating"] == 1
