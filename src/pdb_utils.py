"""
PDB Structure Retrieval, Sanitization, and Synthetic Backbone Utility.

Provides automated fetching of experimental protein structures from RCSB PDB,
strict atom record filtering for NVIDIA NIM DiffDock compatibility,
and dynamic alpha-carbon (C-alpha) backbone synthesis from raw amino acid sequences.
"""

from __future__ import annotations

import os
import re
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

RCSB_PDB_DOWNLOAD_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"


def sanitize_pdb_atom_records(pdb_text: str) -> str:
    """
    Filters raw PDB text to retain only 'ATOM' records and appends 'END'.
    Ensures input compatibility with molecular docking diffusion models like DiffDock.
    """
    if not pdb_text or not pdb_text.strip():
        raise ValueError("PDB content cannot be empty.")

    filtered_lines = [
        line.strip()
        for line in pdb_text.splitlines()
        if line.startswith("ATOM")
    ]

    if not filtered_lines:
        raise ValueError("No valid 'ATOM' records found in provided PDB data.")

    filtered_lines.append("END")
    return "\n".join(filtered_lines) + "\n"


def fetch_rcsb_pdb(
    pdb_id: str,
    cache_dir: str = "data/pdbs",
    timeout: float = 15.0,
) -> str:
    """
    Retrieves experimental PDB coordinates from RCSB PDB.
    Caches the filtered ATOM records locally to avoid redundant network I/O.

    Args:
        pdb_id: 4-character RCSB PDB identifier (e.g., '1UBQ', '1DLS').
        cache_dir: Directory to save and look up cached PDB structures.
        timeout: Network timeout in seconds.

    Returns:
        Sanitized PDB ATOM text string.
    """
    clean_id = pdb_id.strip().upper()
    if not re.match(r"^[0-9A-Z]{4}$", clean_id):
        raise ValueError(f"Invalid PDB ID format: '{clean_id}'. Expected 4-character alphanumeric code.")

    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{clean_id}.pdb")

    # Return cached version if already present on disk
    if os.path.exists(cache_path):
        logger.debug("Loading cached PDB structure from %s", cache_path)
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    # Query RCSB PDB
    download_url = RCSB_PDB_DOWNLOAD_URL.format(pdb_id=clean_id)
    logger.info("Fetching PDB %s from RCSB (%s)...", clean_id, download_url)

    try:
        response = requests.get(download_url, timeout=timeout)
        if response.status_code != 200:
            raise RuntimeError(f"RCSB PDB returned status {response.status_code} for ID '{clean_id}'")

        sanitized_pdb = sanitize_pdb_atom_records(response.text)

        # Write to disk cache
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(sanitized_pdb)

        logger.info("Successfully fetched and cached PDB %s (%s)", clean_id, cache_path)
        return sanitized_pdb

    except Exception as e:
        logger.warning("Failed to fetch PDB %s from RCSB: %s", clean_id, str(e))
        raise


def generate_synthetic_backbone(sequence: str) -> str:
    """
    Synthesizes an idealized alpha-carbon (CA) chain backbone in standard PDB format
    from an arbitrary amino acid sequence. Used as an autonomous fallback when experimental
    crystallography coordinates are unavailable for a novel or de novo protein.

    Args:
        sequence: Validated amino acid sequence string.

    Returns:
        Standard PDB-formatted string with CA atom coordinates.
    """
    clean_seq = re.sub(r"\s+", "", sequence.strip()).upper()
    if not clean_seq:
        raise ValueError("Sequence cannot be empty for synthetic backbone generation.")

    lines = [f"HEADER    SYNTHETIC BACKBONE GENERATED FOR BioNeMo NIM BENCHMARK"]
    # 3.8 Angstroms between consecutive C-alpha atoms in an extended peptide chain
    for i, aa in enumerate(clean_seq, start=1):
        x = round((i - 1) * 3.8, 3)
        y = 0.000
        z = 0.000
        # Standard PDB format: ATOM, atom_num, atom_name, res_name, chain, res_num, x, y, z, occ, b_factor, element
        line = f"ATOM  {i:5d}  CA  {aa:3s} A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C"
        lines.append(line)

    lines.append("END")
    return "\n".join(lines) + "\n"


def resolve_protein_structure(
    pdb_id: Optional[str] = None,
    sequence: Optional[str] = None,
    cache_dir: str = "data/pdbs",
) -> str:
    """
    Unified resolver: attempts local cache, then RCSB PDB fetch,
    and seamlessly falls back to synthetic backbone generation.
    """
    if pdb_id:
        try:
            return fetch_rcsb_pdb(pdb_id, cache_dir=cache_dir)
        except Exception as e:
            logger.warning("PDB resolution failed for '%s': %s. Checking sequence fallback...", pdb_id, str(e))

    if sequence:
        logger.info("Generating synthetic backbone from amino acid sequence (%d residues)...", len(sequence))
        return generate_synthetic_backbone(sequence)

    raise ValueError("Neither a valid pdb_id nor sequence was provided to resolve protein structure.")
