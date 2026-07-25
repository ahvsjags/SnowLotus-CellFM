#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: inspect_rds_structure.R <input.rds> [max_names]", call. = FALSE)
}

input_path <- args[[1]]
max_names <- if (length(args) >= 2) as.integer(args[[2]]) else 30L
if (is.na(max_names) || max_names < 1) {
  max_names <- 30L
}

suppressPackageStartupMessages({
  library(Matrix)
})

print_value <- function(key, value) {
  cat(key, "=", value, "\n", sep = "")
}

package_version_or_missing <- function(package) {
  tryCatch(
    as.character(utils::packageVersion(package)),
    error = function(e) "missing"
  )
}

print_value("r.version", R.version.string)
for (package in c("Matrix", "Seurat", "SeuratObject")) {
  print_value(paste0("package.", package), package_version_or_missing(package))
}

load_optional <- function(package) {
  suppressPackageStartupMessages(
    tryCatch(
      {
        library(package, character.only = TRUE)
        TRUE
      },
      error = function(e) FALSE
    )
  )
}

has_seurat <- load_optional("Seurat")
if (!has_seurat) {
  load_optional("SeuratObject")
}

collapse_head <- function(values, n = max_names) {
  if (is.null(values) || length(values) == 0) {
    return("")
  }
  paste(utils::head(as.character(values), n), collapse = "|")
}

matrix_summary <- function(x) {
  dims <- tryCatch(dim(x), error = function(e) NULL)
  if (is.null(dims) || length(dims) != 2) {
    return(NULL)
  }
  nnz <- tryCatch(length(x@x), error = function(e) NA_integer_)
  paste0(class(x)[[1]], ":", dims[[1]], "x", dims[[2]], ":nnz=", nnz)
}

describe_matrix_or_list <- function(x, prefix) {
  summary <- matrix_summary(x)
  if (!is.null(summary)) {
    print_value(prefix, summary)
    return()
  }
  if (is.list(x) || is.environment(x)) {
    print_value(paste0(prefix, ".class"), paste(class(x), collapse = "|"))
    print_value(paste0(prefix, ".names"), collapse_head(names(x)))
    for (name in utils::head(names(x), max_names)) {
      child <- tryCatch(x[[name]], error = function(e) NULL)
      child_summary <- matrix_summary(child)
      if (!is.null(child_summary)) {
        print_value(paste0(prefix, ".", make.names(name)), child_summary)
      }
    }
  }
}

describe_assay_object <- function(assay, prefix) {
  print_value(paste0(prefix, ".class"), paste(class(assay), collapse = "|"))
  print_value(paste0(prefix, ".isS4"), isS4(assay))
  print_value(paste0(prefix, ".typeof"), typeof(assay))
  print_value(paste0(prefix, ".length"), length(assay))
  print_value(paste0(prefix, ".names"), collapse_head(names(assay)))
  print_value(paste0(prefix, ".attributes"), collapse_head(names(attributes(assay))))
  print_value(paste0(prefix, ".slots"), paste(slotNames(assay), collapse = "|"))
  layers <- tryCatch(Layers(assay), error = function(e) character())
  print_value(paste0(prefix, ".layers"), paste(layers, collapse = "|"))
  for (slot_name in c("layers", "cells", "features", "counts", "data", "scale.data", "meta.data", "misc")) {
    slot_value <- tryCatch(slot(assay, slot_name), error = function(e) NULL)
    if (!is.null(slot_value)) {
      describe_matrix_or_list(slot_value, paste0(prefix, ".slot.", slot_name))
    }
  }
  str_lines <- utils::head(capture.output(str(assay, max.level = 2, list.len = 20)), 60)
  if (length(str_lines) > 0) {
    print_value(paste0(prefix, ".str"), paste(str_lines, collapse = " || "))
  }
}

describe_seurat <- function(obj, prefix = "seurat") {
  print_value(paste0(prefix, ".class"), paste(class(obj), collapse = "|"))
  print_value(paste0(prefix, ".slots"), paste(slotNames(obj), collapse = "|"))
  assays <- tryCatch(Assays(obj), error = function(e) character())
  print_value(paste0(prefix, ".assays"), paste(assays, collapse = "|"))
  print_value(
    paste0(prefix, ".default_assay"),
    tryCatch(DefaultAssay(obj), error = function(e) paste("ERR", conditionMessage(e)))
  )
  if ("assays" %in% slotNames(obj)) {
    slot_assays <- slot(obj, "assays")
    print_value(paste0(prefix, ".slot_assays.class"), paste(class(slot_assays), collapse = "|"))
    print_value(paste0(prefix, ".slot_assays.names"), collapse_head(names(slot_assays)))
    print_value(paste0(prefix, ".slot_assays.length"), length(slot_assays))
    for (assay_name in utils::head(names(slot_assays), max_names)) {
      assay <- slot_assays[[assay_name]]
      describe_assay_object(assay, paste0(prefix, ".assay.", assay_name))
    }
  }
  if ("meta.data" %in% slotNames(obj)) {
    meta <- slot(obj, "meta.data")
    print_value(paste0(prefix, ".meta.dim"), paste(dim(meta), collapse = "x"))
    print_value(paste0(prefix, ".meta.cols"), collapse_head(colnames(meta)))
  }
}

describe_object <- function(obj, prefix = "object", depth = 0L) {
  print_value(paste0(prefix, ".class"), paste(class(obj), collapse = "|"))
  print_value(paste0(prefix, ".length"), length(obj))
  obj_names <- names(obj)
  if (!is.null(obj_names)) {
    print_value(paste0(prefix, ".names"), collapse_head(obj_names))
  }
  if (inherits(obj, "Seurat")) {
    describe_seurat(obj, prefix)
  } else {
    summary <- matrix_summary(obj)
    if (!is.null(summary)) {
      print_value(paste0(prefix, ".matrix"), summary)
    }
  }
  if (depth < 2L && (is.list(obj) || is.environment(obj))) {
    keys <- utils::head(names(obj), max_names)
    for (key in keys) {
      child <- tryCatch(obj[[key]], error = function(e) NULL)
      if (!is.null(child)) {
        describe_object(child, paste0(prefix, ".", make.names(key)), depth + 1L)
      }
    }
  }
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

obj <- read_rds_any(input_path)
describe_object(obj, "object")
