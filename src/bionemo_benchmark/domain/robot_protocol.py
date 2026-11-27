"""
Opentrons OT-2 Robotic Liquid Handler Protocol Generator.
Translates NVIDIA BioNeMo retrosynthesis pathways into executable
Python lab automation scripts (Opentrons API v2.15) and wet-lab SOP cards.
"""

import datetime
from typing import Any

from bionemo_benchmark.core.models import RetrosynthesisPlan, RetrosynthesisStep

OT2_TEMPLATE = '''"""
================================================================================
UNVALIDATED COMPUTATIONAL PROTOCOL FOR RESEARCH USE ONLY
Liquid-Handling Plate Setup Only -- Dry-Run Simulation Required
Generated algorithmically by the BioNeMo NIM Benchmark Suite (Open Source).
Dry-run via `opentrons_simulate` and manual labware/volume verification are
required before hardware execution. Thermal reaction, inert-atmosphere, and
purification steps are performed off-deck.
================================================================================
Opentrons OT-2 Automated Liquid-Handling Plate Setup Protocol
Target Candidate: {candidate_id_safe}
Synthetic Route: {num_steps} Steps ({feasibility_safe})
Generated: {timestamp}
"""

from opentrons import protocol_api

metadata = {{
    "protocolName": {protocol_name_repr},
    "author": "BioNeMo NIM Benchmark Suite (Open Source)",
    "description": {description_repr},
    "apiLevel": "2.15"
}}

CAMPAIGN_SPEC = {{
    "candidate_id": {candidate_id_repr},
    "feasibility": {feasibility_repr},
    "num_steps": {num_steps},
}}

SYNTHESIS_STEPS = {steps_repr}


def run(protocol: protocol_api.ProtocolContext):
    # ================= DECK SETUP =================
    tips_300 = protocol.load_labware("opentrons_96_tiprack_300ul", 1)
    reagents = protocol.load_labware("nest_12_reservoir_15ml", 2)
    temp_mod = protocol.load_module("temperature module gen2", 3)
    rxn_block = temp_mod.load_labware("opentrons_24_aluminumblock_nest_1.5ml_snapcap")
    collection_plate = protocol.load_labware("nest_96_wellplate_200ul_flat", 4)
    tips_1000 = protocol.load_labware("opentrons_96_tiprack_1000ul", 5)

    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips_300])
    p1000 = protocol.load_instrument("p1000_single_gen2", "right", tip_racks=[tips_1000])

    protocol.comment("Starting Plate Setup for " + CAMPAIGN_SPEC["candidate_id"])
    protocol.comment("Route Assessment: " + CAMPAIGN_SPEC["feasibility"])
    temp_mod.set_temperature(celsius=25)

    for step in SYNTHESIS_STEPS:
        dest_well = rxn_block[step["dest_well"]]
        protocol.comment(f"Step {{step['step_number']}}: {{step['reaction_type']}}")
        for well_id in step["reactant_wells"]:
            p300.pick_up_tip()
            p300.aspirate(120, reagents[well_id])
            p300.dispense(120, dest_well)
            p300.mix(3, 80, dest_well)
            p300.drop_tip()
        for well_id in step["reagent_wells"]:
            p300.pick_up_tip()
            p300.aspirate(50, reagents[well_id])
            p300.dispense(50, dest_well)
            p300.mix(4, 100, dest_well)
            p300.drop_tip()

    p1000.pick_up_tip()
    p1000.aspirate(200, rxn_block["A1"])
    p1000.dispense(200, collection_plate["A1"])
    p1000.drop_tip()

    temp_mod.set_temperature(celsius=4)
    protocol.comment("Plate setup complete. Holding at 4 C for off-deck processing.")
'''


