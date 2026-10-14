"""Reporting, visualization, and NVIDIA showcase utilities."""
from bionemo_benchmark.reporting.ind_dossier import generate_ind_pdf
from bionemo_benchmark.reporting.visualizer import plot_pareto_frontier, plot_chemical_leads_grid
from bionemo_benchmark.reporting.nvidia_showcase import (
    GreenComputeProfiler, MultiGpuScalingEngine, BioNeMoBlueprintGenerator
)

__all__ = [
    "generate_ind_pdf",
    "plot_pareto_frontier",
    "plot_chemical_leads_grid",
    "GreenComputeProfiler",
    "MultiGpuScalingEngine",
    "BioNeMoBlueprintGenerator",
]
