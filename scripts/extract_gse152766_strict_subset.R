args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) stop("usage: Rscript extract_gse152766_strict_subset.R <rds> <metadata.tsv> <predictions.csv> <output_dir>")

suppressPackageStartupMessages(library(Matrix))
rds_path <- args[[1]]
metadata_path <- args[[2]]
predictions_path <- args[[3]]
output_dir <- args[[4]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

object <- readRDS(rds_path)
assays <- slot(object, "assays")
required_assays <- c(spliced_counts_filtered = "spliced_RNA", unspliced_counts_filtered = "unspliced_RNA")
if (!all(unname(required_assays) %in% names(assays))) stop("required spliced_RNA and unspliced_RNA assays are missing")
metadata <- read.delim(metadata_path, sep = "\t", stringsAsFactors = FALSE, check.names = FALSE)
predictions <- read.csv(predictions_path, stringsAsFactors = FALSE, check.names = FALSE)
target_ids <- unique(as.character(predictions$cell_id))
target <- metadata[metadata$dataset_id == "arabidopsis_root_atlas" & as.character(metadata$cell_id) %in% target_ids, , drop = FALSE]
target <- target[match(target_ids[target_ids %in% target$cell_id], target$cell_id), , drop = FALSE]
if (nrow(target) != 256L) stop(sprintf("expected 256 root target cells, found %d", nrow(target)))

normalize_barcode <- function(values) {
  values <- sub("(_[0-9]+)+$", "", values)
  values <- sub("-1$", "", values)
  values
}
pieces <- list()
piece_ids <- list()
for (sample_name in names(required_assays)) {
  sample_target <- target[target$sample_id == sample_name, , drop = FALSE]
  if (!nrow(sample_target)) next
  assay_name <- unname(required_assays[[sample_name]])
  counts <- slot(assays[[assay_name]], "counts")
  source_names <- colnames(counts)
  if (is.null(source_names)) stop(sprintf("%s counts has no cell names", assay_name))
  source_keys <- normalize_barcode(source_names)
  target_keys <- normalize_barcode(sub("^.*:", "", as.character(sample_target$cell_id)))
  groups <- split(seq_along(source_keys), source_keys)
  selected <- vapply(target_keys, function(key) {
    candidates <- groups[[key]]
    if (is.null(candidates) || length(candidates) != 1L) return(NA_integer_)
    candidates[[1]]
  }, integer(1))
  if (anyNA(selected)) {
    missing <- sample_target$cell_id[is.na(selected)]
    n_missing <- sum(is.na(selected) & !(target_keys %in% names(groups)))
    n_ambiguous <- sum(is.na(selected)) - n_missing
    stop(sprintf("%s source barcode matching failed: missing=%d ambiguous=%d; examples=%s", assay_name, n_missing, n_ambiguous, paste(head(missing, 10), collapse = ", ")))
  }
  pieces[[sample_name]] <- counts[, selected, drop = FALSE]
  piece_ids[[sample_name]] <- as.character(sample_target$cell_id)
}

subset <- do.call(cbind, pieces)
piece_cell_ids <- unlist(piece_ids, use.names = FALSE)
order_index <- match(as.character(target$cell_id), piece_cell_ids)
if (anyNA(order_index)) stop("assay-wise extraction did not recover every target cell")
subset <- subset[, order_index, drop = FALSE]
rownames(subset) <- make.unique(rownames(subset))
colnames(subset) <- as.character(target$cell_id)
writeMM(subset, file.path(output_dir, "matrix.mtx"))
writeLines(rownames(subset), file.path(output_dir, "features.tsv"))
writeLines(colnames(subset), file.path(output_dir, "barcodes.tsv"))
writeLines(sprintf("source_rows=%d\nsource_cols=%d\nselected_cells=%d\nassays=spliced_RNA:%d,unspliced_RNA:%d", nrow(subset), ncol(slot(assays[["spliced_RNA"]], "counts")), ncol(subset), ncol(pieces[["spliced_counts_filtered"]]), ncol(pieces[["unspliced_counts_filtered"]])), file.path(output_dir, "manifest.txt"))
cat(sprintf("selected %d cells from assay-wise spliced/unspliced source matrices\n", ncol(subset)))