def generate_ot2_protocol(
    plan: RetrosynthesisPlan | None = None,
    lead_id: str | None = None,
    lead_smiles: str | None = None,
    synthesis_steps: list[dict[str, Any]] | None = None,
    **kwargs,
) -> str:
    """
    Generates CWE-94-safe Opentrons API v2.15 Python protocol string.
    """
    if plan is None:
        cid = lead_id or kwargs.get("candidate_id", "LEAD-001")
        sm = lead_smiles or kwargs.get("smiles", "CC(=O)N1CCNCC1")
        steps_raw = synthesis_steps or []
        parsed_steps = []
        for idx, s in enumerate(steps_raw, start=1):
            if isinstance(s, RetrosynthesisStep):
                parsed_steps.append(s)
            elif isinstance(s, dict):
                parsed_steps.append(
                    RetrosynthesisStep(
                        step_number=s.get("step", idx),
                        reaction_type=s.get("reaction_type", "Coupling"),
                        reaction_smarts="",
                        reactants=s.get("reactants", [{"name": f"Reactant_{idx}"}]),
                        reagents=s.get("reagents", ["DIPEA", "DMF"]),
                        product_smiles=sm,
                        estimated_yield_pct=float(s.get("yield_pct", 85.0)),
                        difficulty=s.get("difficulty", "Heuristic"),
                    )
                )
        plan = RetrosynthesisPlan(
            candidate_id=cid,
            target_smiles=sm,
            num_steps=len(parsed_steps) or 1,
            overall_feasibility="Heuristic BRICS / Literature Precedent"
            if len(parsed_steps) <= 2
            else "Multi-Step Heuristic Route",
            steps=parsed_steps,
            starting_materials=["Heuristic Terminal Fragment A", "Heuristic Terminal Fragment B"],
        )

    from bionemo_benchmark.infra.security_sentinel import SafeSanitizer

    safe_candidate_id = SafeSanitizer.sanitize_code_literal(plan.candidate_id, 40) or "LEAD-001"
    raw_feasibility = str(plan.overall_feasibility).replace("Commercially Accessible", "Heuristic BRICS / Literature Precedent")
    safe_feasibility = SafeSanitizer.sanitize_code_literal(raw_feasibility, 60) or "Heuristic"

    steps_payload: list[dict[str, Any]] = []
    for idx, step in enumerate(plan.steps, start=1):
        safe_rxn_type = SafeSanitizer.sanitize_code_literal(step.reaction_type, 60) or "Step"
        safe_difficulty = SafeSanitizer.sanitize_code_literal(step.difficulty, 40) or "Heuristic"
        reactant_wells = [f"A{((idx - 1) * 2 + r_idx) % 12 + 1}" for r_idx, _ in enumerate(step.reactants, start=1)]
        reagent_wells = [f"A{min(12, rg_idx + 6)}" for rg_idx, _ in enumerate(step.reagents, start=1)]
        steps_payload.append(
            {
                "step_number": int(step.step_number),
                "reaction_type": safe_rxn_type,
                "difficulty": safe_difficulty,
                "dest_well": f"A{min(24, idx)}",
                "reactant_wells": reactant_wells or ["A1"],
                "reagent_wells": reagent_wells or ["A7"],
            }
        )

    if not steps_payload:
        steps_payload.append(
            {
                "step_number": 1,
                "reaction_type": "Stock Plate Setup",
                "difficulty": "Heuristic",
                "dest_well": "A1",
                "reactant_wells": ["A1"],
                "reagent_wells": ["A7"],
            }
        )

    return OT2_TEMPLATE.format(
        candidate_id_safe=safe_candidate_id,
        num_steps=plan.num_steps,
        feasibility_safe=safe_feasibility,
        timestamp=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC"),
        protocol_name_repr=repr(f"BioNeMo Plate Setup: {safe_candidate_id}"),
        description_repr=repr(f"Liquid-handling plate setup for {safe_candidate_id} (Unvalidated)"),
        candidate_id_repr=repr(safe_candidate_id),
        feasibility_repr=repr(safe_feasibility),
        steps_repr=repr(steps_payload),
    )


