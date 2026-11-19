"""
BioNeMo Benchmark Interactive Cockpit Server launcher.
Delegates to modular bionemo_benchmark.server package.
"""

from bionemo_benchmark.server.app import app, main
from bionemo_benchmark.server.routes_benchmark import get_hardware_speedup_benchmark
from bionemo_benchmark.server.serializers import client_ip, sanitize_target_query

__all__ = [
    "app",
    "main",
    "client_ip",
    "sanitize_target_query",
    "get_hardware_speedup_benchmark",
]

if __name__ == "__main__":
    main()
