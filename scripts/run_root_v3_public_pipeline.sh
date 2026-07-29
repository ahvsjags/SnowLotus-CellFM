#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
ROOT_STAGE="${SNOWCELL_PUBLIC_DATA_STAGE_ROOT:-/root/snowlotus_public_data_stage}"
STAGE_PROJECT="${SNOWCELL_PUBLIC_DATA_STAGE_PROJECT:-/root/snowlotus_public_data_stage_project}"
V3_ROOT="${SNOWCELL_V3_ROOT:-/root/snowlotus_public_plants_v3}"
V3_TRAIN="/root/snowlotus_cellfm_v3_4090"
LOG_DIR="${V3_ROOT}/logs"
mkdir -p "${V3_ROOT}" "${V3_TRAIN}" "${LOG_DIR}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "${LOG_DIR}/pipeline.log"
}

wait_for_inputs() {
  while true; do
    if [ -s "${ROOT_STAGE}/data/corpus_manifest.gse270140.tsv" ] \
      && [ -s "${STAGE_PROJECT}/data/corpus_manifest.gse243419.tsv" ] \
      && find "${STAGE_PROJECT}/data/public/GSE243419_npz" -maxdepth 1 -type f -name '*.npz' -print -quit | grep -q . \
      && find "${ROOT_STAGE}/data/public/GSE270140_npz" -maxdepth 1 -type f -name '*.npz' -print -quit | grep -q .; then
      return 0
    fi
    log "waiting for GSE243419 and GSE270140 staged manifests and NPZ files"
    sleep "${SNOWCELL_V3_POLL_SECONDS:-120}"
  done
}

wait_for_inputs
log "staged inputs ready; copying GSE243419 NPZ files into shared root stage"
mkdir -p "${ROOT_STAGE}/data/public/GSE243419_npz"
cp -a "${STAGE_PROJECT}/data/public/GSE243419_npz/." "${ROOT_STAGE}/data/public/GSE243419_npz/"
cp -f "${STAGE_PROJECT}/data/corpus_manifest.gse243419.tsv" "${ROOT_STAGE}/data/corpus_manifest.gse243419.tsv"

extra_manifest="${V3_ROOT}/corpus_manifest_v3_extra.tsv"
python - "${ROOT_STAGE}" "${STAGE_PROJECT}" "${extra_manifest}" <<'PY'
import csv
import sys
from pathlib import Path

