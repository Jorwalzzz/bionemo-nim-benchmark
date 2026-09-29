"""
NVIDIA BioNeMo MCP Server for Antigravity IDE.

Provides native Model Context Protocol (MCP) tools for interacting with:
- NVIDIA BioNeMo & NIM microservices (ESM-2 embeddings, DiffDock molecular docking)
- RDKit cheminformatics (SMILES sanitization, valency, molecular descriptors)
- Macromolecular sequence & PDB preprocessing (IUPAC validation, residue counting)
- BioNeMo benchmark runner and metric profiling
"""

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from src.client import NimBioClient, CANONICAL_AMINO_ACIDS
from src.pipeline import BenchmarkPipeline
from src.pdb_utils import sanitize_pdb_atom_records, generate_synthetic_backbone

mcp = FastMCP("bionemo-tools")


@mcp.tool()
def bionemo_validate_sequence(sequence: str) -> Dict[str, Any]:
    """
    Validate and profile a protein amino acid sequence for NVIDIA BioNeMo / ESM-2.
    
    Args:
        sequence: Single-letter amino acid sequence (IUPAC format).
        
    Returns:
        Dictionary with validation status, clean sequence, length, and residue frequency.
    """
    try:
        clean_seq = NimBioClient.validate_protein_sequence(sequence)
        counts = {aa: clean_seq.count(aa) for aa in sorted(set(clean_seq))}
        est_mw_kda = round((len(clean_seq) * 110.0) / 1000.0, 2)
        return {
            "valid": True,
            "length": len(clean_seq),
            "estimated_mw_kda": est_mw_kda,
            "residue_counts": counts,
            "sanitized_sequence": clean_seq[:60] + ("..." if len(clean_seq) > 60 else ""),
            "full_sequence": clean_seq,
        }
    except Exception as exc:
        return {
            "valid": False,
            "error": str(exc),
            "allowed_canonical_amino_acids": sorted(list(CANONICAL_AMINO_ACIDS)),
        }


@mcp.tool()
def bionemo_sanitize_smiles(smiles: str) -> Dict[str, Any]:
    """
    Validate, sanitize, and extract physicochemical descriptors for a small molecule SMILES
    before dispatching to NVIDIA NIM DiffDock or MolMIM.
    
    Args:
        smiles: Chemical structure SMILES string.
        
    Returns:
        Dictionary containing canonical SMILES, Molecular Weight, LogP, TPSA, HBD, HBA.
    """
    sanitization_result = BenchmarkPipeline.sanitize_ligand_smiles(smiles)
    if not sanitization_result.is_valid:
        return {
            "valid": False,
            "error": sanitization_result.error_message,
            "input_smiles": smiles,
        }
    
    return {
        "valid": True,
        "canonical_smiles": sanitization_result.canonical_smiles,
        "molecular_formula": sanitization_result.molecular_formula,
        "molecular_weight": sanitization_result.molecular_weight,
        "logp": sanitization_result.log_p,
        "tpsa": sanitization_result.tpsa,
        "h_bond_donors": sanitization_result.num_hbd,
        "h_bond_acceptors": sanitization_result.num_hba,
        "rotatable_bonds": sanitization_result.num_rotatable_bonds,
    }


@mcp.tool()
def bionemo_query_esm2_embedding(sequence: str, mock: bool = True) -> Dict[str, Any]:
    """
    Query NVIDIA NIM ESM-2 (650M) for per-residue embeddings.
    
    Args:
        sequence: Valid IUPAC protein amino acid sequence.
        mock: If True, uses the realistic simulation mock (zero API credits required).
              If False, calls live NVIDIA NIM microservice using NVIDIA_API_KEY.
              
    Returns:
        Summary of sequence length, hidden dimension, latency breakdown, and embedding shape.
    """
    client = NimBioClient(mock=mock)
    resp = client.get_esm2_embeddings(sequence)
    total_ms = resp.latency.total_latency_ms
    tok_sec = round((resp.sequence_length / (total_ms / 1000.0)), 1) if total_ms > 0 else 0
    return {
        "model": resp.model,
        "is_mock": resp.is_mock,
        "sequence_length": resp.sequence_length,
        "hidden_dim": resp.hidden_dim,
        "total_latency_ms": round(total_ms, 2),
        "server_inference_ms": round(resp.latency.server_inference_ms, 2),
        "network_overhead_ms": round(resp.latency.network_overhead_ms, 2),
        "tokens_per_second": tok_sec,
    }


