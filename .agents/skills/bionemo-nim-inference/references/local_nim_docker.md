# Deploying NVIDIA BioNeMo NIM Locally via Docker

For air-gapped enterprise environments, offline compute, or unmetered inference, deploy NIM containers directly to local NVIDIA GPUs.

## 1. Prerequisites
- NVIDIA GPU with compute capability $\ge 8.0$ (Ampere, Ada, Hopper: A100, H100, RTX 4090, L40S)
- NVIDIA Container Toolkit (`nvidia-ctk`)
- Docker 24.0+
- NGC API Key logged in (`docker login nvcr.io`)

## 2. Running ESM-2 NIM Container
```bash
# Export NGC API Key and local cache dir
export NGC_API_KEY="your-ngc-key"
export LOCAL_NIM_CACHE="$HOME/.cache/nim"
mkdir -p "$LOCAL_NIM_CACHE"

# Launch ESM-2 NIM container on port 8000
docker run -it --rm \
  --gpus all \
  --shm-size=16g \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v $LOCAL_NIM_CACHE:/opt/nim/.cache \
  -p 8000:8000 \
  nvcr.io/nim/meta/esm2-650m:latest
```

## 3. Configuring Benchmark Suite for Local NIM
Set the environment variable in `.env`:
```env
NIM_BASE_URL=http://localhost:8000/v1
ESM2_ENDPOINT=http://localhost:8000/v1/biology/nvidia/esm2-650m
```
Then run the benchmark:
```bash
python run_benchmark.py --iterations 5 --save-plots
```
Local NIM deployment bypasses internet latency entirely, yielding raw TensorRT-LLM hardware performance (typically 10,000+ tokens/sec).