def generate_lab_card(
    plan: RetrosynthesisPlan | None = None,
    lead_id: str | None = None,
    target_name: str | None = None,
    synthesis_steps: list[dict[str, Any]] | None = None,
    **kwargs,
) -> str:
    """
    Generates standard markdown wet-lab card with reagent requirements and safety precautions.
    """
    cid = lead_id or (plan.candidate_id if plan else "LEAD-001")
    if plan is None:
        steps_raw = synthesis_steps or []
        parsed_steps = []
        for idx, s in enumerate(steps_raw, start=1):
            if isinstance(s, RetrosynthesisStep):
                parsed_steps.append(s)
            elif isinstance(s, dict):
                parsed_steps.append(
                    RetrosynthesisStep(
                        step_number=s.get("step", idx),
                        reaction_type=s.get("reaction_type", "Coupling"),
                        reaction_smarts="",
                        reactants=s.get("reactants", [{"name": f"Reactant_{idx}"}]),
                        reagents=s.get("reagents", ["DIPEA", "DMF"]),
                        product_smiles="CC(=O)N1CCNCC1",
                        estimated_yield_pct=float(s.get("yield_pct", 85.0)),
                        difficulty=s.get("difficulty", "Heuristic"),
                    )
                )
        plan = RetrosynthesisPlan(
            candidate_id=cid,
            target_smiles=kwargs.get("lead_smiles", "CC(=O)N1CCNCC1"),
            num_steps=len(parsed_steps) or 1,
            overall_feasibility="Heuristic BRICS / Literature Precedent",
            steps=parsed_steps,
            starting_materials=["Heuristic Terminal Fragment A", "Heuristic Terminal Fragment B"],
        )

    now_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    feas_str = str(plan.overall_feasibility).replace("Commercially Accessible", "Heuristic BRICS / Literature Precedent")
    lines = [
        f"# Wet-Lab Protocol Card -- {cid}",
        "> [!WARNING]",
        "> **UNVALIDATED COMPUTATIONAL PROTOCOL -- RESEARCH USE ONLY**",
        "> This protocol was algorithmically generated by the open-source BioNeMo NIM Benchmark Suite.",
        "> It has not undergone empirical wet-lab validation. Verify chemical compatibility, solvent volatility, and PPE requirements before execution.",
        "",
        f"> **Generated:** {now_str} | **Target Scaffold:** `{plan.target_smiles}`",
        "",
        "## 1. Route Overview",
        f"- **Synthetic Complexity:** {feas_str}",
        f"- **Total Transformations:** {plan.num_steps} Steps",
        f"- **Estimated Turnaround Time:** {plan.estimated_turnaround_days} Days",
        "",
        "## 2. Heuristic Terminal Fragments",
    ]

    for sm in plan.starting_materials:
        lines.append(f"- [ ] **Fragment:** `{sm}` (Heuristic Terminal Fragment)")

    lines.extend(["", "## 3. Step-by-Step Reaction Conditions"])

    for step in plan.steps:
        lines.append(f"### Step {step.step_number}: {step.reaction_type}")
        lines.append(f"- **Difficulty:** {step.difficulty}")
        lines.append(f"- **Anticipated Isolated Yield:** {step.estimated_yield_pct:.0f}%")
        lines.append(f"- **Reagents / Catalysts:** {', '.join(step.reagents)}")
        if step.reactants:
            r_names = [f"`{r.get('name', 'Compound')}`" for r in step.reactants]
            lines.append(f"- **Reactants:** {', '.join(r_names)}")
        lines.append("- **Quality Control:** Analyze aliquot by LC-MS (ESI+) to confirm product mass before downstream step.")
        lines.append("")

    lines.extend(
        [
            "## 4. Robotic Automation Instructions (Opentrons OT-2)",
            "1. Simulate the protocol via `opentrons_simulate` before hardware execution.",
            "2. Place 300 uL tip rack in **Slot 1** and 1000 uL tip rack in **Slot 5**.",
            "3. Prime Reagent Reservoir in **Slot 2** with stock solutions as outlined in deck map.",
            "4. Mount Temperature Module Gen2 in **Slot 3** with 24-well 1.5 mL aluminum block.",
            "5. Thermal reaction, inert-atmosphere, and purification steps are performed off-deck.",
            "",
            "---",
            "*Safety & Regulatory Notice (AGPL-3.0-only): Provided for research exploration only. "
            "NVIDIA, BioNeMo, NIM, TensorRT, and Hopper are trademarks of NVIDIA Corporation; independently developed by Aarav Jorwal (@Jorwalzzz).*",
        ]
    )

    return "\n".join(lines)
