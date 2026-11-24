"""Pytest configuration ensuring hermetic test isolation from tracked `results/` and `data/`."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

_SESSION_ISOLATION_DIR = Path(tempfile.mkdtemp(prefix="bionemo_pytest_session_"))


def _init_session_isolation_env() -> None:
    """Point import-time ledgers and secrets to a temporary directory before test collection."""
    data_dir = _SESSION_ISOLATION_DIR / "data"
    results_dir = _SESSION_ISOLATION_DIR / "results"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("AUTH_LEDGER_PATH", str(data_dir / "users_auth.json"))
    os.environ.setdefault("FEEDBACK_LEDGER_PATH", str(data_dir / "feedback_submissions.json"))
    os.environ.setdefault("TRIAL_LEDGER_PATH", str(data_dir / "trial_ledger.json"))
    os.environ.setdefault("BIONEMO_OWNER_AUTH_PATH", str(data_dir / "owner_auth.json"))
    os.environ.setdefault("AUTH_SECRET_KEY", "pytest-hermetic-auth-secret-key-0123456789abcdef")
    os.environ.setdefault("TRIAL_SECRET_KEY", "pytest-hermetic-trial-secret-key-0123456789abcdef")


_init_session_isolation_env()


def pytest_unconfigure(config: pytest.Config) -> None:
    """Remove session-level temporary ledger directory after pytest completes."""
    shutil.rmtree(_SESSION_ISOLATION_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def isolate_workspace_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Redirect all filesystem writes targeting `results/` and `data/` into `tmp_path`."""
    import bionemo_benchmark.agents.orchestrator as orchestrator_mod
    import bionemo_benchmark.core.metrics as metrics_mod
    import bionemo_benchmark.domain.pdb_utils as pdb_utils_mod
    import bionemo_benchmark.infra.auth_manager as auth_manager_mod
    import bionemo_benchmark.infra.trial_limiter as trial_limiter_mod
    import bionemo_benchmark.server.routes_auth as routes_auth_mod
    import bionemo_benchmark.server.routes_campaign as routes_campaign_mod
    import bionemo_benchmark.server.routes_structure as routes_structure_mod
    import bionemo_benchmark.server.serializers as serializers_mod

    tmp_results = tmp_path / "results"
    tmp_data = tmp_path / "data"
    tmp_pdbs = tmp_data / "pdbs"
    tmp_results.mkdir(parents=True, exist_ok=True)
    tmp_pdbs.mkdir(parents=True, exist_ok=True)

    auth_ledger = str(tmp_data / "users_auth.json")
    feedback_ledger = str(tmp_data / "feedback_submissions.json")
    trial_ledger = str(tmp_data / "trial_ledger.json")
    trial_secret = str(tmp_data / ".trial_secret")
    owner_auth = str(tmp_data / "owner_auth.json")

    monkeypatch.setenv("AUTH_LEDGER_PATH", auth_ledger)
    monkeypatch.setenv("FEEDBACK_LEDGER_PATH", feedback_ledger)
    monkeypatch.setenv("TRIAL_LEDGER_PATH", trial_ledger)
    monkeypatch.setenv("BIONEMO_OWNER_AUTH_PATH", owner_auth)
    monkeypatch.setenv("AUTH_SECRET_KEY", "pytest-hermetic-auth-secret-key-0123456789abcdef")
    monkeypatch.setenv("TRIAL_SECRET_KEY", "pytest-hermetic-trial-secret-key-0123456789abcdef")

    monkeypatch.setattr(auth_manager_mod, "DATA_DIR", str(tmp_data))
    monkeypatch.setattr(auth_manager_mod, "AUTH_LEDGER_PATH", auth_ledger)
    monkeypatch.setattr(auth_manager_mod, "FEEDBACK_LEDGER_PATH", feedback_ledger)

    monkeypatch.setattr(trial_limiter_mod, "DATA_DIR", str(tmp_data))
    monkeypatch.setattr(trial_limiter_mod, "LEDGER_PATH", trial_ledger)
    monkeypatch.setattr(trial_limiter_mod, "SECRET_KEY_PATH", trial_secret)

    monkeypatch.setattr(serializers_mod, "DATA_DIR", str(tmp_data))
    monkeypatch.setattr(serializers_mod, "RESULTS_DIR", str(tmp_results))
    monkeypatch.setattr(serializers_mod, "ASSETS_DIR", str(tmp_results / "assets"))
    monkeypatch.setattr(routes_campaign_mod, "RESULTS_DIR", str(tmp_results))

    fresh_auth = auth_manager_mod.AuthManager(
        ledger_path=auth_ledger,
        feedback_path=feedback_ledger,
    )
    fresh_limiter = trial_limiter_mod.TrialLimiter(ledger_path=trial_ledger)

    monkeypatch.setattr(serializers_mod, "auth_manager", fresh_auth)
    monkeypatch.setattr(routes_auth_mod, "auth_manager", fresh_auth)

    monkeypatch.setattr(serializers_mod, "trial_limiter", fresh_limiter)
    monkeypatch.setattr(routes_auth_mod, "trial_limiter", fresh_limiter)
    monkeypatch.setattr(routes_campaign_mod, "trial_limiter", fresh_limiter)
    monkeypatch.setattr(routes_structure_mod, "trial_limiter", fresh_limiter)

    orig_run_campaign = orchestrator_mod.AgenticScientistOrchestrator.run_discovery_campaign

    def _isolated_run_campaign(
        self: Any,
        target_query: str = "KRAS G12D",
        num_candidates: int = 12,
        rounds: int = 1,
        enable_feedback_loop: bool = True,
        output_dir: str = "results",
    ) -> Any:
        safe_out = str(tmp_results) if output_dir == "results" else output_dir
        return orig_run_campaign(
            self,
            target_query=target_query,
            num_candidates=num_candidates,
            rounds=rounds,
            enable_feedback_loop=enable_feedback_loop,
            output_dir=safe_out,
        )

    monkeypatch.setattr(
        orchestrator_mod.AgenticScientistOrchestrator,
        "run_discovery_campaign",
        _isolated_run_campaign,
    )

    orig_reporter_init = metrics_mod.BenchmarkReporter.__init__

    def _isolated_reporter_init(
        self: Any,
        records: list[Any],
        output_dir: str = "results",
    ) -> None:
        safe_out = str(tmp_results) if output_dir == "results" else output_dir
        orig_reporter_init(self, records, output_dir=safe_out)

    monkeypatch.setattr(metrics_mod.BenchmarkReporter, "__init__", _isolated_reporter_init)

    orig_fetch_pdb = pdb_utils_mod.fetch_rcsb_pdb

    def _isolated_fetch_pdb(
        pdb_id: str,
        cache_dir: str = "data/pdbs",
        timeout: float = 15.0,
    ) -> str:
        safe_cache = str(tmp_pdbs) if cache_dir == "data/pdbs" else cache_dir
        return orig_fetch_pdb(pdb_id, cache_dir=safe_cache, timeout=timeout)

    monkeypatch.setattr(pdb_utils_mod, "fetch_rcsb_pdb", _isolated_fetch_pdb)
    yield
