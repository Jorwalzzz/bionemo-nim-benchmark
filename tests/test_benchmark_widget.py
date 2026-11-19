"""
Unit and integration tests for NVIDIA Hardware Acceleration Benchmark endpoint.
Part of NVIDIA BioNeMo Agentic Scientist Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.server.app import app
from bionemo_benchmark.server.routes_benchmark import get_hardware_speedup_benchmark


@pytest.fixture
def client():
    return TestClient(app)


def test_hardware_speedup_benchmark_direct():
    """Verify direct functional execution of hardware speedup benchmark calculation."""
    res = get_hardware_speedup_benchmark()

    assert res["status"] == "success"
    assert "cpu_hardware" in res
    assert "NVIDIA H100" in res["gpu_hardware"]
    assert res["overall_speedup_multiplier"] > 10.0
    assert res["total_cpu_latency_sec"] > res["total_h100_latency_sec"]
    assert len(res["tasks"]) == 3

    modules = [t["module"] for t in res["tasks"]]
    assert any("ESM-2" in m for m in modules)
    assert any("MolMIM" in m for m in modules)
    assert any("DiffDock" in m for m in modules)

    for task in res["tasks"]:
        assert task["speedup"] > 1.0
        assert task["cpu_latency_ms"] > task["h100_latency_ms"]
        assert task["h100_latency_ms"] > 0
        assert isinstance(task["purpose"], str)

    assert res["time_saved_hours_10k_campaign"] > 0.0


def test_hardware_speedup_benchmark_api_endpoint(client):
    """Verify HTTP GET /api/benchmark/speedup returns 200 with hardened headers."""
    resp = client.get("/api/benchmark/speedup")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.headers["x-content-type-options"] == "nosniff"

    data = resp.json()
    assert data["status"] == "success"
    assert data["overall_speedup_multiplier"] >= 15.0
    assert "tasks" in data
    assert len(data["tasks"]) == 3
