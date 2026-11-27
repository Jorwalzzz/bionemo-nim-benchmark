"""
Structural biochemistry, RCSB PDB ingestion, real-time molecular redocking,
IND briefing dossier compilation, Opentrons OT-2 robotics, and resistance escape routes.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from bionemo_benchmark.agents.orchestrator import AgenticScientistOrchestrator
from bionemo_benchmark.agents.resistance_engine import ResistanceEscapeEngine
from bionemo_benchmark.agents.target_scout import TargetScoutAgent
from bionemo_benchmark.core.models import (
    MoleculeCandidate,
    RetrosynthesisPlan,
    RetrosynthesisStep,
)
from bionemo_benchmark.domain.robot_protocol import generate_lab_card, generate_ot2_protocol
from bionemo_benchmark.infra.security_sentinel import SafeSanitizer, SecretScrubber
from bionemo_benchmark.reporting.ind_dossier import generate_ind_pdf
from bionemo_benchmark.server.serializers import (
    BASE_DIR,
    auth_manager,
    get_authenticated_user,
    get_client_identifiers,
    logger,
    sanitize_json_numbers,
    sanitize_target_query,
    trial_limiter,
    verify_request_origin,
)

router: APIRouter = APIRouter()


def _authorize_heavy_structure_op(request: Request, action_label: str) -> tuple[Response | None, str | None]:
    """Enforce owner bypass or authenticated atomic quota reservation when trial limits are enabled."""
    if os.environ.get("DISABLE_TRIAL_LIMIT", "").lower() in ("true", "1", "yes"):
        return None, None

    from bionemo_benchmark.server.routes_owner import get_trial_policy

    if get_trial_policy(request).is_owner:
        return None, None

    user = get_authenticated_user(request)
    if not user:
        return (
            JSONResponse(
                status_code=401,
                content={
                    "error": "AUTHENTICATION_REQUIRED",
                    "message": f"Sign in required to perform {action_label}.",
                    "requires_auth": True,
                },
            ),
            None,
        )

    decision = auth_manager.consume_run(user["id"])
    if not decision.allowed:
        return (
            JSONResponse(
                status_code=429,
                content={
                    "error": "DAILY_QUOTA_EXCEEDED",
                    "message": decision.message or "Daily trial quota reached.",
                    "quota": decision.quota_info,
                },
            ),
            None,
        )
    return None, decision.reservation_id


@router.post("/api/target/fetch")
async def api_fetch_target(request: Request) -> Any:
    """Universal Target Ingestion: fetches any RCSB PDB code or resolves query."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin execution blocked for security.",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    target_raw = body.get("target", "KRAS G12D")
    try:
        query = sanitize_target_query(target_raw)
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "error": "VALIDATION_FAILED",
                "message": SecretScrubber.scrub(str(ve)),
            },
        )

    scout = TargetScoutAgent()
    profile, _ = scout.scout_target(query)

    return {
        "success": True,
        "name": profile.name,
        "gene": profile.gene,
        "pdb_id": profile.pdb_id,
        "uniprot_id": profile.uniprot_id,
        "description": profile.description,
        "residue_count": len(profile.canonical_sequence),
        "sequence_preview": profile.canonical_sequence[:45] + "...",
        "pocket_residues": profile.pocket_residues,
        "reference_ligand": profile.reference_ligand_name,
        "pocket_coords": profile.target_pocket_coords,
        "is_esmfold": profile.is_esmfold,
        "mean_plddt": profile.mean_plddt,
        "pdb_text": profile.pdb_text,
    }


