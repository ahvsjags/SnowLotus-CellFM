args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) stop("usage: Rscript extract_gse302041_strict_subset.R <rds> <metadata.tsv> <predictions.csv> <output_dir>")

suppressPackageStartupMessages(library(Matrix))
rds_path <- args[[1]]
metadata_path <- args[[2]]
predictions_path <- args[[3]]
output_dir <- args[[4]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

object <- readRDS(rds_path)
assays <- slot(object, "assays")
if (!"RNA" %in% names(assays)) stop("RNA assay is missing")
counts <- slot(assays[["RNA"]], "counts")
metadata <- read.delim(metadata_path, sep = "\t", stringsAsFactors = FALSE, check.names = FALSE)
predictions <- read.csv(predictions_path, stringsAsFactors = FALSE, check.names = FALSE)
target_ids <- unique(as.character(predictions$cell_id))
target <- metadata[metadata$dataset_id == "arabidopsis_lateral_root_founder_atlas" & as.character(metadata$cell_id) %in% target_ids, , drop = FALSE]
target <- target[match(target_ids[target_ids %in% target$cell_id], target$cell_id), , drop = FALSE]
if (nrow(target) != 256L) stop(sprintf("expected 256 lateral-root target cells, found %d", nrow(target)))

normalize_cell <- function(values) {
  values <- sub("(_[0-9]+)+$", "", values)
  values <- sub("-1$", "", values)
  values
}
source_names <- colnames(counts)
if (is.null(source_names)) stop("RNA counts has no cell names")
source_keys <- normalize_cell(source_names)
target_keys <- normalize_cell(sub("^.*:", "", as.character(target$cell_id)))
groups <- split(seq_along(source_keys), source_keys)
selected <- vapply(target_keys, function(key) {
  candidates <- groups[[key]]
  if (is.null(candidates) || length(candidates) != 1L) return(NA_integer_)
  candidates[[1]]
}, integer(1))
if (anyNA(selected)) {
  missing <- target$cell_id[is.na(selected)]
  n_missing <- sum(is.na(selected) & !(target_keys %in% names(groups)))
  n_ambiguous <- sum(is.na(selected)) - n_missing
  stop(sprintf("RNA source barcode matching failed: missing=%d ambiguous=%d; examples=%s", n_missing, n_ambiguous, paste(head(missing, 10), collapse = ", ")))
}

subset <- counts[, selected, drop = FALSE]
rownames(subset) <- make.unique(rownames(subset))
colnames(subset) <- as.character(target$cell_id)
writeMM(subset, file.path(output_dir, "matrix.mtx"))
writeLines(rownames(subset), file.path(output_dir, "features.tsv"))
writeLines(colnames(subset), file.path(output_dir, "barcodes.tsv"))
writeLines(sprintf("source_rows=%d\nsource_cols=%d\nselected_cells=%d\nassay=RNA", nrow(counts), ncol(counts), ncol(subset)), file.path(output_dir, "manifest.txt"))
cat(sprintf("selected %d cells from %d x %d RNA matrix\n", ncol(subset), nrow(counts), ncol(counts)))
