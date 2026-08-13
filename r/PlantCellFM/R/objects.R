#' Annotate a SingleCellExperiment object.
#'
#' @param object A SingleCellExperiment object.
#' @param checkpoint Path to a Plant-CellFM checkpoint.
#' @param output_dir Directory for the Agent bundle.
#' @param ... Arguments passed to [plantcellfm_annotate()].
#' @return A list with `object` containing predictions and `bundle` containing artifacts.
#' @export
plantcellfm_annotate_sce <- function(object, checkpoint, output_dir, ...) {
  if (!requireNamespace("zellkonverter", quietly = TRUE)) {
    stop("zellkonverter is required for SingleCellExperiment input", call. = FALSE)
  }
  output_dir <- normalizePath(output_dir, winslash = "/", mustWork = FALSE)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  input_path <- file.path(output_dir, "input_from_r.h5ad")
  zellkonverter::writeH5AD(object, file = input_path, overwrite = TRUE)
  bundle <- plantcellfm_annotate(data = input_path, checkpoint = checkpoint,
                                 output_dir = output_dir, ...)
  list(object = plantcellfm_apply_predictions(object, bundle), bundle = bundle)
}

#' Annotate a Seurat object.
#'
#' @param object A Seurat object.
#' @param checkpoint Path to a Plant-CellFM checkpoint.
#' @param output_dir Directory for the Agent bundle.
#' @param ... Arguments passed to [plantcellfm_annotate()].
#' @return A list with `object` containing predictions and `bundle` containing artifacts.
#' @export
plantcellfm_annotate_seurat <- function(object, checkpoint, output_dir, ...) {
  if (!requireNamespace("SeuratDisk", quietly = TRUE)) {
    stop("SeuratDisk is required for Seurat input", call. = FALSE)
  }
  if (!requireNamespace("Seurat", quietly = TRUE)) {
    stop("Seurat is required for Seurat input", call. = FALSE)
  }
  output_dir <- normalizePath(output_dir, winslash = "/", mustWork = FALSE)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  h5seurat <- file.path(output_dir, "input_from_r.h5Seurat")
  h5ad <- file.path(output_dir, "input_from_r.h5ad")
  SeuratDisk::SaveH5Seurat(object, filename = h5seurat, overwrite = TRUE)
  SeuratDisk::Convert(h5seurat, dest = "h5ad", filename = h5ad, overwrite = TRUE)
  bundle <- plantcellfm_annotate(data = h5ad, checkpoint = checkpoint,
                                 output_dir = output_dir, ...)
  predictions <- bundle$predictions
  ids <- colnames(object)
  index <- match(ids, predictions$cell_id)
  if (anyNA(index)) stop("not every Seurat cell was found in predictions$cell_id", call. = FALSE)
  object[["PlantCellFM_label"]] <- predictions$fine_label[index]
  object[["PlantCellFM_confidence"]] <- as.numeric(predictions$fine_confidence[index])
  object[["PlantCellFM_review"]] <- ids %in% if (is.null(bundle$review)) character() else bundle$review$cell_id
  list(object = object, bundle = bundle)
}
