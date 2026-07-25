#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: inspect_seurat_slots_without_signac.R <input.rds[.gz]> [max_names]", call. = FALSE)
}

input_path <- args[[1]]
max_names <- if (length(args) >= 2) as.integer(args[[2]]) else 30L
if (is.na(max_names) || max_names < 1) {
  max_names <- 30L
}

suppressPackageStartupMessages(library(Matrix))

print_value <- function(key, value) {
  cat(key, "=", value, "\n", sep = "")
}

collapse_head <- function(values, n = max_names) {
  if (is.null(values) || length(values) == 0) {
    return("")
  }
  paste(utils::head(as.character(values), n), collapse = "|")
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

safe_class <- function(x) {
  tryCatch(paste(class(x), collapse = "|"), error = function(e) paste("ERR", conditionMessage(e)))
}

safe_length <- function(x) {
  tryCatch(length(x), error = function(e) NA_integer_)
}

safe_names <- function(x) {
  tryCatch(names(x), error = function(e) NULL)
}

safe_slot_names <- function(x) {
  tryCatch(slotNames(x), error = function(e) character())
}

safe_slot <- function(x, slot_name) {
  tryCatch(slot(x, slot_name), error = function(e) NULL)
}

safe_dim <- function(x) {
  tryCatch(dim(x), error = function(e) NULL)
}

safe_rownames <- function(x) {
  tryCatch(rownames(x), error = function(e) NULL)
}

safe_colnames <- function(x) {
  tryCatch(colnames(x), error = function(e) NULL)
}

matrix_summary <- function(x, prefix) {
  dims <- safe_dim(x)
  if (is.null(dims) || length(dims) != 2) {
    return(FALSE)
  }
  nnz <- tryCatch(length(x@x), error = function(e) NA_integer_)
  if (is.na(nnz)) {
    nnz <- tryCatch(Matrix::nnzero(x), error = function(e) NA_integer_)
  }
  print_value(paste0(prefix, ".matrix"), paste0(safe_class(x), ":", dims[[1]], "x", dims[[2]], ":nnz=", nnz))
  print_value(paste0(prefix, ".rownames.head"), collapse_head(safe_rownames(x), 10L))
  print_value(paste0(prefix, ".colnames.head"), collapse_head(safe_colnames(x), 10L))
  TRUE
}

child_names <- function(x) {
  if (is.environment(x)) {
    return(sort(ls(x, all.names = TRUE)))
  }
  names <- safe_names(x)
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

describe_value <- function(x, prefix, depth = 0L) {
  print_value(paste0(prefix, ".class"), safe_class(x))
  print_value(paste0(prefix, ".isS4"), isS4(x))
  print_value(paste0(prefix, ".typeof"), typeof(x))
  print_value(paste0(prefix, ".length"), safe_length(x))
  names <- child_names(x)
  if (length(names) > 0) {
    print_value(paste0(prefix, ".names"), collapse_head(names))
  }
  slots <- safe_slot_names(x)
  if (length(slots) > 0) {
    print_value(paste0(prefix, ".slots"), paste(slots, collapse = "|"))
  }
  if (matrix_summary(x, prefix)) {
    return(invisible(TRUE))
  }
  if (depth >= 2L) {
    return(invisible(FALSE))
  }
  for (name in utils::head(names, max_names)) {
    child <- child_value(x, name)
    if (!is.null(child)) {
      describe_value(child, paste0(prefix, ".", make.names(name)), depth + 1L)
    }
  }
  invisible(FALSE)
}

describe_slot <- function(x, prefix, slot_name) {
  value <- safe_slot(x, slot_name)
  if (is.null(value)) {
    return()
  }
  describe_value(value, paste0(prefix, ".slot.", make.names(slot_name)), 1L)
}

describe_assay <- function(assay, prefix) {
  describe_value(assay, prefix, 1L)
  for (slot_name in c(
    "counts", "data", "scale.data", "layers", "cells", "features",
    "meta.features", "meta.data", "var.features", "key", "assay.orig",
    "ranges", "motifs", "fragments", "misc"
  )) {
    describe_slot(assay, prefix, slot_name)
  }
}

describe_seurat_like <- function(obj, prefix) {
  describe_value(obj, prefix, 0L)
  if (!("assays" %in% safe_slot_names(obj))) {
    return()
  }
  assays <- safe_slot(obj, "assays")
  print_value(paste0(prefix, ".slot.assays.class"), safe_class(assays))
  assay_names <- child_names(assays)
  print_value(paste0(prefix, ".slot.assays.names"), collapse_head(assay_names))
  print_value(paste0(prefix, ".slot.assays.length"), length(assay_names))
  for (assay_name in utils::head(assay_names, max_names)) {
    assay <- child_value(assays, assay_name)
    if (!is.null(assay)) {
      describe_assay(assay, paste0(prefix, ".assay.", make.names(assay_name)))
    }
  }
  if ("meta.data" %in% safe_slot_names(obj)) {
    meta <- safe_slot(obj, "meta.data")
    print_value(paste0(prefix, ".meta.class"), safe_class(meta))
    print_value(paste0(prefix, ".meta.dim"), paste(safe_dim(meta), collapse = "x"))
    print_value(paste0(prefix, ".meta.cols"), collapse_head(colnames(meta)))
  }
}

print_value("r.version", R.version.string)
print_value("input_path", input_path)
obj <- read_rds_any(input_path)
describe_seurat_like(obj, "object")
