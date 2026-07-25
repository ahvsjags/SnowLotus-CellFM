#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(Seurat))
suppressPackageStartupMessages(library(SingleCellExperiment))
suppressPackageStartupMessages(library(zellkonverter))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: convert_seurat_rds_to_h5ad.R <input_dir> <output_dir>", call. = FALSE)
}

input_dir <- args[[1]]
output_dir <- args[[2]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

files <- list.files(input_dir, pattern = "\\.rds$", full.names = TRUE)
if (length(files) == 0) {
  stop(sprintf("No .rds files found under %s", input_dir), call. = FALSE)
}

for (path in files) {
  sample_id <- sub("\\.rds$", "", basename(path))
  output <- file.path(output_dir, paste0(sample_id, ".h5ad"))
  message("Converting ", path, " -> ", output)
  obj <- readRDS(path)
  if (!inherits(obj, "Seurat")) {
    warning("Skipping non-Seurat RDS: ", path)
    next
  }
  obj$sample_id <- if ("sample_id" %in% colnames(obj@meta.data)) obj$sample_id else sample_id
  sce <- as.SingleCellExperiment(obj)
  zellkonverter::writeH5AD(sce, output, X_name = "counts")
}
