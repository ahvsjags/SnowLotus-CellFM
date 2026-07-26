# SnowLotus-CellFM Environment Snapshot

## Python

- Executable: `/root/snowlotus-cellfm/.venv/bin/python`
- Version: `3.10.12 (main, Jun 22 2026, 18:55:27) [GCC 11.4.0]`
- Implementation: `CPython`

## Platform

- System: `Linux`
- Release: `5.15.0-161-generic`
- Machine: `x86_64`
- Platform: `Linux-5.15.0-161-generic-x86_64-with-glibc2.35`

## Reproduction Commands

```bash
python -m pip install -e ".[singlecell,dev]"
bash scripts/ensure_public_data_jobs.sh
bash scripts/build_public_mlm_corpus.sh
snowcell train --config configs/foundation_5090_pretrain.yaml --device cuda
snowcell train --config configs/foundation_5090_mlm_public_expansion.yaml --device cuda
bash scripts/start_public_mlm_continuation_training.sh
bash scripts/start_public_mlm_continuation_watchdog.sh
bash scripts/start_public_mlm_continuation_package_watchdog.sh
bash scripts/run_strict_benchmark_audits.sh
bash scripts/generate_publication_package.sh
```

## Command Outputs

### `git rev-parse --short HEAD`

Return code: `128`

stderr:

```text
fatal: not a git repository (or any of the parent directories): .git
```

### `git status --short`

Return code: `128`

stderr:

```text
fatal: not a git repository (or any of the parent directories): .git
```

### `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`

Return code: `0`

```text
NVIDIA GeForce RTX 5090, 595.84, 32607 MiB
```

### `nvidia-smi`

Return code: `0`

```text
Sun Jul 26 08:00:56 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 595.84                 Driver Version: 595.84         CUDA Version: 13.2     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5090        On  |   00000000:98:00.0 Off |                  N/A |
| 42%   62C    P1            398W /  575W |   30652MiB /  32607MiB |     77%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A          452726      C   ...lotus-cellfm/.venv/bin/python      30642MiB |
+-----------------------------------------------------------------------------------------+
```

## Python Packages

```text
anndata==0.11.4
annotated-types==0.7.0
array-api-compat==1.15.0
certifi==2026.7.22
charset-normalizer==3.4.9
click==8.4.2
contourpy==1.3.2
cuda-bindings==13.3.1
cuda-pathfinder==1.6.0
cuda-toolkit==13.0.3.0
cycler==0.12.1
exceptiongroup==1.3.1
filelock==3.32.0
fonttools==4.63.0
fsspec==2026.6.0
h5py==3.16.0
idna==3.18
iniconfig==2.3.0
Jinja2==3.1.6
joblib==1.5.3
kiwisolver==1.5.0
llvmlite==0.48.0
MarkupSafe==3.0.3
matplotlib==3.10.9
mpmath==1.3.0
narwhals==2.24.0
natsort==8.4.0
networkx==3.4.2
numba==0.66.0
numpy==2.2.6
nvidia-cublas==13.1.1.3
nvidia-cuda-cupti==13.0.85
nvidia-cuda-nvrtc==13.0.88
nvidia-cuda-runtime==13.0.96
nvidia-cudnn-cu13==9.20.0.48
nvidia-cufft==12.0.0.61
nvidia-cufile==1.15.1.6
nvidia-curand==10.4.0.35
nvidia-cusolver==12.0.4.66
nvidia-cusparse==12.6.3.3
nvidia-cusparselt-cu13==0.8.1
nvidia-nccl-cu13==2.29.7
nvidia-nvjitlink==13.3.33
nvidia-nvshmem-cu13==3.4.5
nvidia-nvtx==13.0.85
packaging==26.2
pandas==2.3.3
pillow==12.3.0
platformdirs==4.11.0
plotly==6.9.0
pluggy==1.6.0
protobuf==7.35.1
pydantic==2.13.4
pydantic_core==2.46.4
Pygments==2.20.0
pynndescent==0.6.0
pyparsing==3.3.2
pytest==9.1.1
python-dateutil==2.9.0.post0
pytz==2026.2
PyYAML==6.0.3
requests==2.34.2
ruff==0.15.22
scikit-learn==1.7.2
scipy==1.15.3
seaborn==0.13.2
sentry-sdk==2.66.1
six==1.17.0
# Editable install with no version control (snowlotus-cellfm==0.1.0)
-e /root/snowlotus-cellfm
sympy==1.14.0
threadpoolctl==3.6.0
tomli==2.4.1
torch==2.13.0
tqdm==4.69.0
triton==3.7.1
typing-inspection==0.4.2
typing_extensions==4.16.0
tzdata==2026.3
umap-learn==0.5.12
urllib3==2.7.0
wandb==0.28.1
```
