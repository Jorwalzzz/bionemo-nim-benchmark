"""
TDD verification tests for Task 5: Depth-3 Binary Recursive BRICS Retrosynthesis Tree.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

from bionemo_benchmark.agents.retrosynthesis_agent import RetrosynthesisAgent
from bionemo_benchmark.core.models import MoleculeCandidate


def _walk_tree(node: dict) -> list[dict]:
    nodes = [node]
    for child in node.get("children", []):
        nodes.extend(_walk_tree(child))
    return nodes


def test_recursive_binary_brics_tree_and_clean_terminal_fragments() -> None:
    agent = RetrosynthesisAgent()
    # Multi-ring amide + ether drug (Gefitinib-like): splits recursively up to depth 3
    cand = MoleculeCandidate(
        id="RETRO-1",
        smiles="COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCC1CCN(C)CC1",
        parent_smiles="COc1cc2ncnc(Nc3ccccc3)c2cc1",
    )
    plan = agent.plan_synthesis_route(cand)

    assert isinstance(plan.route_tree, dict)
    assert plan.route_tree["depth"] == 0
    assert isinstance(plan.is_convergent, bool)

    all_nodes = _walk_tree(plan.route_tree)
    assert len(all_nodes) >= 3
    assert max(n["depth"] for n in all_nodes) <= 3

    leaves = [n for n in all_nodes if not n.get("children")]
    assert len(leaves) >= 2
    for leaf in leaves:
        assert leaf.get("status") == "Heuristic Terminal Fragment"
        assert "*" not in leaf["smiles"]

    # Backwards compatibility preserved
    assert plan.num_steps >= 1
    assert len(plan.steps) == plan.num_steps
    assert len(plan.starting_materials) >= 1
