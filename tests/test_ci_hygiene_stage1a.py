"""Regression checks for Stage 1A container hygiene, port alignment, and hermetic test isolation."""

from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi.testclient import TestClient

from bionemo_benchmark.reporting.nvidia_showcase import BioNeMoBlueprintGenerator
from bionemo_benchmark.server.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_dockerignore_uses_default_deny_and_blocks_secrets():
    dockerignore = REPO_ROOT / ".dockerignore"
    assert dockerignore.is_file()
    raw_lines = [line.strip() for line in dockerignore.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    assert raw_lines[0] == "*", ".dockerignore must start with default-deny '*'"

    required_allows = {
        "!pyproject.toml",
        "!src/",
        "!src/**",
        "!data/sample_complexes.json",
        "!results/benchmark_summary.json",
        "!cockpit.html",
        "!index.html",
        "!js/",
        "!js/**",
        "!css/",
        "!css/**",
    }
    missing = required_allows - set(raw_lines)
    assert not missing, f"Missing required runtime allowlist rules: {sorted(missing)}"

    required_denies = {
        "data/.*",
        "data/*_auth.json",
        "data/*_ledger.json",
        "scratch/",
        "dist_npm/",
        "audit/",
        ".git/",
        ".venv/",
        ".env",
        ".env.*",
        "**/*.egg-info/",
        "src/bionemo_benchmark/data/",
    }
    missing_denies = required_denies - set(raw_lines)
    assert not missing_denies, f"Missing required explicit deny exclusions: {sorted(missing_denies)}"


def test_docker_compose_excludes_env_file_and_exposes_explicit_runtime_vars():
    compose_text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "env_file" not in compose_text, "docker-compose.yml must not load blanket .env via env_file"
    for key in (
        "NVIDIA_API_KEY",
        "PORT",
        "DISABLE_TRIAL_LIMIT",
        "NIM_ALLOWED_HOSTS",
        "NIM_ALLOW_PRIVATE_HOSTS",
    ):
        assert key in compose_text, f"docker-compose.yml must pass explicit runtime var {key}"
    assert "8088:8088" in compose_text


def test_env_example_contains_runtime_only_keys():
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    for forbidden in ("PYPI_API_TOKEN", "DOCKER_PAT", "NPM_TOKEN", "READTHEDOCS_TOKEN", "CRATES_IO_TOKEN"):
        assert forbidden not in env_example
    for required in ("NVIDIA_API_KEY", "PORT", "DISABLE_TRIAL_LIMIT", "NIM_ALLOWED_HOSTS", "NIM_ALLOW_PRIVATE_HOSTS"):
        assert required in env_example


def test_dockerfile_and_blueprint_ports_aligned_to_8088():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "EXPOSE 8088" in dockerfile
    assert "PORT=8088" in dockerfile
    assert '"--port", "8088"' in dockerfile

    blueprint_compose = BioNeMoBlueprintGenerator.generate_docker_compose()
    assert re.search(r'"8088:8088"', blueprint_compose), "Blueprint compose must expose cockpit port 8088:8088"
    assert '"8000:8000"' not in blueprint_compose
    assert "PORT=8088" in blueprint_compose


def test_pytest_isolation_redirects_results_and_data_writes():
    import bionemo_benchmark.infra.auth_manager as auth_manager_mod
    import bionemo_benchmark.infra.trial_limiter as trial_limiter_mod
    import bionemo_benchmark.server.routes_campaign as routes_campaign_mod
    import bionemo_benchmark.server.serializers as serializers_mod

    repo_results = os.path.abspath(str(REPO_ROOT / "results"))
    repo_data = os.path.abspath(str(REPO_ROOT / "data"))

    assert not os.path.abspath(routes_campaign_mod.RESULTS_DIR).startswith(repo_results)
    assert not os.path.abspath(serializers_mod.RESULTS_DIR).startswith(repo_results)
    assert not os.path.abspath(auth_manager_mod.AUTH_LEDGER_PATH).startswith(repo_data)
    assert not os.path.abspath(trial_limiter_mod.LEDGER_PATH).startswith(repo_data)

    client = TestClient(app)
    run_res = client.post("/api/run?target=KRAS+G12D&candidates=2", headers={"X-BioNeMo-CSRF": "1"})
    assert run_res.status_code == 200
    assert (Path(routes_campaign_mod.RESULTS_DIR) / "CANDIDATE_SELECTION_DOSSIER.md").is_file()
