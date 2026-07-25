#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(Seurat))
suppressPackageStartupMessages(library(Matrix))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: export_seurat_rds_to_mtx.R <input_dir> <output_dir>", call. = FALSE)
}

input_dir <- args[[1]]
output_dir <- args[[2]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

files <- list.files(input_dir, pattern = "\\.rds(\\.gz)?$", full.names = TRUE, ignore.case = TRUE)
if (length(files) == 0) {
  stop(sprintf("No .rds files found under %s", input_dir), call. = FALSE)
}

nonempty_matrix <- function(matrix) {
  !is.null(matrix) && length(dim(matrix)) == 2 && nrow(matrix) > 0 && ncol(matrix) > 0
}

get_layer_names <- function(assay_obj) {
  api_layers <- tryCatch(
    Layers(assay_obj),
    error = function(e) character()
  )
  direct_layers <- tryCatch(
    names(slot(assay_obj, "layers")),
    error = function(e) character()
  )
  unique(c(api_layers, direct_layers))
}

get_direct_layer <- function(assay_obj, layer) {
  layers <- tryCatch(
    slot(assay_obj, "layers"),
    error = function(e) NULL
  )
  if (is.null(layers) || is.null(names(layers)) || !(layer %in% names(layers))) {
    return(NULL)
  }
  layers[[layer]]
}

get_logmap_names <- function(assay_obj, slot_name) {
  mapping <- tryCatch(
    slot(assay_obj, slot_name),
    error = function(e) NULL
  )
  names <- tryCatch(
    rownames(mapping),
    error = function(e) NULL
  )
  if (is.null(names)) {
    character()
  } else {
    names
  }
}

repair_dimnames <- function(matrix, obj, assay_obj) {
  genes <- rownames(matrix)
  cells <- colnames(matrix)
  if (is.null(genes) || length(genes) != nrow(matrix)) {
    feature_names <- get_logmap_names(assay_obj, "features")
    if (length(feature_names) == nrow(matrix)) {
      genes <- feature_names
    }
  }
  if (is.null(cells) || length(cells) != ncol(matrix)) {
    cell_names <- get_logmap_names(assay_obj, "cells")
    if (length(cell_names) == ncol(matrix)) {
      cells <- cell_names
    } else if ("meta.data" %in% slotNames(obj) && nrow(obj@meta.data) == ncol(matrix)) {
      cells <- rownames(obj@meta.data)
    }
  }
  if (!is.null(genes) && length(genes) == nrow(matrix) && !is.null(cells) && length(cells) == ncol(matrix)) {
    dimnames(matrix) <- list(genes, cells)
  }
  matrix
}

get_assay_matrix <- function(obj, assay) {
  assay_obj <- obj[[assay]]
  layers <- get_layer_names(assay_obj)
  layer_candidates <- unique(c(
    "counts",
    grep("^counts", layers, value = TRUE),
    "data",
    grep("^data", layers, value = TRUE),
    layers
  ))
  layer_candidates <- layer_candidates[nzchar(layer_candidates)]
  for (layer in layer_candidates) {
    matrix <- tryCatch(
      GetAssayData(obj, assay = assay, layer = layer),
      error = function(e) NULL
    )
    if (!nonempty_matrix(matrix)) {
      matrix <- tryCatch(
        LayerData(assay_obj, layer = layer),
        error = function(e) NULL
      )
    }
    if (!nonempty_matrix(matrix)) {
      matrix <- get_direct_layer(assay_obj, layer)
    }
    if (nonempty_matrix(matrix)) {
      message("Using assay=", assay, " layer=", layer)
      return(repair_dimnames(matrix, obj, assay_obj))
    }
  }
  for (slot in c("counts", "data")) {
    matrix <- tryCatch(
      GetAssayData(obj, assay = assay, slot = slot),
      error = function(e) NULL
    )
    if (nonempty_matrix(matrix)) {
      message("Using assay=", assay, " slot=", slot)
      return(repair_dimnames(matrix, obj, assay_obj))
    }
  }
  NULL
}

get_assay_names <- function(obj) {
  api_assays <- tryCatch(
    Assays(obj),
    error = function(e) character()
  )
  slot_assays <- tryCatch(
    names(slot(obj, "assays")),
    error = function(e) character()
  )
  unique(c(api_assays, slot_assays))
}

get_counts <- function(obj) {
  assay_names <- get_assay_names(obj)
  assay_candidates <- unique(c(DefaultAssay(obj), "RNA", "SCT", assay_names))
  assay_candidates <- assay_candidates[assay_candidates %in% assay_names]
  for (assay in assay_candidates) {
    matrix <- get_assay_matrix(obj, assay)
    if (nonempty_matrix(matrix)) {
      return(matrix)
    }
  }
  stop("No non-empty counts/data matrix found in Seurat object assays: ", paste(assay_names, collapse = ", "))
}

is_gzip_file <- function(path) {
  con <- file(path, open = "rb")
  on.exit(close(con), add = TRUE)
  magic <- readBin(con, what = "raw", n = 2)
  length(magic) == 2 && identical(magic, as.raw(c(0x1f, 0x8b)))
}

gunzip_to_temp <- function(path) {
  tmp <- tempfile(fileext = ".rds")
  input <- gzfile(path, open = "rb")
  output <- file(tmp, open = "wb")
  on.exit(close(input), add = TRUE)
  on.exit(close(output), add = TRUE)
  repeat {
    block <- readBin(input, what = "raw", n = 1024 * 1024)
    if (length(block) == 0) {
      break
    }
    writeBin(block, output)
  }
  tmp
}

read_rds_any <- function(path, max_gzip_layers = 3) {
  current <- path
  cleanup <- character()
  on.exit(unlink(cleanup), add = TRUE)
  for (layer in seq_len(max_gzip_layers)) {
    if (!is_gzip_file(current)) {
      break
    }
    current <- gunzip_to_temp(current)
    cleanup <- c(cleanup, current)
  }
  readRDS(current)
}

for (path in files) {
  sample_id <- sub("\\.rds(\\.gz)?$", "", basename(path), ignore.case = TRUE)
  out <- file.path(output_dir, sample_id)
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  message("Exporting ", path, " -> ", out)
  obj <- read_rds_any(path)
  if (!inherits(obj, "Seurat")) {
    warning("Skipping non-Seurat RDS: ", path)
    next
  }
  counts <- get_counts(obj)
  if (is.null(rownames(counts)) || is.null(colnames(counts))) {
    stop("Exported matrix is missing gene or cell names after dimname repair: ", path)
  }
  Matrix::writeMM(t(counts), file.path(out, "matrix_cells_by_genes.mtx"))
  writeLines(rownames(counts), file.path(out, "genes.txt"))
  writeLines(colnames(counts), file.path(out, "cells.txt"))
  meta <- obj@meta.data
  meta$cell_id <- rownames(meta)
  write.csv(meta, file.path(out, "metadata.csv"), row.names = FALSE, quote = TRUE)
}
