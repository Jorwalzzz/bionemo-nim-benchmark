---
name: bionemo-nim-inference
description: >-
  Use this skill whenever interacting with, developing, testing, or deploying NVIDIA BioNeMo
  and NVIDIA NIM (Inference Microservices) for biology, including ESM-2 protein language models,
  DiffDock molecular docking, ESMFold, MolMIM small molecule generation, and OpenFold.
  Covers hosted Cloud APIs (build.nvidia.com, health.api.nvidia.com), local GPU Docker containers,
  rate-limiting, payload schemas, and mock testing.
---

# NVIDIA BioNeMo & NIM Inference

NVIDIA BioNeMo and NVIDIA NIM microservices offer accelerated containerized inference endpoints for generative biology and molecular modeling.

## Microservices Overview

Model | Task | Hosted Endpoint URL | Key Inputs
:--- | :--- | :--- | :---
**ESM-2 (650M / 3B)** | Protein language model per-residue & sequence embeddings | `https://integrate.api.nvidia.com/v1/biology/nvidia/esm2-650m` | `sequence` (IUPAC string)
**DiffDock** | Small molecule blind docking, poses, binding affinities | `https://health.api.nvidia.com/v1/biology/mit/diffdock` | `ligand` (SMILES), `protein` (PDB/backbone)
**ESMFold** | De novo 3D protein structure prediction | `https://health.api.nvidia.com/v1/biology/meta/esmfold` | `sequence` (IUPAC string)
**MolMIM** | Controlled small molecule generation & property optimization | `https://health.api.nvidia.com/v1/biology/nvidia/molmim` | `smi` (SMILES), `algorithm`

---

## Workflow: Interacting with BioNeMo NIM

### 1. Authentication & Client Initialization
Read the API key from `.env` using `python-dotenv`:
```python
from src.client import NimBioClient

# Automatically reads NVIDIA_API_KEY from environment or .env
client = NimBioClient(mock=False)
```

For zero-cost testing, automated unit tests, and CI/CD pipelines, enable mock mode:
```python
client = NimBioClient(mock=True)
```

### 2. Querying ESM-2 Embeddings
Validate sequence first, then query embeddings:
```python
seq = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
clean_seq = NimBioClient.validate_protein_sequence(seq)
response = client.get_esm2_embeddings(clean_seq)

print(f"Sequence length: {response.sequence_length}")
print(f"Hidden dim: {response.hidden_dim}")  # 1280 for 650M
print(f"Server inference latency: {response.latency.server_inference_ms:.2f} ms")
```

### 3. Querying DiffDock for Molecular Docking
Sanitize ligand SMILES with RDKit and submit to DiffDock:
```python
from src.pipeline import BenchmarkPipeline
from src.pdb_utils import generate_synthetic_backbone

ligand = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
chem_res = BenchmarkPipeline.sanitize_ligand_smiles(ligand)
pdb_text = generate_synthetic_backbone(clean_seq)

diffdock_resp = client.run_diffdock(pdb_text, chem_res.canonical_smiles)
print(f"Top Affinity: {diffdock_resp.top_affinity_kcal_mol} kcal/mol")
for pose in diffdock_resp.poses:
    print(f"Pose Rank {pose.rank}: Affinity={pose.predicted_affinity_kcal_mol} kcal/mol, Conf={pose.confidence_score}")
```

---

## Detailed References
- [API Endpoints & Schemas](./references/api_endpoints.md): Full payload formats, NVCF task polling, error codes, and headers.
- [Local NIM Docker Deployment](./references/local_nim_docker.md): How to pull and run NGC containers on local GPUs with TensorRT-LLM.
- [Endpoint Health Test Script](./scripts/test_nim_endpoint.py): Executable script to probe NIM endpoints and measure round-trip latency.
