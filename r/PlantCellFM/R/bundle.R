#' Read a PlantCell-Agent output bundle into R.
#'
#' @param output_dir Agent output directory.
#' @return A list of tables, metadata, trace and artifact paths.
#' @export
plantcellfm_read_bundle <- function(output_dir) {
  output_dir <- .abs_path(output_dir, "output_dir", must_exist = TRUE)
  structure(list(
    output_dir = output_dir,
    predictions = .read_table(file.path(output_dir, "predictions.csv")),
    predictions_direct = .read_table(file.path(output_dir, "predictions_direct.csv")),
    review = .read_table(file.path(output_dir, "uncertainty_review.tsv"), sep = "\t"),
    markers = .read_table(file.path(output_dir, "marker_evidence.tsv"), sep = "\t"),
    route = .as_json(file.path(output_dir, "route_decision.json")),
    plan = .as_json(file.path(output_dir, "agent_plan.json")),
    specialist_plan = .as_json(file.path(output_dir, "specialist_plan.json")),
    verification = .as_json(file.path(output_dir, "evidence_verification.json")),
    metadata = .as_json(file.path(output_dir, "annotation_metadata.json")),
    report = if (file.exists(file.path(output_dir, "agent_report.md"))) readLines(file.path(output_dir, "agent_report.md"), warn = FALSE) else character(),
    trace = if (file.exists(file.path(output_dir, "agent_trace.jsonl"))) readLines(file.path(output_dir, "agent_trace.jsonl"), warn = FALSE) else character(),
    artifacts = list(
      embeddings = file.path(output_dir, "embeddings.npy"),
      predictions = file.path(output_dir, "predictions.csv"),
      review = file.path(output_dir, "uncertainty_review.tsv"),
      markers = file.path(output_dir, "marker_evidence.tsv"),
      trace = file.path(output_dir, "agent_trace.jsonl")
    )
  ), class = "plantcellfm_bundle")
}

#' Add Agent predictions to a SingleCellExperiment object.
#'
#' @param object A SingleCellExperiment object.
#' @param bundle A bundle returned by [plantcellfm_read_bundle()], or a path.
#' @return The object with prediction columns in `colData`.
#' @export
plantcellfm_apply_predictions <- function(object, bundle) {
  if (!requireNamespace("SummarizedExperiment", quietly = TRUE)) {
    stop("SummarizedExperiment is required to apply predictions to an R object", call. = FALSE)
  }
  if (is.character(bundle)) bundle <- plantcellfm_read_bundle(bundle)
  predictions <- bundle$predictions
  if (is.null(predictions) || !nrow(predictions)) stop("bundle has no predictions.csv", call. = FALSE)
  ids <- colnames(object)
  if (is.null(ids)) stop("object must have cell names in colnames()", call. = FALSE)
  index <- match(ids, predictions$cell_id)
  if (anyNA(index)) stop("not every object cell was found in predictions$cell_id", call. = FALSE)
  cd <- SummarizedExperiment::colData(object)
  cd$predicted_label <- predictions$fine_label[index]
  cd$prediction_confidence <- as.numeric(predictions$fine_confidence[index])
  cd$coarse_label <- predictions$coarse_label[index]
  cd$review_required <- ids %in% if (is.null(bundle$review)) character() else bundle$review$cell_id
  SummarizedExperiment::colData(object) <- cd
  object
}