@mcp.tool()
def bionemo_query_diffdock(
    protein_sequence: str,
    ligand_smiles: str,
    pdb_content: Optional[str] = None,
    mock: bool = True,
) -> Dict[str, Any]:
    """
    Predict small molecule binding poses and affinities using NVIDIA NIM DiffDock.
    
    Args:
        protein_sequence: Amino acid sequence of the target protein.
        ligand_smiles: SMILES string of the small molecule drug/ligand.
        pdb_content: Optional raw PDB file string. If not provided, a synthetic backbone is generated.
        mock: If True, uses simulated realistic response. If False, calls live NIM endpoint.
        
    Returns:
        Docking results including top affinity (kcal/mol), number of poses, and latency profile.
    """
    clean_seq = NimBioClient.validate_protein_sequence(protein_sequence)
    chem_res = BenchmarkPipeline.sanitize_ligand_smiles(ligand_smiles)
    if not chem_res.is_valid:
        return {"error": f"Invalid SMILES: {chem_res.error_message}"}
    
    client = NimBioClient(mock=mock)
    pdb_str = pdb_content or generate_synthetic_backbone(clean_seq)
    resp = client.run_diffdock(pdb_str, chem_res.canonical_smiles)
    
    poses_summary = [
        {
            "rank": p.rank,
            "confidence_score": round(p.confidence_score, 3),
            "affinity_kcal_mol": round(p.predicted_affinity_kcal_mol, 2),
            "rmsd": round(p.rmsd, 2),
        }
        for p in resp.poses
    ]
    
    return {
        "model": resp.model,
        "is_mock": resp.is_mock,
        "num_poses": resp.num_poses,
        "top_affinity_kcal_mol": resp.top_affinity_kcal_mol,
        "poses": poses_summary,
        "latency_ms": round(resp.latency.total_latency_ms, 2),
    }


@mcp.tool()
def bionemo_run_benchmark(
    mock: bool = True,
    complexes_path: str = "data/sample_complexes.json",
    save_plots: bool = False,
) -> Dict[str, Any]:
    """
    Execute the NVIDIA BioNeMo & NIM Inference Benchmark Suite across the sample complexes.
    
    Args:
        mock: If True, executes using zero-configuration simulated responses.
              If False, connects to live NVIDIA NIM endpoints using NVIDIA_API_KEY.
        complexes_path: Path to JSON file containing complexes (default: data/sample_complexes.json).
        save_plots: Whether to save visualization PNG charts to results/.
        
    Returns:
        Consolidated summary metrics table, speedup factors, and throughput.
    """
    json_path = PROJECT_ROOT / complexes_path
    if not json_path.exists():
        return {"error": f"Complexes file not found at {json_path}"}
        
    with open(json_path, "r", encoding="utf-8") as f:
        complexes = json.load(f)
        
    pipeline = BenchmarkPipeline(mock=mock)
    records = [pipeline.evaluate_complex(c, benchmark_runs=1) for c in complexes]
    
    summary = []
    for r in records:
        summary.append({
            "complex_id": r.complex_id,
            "protein_name": r.target_name,
            "length_aa": r.residue_count,
            "ligand_name": r.drug_name,
            "cpu_latency_ms": round(r.cpu_total_latency_ms, 1),
            "cpu_throughput_tok_s": round(r.cpu_tokens_per_sec, 1),
            "nim_latency_ms": round(r.nim_total_latency_ms, 1),
            "nim_throughput_tok_s": round(r.nim_tokens_per_sec, 1),
            "speedup": round(r.speedup_factor, 2),
            "diffdock_top_affinity_kcal_mol": r.diffdock_top_affinity_kcal_mol,
        })
        
    return {
        "status": "success",
        "mock_mode": mock,
        "num_complexes_evaluated": len(records),
        "results": summary,
    }


