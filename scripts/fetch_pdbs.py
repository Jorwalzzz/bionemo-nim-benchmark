#!/usr/bin/env python3
"""
PDB Dataset Footprint Auditor & Fetcher for BioNeMo NIM Benchmark Suite.

Audits, verifies, and synchronizes the 10 reference crystallographic PDBs in `data/pdbs/`
consumed by the Discovery Cockpit, Stage B 3D Pose Lab, and benchmark suites.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Add src to sys.path to access security sentinel
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from bionemo_benchmark.infra.security_sentinel import SafeSanitizer

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PDBS_DIR = BASE_DIR / "data" / "pdbs"

RCSB_URL_TEMPLATE = "https://files.rcsb.org/download/{pdb_id}.pdb"


@dataclass(frozen=True)
class PDBMetadata:
    pdb_id: str
    target_name: str
    indication: str
    expected_size_kb: float


ACTIVE_PDBS: tuple[PDBMetadata, ...] = (
    PDBMetadata("1DLS", "Dihydrofolate Reductase", "Oncology / Antibacterial", 120.6),
    PDBMetadata("1IEP", "Abl Tyrosine Kinase", "Chronic Myeloid Leukemia", 357.0),
    PDBMetadata("1M17", "EGFR Kinase Domain", "Non-Small Cell Lung Cancer", 201.1),
    PDBMetadata("1UBQ", "Ubiquitin", "Structural Reference Standard", 48.2),
    PDBMetadata("2ITZ", "EGFR T790M Mutant", "Drug-Resistant NSCLC", 251.8),
    PDBMetadata("3PP0", "HER2 Kinase Domain", "Breast & Gastric Cancers", 828.3),
    PDBMetadata("4MNE", "KRAS Switch II Pocket", "Pancreatic & Colorectal Cancer", 1559.3),
    PDBMetadata("7BQY", "SARS-CoV-2 Mpro Protease", "COVID-19 Antiviral Target", 445.0),
    PDBMetadata("7BV2", "SARS-CoV-2 RNA Polymerase", "Viral Replication Target", 687.7),
    PDBMetadata("8AZV", "KRAS G12D Mutant", "Oncogenic Driver Mutation", 220.9),
)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def audit_pdbs(download_missing: bool = False) -> int:
    """Verify presence and integrity of all required PDB structures."""
    DATA_PDBS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 80)
    print(f"PDB DATASET FOOTPRINT AUDIT | Directory: {DATA_PDBS_DIR}")
    print("=" * 80)
    print(f"{'PDB ID':<8} {'Target Name':<28} {'Size (KB)':<12} {'Status':<10} {'SHA-256 (Prefix)':<16}")
    print("-" * 80)

    total_bytes = 0
    missing_count = 0

    for meta in ACTIVE_PDBS:
        pdb_path = DATA_PDBS_DIR / f"{meta.pdb_id}.pdb"
        if pdb_path.is_file():
            size_bytes = pdb_path.stat().st_size
            total_bytes += size_bytes
            sha_prefix = compute_sha256(pdb_path)[:12]
            status = "PRESENT"
            print(f"{meta.pdb_id:<8} {meta.target_name:<28} {size_bytes / 1024:>9.1f} KB  {status:<10} {sha_prefix:<16}")
        else:
            if download_missing:
                print(f"{meta.pdb_id:<8} {meta.target_name:<28} {'MISSING':>9}     DOWNLOADING...", end="\r")
                try:
                    clean_id = SafeSanitizer.validate_pdb_id(meta.pdb_id)
                    safe_path = SafeSanitizer.validate_safe_path(f"{clean_id}.pdb", DATA_PDBS_DIR)
                    url = SafeSanitizer.validate_outbound_url(RCSB_URL_TEMPLATE.format(pdb_id=clean_id))
                    urllib.request.urlretrieve(url, safe_path)  # nosec B310
                    size_bytes = safe_path.stat().st_size
                    total_bytes += size_bytes
                    sha_prefix = compute_sha256(safe_path)[:12]
                    print(f"{meta.pdb_id:<8} {meta.target_name:<28} {size_bytes / 1024:>9.1f} KB  FETCHED    {sha_prefix:<16}")
                except Exception as exc:
                    print(f"{meta.pdb_id:<8} {meta.target_name:<28} {'FAILED':>9}     ERROR      {exc}")
                    missing_count += 1
            else:
                print(f"{meta.pdb_id:<8} {meta.target_name:<28} {'MISSING':>9}     NOT FOUND  —")
                missing_count += 1

    print("-" * 80)
    print(f"Total Dataset Footprint: {total_bytes / (1024 * 1024):.2f} MB across {len(ACTIVE_PDBS) - missing_count}/{len(ACTIVE_PDBS)} PDBs.")
    print("=" * 80)
    return 0 if missing_count == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and download reference PDB structures.")
    parser.add_argument("--fetch", action="store_true", help="Download missing PDB files from RCSB.")
    args = parser.parse_args()
    code = audit_pdbs(download_missing=args.fetch)
    sys.exit(code)


if __name__ == "__main__":
    main()
