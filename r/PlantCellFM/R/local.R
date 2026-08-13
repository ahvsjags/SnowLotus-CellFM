#' Run PlantCell-Agent on an expression matrix.
#'
#' @param data Path to an `.h5ad` or `.npz` matrix.
#' @param checkpoint Path to a Plant-CellFM checkpoint.
#' @param output_dir Directory for the auditable output bundle.
#' @param species Optional species name used by the adapter router.
#' @param support_labels Optional path or data.frame with `cell_id` and a label column.
#' @param ortholog_map Optional TSV orthology map.
#' @param project_root Root of the SnowLotus-CellFM repository.
#' @param python Python executable, default `python`.
#' @param device `auto`, `cpu`, `cuda` or `cuda:N`.
#' @param review_threshold Confidence threshold for automatic release.
#' @param coverage_target Minimum accepted coverage target.
#' @param batch_size Inference batch size.
#' @param layer Optional AnnData layer.
#' @param ortholog_aggregation `first` or `mean`.
#' @param registry Optional species-adapter registry path.
#' @return A `plantcellfm_bundle` list. See [plantcellfm_read_bundle()].
#' @export
plantcellfm_annotate <- function(data, checkpoint, output_dir, species = NULL,
                                 support_labels = NULL, ortholog_map = NULL,
                                 project_root = ".", python = "python", device = "auto",
                                 review_threshold = 0.70, coverage_target = 0.80,
                                 batch_size = 128L, layer = NULL,
                                 ortholog_aggregation = NULL, registry = NULL) {
  project_root <- .abs_path(project_root, "project_root", must_exist = TRUE)
  data <- .abs_path(data, "data", must_exist = TRUE)
  checkpoint <- .abs_path(checkpoint, "checkpoint", must_exist = TRUE)
  output_dir <- normalizePath(output_dir, winslash = "/", mustWork = FALSE)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  if (!is.numeric(review_threshold) || length(review_threshold) != 1L || review_threshold < 0 || review_threshold > 1) {
    stop("review_threshold must be a number between 0 and 1", call. = FALSE)
  }
  if (!is.numeric(coverage_target) || length(coverage_target) != 1L || coverage_target < 0 || coverage_target > 1) {
    stop("coverage_target must be a number between 0 and 1", call. = FALSE)
  }
  if (length(batch_size) != 1L || batch_size < 1) stop("batch_size must be positive", call. = FALSE)

  support_path <- NULL
  if (is.data.frame(support_labels)) {
    if (!"cell_id" %in% names(support_labels)) stop("support_labels needs a cell_id column", call. = FALSE)
    label_candidates <- intersect(c("fine_label", "label", "cell_type"), names(support_labels))
    if (!length(label_candidates)) stop("support_labels needs fine_label, label or cell_type", call. = FALSE)
    support_path <- file.path(output_dir, "support_labels_from_r.tsv")
    utils::write.table(support_labels, support_path, sep = "\t", row.names = FALSE, quote = FALSE)
  } else if (!is.null(support_labels)) {
    support_path <- .abs_path(support_labels, "support_labels", must_exist = TRUE)
  }

  if (is.null(registry)) registry <- file.path(project_root, "release_metadata", "plant_species_adapters.json")
  registry <- .abs_path(registry, "registry", must_exist = TRUE)
  args <- c("-m", "snowcell", "agent-annotate", "--checkpoint", checkpoint,
            "--data", data, "--output-dir", output_dir, "--registry", registry,
            "--review-threshold", format(review_threshold, scientific = FALSE),
            "--coverage-target", format(coverage_target, scientific = FALSE),
            "--batch-size", as.character(as.integer(batch_size)), "--device", device)
  args <- .nullable_argument(args, "--species", species)
  args <- .nullable_argument(args, "--support-labels", support_path)
  args <- .nullable_argument(args, "--ortholog-map", if (is.null(ortholog_map)) NULL else .abs_path(ortholog_map, "ortholog_map", TRUE))
  args <- .nullable_argument(args, "--ortholog-aggregation", ortholog_aggregation)
  args <- .nullable_argument(args, "--layer", layer)
  .run_python(python, args, project_root)
  plantcellfm_read_bundle(output_dir)
}

#' Annotate an H5AD file with PlantCell-Agent.
#'
#' @param data Path to an H5AD file.
#' @param ... Arguments passed to [plantcellfm_annotate()].
#' @export
plantcellfm_annotate_h5ad <- function(data, ...) {
  plantcellfm_annotate(data = data, ...)
}

#' Check that the Python Plant-CellFM runtime is visible to R.
#'
#' @param python Python executable.
#' @param project_root Root of the SnowLotus-CellFM repository.
#' @return A list containing the runtime status and captured output.
#' @export
plantcellfm_check_installation <- function(python = "python", project_root = ".") {
  project_root <- .abs_path(project_root, "project_root", must_exist = TRUE)
  restore <- .pythonpath(project_root)
  on.exit(restore(), add = TRUE)
  output <- tryCatch(
    system2(python, c("-c", "import snowcell, torch; print('snowcell=' + snowcell.__file__); print('torch=' + torch.__version__); print('cuda=' + str(torch.cuda.is_available()))"), stdout = TRUE, stderr = TRUE),
    error = function(error) structure(conditionMessage(error), status = 1L)
  )
  status <- attr(output, "status")
  list(ok = is.null(status) || status == 0L, status = if (is.null(status)) 0L else status,
       python = python, output = as.character(output))
}