@mcp.tool()
def bionemo_fetch_rcsb_pdb(pdb_id: str) -> Dict[str, Any]:
    """
    Fetch, clean, and validate macromolecular structures directly from RCSB PDB.
    Strips solvent, crystallographic waters, and isolates canonical protein chains.
    
    Args:
        pdb_id: 4-character PDB code (e.g. '2ITZ', '6LU7', '8AZV', '4MNE').
        
    Returns:
        Dictionary with status, clean PDB atom count, residue count, and extracted sequence.
    """
    import urllib.request
    
    clean_id = pdb_id.strip().upper()
    if len(clean_id) != 4 or not clean_id.isalnum():
        return {"valid": False, "error": f"Invalid PDB ID format: '{pdb_id}'. Must be 4 alphanumeric characters."}
        
    url = f"https://files.rcsb.org/download/{clean_id}.pdb"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BioNeMo-Antigravity/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_pdb = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"valid": False, "error": f"Failed to download PDB {clean_id} from RCSB: {str(exc)}"}
        
    clean_pdb = sanitize_pdb_atom_records(raw_pdb)
    atom_lines = [l for l in clean_pdb.splitlines() if l.startswith("ATOM  ")]
    
    # Extract unique residue IDs
    residues = set()
    for l in atom_lines:
        if len(l) >= 26:
            residues.add((l[21], l[22:26].strip())) # (chain, resseq)
            
    return {
        "valid": True,
        "pdb_id": clean_id,
        "total_atoms": len(atom_lines),
        "total_residues": len(residues),
        "download_url": url,
        "sanitized_pdb_preview": "\n".join(atom_lines[:15]) + ("\n..." if len(atom_lines) > 15 else ""),
    }


@mcp.tool()
def bionemo_query_esmfold(sequence: str, mock: bool = True) -> Dict[str, Any]:
    """
    Predict atomic 3D protein structure from amino acid sequence via NVIDIA BioNeMo ESMFold NIM.
    
    Args:
        sequence: IUPAC protein amino acid sequence.
        mock: If True, uses zero-credit realistic simulation with predicted pLDDT confidence.
              If False, calls live NVIDIA NIM ESMFold endpoint.
              
    Returns:
        Dictionary with predicted structure status, average pLDDT confidence, and atom records.
    """
    try:
        clean_seq = NimBioClient.validate_protein_sequence(sequence)
    except Exception as exc:
        return {"valid": False, "error": str(exc)}
        
    if mock:
        synthetic_pdb = generate_synthetic_backbone(clean_seq)
        avg_plddt = 88.5
        return {
            "model": "meta/esmfold",
            "is_mock": True,
            "sequence_length": len(clean_seq),
            "mean_plddt": avg_plddt,
            "confidence_assessment": "High confidence backbone and active pocket geometry",
            "total_atoms": len(synthetic_pdb.splitlines()),
            "estimated_latency_ms": 1420.0,
            "pdb_preview": "\n".join(synthetic_pdb.splitlines()[:10]),
        }
        
    # Live NIM ESMFold call
    import urllib.request
    api_key = os.getenv("NVIDIA_API_KEY", "")
    if not api_key:
        return {"valid": False, "error": "NVIDIA_API_KEY not configured in environment"}
        
    url = "https://health.api.nvidia.com/v1/biology/meta/esmfold"
    payload = json.dumps({"sequence": clean_seq}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "model": "meta/esmfold",
                "is_mock": False,
                "sequence_length": len(clean_seq),
                "data": data,
            }
    except Exception as exc:
        return {"valid": False, "error": f"NIM ESMFold call failed: {str(exc)}"}


