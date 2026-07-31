#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(Matrix))
if (requireNamespace("SeuratObject", quietly = TRUE)) {
  suppressPackageStartupMessages(library(SeuratObject))
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop(
    "Usage: export_seurat_rds_expression_slot_to_mtx.R <input_dir> <output_dir> [assay] [slot]",
    call. = FALSE
  )
}

input_dir <- args[[1]]
output_dir <- args[[2]]
preferred_assay <- if (length(args) >= 3) args[[3]] else "RNA"
preferred_slot <- if (length(args) >= 4) args[[4]] else "counts"
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

files <- list.files(input_dir, pattern = "\\.rds(\\.gz)?$", full.names = TRUE, ignore.case = TRUE)
if (length(files) == 0) {
  stop(sprintf("No .rds files found under %s", input_dir), call. = FALSE)
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

read_rds_any <- function(path, max_gzip_layers = 3L) {
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

safe_slot_names <- function(x) {
  tryCatch(slotNames(x), error = function(e) character())
}

safe_slot <- function(x, name) {
  tryCatch(slot(x, name), error = function(e) NULL)
}

child_names <- function(x) {
  if (is.environment(x)) {
    return(sort(ls(x, all.names = TRUE)))
  }
  names <- tryCatch(names(x), error = function(e) NULL)
  if (is.null(names)) {
    character()
  } else {
    names
  }
}

child_value <- function(x, name) {
  if (is.environment(x)) {
    return(tryCatch(get(name, envir = x, inherits = FALSE), error = function(e) NULL))
  }
  tryCatch(x[[name]], error = function(e) NULL)
}

nonempty_matrix <- function(matrix) {
  !is.null(matrix) &&
    (is.matrix(matrix) || inherits(matrix, "Matrix")) &&
    length(dim(matrix)) == 2 &&
    nrow(matrix) > 0 &&
    ncol(matrix) > 0
}

get_named_assay <- function(obj, assay_name) {
  if (!("assays" %in% safe_slot_names(obj))) {
    return(NULL)
  }
  assays <- safe_slot(obj, "assays")
  if (is.null(assays) || !(assay_name %in% child_names(assays))) {
    return(NULL)
  }
  child_value(assays, assay_name)
}

get_matrix_from_assay <- function(assay, slot_name) {
  matrix <- safe_slot(assay, slot_name)
  if (nonempty_matrix(matrix)) {
    return(matrix)
  }
  layers <- safe_slot(assay, "layers")
  if (!is.null(layers) && slot_name %in% child_names(layers)) {
    matrix <- child_value(layers, slot_name)
    if (nonempty_matrix(matrix)) {
      return(matrix)
    }
  }
  NULL
}

repair_dimnames <- function(matrix, obj, assay) {
  genes <- rownames(matrix)
  cells <- colnames(matrix)
  if (is.null(genes) || length(genes) != nrow(matrix)) {
    meta_features <- safe_slot(assay, "meta.features")
    feature_names <- tryCatch(rownames(meta_features), error = function(e) NULL)
    if (!is.null(feature_names) && length(feature_names) == nrow(matrix)) {
      genes <- feature_names
    }
  }
  if (is.null(cells) || length(cells) != ncol(matrix)) {
    cell_mapping <- safe_slot(assay, "cells")
    cell_names <- tryCatch(rownames(cell_mapping), error = function(e) NULL)
    if (!is.null(cell_names) && length(cell_names) == ncol(matrix)) {
      cells <- cell_names
    } else if ("meta.data" %in% safe_slot_names(obj)) {
      meta <- safe_slot(obj, "meta.data")
      meta_cells <- tryCatch(rownames(meta), error = function(e) NULL)
      if (!is.null(meta_cells) && length(meta_cells) == ncol(matrix)) {
        cells <- meta_cells
      }
    }
  }
  if (!is.null(genes) && !is.null(cells) && length(genes) == nrow(matrix) && length(cells) == ncol(matrix)) {
    dimnames(matrix) <- list(genes, cells)
  }
  matrix
}

get_expression_matrix <- function(obj) {
  if (nonempty_matrix(obj)) {
    message("Using direct matrix object")
    return(list(matrix = obj, assay = "direct", slot = "object"))
  }
  assay_names <- if ("assays" %in% safe_slot_names(obj)) child_names(safe_slot(obj, "assays")) else character()
  assay_candidates <- unique(c(preferred_assay, "RNA", "SCT", assay_names))
  slot_candidates <- unique(c(preferred_slot, "counts", "data"))
  for (assay_name in assay_candidates) {
    assay <- get_named_assay(obj, assay_name)
    if (is.null(assay)) {
      next
    }
    for (slot_name in slot_candidates) {
      matrix <- get_matrix_from_assay(assay, slot_name)
      if (nonempty_matrix(matrix)) {
        message("Using assay=", assay_name, " slot=", slot_name)
        return(list(matrix = repair_dimnames(matrix, obj, assay), assay = assay_name, slot = slot_name))
      }
    }
  }
  stop("No non-empty expression matrix found in preferred assay/slot candidates: assays=", paste(assay_names, collapse = ", "))
}

for (path in files) {
  sample_id <- sub("\\.rds(\\.gz)?$", "", basename(path), ignore.case = TRUE)
  out <- file.path(output_dir, sample_id)
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  message("Direct-exporting ", path, " -> ", out)
  obj <- read_rds_any(path)
  result <- get_expression_matrix(obj)
  counts <- result$matrix
  if (is.null(rownames(counts)) || is.null(colnames(counts))) {
    stop("Exported matrix is missing gene or cell names after dimname repair: ", path)
  }
  Matrix::writeMM(t(counts), file.path(out, "matrix_cells_by_genes.mtx"))
  writeLines(rownames(counts), file.path(out, "genes.txt"))
  writeLines(colnames(counts), file.path(out, "cells.txt"))
  meta <- if ("meta.data" %in% safe_slot_names(obj)) safe_slot(obj, "meta.data") else data.frame()
  if (nrow(meta) != ncol(counts)) {
    meta <- data.frame(row.names = colnames(counts))
  }
  meta$cell_id <- rownames(meta)
  meta$snowcell_export_assay <- result$assay
  meta$snowcell_export_slot <- result$slot
  utils::write.csv(meta, file.path(out, "metadata.csv"), row.names = FALSE, quote = TRUE)
}
