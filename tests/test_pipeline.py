"""
Unit and Integration Test Suite for BioNeMo & NIM Inference Benchmark.

Tests:
1. RDKit SMILES sanitization and valency validation (valid molecules vs invalid/hypervalent SMILES).
2. NimBioClient mock responses, status codes, and latency profiling.
3. ESM-2 output tensor shape and hidden dimension integrity.
4. DiffDock molecular docking response envelope, pose rankings, and binding affinity values.
5. LocalCPUBaseline latency, throughput, and memory tracking.
6. End-to-end pipeline execution across complex samples.
"""

from __future__ import annotations

import pytest
import numpy as np

from src.client import NimBioClient, ESM2Response, DiffDockResponse
from src.baseline import LocalCPUBaseline, BaselineProfileResult
from src.pipeline import BenchmarkPipeline, LigandValidationResult, ComplexBenchmarkRecord


class TestSmilesSanitization:
    """Tests RDKit small-molecule sanitization and valency checks."""

    def test_valid_fda_smiles(self):
        # Aspirin
        aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
        result = BenchmarkPipeline.sanitize_ligand_smiles(aspirin_smiles)
        assert result.is_valid is True
        assert result.canonical_smiles == "CC(=O)Oc1ccccc1C(=O)O"
        assert result.molecular_formula == "C9H8O4"
        assert result.molecular_weight is not None and abs(result.molecular_weight - 180.16) < 0.5
        assert result.error_message is None

    def test_imatinib_smiles(self):
        # Imatinib
        imatinib = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc4nccc(-c5cccnc5)n4"
        result = BenchmarkPipeline.sanitize_ligand_smiles(imatinib)
        assert result.is_valid is True
        assert result.molecular_weight is not None and abs(result.molecular_weight - 493.6) < 1.0
        assert result.num_hbd == 2
        assert result.num_hba == 7

    def test_invalid_syntax_smiles(self):
        # Malformed SMILES
        bad_smiles = "C1CC(INVALID)C"
        result = BenchmarkPipeline.sanitize_ligand_smiles(bad_smiles)
        assert result.is_valid is False
        assert result.canonical_smiles == ""
        assert result.error_message is not None

    def test_hypervalent_nitrogen_valency_failure(self):
        # Chemically impossible 6-valent carbon / nitrogen
        hypervalent = "C(=O)(=O)(=O)(=O)C"
        result = BenchmarkPipeline.sanitize_ligand_smiles(hypervalent)
        assert result.is_valid is False
        assert "Explicit valence" in result.error_message or "sanitization" in result.error_message.lower()

    def test_empty_smiles_handling(self):
        result = BenchmarkPipeline.sanitize_ligand_smiles("")
        assert result.is_valid is False
        assert "Empty" in result.error_message


class TestSequenceValidation:
    """Tests protein sequence sanitization and IUPAC checking."""

    def test_valid_canonical_sequence(self):
        seq = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
        cleaned = NimBioClient.validate_protein_sequence(seq)
        assert cleaned == seq

    def test_sequence_with_whitespace_and_lowercase(self):
        seq = "  mqifvkt ltgkt \n itleve  "
        cleaned = NimBioClient.validate_protein_sequence(seq)
        assert cleaned == "MQIFVKTLTGKTITLEVE"

    def test_non_canonical_amino_acid_rejected(self):
        bad_seq = "MQIFBZX123"
        with pytest.raises(ValueError, match="invalid non-canonical amino acid"):
            NimBioClient.validate_protein_sequence(bad_seq)

    def test_empty_sequence_rejected(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            NimBioClient.validate_protein_sequence("   ")


class TestNimBioClientMock:
    """Tests NimBioClient mock simulation behavior."""

    @pytest.fixture
    def client(self):
        return NimBioClient(mock=True)

    def test_esm2_mock_envelope(self, client):
        seq = "MQIFVKTLTGKTITLEVE"
        resp: ESM2Response = client.get_esm2_embeddings(seq)
        assert resp.is_mock is True
        assert resp.sequence_length == len(seq)
        assert resp.hidden_dim == 1280
        assert len(resp.embeddings) == len(seq)
        assert len(resp.embeddings[0]) == 1280
        assert resp.latency.total_latency_ms > 0
        assert resp.latency.server_inference_ms > 0
        assert resp.latency.status_code == 200

    def test_diffdock_mock_envelope(self, client):
        seq = "MQIFVKTLTGKTITLEVE"
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        resp: DiffDockResponse = client.dock_complex(seq, smiles, num_poses=5)
        assert resp.is_mock is True
        assert resp.num_poses == 5
        assert len(resp.poses) == 5
        assert resp.poses[0].rank == 1
        assert resp.top_affinity_kcal_mol < 0.0  # Exothermic binding affinity
        assert resp.latency.total_latency_ms > 0


class TestLocalCPUBaseline:
    """Tests CPU baseline execution and profiling."""

    def test_baseline_execution_mock_or_real(self):
        baseline = LocalCPUBaseline(mock_fallback=True)
        seq = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEG"
        res: BaselineProfileResult = baseline.benchmark_sequence(seq, warmup_runs=0, benchmark_runs=1)
        assert res.sequence_length == len(seq)
        assert res.total_cpu_latency_ms > 0.0
        assert res.ms_per_residue > 0.0
        assert res.tokens_per_sec > 0.0
        assert len(res.tensor_shape) == 3  # [batch, seq_len, hidden]


class TestBenchmarkPipelineEndToEnd:
    """Tests end-to-end integration across the orchestrator pipeline."""

    def test_evaluate_single_complex(self):
        client = NimBioClient(mock=True)
        baseline = LocalCPUBaseline(mock_fallback=True)
        pipeline = BenchmarkPipeline(nim_client=client, cpu_baseline=baseline)

        sample = {
            "id": "test_01",
            "target_name": "Ubiquitin",
            "uniprot_id": "P62988",
            "residue_count": 25,
            "sequence": "MQIFVKTLTGKTITLEVEPSDTIEN",
            "drug_name": "Aspirin",
            "drug_indication": "Pain relief",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        }

        record: ComplexBenchmarkRecord = pipeline.evaluate_complex(sample, benchmark_runs=1)
        assert record.complex_id == "test_01"
        assert record.ligand_validation.is_valid is True
        assert record.nim_tokens_per_sec > 0
        assert record.cpu_tokens_per_sec > 0
        assert record.speedup_factor > 0
        assert record.diffdock_poses_count == 5
        assert record.diffdock_top_affinity_kcal_mol < 0.0

        # Validate dictionary serialization
        flat_dict = record.to_dict()
        assert flat_dict["complex_id"] == "test_01"
        assert flat_dict["is_smiles_valid"] is True
        assert "speedup_factor" in flat_dict