@mcp.tool()
def bionemo_compare_known_inhibitors(target_name: str, candidate_affinity_kcal_mol: Optional[float] = None) -> Dict[str, Any]:
    """
    Benchmark AI-generated candidate molecules against clinically approved reference drugs.
    
    Args:
        target_name: Target identifier or disease (e.g. 'EGFR', 'Mpro', 'HER2', 'KRAS', 'PARP1').
        candidate_affinity_kcal_mol: Optional predicted affinity of candidate (in kcal/mol, e.g. -9.5).
        
    Returns:
        Clinical reference drug benchmarks with IC50, experimental affinity, and comparative score.
    """
    database = {
        "EGFR": {
            "disease": "Non-Small Cell Lung Cancer (NSCLC)",
            "reference_drugs": [
                {"name": "Osimertinib (Tagrisso)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -9.2, "ic50_nm": 12.0, "mechanism": "Irreversible 3rd-gen T790M mutant inhibitor"},
                {"name": "Gefitinib (Iressa)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -8.7, "ic50_nm": 33.0, "mechanism": "1st-gen ATP-competitive kinase inhibitor"},
            ]
        },
        "MPRO": {
            "disease": "SARS-CoV-2 / COVID-19",
            "reference_drugs": [
                {"name": "Nirmatrelvir (Paxlovid)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -10.1, "ic50_nm": 3.2, "mechanism": "Covalent inhibitor targeting catalytic Cys145"},
                {"name": "Ensitrelvir (Xocova)", "status": "Approved (Japan)", "experimental_affinity_kcal_mol": -9.6, "ic50_nm": 13.0, "mechanism": "Non-covalent non-peptidic Mpro inhibitor"},
            ]
        },
        "HER2": {
            "disease": "HER2+ Metastatic Breast Cancer",
            "reference_drugs": [
                {"name": "Tucatinib (Tukysa)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -9.5, "ic50_nm": 6.9, "mechanism": "Highly selective HER2 kinase inhibitor"},
                {"name": "Lapatinib (Tykerb)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -9.1, "ic50_nm": 10.8, "mechanism": "Dual EGFR / HER2 reversible inhibitor"},
            ]
        },
        "KRAS": {
            "disease": "Colorectal and Pancreatic Ductal Adenocarcinoma",
            "reference_drugs": [
                {"name": "Sotorasib (Lumakras)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -8.9, "ic50_nm": 48.0, "mechanism": "Switch-II pocket covalent G12C inhibitor"},
                {"name": "MRTX1133", "status": "Clinical Trials", "experimental_affinity_kcal_mol": -9.4, "ic50_nm": 5.0, "mechanism": "Selective non-covalent G12D inhibitor"},
            ]
        },
        "PARP1": {
            "disease": "BRCA-Mutated Ovarian & Breast Cancer",
            "reference_drugs": [
                {"name": "Olaparib (Lynparza)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -10.3, "ic50_nm": 5.0, "mechanism": "NAD+ competitor inducing synthetic lethality"},
                {"name": "Niraparib (Zejula)", "status": "FDA Approved", "experimental_affinity_kcal_mol": -9.8, "ic50_nm": 3.8, "mechanism": "PARP-1/2 catalytic trapping inhibitor"},
            ]
        }
    }
    
    key = target_name.strip().upper()
    matched_entry = None
    for k in database:
        if k in key or key in k:
            matched_entry = database[k]
            break
            
    if not matched_entry:
        return {
            "found": False,
            "message": f"Target '{target_name}' not in standard clinical reference set.",
            "available_targets": list(database.keys()),
        }
        
    result = {
        "found": True,
        "target": target_name.upper(),
        "disease_indication": matched_entry["disease"],
        "clinical_reference_benchmarks": matched_entry["reference_drugs"],
    }
    
    if candidate_affinity_kcal_mol is not None:
        best_ref = min(r["experimental_affinity_kcal_mol"] for r in matched_entry["reference_drugs"])
        delta = candidate_affinity_kcal_mol - best_ref
        result["comparison"] = {
            "candidate_affinity_kcal_mol": candidate_affinity_kcal_mol,
            "best_clinical_benchmark_kcal_mol": best_ref,
            "affinity_delta_kcal_mol": round(delta, 2),
            "assessment": "Superior binding energy to clinical drug" if delta < 0 else "Comparable / sub-nanomolar range" if delta <= 0.5 else "Moderate binding energy",
        }
        
    return result


if __name__ == "__main__":
    mcp.run()
