# SnowLotus-CellFM Remote Operations

The active server is reached through the configured alias `matpool-px1-jcy`.
The project directory is `/mnt/snowlotus_cellfm` and the conda environment is
`myconda`.

## Inspect jobs

```bash
ssh matpool-px1-jcy
cd /mnt/snowlotus_cellfm
tmux ls
nvidia-smi
```

Important sessions:

- `snowcell_joint_vocab_filter`: builds the 60,000-gene joint corpus.
- `snowcell_joint_train_4090_wait`: starts joint MLM pretraining after the corpus is ready.
- `snowcell_joint_init_hybrid_wait`: starts SRP169576 initialization fine-tuning after pretraining.
- `snowcell_service_hybrid`: serves the current hybrid checkpoint on loopback port 8000.

## Start the inference service

```bash
cd /mnt/snowlotus_cellfm
bash scripts/start_snowlotus_service.sh
```

For a detached process:

```bash
tmux new-session -d -s snowcell_service_hybrid \
  'bash /mnt/snowlotus_cellfm/scripts/start_snowlotus_service.sh > /mnt/snowlotus_cellfm/logs/snowlotus_service.log 2>&1'
```

The service provides `GET /health`, `GET /metadata`, and `POST /annotate`.
The annotation request body contains `data_path`, `output_dir`, and optional
`batch_size` and `layer` fields. Inputs are restricted to the configured data
root by default.

To access the loopback service from a local machine, create an SSH tunnel:

```bash
ssh -L 8000:127.0.0.1:8000 matpool-px1-jcy
```

Then call `http://127.0.0.1:8000/health` locally.
