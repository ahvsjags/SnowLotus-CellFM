#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
config="${SNOWCELL_PUBLIC_PLANTS_CONTINUATION_CONFIG:-configs/generated/foundation_5090_public_plants_continuation.yaml}"
output_dir="${SNOWCELL_PUBLIC_PLANTS_CONTINUATION_OUTPUT_DIR:-outputs/plant_general_public_plants_continuation_5090}"
session_log="${SNOWCELL_PUBLIC_PLANTS_CONTINUATION_LOG:-logs/public_plants_continuation_5090.log}"
pid_file="${output_dir}/training.pid"
python_bin="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"

cd "$project_dir"
export PATH="/root/miniconda3/envs/myconda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
mkdir -p "$output_dir" "$(dirname "$session_log")"

if [ -s "$pid_file" ]; then
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "public plants continuation already running: pid=$pid"
    exit 0
  fi
  rm -f "$pid_file"
fi

nohup /bin/bash -c "cd '$project_dir'; export PATH='/root/miniconda3/envs/myconda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'; PYTHONPATH=src '$python_bin' -m snowcell.cli train --config '$config' --device cuda; PYTHONPATH=src '$python_bin' scripts/benchmark_public_plants_v1.py --project-dir '$project_dir' --data data/plant_foundation_corpus_public_plants_v1.h5ad --manifest data/corpus_manifest_public_plants_v1.tsv --max-cells-per-dataset 256 --batch-size 64 --device cuda --output outputs/benchmarks/public_plants_v1_continuation_5090.json || true; bash scripts/generate_publication_package.sh || true" \
  >> "$session_log" 2>&1 < /dev/null &

pid="$!"
printf '%s\n' "$pid" > "$pid_file"
echo "started public plants continuation: pid=$pid"
echo "log: $session_log"
echo "config: $config"
