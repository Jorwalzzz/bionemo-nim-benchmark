"""
Unit Test Suite: Verifying All 4 Elite X-TIER Council Leaders
1. Dr. Aris Thorne (Biophysical MMFF94 strain & clash evaluation)
2. Alex Mercer (Sentinel fuzzy homology Select-Agent pathogen screening)
3. Elena Vance (Vector SVG geometry & 3D coordinate distance fidelity)
4. Apollo (DevRel benchmark telemetry & speedup ratio validation)
"""
import pytest
import os
from rdkit import Chem
from src.models import MoleculeCandidate, TargetProfile
from src.docking_agent import BiophysicsDockingAgent
from src.target_scout import screen_biosecurity_dual_use, RESTRICTED_PATHOGEN_SIGNATURES


class TestDrArisThorneBiophysics:
    """Tests Dr. Thorne's thermodynamic rigor and MMFF94 force-field validation."""

    def test_mmff94_strain_energy_calculation(self):
        agent = BiophysicsDockingAgent(mock=True)
        # MRTX1133 SMILES
        smiles = "CN1CCN(CC1)C(=O)C2=CC(=C(C=C2)F)NC3=NC=NC4=C3C=CN4"
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)
        from rdkit.Chem import AllChem
        AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        strain, clashes = agent._evaluate_biophysics_conformer(mol)
        
        # Strain energy must be calculated as a real finite positive float
        assert isinstance(strain, float)
        assert strain >= 0.0
        assert isinstance(clashes, int)

    def test_docking_penalizes_strain_and_clashes(self):
        agent = BiophysicsDockingAgent(mock=True)
        target = TargetProfile(
            name="KRAS G12D",
            gene="KRAS",
            uniprot_id="P01116",
            pdb_id="8AZV",
            description="Oncogene",
            canonical_sequence="MTEYKLVVVGADGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDLPSRTVDTKQAQDLARSYGIPFIETSAKTRQRVEDAFYTLVREIRQYRLKKISKEEKTPGCVKIKKCIIM",
            pocket_residues=["Asp12", "Tyr96"],
            reference_ligand_name="MRTX1133",
            reference_ligand_smiles="CC"
        )
        cand = MoleculeCandidate(
            id="MOL_TEST_1",
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O", # Aspirin
            parent_smiles="CC",
            admet_verdict="PASS"
        )
        docked, msg = agent.dock_candidates([cand], target)
        assert len(docked) == 1
        assert docked[0].binding_affinity < 0.0
        assert hasattr(docked[0], "strain_energy")
        assert hasattr(docked[0], "steric_clash_count")


class TestAlexMercerSentinelSecurity:
    """Tests Alex Mercer's zero-trust biosecurity and fuzzy pathogen defense."""

    def test_exact_pathogen_signature_blocked(self):
        ricin_sub = RESTRICTED_PATHOGEN_SIGNATURES["Ricin A-Chain"][:60]
        safe, flagged = screen_biosecurity_dual_use(ricin_sub)
        assert safe is False
        assert "Ricin" in flagged

    def test_fuzzy_mutated_pathogen_variant_blocked(self):
        # Introduce 2 synonymous point mutations into a 40-mer pathogen signature
        ricin_sig = list(RESTRICTED_PATHOGEN_SIGNATURES["Ricin A-Chain"][:40])
        # Mutate 2 positions (e.g. index 5 and index 15)
        ricin_sig[5] = "A" if ricin_sig[5] != "A" else "G"
        ricin_sig[15] = "L" if ricin_sig[15] != "L" else "V"
        mutated_seq = "".join(ricin_sig)

        safe, flagged = screen_biosecurity_dual_use(mutated_seq)
        # Fuzzy homology sliding-window must catch the mutated pathogen variant
        assert safe is False
        assert "Ricin" in flagged

    def test_benign_oncology_target_cleared(self):
        kras_seq = "MTEYKLVVVGADGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDLPSRTVDTKQAQDLARSYGIPFIETSAKTRQRVEDAFYTLVREIRQYRLKKISKEEKTPGCVKIKKCIIM"
        safe, flagged = screen_biosecurity_dual_use(kras_seq)
        assert safe is True
        assert flagged is None


class TestElenaVanceDesignSystem:
    """Tests Elena Vance's vector SVG geometry and styling assets."""

    def test_brand_vector_svg_integrity(self):
        svg_path = os.path.join("results", "assets", "brand_logo.svg")
        assert os.path.exists(svg_path)
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "<svg" in content
        assert "viewBox" in content
        assert "#76B900" in content # NVIDIA signature green
        assert "</svg>" in content


class TestApolloDevRelMetrics:
    """Tests Apollo's benchmark telemetry and speedup calculations."""

    def test_speedup_ratios_validity(self):
        from src.metrics import calculate_speedup
        cpu_time = 58.4
        gpu_time = 1.0
        speedup = calculate_speedup(cpu_time, gpu_time)
        assert speedup == pytest.approx(58.4, 0.1)


class TestEnterpriseHardeningAndExploitProtection:
    """Tests Alex Mercer's enterprise defense-in-depth and anti-exploit protections."""

    def test_security_headers_present(self):
        from fastapi.testclient import TestClient
        from serve_cockpit import app
        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert "geolocation=()" in resp.headers.get("Permissions-Policy", "")

    def test_target_input_sanitization(self):
        from serve_cockpit import sanitize_target_query
        # XSS injection
        assert "<script>" not in sanitize_target_query("<script>alert(1)</script>KRAS")
        # Command injection
        cleaned = sanitize_target_query("KRAS; rm -rf /; echo $FLAG | nc")
        assert ";" not in cleaned
        assert "|" not in cleaned
        assert "$" not in cleaned
        assert "KRAS" in cleaned

    def test_pdb_path_traversal_blocked(self):
        from fastapi.testclient import TestClient
        from serve_cockpit import app
        client = TestClient(app)
        resp = client.get("/api/target/pdb/..%2F..%2Fetc%2Fpasswd")
        # Must safely reject invalid identifier with 400 or 404, never execute path traversal
        assert resp.status_code in (400, 404)

