suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(Seurat))
suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
arg_value <- function(flag, default = NULL) {
  hit <- which(args == flag)
  if (length(hit) == 0 || hit == length(args)) {
    return(default)
  }
  args[[hit + 1]]
}

input_dir <- arg_value("--input-dir")
output_json <- arg_value("--output-json")
label_key <- arg_value("--label-key", "cell_type")
coarse_label_key <- arg_value("--coarse-label-key", "cell_type_coarse")
max_dims <- as.integer(arg_value("--dims", "30"))
variable_features <- as.integer(arg_value("--variable-features", "2000"))

if (is.null(input_dir) || is.null(output_json)) {
  stop("Usage: Rscript scripts/run_seurat_label_transfer_benchmark.R --input-dir DIR --output-json OUT.json")
}

log_step <- function(message) {
  cat(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), message, "\n")
  flush.console()
}

read_split <- function(name) {
  log_step(paste("reading", name))
  matrix <- readMM(file.path(input_dir, paste0(name, ".mtx")))
  genes <- readLines(file.path(input_dir, "genes.tsv"), warn = FALSE)
  meta <- read.delim(file.path(input_dir, paste0(name, "_metadata.tsv")), stringsAsFactors = FALSE)
  rownames(matrix) <- make.unique(genes)
  colnames(matrix) <- make.unique(meta$cell_id)
  rownames(meta) <- colnames(matrix)
  object <- CreateSeuratObject(counts = matrix, meta.data = meta)
  log_step(paste("normalizing", name, "cells", ncol(object), "genes", nrow(object)))
  object <- NormalizeData(object, verbose = FALSE)
  object <- FindVariableFeatures(object, nfeatures = variable_features, verbose = FALSE)
  features <- VariableFeatures(object)
  log_step(paste("scaling", name, "variable_features", length(features)))
  object <- ScaleData(object, features = features, verbose = FALSE)
  object <- RunPCA(object, features = features, npcs = max_dims, verbose = FALSE)
  object
}

macro_f1 <- function(truth, pred) {
  labels <- sort(unique(c(truth, pred)))
  scores <- c()
  for (label in labels) {
    tp <- sum(truth == label & pred == label)
    fp <- sum(truth != label & pred == label)
    fn <- sum(truth == label & pred != label)
    precision <- ifelse(tp + fp == 0, 0, tp / (tp + fp))
    recall <- ifelse(tp + fn == 0, 0, tp / (tp + fn))
    scores <- c(scores, ifelse(precision + recall == 0, 0, 2 * precision * recall / (precision + recall)))
  }
  mean(scores)
}

accuracy <- function(truth, pred) {
  mean(truth == pred)
}

log_step("starting Seurat label-transfer benchmark")
reference <- read_split("train")
query <- read_split("test")
dims <- seq_len(min(max_dims, ncol(Embeddings(reference, "pca"))))
log_step(paste("finding transfer anchors dims", length(dims)))
anchors <- FindTransferAnchors(reference = reference, query = query, dims = dims, verbose = FALSE)

log_step("transferring fine labels")
fine_pred <- TransferData(
  anchorset = anchors,
  refdata = reference[[label_key, drop = TRUE]],
  dims = dims,
  verbose = FALSE
)
log_step("transferring coarse labels")
coarse_pred <- TransferData(
  anchorset = anchors,
  refdata = reference[[coarse_label_key, drop = TRUE]],
  dims = dims,
  verbose = FALSE
)

fine_truth <- query[[label_key, drop = TRUE]]
coarse_truth <- query[[coarse_label_key, drop = TRUE]]
result <- list(
  method = "seurat_label_transfer",
  input_dir = input_dir,
  label_key = label_key,
  coarse_label_key = coarse_label_key,
  test_cells = length(fine_truth),
  fine_test_accuracy = accuracy(fine_truth, fine_pred$predicted.id),
  fine_test_macro_f1 = macro_f1(fine_truth, fine_pred$predicted.id),
  coarse_test_accuracy = accuracy(coarse_truth, coarse_pred$predicted.id),
  coarse_test_macro_f1 = macro_f1(coarse_truth, coarse_pred$predicted.id)
)

dir.create(dirname(output_json), recursive = TRUE, showWarnings = FALSE)
writeLines(toJSON(result, auto_unbox = TRUE, pretty = TRUE), output_json)
log_step("finished Seurat label-transfer benchmark")
cat(output_json, "\n")
