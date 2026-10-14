"""
BioNeMo Benchmark Root Package
Provides transparent backward-compatibility shims mapping legacy 'src.<module>'
imports directly into the modular 'bionemo_benchmark' subpackages.
"""
import sys

from bionemo_benchmark.core import baseline, client, metrics, models, pipeline
from bionemo_benchmark.agents import (
    admet_critic, docking_agent, generative_chemist,
    orchestrator, pi_agent, resistance_engine,
    retrosynthesis_agent, target_scout
)
from bionemo_benchmark.infra import message_bus, security_sentinel, trial_limiter
from bionemo_benchmark.domain import pdb_utils, robot_protocol
from bionemo_benchmark.reporting import ind_dossier, nvidia_showcase, visualizer

_LEGACY_MODULES = {
    "src.client": client,
    "src.models": models,
    "src.baseline": baseline,
    "src.metrics": metrics,
    "src.pipeline": pipeline,
    "src.orchestrator": orchestrator,
    "src.pi_agent": pi_agent,
    "src.target_scout": target_scout,
    "src.generative_chemist": generative_chemist,
    "src.docking_agent": docking_agent,
    "src.admet_critic": admet_critic,
    "src.retrosynthesis_agent": retrosynthesis_agent,
    "src.resistance_engine": resistance_engine,
    "src.message_bus": message_bus,
    "src.bus.message_bus": message_bus,
    "src.security_sentinel": security_sentinel,
    "src.trial_limiter": trial_limiter,
    "src.pdb_utils": pdb_utils,
    "src.robot_protocol": robot_protocol,
    "src.ind_dossier": ind_dossier,
    "src.nvidia_showcase": nvidia_showcase,
    "src.visualizer": visualizer,
}

for legacy_name, mod in _LEGACY_MODULES.items():
    sys.modules[legacy_name] = mod
