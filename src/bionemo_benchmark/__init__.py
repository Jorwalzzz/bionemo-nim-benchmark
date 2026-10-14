"""
BioNeMo Benchmark: Autonomous Multi-Agent AI Drug Discovery & Biocompute Suite.
"""

__version__ = "1.0.0"

from bionemo_benchmark.core.client import NimBioClient
from bionemo_benchmark.core.pipeline import BenchmarkPipeline
from bionemo_benchmark.agents.orchestrator import AgenticScientistOrchestrator
from bionemo_benchmark.domain.pdb_utils import resolve_protein_structure, fetch_rcsb_pdb

__all__ = [
    "NimBioClient",
    "BenchmarkPipeline",
    "AgenticScientistOrchestrator",
    "resolve_protein_structure",
    "fetch_rcsb_pdb",
]
