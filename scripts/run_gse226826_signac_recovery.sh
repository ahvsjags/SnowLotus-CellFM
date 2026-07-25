#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
cd "${PROJECT_DIR}"

mkdir -p logs

Rscript scripts/install_r_signac_if_missing.R > logs/install_r_signac_if_missing.latest.log 2>&1

Rscript scripts/inspect_rds_structure.R \
  data/public/GSE226826_rds/GSE226826_AvrRpm1_24h_peak.rds.gz \
  > logs/gse226826_rds_structure.txt 2>&1 || true

bash scripts/run_gse226826_recovery_once.sh \
  > logs/run_gse226826_recovery_once.latest.log 2>&1 || true

bash scripts/generate_publication_package.sh \
  > logs/generate_publication_package.after_gse226826.log 2>&1 || true

bash scripts/sync_github_release_repo.sh \
  > logs/sync_github_release_repo.after_gse226826.log 2>&1 || true
