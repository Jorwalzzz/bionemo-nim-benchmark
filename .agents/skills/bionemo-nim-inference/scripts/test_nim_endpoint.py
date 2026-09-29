#!/usr/bin/env python3
"""
Diagnostic script to test connectivity, latency, and response integrity of NVIDIA NIM endpoints.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.client import NimBioClient

def main():
    print("=" * 60)
    print("NVIDIA BioNeMo NIM Endpoint Diagnostic Probe")
    print("=" * 60)

    client = NimBioClient(mock=False)
    has_api_key = bool(client.api_key and client.api_key.startswith("nvapi-"))
    
    print(f"API Key Detected: {'Yes (nvapi-...)' if has_api_key else 'No (Testing with mock fallback)'}")
    print(f"ESM-2 Target URL: {client.esm2_endpoint}")
    print(f"DiffDock Target URL: {client.diffdock_endpoint}")
    print("-" * 60)

    # 1. Test ESM-2
    test_seq = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
    print(f"Testing ESM-2 inference on Ubiquitin ({len(test_seq)} aa)...")
    
    start_time = time.perf_counter()
    try:
        if not has_api_key:
            client.mock = True
        resp = client.get_esm2_embeddings(test_seq)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        print(f"  [SUCCESS] Status: 200 OK (Mock: {resp.is_mock})")
        print(f"  Hidden Dim: {resp.hidden_dim}")
        print(f"  Server Latency: {resp.latency.server_inference_ms:.2f} ms")
        print(f"  Network Latency: {resp.latency.network_overhead_ms:.2f} ms")
        print(f"  Total Round-trip: {elapsed_ms:.2f} ms")
    except Exception as exc:
        print(f"  [FAILED] ESM-2 probe error: {exc}")

    print("-" * 60)
    print("Probe Complete.")

if __name__ == "__main__":
    main()
