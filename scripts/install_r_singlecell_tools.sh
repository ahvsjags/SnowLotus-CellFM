#!/usr/bin/env bash
set -euo pipefail

if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    r-base \
    r-cran-seurat \
    r-cran-matrix \
    r-cran-jsonlite \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libhdf5-dev
fi

Rscript - <<'RSCRIPT'
stopifnot(requireNamespace("Seurat", quietly = TRUE))
stopifnot(requireNamespace("Matrix", quietly = TRUE))
stopifnot(requireNamespace("jsonlite", quietly = TRUE))
message("R single-cell tools ready")
RSCRIPT
