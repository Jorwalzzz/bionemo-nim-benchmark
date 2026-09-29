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


if __name__ == "__main__":
    mcp.run()
