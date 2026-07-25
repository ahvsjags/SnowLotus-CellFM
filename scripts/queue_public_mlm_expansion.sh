#!/usr/bin/env bash
set -euo pipefail

cd /root/snowlotus-cellfm
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs outputs

poll_seconds="${SNOWCELL_QUEUE_POLL_SECONDS:-300}"
gse_manifest="data/corpus_manifest.gse268881.tsv"
mlm_corpus="${SNOWCELL_MLM_CORPUS_OUTPUT:-data/plant_foundation_corpus_public_mlm.h5ad}"
mlm_session="${SNOWCELL_MLM_SESSION:-snowcell_mlm_public_expansion}"
available_mlm_session="${SNOWCELL_AVAILABLE_MLM_SESSION:-snowcell_mlm_public_available_expansion}"
foundation_session="${SNOWCELL_FOUNDATION_SESSION:-snowcell_foundation_long}"
continuation_session="${SNOWCELL_MLM_CONTINUATION_SESSION:-snowcell_mlm_public_expansion_continuation}"
continuation_output="${SNOWCELL_MLM_CONTINUATION_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_continuation}"
optional_public_manifests=(
  data/corpus_manifest.gse146034.tsv
  data/corpus_manifest.gse152766.tsv
  data/corpus_manifest.gse226097.tsv
  data/corpus_manifest.gse243419.tsv
  data/corpus_manifest.gse251706.tsv
  data/corpus_manifest.gse270140.tsv
  data/corpus_manifest.gse270342.tsv
)

collect_public_extra_manifests() {
  find data -maxdepth 1 -type f \( -name "corpus_manifest.gse*.tsv" -o -name "corpus_manifest.scplantdb*.tsv" \) ! -name "*.available.tsv" | sort | tr '\n' ' '
}

build_full_public_mlm_corpus() {
  local extra_manifests
  extra_manifests="$(collect_public_extra_manifests)"
  SNOWCELL_EXTRA_CORPUS_MANIFESTS="$extra_manifests" bash scripts/build_public_mlm_corpus.sh
}

continuation_artifact_exists() {
  [ -s "$continuation_output/latest.pt" ] || [ -s "$continuation_output/best.pt" ]
}

exit_if_continuation_exists() {
  if tmux has-session -t "$continuation_session" 2>/dev/null || continuation_artifact_exists; then
    echo "[$(date)] public MLM continuation is active or checkpointed; skipping legacy launch: $continuation_session"
    python scripts/write_pending_corpus_additions.py \
      --project-dir . \
      --output-md outputs/publication_package/pending_corpus_additions.md \
      --output-json outputs/publication_package/pending_corpus_additions.json || true
    bash scripts/generate_publication_package.sh || true
    exit 0
  fi
}

echo "[$(date)] SnowCell public MLM queue started"
bash scripts/ensure_public_data_jobs.sh || true

while [ ! -s "$gse_manifest" ]; do
  bash scripts/ensure_public_data_jobs.sh || true
  bash scripts/convert_gse268881_available.sh || true
  bash scripts/build_available_public_mlm_corpus.sh || true
  bash scripts/run_strict_benchmark_audits.sh || true
  if [ -s data/plant_foundation_corpus_public_mlm_available.h5ad ] \
    && ! tmux has-session -t "$foundation_session" 2>/dev/null \
    && ! tmux has-session -t "$available_mlm_session" 2>/dev/null \
    && [ ! -f outputs/foundation_5090_mlm_public_available_expansion/best.pt ]; then
    stamp="$(date +%Y%m%d_%H%M%S)"
    echo "[$(date)] launching available public MLM expansion in tmux: $available_mlm_session"
    tmux new-session -d -s "$available_mlm_session" \
      "cd /root/snowlotus-cellfm && source .venv/bin/activate 2>/dev/null || true; snowcell train --config configs/foundation_5090_mlm_public_available_expansion.yaml --device cuda 2>&1 | tee logs/mlm_public_available_expansion_${stamp}.log; bash scripts/run_strict_benchmark_audits.sh; bash scripts/generate_publication_package.sh"
  fi
  if tmux has-session -t snowcell_gse268881_subset 2>/dev/null; then
    echo "[$(date)] waiting for GSE268881 subset conversion: $gse_manifest"
  else
    echo "[$(date)] GSE268881 session is not running; restarting downloader/converter"
    bash scripts/download_gse268881_subset.sh
  fi
  sleep "$poll_seconds"
done

if [ ! -s "$mlm_corpus" ]; then
  echo "[$(date)] building public MLM corpus: $mlm_corpus"
  build_full_public_mlm_corpus
else
  echo "[$(date)] public MLM corpus already exists: $mlm_corpus"
fi

echo "[$(date)] running strict benchmark audits"
bash scripts/run_strict_benchmark_audits.sh || true

exit_if_continuation_exists

while tmux has-session -t "$foundation_session" 2>/dev/null; do
  echo "[$(date)] waiting for GPU foundation session to finish: $foundation_session"
  bash scripts/ensure_public_data_jobs.sh || true
  bash scripts/build_available_public_mlm_corpus.sh || true
  sleep "$poll_seconds"
done

while tmux has-session -t "$available_mlm_session" 2>/dev/null; do
  echo "[$(date)] waiting for available public MLM session to finish: $available_mlm_session"
  bash scripts/ensure_public_data_jobs.sh || true
  bash scripts/build_available_public_mlm_corpus.sh || true
  sleep "$poll_seconds"
done

exit_if_continuation_exists

echo "[$(date)] refreshing public MLM corpus before launch to include late optional manifests"
bash scripts/ensure_public_data_jobs.sh || true
bash scripts/build_available_public_mlm_corpus.sh || true
build_full_public_mlm_corpus

if tmux has-session -t "$mlm_session" 2>/dev/null; then
  echo "[$(date)] MLM session already running: $mlm_session"
  exit 0
fi

stamp="$(date +%Y%m%d_%H%M%S)"
echo "[$(date)] launching public MLM expansion in tmux: $mlm_session"
tmux new-session -d -s "$mlm_session" \
  "cd /root/snowlotus-cellfm && source .venv/bin/activate 2>/dev/null || true; snowcell train --config configs/foundation_5090_mlm_public_expansion.yaml --device cuda 2>&1 | tee logs/mlm_public_expansion_${stamp}.log; bash scripts/run_strict_benchmark_audits.sh; bash scripts/generate_publication_package.sh"

echo "[$(date)] launched $mlm_session"
