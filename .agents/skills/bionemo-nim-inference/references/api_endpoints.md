# NVIDIA BioNeMo & NIM API Reference

## 1. ESM-2 Protein Embeddings
- **URL**: `https://integrate.api.nvidia.com/v1/biology/nvidia/esm2-650m`
- **Method**: `POST`
- **Headers**:
  ```http
  Authorization: Bearer nvapi-xxxxxxxx
  Content-Type: application/json
  Accept: application/json
  ```
- **Payload**:
  ```json
  {
    "model": "nvidia/esm2-650m",
    "input": ["MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"]
  }
  ```
- **Response**:
  ```json
  {
    "data": [
      {
        "embedding": [[0.012, -0.45, ...]],
        "index": 0
      }
    ],
    "usage": {
      "prompt_tokens": 76,
      "total_tokens": 76
    }
  }
  ```

## 2. DiffDock Molecular Docking
- **URL**: `https://health.api.nvidia.com/v1/biology/mit/diffdock`
- **Method**: `POST`
- **Headers**:
  ```http
  Authorization: Bearer nvapi-xxxxxxxx
  Content-Type: application/json
  ```
- **Payload**:
  ```json
  {
    "ligand": "CC(=O)Oc1ccccc1C(=O)O",
    "ligand_file_type": "smiles",
    "protein": "ATOM      1  N   MET A   1...",
    "num_poses": 5,
    "time_divisions": 20,
    "steps": 18
  }
  ```
- **Polling (NVCF)**:
  When asynchronous jobs are returned with HTTP 202:
  - Check status header `NVCF-REQID: <req_id>`
  - Poll `https://health.api.nvidia.com/v1/biology/mit/diffdock/status/<req_id>` until `status == "fulfilled"`.

## 3. Error Codes & Recovery
- **401 Unauthorized**: Missing or expired `NVIDIA_API_KEY`.
- **429 Rate Limited**: NVIDIA build.nvidia.com credit exhaustion or burst rate exceeded. Engage exponential backoff ($backoff\_factor \times 2^{retry} + jitter$).
- **503 Service Unavailable / NVCF Cold Start**: Wait 5-10 seconds for worker container allocation.