root_stage = Path(sys.argv[1])
stage_project = Path(sys.argv[2])
output = Path(sys.argv[3])
sources = [
    (root_stage / "data/corpus_manifest.gse270140.tsv", root_stage),
    (root_stage / "data/corpus_manifest.gse243419.tsv", root_stage),
]
columns = ["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"]
rows = []
seen = set()
for manifest, base in sources:
    with manifest.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            path = Path(row.get("path", ""))
            if not path.is_absolute():
                path = base / path
            row["path"] = path.as_posix()
            key = (row.get("path", ""), row.get("dataset_id", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
    writer.writeheader()
    writer.writerows({column: row.get(column, "") for column in columns} for row in rows)
print(f"wrote {output} rows={len(rows)}")
PY

v3_manifest="${V3_ROOT}/corpus_manifest_public_plants_v3.tsv"
v3_corpus="${V3_ROOT}/plant_foundation_corpus_public_plants_v3.h5ad"
v3_summary="${V3_ROOT}/public_plants_v3_summary.json"
if [ ! -s "${v3_summary}" ]; then
  log "building v3 on-disk corpus"
  PYTHONPATH="${PROJECT_DIR}/src" /root/miniconda3/envs/myconda/bin/python -u \
    "${PROJECT_DIR}/scripts/build_public_mlm_corpus_on_disk.py" \
    --base-manifest /root/snowlotus_public_plants_v2/corpus_manifest_public_plants_v2_fixed.tsv \
    --extra-manifest "${extra_manifest}" \
    --manifest-output "${v3_manifest}" \
    --output "${v3_corpus}" \
    --work-dir "${V3_ROOT}/work" \
    --summary-output "${v3_summary}" \
    --skip-errors --keep-shards >> "${LOG_DIR}/build_v3.log" 2>&1
fi

if [ -s "${v3_summary}" ] && ! tmux has-session -t snowcell_public_plants_v3_train 2>/dev/null; then
  log "starting v3 training"
  tmux new-session -d -s snowcell_public_plants_v3_train \
    "cd ${PROJECT_DIR} && PYTHONPATH=src /root/miniconda3/envs/myconda/bin/python -u -X utf8 -m snowcell.cli train --config configs/generated/foundation_public_plants_v3_4090.yaml --device cuda > ${V3_TRAIN}/train.log 2>&1"
fi

while [ ! -s "${V3_TRAIN}/test_metrics.json" ]; do
  log "waiting for v3 training test metrics"
  sleep "${SNOWCELL_V3_POLL_SECONDS:-120}"
done

benchmark="${V3_TRAIN}/v3_cross_species_benchmark.json"
if [ ! -s "${benchmark}" ] && ! tmux has-session -t snowcell_public_plants_v3_benchmark 2>/dev/null; then
  log "starting v3 cross-species benchmark"
  tmux new-session -d -s snowcell_public_plants_v3_benchmark \
    "cd ${PROJECT_DIR} && PYTHONPATH=src /root/miniconda3/envs/myconda/bin/python -u scripts/benchmark_public_plants_v1.py --project-dir ${PROJECT_DIR} --checkpoint ${V3_TRAIN}/best.pt --data ${v3_corpus} --manifest ${v3_manifest} --output ${benchmark} --max-cells-per-dataset 256 --batch-size 64 --device cuda > ${V3_TRAIN}/benchmark.log 2>&1"
fi

while [ ! -s "${benchmark}" ]; do
  log "waiting for v3 benchmark"
  sleep "${SNOWCELL_V3_POLL_SECONDS:-120}"
done

comparison_json="${V3_TRAIN}/v3_vs_v1_checkpoint_comparison.json"
comparison_md="${V3_TRAIN}/v3_vs_v1_checkpoint_comparison.md"
if [ ! -s "${comparison_json}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" /root/miniconda3/envs/myconda/bin/python -X utf8 \
    "${PROJECT_DIR}/scripts/compare_all_plant_checkpoint_benchmarks.py" \
    --baseline "${PROJECT_DIR}/outputs/benchmarks/public_plants_v1_continuation_checkpoint.json" \
    --candidate "${benchmark}" --output-json "${comparison_json}" --output-md "${comparison_md}"
fi

package="${PROJECT_DIR}/outputs/publication_package"
mkdir -p "${package}/benchmarks/v3" "${package}/strict_benchmarks/v3" "${package}/v3_training"
cp -f "${v3_manifest}" "${package}/benchmarks/v3/v3_public_plants_corpus_manifest.tsv"
cp -f "${v3_summary}" "${package}/benchmarks/v3/v3_public_plants_corpus_summary.json"
cp -f "${benchmark}" "${package}/benchmarks/v3/v3_public_plants_cross_species.json"
cp -f "${comparison_json}" "${package}/benchmarks/v3/v3_vs_v1_checkpoint_comparison.json"
cp -f "${comparison_md}" "${package}/benchmarks/v3/v3_vs_v1_checkpoint_comparison.md"
for file in config.resolved.json history.json test_metrics.json preprocessing_stats.json progress_latest.json; do
  [ -f "${V3_TRAIN}/${file}" ] && cp -f "${V3_TRAIN}/${file}" "${package}/strict_benchmarks/v3/v3_${file}"
done
cp -f "${V3_TRAIN}/train.log" "${package}/v3_training/v3_train.log" 2>/dev/null || true
cp -f "${V3_TRAIN}/benchmark.log" "${package}/v3_training/v3_benchmark.log" 2>/dev/null || true
PYTHONPATH="${PROJECT_DIR}/src" /root/miniconda3/envs/myconda/bin/python -X utf8 \
  "${PROJECT_DIR}/scripts/write_artifact_checksums.py" \
  --output "${package}/artifact_checksums.tsv" >> "${LOG_DIR}/pipeline.log" 2>&1 || true
log "v3 pipeline complete"
