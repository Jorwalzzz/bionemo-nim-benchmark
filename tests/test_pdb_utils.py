"""
Deterministic unit tests for Macromolecular PDB Structure Retrieval,
Sanitization, Sequence Extraction, and C-alpha Synthetic Backbone Synthesis.
Part of NVIDIA BioNeMo Benchmark Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import pytest

from bionemo_benchmark.domain.pdb_utils import (
    clean_pdb_structure,
    extract_sequence_from_pdb,
    fetch_rcsb_pdb,
    generate_synthetic_backbone,
    resolve_protein_structure,
    sanitize_pdb_atom_records,
    validate_sequence,
)

SAMPLE_RAW_PDB = """HEADER    HYDROLASE/HYDROLASE INHIBITOR           09-AUG-23   8AZV
TITLE     CRYSTAL STRUCTURE OF KRAS G12D IN COMPLEX WITH MRTX1133
REMARK    2 RESOLUTION. 1.25 ANGSTROMS.
ATOM      1  N   MET A   1      23.142  12.451  45.123  1.00 15.20           N
ATOM      2  CA  MET A   1      24.201  13.204  45.892  1.00 14.80           C
ATOM      3  C   MET A   1      25.431  12.350  46.120  1.00 15.00           C
ATOM      4  O   MET A   1      26.502  12.890  46.340  1.00 16.10           O
HETATM  500  O   HOH A 101      30.120  15.420  50.110  1.00 22.00           O
HETATM  501  SO4 SO4 A 102      32.100  18.200  48.000  1.00 35.00           S
HETATM  502  C1  LIG B   1      15.000  20.000  25.000  1.00 10.00           C
TER     503      MET A   1
END
"""

SAMPLE_MULTI_CHAIN_PDB = """ATOM      1  N   GLY A   1      10.000  10.000  10.000  1.00 20.00           N
ATOM      2  CA  GLY A   1      11.000  10.000  10.000  1.00 20.00           C
ATOM      3  N   ALA B   1      20.000  20.000  20.000  1.00 20.00           N
ATOM      4  CA  ALA B   1      21.000  20.000  20.000  1.00 20.00           C
END
"""


class TestSanitizePdbAtomRecords:
    """Verifies strict ATOM record filtering for diffusion docking models."""

    def test_retains_atom_records_and_appends_end(self):
        cleaned = sanitize_pdb_atom_records(SAMPLE_RAW_PDB)
        lines = cleaned.strip().splitlines()
        assert len(lines) == 5  # 4 ATOM lines + 1 END
        assert all(line.startswith("ATOM") for line in lines[:-1])
        assert lines[-1] == "END"

    def test_empty_pdb_string_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_pdb_atom_records("")
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_pdb_atom_records("   \n\t  ")

    def test_pdb_without_atom_records_raises_value_error(self):
        no_atoms = "HEADER TEST\nREMARK NO ATOMS HERE\nHETATM 1 O HOH 1 0 0 0\nEND\n"
        with pytest.raises(ValueError, match="No valid 'ATOM' records"):
            sanitize_pdb_atom_records(no_atoms)


class TestGenerateSyntheticBackbone:
    """Verifies autonomous peptide coordinate generation for de novo sequences."""

    def test_synthetic_backbone_geometry(self):
        seq = "MTEYKLVV"
        pdb_str = generate_synthetic_backbone(seq)
        lines = pdb_str.strip().splitlines()

        assert lines[0].startswith("HEADER")
        atom_lines = [line for line in lines if line.startswith("ATOM")]
        assert len(atom_lines) == len(seq)
        assert lines[-1] == "END"

        # Check consecutive C-alpha spacing (3.8 Angstroms on x-axis)
        x_coords = []
        for line in atom_lines:
            x_val = float(line[30:38].strip())
            x_coords.append(x_val)

        for i in range(1, len(x_coords)):
            delta = round(x_coords[i] - x_coords[i - 1], 3)
            assert delta == 3.8

    def test_empty_sequence_raises_value_error(self):
        with pytest.raises(ValueError, match="Sequence cannot be empty"):
            generate_synthetic_backbone("")
        with pytest.raises(ValueError, match="Sequence cannot be empty"):
            generate_synthetic_backbone("   \n ")

    def test_sequence_whitespace_stripped(self):
        seq = " M T E Y\nK L V V "
        pdb_str = generate_synthetic_backbone(seq)
        atom_lines = [line for line in pdb_str.splitlines() if line.startswith("ATOM")]
        assert len(atom_lines) == 8


class TestValidateSequence:
    """Verifies sequence validation against the canonical 20 IUPAC residues."""

    def test_canonical_20_residues_pass(self):
        canonical = "ACDEFGHIKLMNPQRSTVWY"
        valid, invalid = validate_sequence(canonical)
        assert valid is True
        assert invalid == []

    def test_lowercase_canonical_residues_pass(self):
        valid, invalid = validate_sequence("acdefghiklmnpqrstvwy")
        assert valid is True
        assert invalid == []

    def test_non_canonical_residues_flagged(self):
        dirty = "ACDEFGHIKLMNPQRSTVWY-BZX12*"
        valid, invalid = validate_sequence(dirty)
        assert valid is False
        assert set(invalid) == {"-", "B", "Z", "X", "1", "2", "*"}


class TestCleanPdbStructure:
    """Verifies heteroatom stripping and crystallographic water elimination."""

    def test_strip_waters_and_solvents(self):
        cleaned = clean_pdb_structure(SAMPLE_RAW_PDB, keep_hetero=False)
        assert "HOH" not in cleaned
        assert "SO4" not in cleaned
        assert "LIG" not in cleaned
        assert "ATOM" in cleaned
        assert "TER" in cleaned
        assert "END" in cleaned

    def test_retain_non_solvent_heteroatoms(self):
        cleaned = clean_pdb_structure(SAMPLE_RAW_PDB, keep_hetero=True)
        assert "HOH" not in cleaned
        assert "SO4" not in cleaned
        assert "LIG" in cleaned


class TestExtractSequenceFromPdb:
    """Verifies canonical 1-letter residue extraction from crystallographic coordinates."""

    def test_extract_sequence_single_chain(self):
        seq = extract_sequence_from_pdb(SAMPLE_RAW_PDB, chain_id="A")
        assert seq == "M"

    def test_extract_sequence_multi_chain_filtering(self):
        seq_a = extract_sequence_from_pdb(SAMPLE_MULTI_CHAIN_PDB, chain_id="A")
        seq_b = extract_sequence_from_pdb(SAMPLE_MULTI_CHAIN_PDB, chain_id="B")
        assert seq_a == "G"
        assert seq_b == "A"


class TestResolveProteinStructure:
    """Verifies hierarchical resolver across cached PDBs, network, and synthetic generation."""

    def test_resolve_from_local_cache(self):
        # 8AZV is present in data/pdbs/
        pdb_content = resolve_protein_structure(pdb_id="8AZV")
        assert "ATOM" in pdb_content
        assert len(pdb_content) > 100

    def test_fallback_to_synthetic_backbone(self):
        pdb_content = resolve_protein_structure(pdb_id=None, sequence="MTEYKLVVVGAGDVGKSALTIQLIQ")
        assert "HEADER    SYNTHETIC BACKBONE" in pdb_content
        assert "CA  M" in pdb_content

    def test_missing_both_args_raises_value_error(self):
        with pytest.raises(ValueError, match="Neither a valid pdb_id nor sequence"):
            resolve_protein_structure(pdb_id=None, sequence=None)

    def test_invalid_pdb_id_format(self):
        with pytest.raises(ValueError, match="Invalid PDB ID format"):
            fetch_rcsb_pdb("TOOLONG_PDB")