@router.get("/api/target/pdb/{pdb_id}")
def get_target_pdb(pdb_id: str) -> Response:
    """Fetches PDB structure text for the 3D WebGL viewer with strict anti-traversal & SSRF controls."""
    try:
        clean_id = SafeSanitizer.validate_pdb_id(pdb_id)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": "INVALID_PDB_ID", "message": str(exc)},
        )

    target_dir = Path(BASE_DIR) / "data" / "pdbs"
    try:
        file_path = SafeSanitizer.validate_safe_path(f"{clean_id}.pdb", target_dir)
    except ValueError as exc:
        return JSONResponse(
            status_code=403,
            content={
                "error": "PATH_TRAVERSAL_DETECTED",
                "message": str(exc),
            },
        )

    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            return Response(content=f.read(), media_type="chemical/x-pdb")

    try:
        url = SafeSanitizer.validate_outbound_url(f"https://files.rcsb.org/download/{clean_id}.pdb")
        resp = SafeSanitizer.safe_http_request(
            "GET",
            url,
            headers={"User-Agent": "BioNeMo-Scout/1.0"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.content[: 5 * 1024 * 1024].decode("utf-8", errors="replace")
            return Response(content=data, media_type="chemical/x-pdb")
    except Exception as exc:
        logger.warning(f"RCSB fetch failed for {clean_id}: {exc}")
    return JSONResponse(
        status_code=404, content={"error": f"PDB {clean_id} not found."}
    )


@router.post("/api/redock")
async def api_redock(request: Request) -> Any:
    """Interactive Chemical Workbench: Re-docks a human-edited molecule in real-time."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin execution blocked for security.",
            },
        )

    auth_err, reservation_id = _authorize_heavy_structure_op(
        request, "interactive molecular redocking"
    )
    if auth_err is not None:
        return auth_err

    session_id, signed_token, fp_hash, client_ip, _ = get_client_identifiers(request)
    usage = trial_limiter.check_usage(session_id, fp_hash, client_ip)
    if usage.get("is_locked", False):
        if reservation_id:
            auth_manager.refund_run(reservation_id)
        return JSONResponse(
            status_code=403,
            content={
                "error": "TRIAL_LIMIT_EXCEEDED",
                "message": "Demo trial quota exhausted. Run the local version for unlimited redocking.",
            },
        )

    try:
        body = await request.json()
        raw_smiles = body.get("smiles", "")
        modified_smiles = SafeSanitizer.sanitize_chemical_smiles(raw_smiles, max_length=500)
        target_name = sanitize_target_query(body.get("target", "KRAS G12D"))
    except Exception as e:
        if reservation_id:
            auth_manager.refund_run(reservation_id)
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid request body: {SecretScrubber.scrub(str(e))}"},
        )

    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    use_mock = os.getenv("USE_MOCK", "false").lower() == "true" or not api_key
    orchestrator = AgenticScientistOrchestrator(api_key=api_key, mock=use_mock)

    try:
        redock_result = orchestrator.redock_modified_candidate(modified_smiles, target_name)
    except Exception:
        if reservation_id:
            auth_manager.refund_run(reservation_id)
        raise
    if reservation_id:
        auth_manager.commit_run(reservation_id)
    return sanitize_json_numbers(redock_result)


@router.post("/api/dossier/pdf")
async def api_generate_ind_pdf(request: Request) -> Response:
    """Generate FDA IND Section 2 nonclinical pharmacology briefing dossier PDF."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin execution blocked for security.",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    dossier_data = body.get("dossier", {})
    benchmark_data = body.get("benchmark", {})

    if not dossier_data:
        dossier_data = {
            "target": "KRAS G12D",
            "pdb_id": "7RPZ",
            "nominated_lead": "LEAD-001",
            "binding_affinity": -9.4,
            "residue_count": 168,
            "screened": 10,
            "pareto_count": 3,
            "provenance": {
                "overall_mode": "HEURISTIC_SIMULATION",
                "mode": "HEURISTIC_SIMULATION",
                "is_simulated": True,
                "pdf_watermark": "HEURISTIC SIMULATION — NOT FOR CLINICAL USE",
                "stages": [
                    {
                        "stage_name": "default_sample_dossier",
                        "status": "MOCK",
                        "notes": "Fallback illustrative dossier preview",
                    }
                ],
            },
            "leads": [
                {
                    "id": "LEAD-001",
                    "smiles": "O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5",
                    "mw": 482.3,
                    "logp": 3.1,
                    "qed": 0.78,
                    "sascore": 2.7,
                    "admet_verdict": "PASS",
                }
            ],
            "retrosynthesis": {
                "num_steps": 2,
                "feasibility": "Commercially Accessible (1-2 steps)",
                "steps": [
                    {
                        "step": 1,
                        "reaction_type": "Amide Coupling (PyBOP/DIPEA)",
                        "reagents": ["DIPEA", "DMF", "rt 2h"],
                        "yield_pct": 84.0,
                        "difficulty": "Routine (★☆☆)",
                    },
                    {
                        "step": 2,
                        "reaction_type": "Suzuki-Miyaura Cross-Coupling",
                        "reagents": ["Pd(dppf)Cl2", "K2CO3", "80°C"],
                        "yield_pct": 78.0,
                        "difficulty": "Routine (★☆☆)",
                    },
                ],
            },
        }

    try:
        pdf_bytes = generate_ind_pdf(dossier_data, benchmark_data)
    except Exception as exc:
        safe_msg = SecretScrubber.scrub(str(exc))
        logger.error("IND Dossier PDF compilation failed: %s", safe_msg)
        return JSONResponse(
            status_code=500,
            content={
                "error": "PDF_GENERATION_FAILED",
                "message": "Failed to compile IND Section 2 Dossier.",
            },
        )

    target_clean = (
        re.sub(r"[^A-Za-z0-9_-]", "_", str(dossier_data.get("target", "Candidate")))[:40]
        or "Candidate"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=FDA_IND_Section2_Briefing_{target_clean}.pdf"
        },
    )


@router.post("/api/robot/protocol")
async def api_robot_protocol(request: Request) -> Response:
    """Generate Opentrons OT-2 automated pipetting protocol (.py) and wet-lab SOP Card (.md)."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin execution blocked for security.",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    lead_id = (
        SafeSanitizer.sanitize_code_literal(str(body.get("lead_id", "LEAD-001")), 30)
        or "LEAD-001"
    )
    raw_smiles = str(body.get("smiles", "CC(=O)N1CCNCC1"))
    smiles = SafeSanitizer.sanitize_chemical_smiles(raw_smiles, 500)
    retro_data = body.get("retrosynthesis", {})

    steps_raw = retro_data.get("steps", [])
    if not steps_raw:
        steps = [
            RetrosynthesisStep(
                step_number=1,
                reaction_type="Amide Coupling (PyBOP/DIPEA)",
                reaction_smarts="",
                reactants=[{"name": "Building Block A (Amine Scaffold)"}],
                reagents=["DIPEA", "DMF", "rt 2h"],
                product_smiles=smiles,
                estimated_yield_pct=85.0,
                difficulty="Routine (★☆☆)",
            ),
            RetrosynthesisStep(
                step_number=2,
                reaction_type="Suzuki-Miyaura Cross-Coupling",
                reaction_smarts="",
                reactants=[{"name": "Boronic Acid Intermediate"}],
                reagents=["Pd(dppf)Cl2", "K2CO3", "80°C"],
                product_smiles=smiles,
                estimated_yield_pct=78.0,
                difficulty="Routine (★☆☆)",
            ),
        ]
    else:
        steps = [
            RetrosynthesisStep(
                step_number=s.get("step", idx + 1),
                reaction_type=re.sub(
                    r"[^A-Za-z0-9\(\)\/\-\s★☆]",
                    "",
                    str(s.get("reaction_type", "Coupling Transformation")),
                )[:100],
                reaction_smarts="",
                reactants=s.get("reactants", [{"name": f"Reactant {idx + 1}"}]),
                reagents=s.get("reagents", ["Standard Reagents"]),
                product_smiles=re.sub(
                    r"[^A-Za-z0-9@+\-\[\]\(\)\\\/=#%.:]",
                    "",
                    str(s.get("product_smiles", smiles)),
                )[:500],
                estimated_yield_pct=float(s.get("yield_pct", 75.0)),
                difficulty=str(s.get("difficulty", "Routine (★☆☆)"))[:50],
            )
            for idx, s in enumerate(steps_raw)
        ]

    starting_materials = retro_data.get(
        "starting_materials",
        [
            "4-bromo-2-fluorobenzonitrile (CAS: 105942-08-3)",
            "N-Boc-piperazine (CAS: 57260-71-6)",
        ],
    )

    plan = RetrosynthesisPlan(
        candidate_id=lead_id,
        target_smiles=smiles,
        num_steps=len(steps),
        overall_feasibility=str(
            retro_data.get("feasibility", "Commercially Accessible (1-2 steps)")
        )[:100],
        steps=steps,
        starting_materials=starting_materials,
        estimated_turnaround_days=7,
    )

    ot2_py = generate_ot2_protocol(plan)
    lab_card_md = generate_lab_card(plan, lead_id)

    return JSONResponse(
        {
            "status": "success",
            "candidate_id": lead_id,
            "ot2_protocol_py": ot2_py,
            "lab_card_md": lab_card_md,
            "num_steps": len(steps),
            "feasibility": plan.overall_feasibility,
            "filename_py": f"ot2_protocol_{lead_id}.py",
            "filename_md": f"wetlab_card_{lead_id}.md",
        }
    )


@router.post("/api/resistance/evolve")
async def api_resistance_evolve(request: Request) -> Response:
    """Adaptive Resistance Escape Engine simulation."""
    if not verify_request_origin(request):
        return JSONResponse(
            status_code=403,
            content={
                "error": "CSRF_ORIGIN_REJECTED",
                "message": "Cross-origin execution blocked for security.",
            },
        )

    auth_err, reservation_id = _authorize_heavy_structure_op(
        request, "adaptive resistance escape mutations"
    )
    if auth_err is not None:
        return auth_err

    session_id, signed_token, fp_hash, client_ip, _ = get_client_identifiers(request)
    usage = trial_limiter.check_usage(session_id, fp_hash, client_ip)
    if usage.get("is_locked", False):
        if reservation_id:
            auth_manager.refund_run(reservation_id)
        return JSONResponse(
            status_code=403,
            content={
                "error": "TRIAL_LIMIT_EXCEEDED",
                "message": "Demo trial quota exhausted. Run the local version for unlimited resistance scans.",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    lead_smiles = (
        re.sub(r"[^A-Za-z0-9@+\-\[\]\(\)\\\/=#%.:]", "", str(body.get("smiles", "")))[:500]
        or "O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5"
    )
    lead_id = (
        re.sub(r"[^A-Za-z0-9_-]", "", str(body.get("lead_id", "LEAD-001")))[:30]
        or "LEAD-001"
    )
    target_name = sanitize_target_query(body.get("target", "KRAS G12D"))
    try:
        affinity = float(body.get("binding_affinity", -9.2))
    except (ValueError, TypeError):
        affinity = -9.2

    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    mock = os.getenv("USE_MOCK", "false").lower() == "true" or not api_key

    try:
        scout = TargetScoutAgent(api_key=api_key, mock=mock)
        target_prof, _ = scout.scout_target(target_name)

        lead_cand = MoleculeCandidate(
            id=lead_id,
            smiles=lead_smiles,
            parent_smiles=lead_smiles,
            binding_affinity=affinity,
        )

        engine = ResistanceEscapeEngine(api_key=api_key, mock=mock)
        scan = engine.scan_and_evolve(lead=lead_cand, target=target_prof)
    except Exception:
        if reservation_id:
            auth_manager.refund_run(reservation_id)
        raise
    if reservation_id:
        auth_manager.commit_run(reservation_id)

    return JSONResponse(
        {
            "status": "success",
            "original_lead_id": scan.original_lead_id,
            "original_affinity": scan.original_affinity,
            "hotspot_residues": scan.hotspot_residues,
            "mutation_simulated": scan.mutation_simulated,
            "mutant_affinity": scan.mutant_affinity,
            "resistance_detected": scan.resistance_detected,
            "evolved_lead_id": scan.evolved_lead_id,
            "evolved_smiles": scan.evolved_lead_smiles,
            "evolved_lead_smiles": scan.evolved_lead_smiles,
            "evolved_affinity": scan.evolved_affinity,
            "delta_recovery": scan.delta_recovery,
            "nim_calls_made": scan.nim_calls_made,
            "structural_mechanism": scan.structural_mechanism,
            "verdict": "RESISTANCE BYPASSED" if scan.resistance_detected else "STABLE LEAD",
        }
    )


@router.post("/api/molecule/svg")
async def render_molecule_svg(request: Request) -> Response:
    """Render a 2D RDKit SVG depiction for a validated SMILES string."""
    origin_err = verify_request_origin(request)
    if origin_err:
        return origin_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "INVALID_JSON"})

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "INVALID_PAYLOAD"})

    raw_smiles = body.get("smiles", "")
    if not isinstance(raw_smiles, str):
        return JSONResponse(status_code=400, content={"error": "INVALID_SMILES"})

    smiles = raw_smiles.strip()
    if not smiles or len(smiles) > 512:
        return JSONResponse(
            status_code=400,
            content={"error": "SMILES must be between 1 and 512 characters."},
        )
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in smiles):
        return JSONResponse(status_code=400, content={"error": "INVALID_CONTROL_CHARS"})

    theme = str(body.get("theme", "dark")).lower()

    try:
        from rdkit import Chem
        from rdkit.Chem import rdDepictor
        from rdkit.Chem.Draw import rdMolDraw2D

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return JSONResponse(status_code=400, content={"error": "UNPARSEABLE_SMILES"})

        rdDepictor.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(260, 150)
        opts = drawer.drawOptions()
        opts.clearBackground = False
        if theme == "dark":
            opts.setBackgroundColour((0.043, 0.055, 0.078, 0.0))
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as exc:
        logger.warning("2D SVG render failed: %s", SecretScrubber.redact(str(exc)))
        return JSONResponse(status_code=500, content={"error": "SVG_RENDER_FAILED"})
