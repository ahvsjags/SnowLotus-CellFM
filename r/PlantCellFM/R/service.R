.service_get <- function(base_url, route) {
  response <- httr2::request(paste0(sub("/$", "", base_url), route)) |>
    httr2::req_perform()
  httr2::resp_body_json(response, simplifyVector = FALSE)
}

#' Query Plant-CellFM service health.
#' @param base_url Service base URL.
#' @return Parsed JSON response.
#' @export
plantcellfm_health <- function(base_url = "http://127.0.0.1:8000") {
  .service_get(base_url, "/health")
}

#' Query Plant-CellFM service capabilities.
#' @param base_url Service base URL.
#' @return Parsed JSON response.
#' @export
plantcellfm_capabilities <- function(base_url = "http://127.0.0.1:8000") {
  .service_get(base_url, "/capabilities")
}

#' Query registered and dynamic plant adapters.
#' @param base_url Service base URL.
#' @return Parsed JSON response.
#' @export
plantcellfm_adapters <- function(base_url = "http://127.0.0.1:8000") {
  .service_get(base_url, "/adapters")
}

#' Submit a server-side Plant-CellFM annotation job.
#'
#' @param base_url Service base URL.
#' @param data_path Path visible to the server.
#' @param output_dir Output path visible to the server.
#' @param species Optional species name.
#' @param mode `annotation` or `embedding`.
#' @param ortholog_map Optional server-side orthology map.
#' @param layer Optional AnnData layer.
#' @param batch_size Inference batch size.
#' @return Parsed JSON response from the service.
#' @export
plantcellfm_service_annotate <- function(base_url = "http://127.0.0.1:8000", data_path,
                                         output_dir, species = NULL,
                                         mode = c("annotation", "embedding"),
                                         ortholog_map = NULL, layer = NULL,
                                         batch_size = 128L) {
  mode <- match.arg(mode)
  body <- list(data_path = data_path, output_dir = output_dir, mode = mode,
               batch_size = as.integer(batch_size))
  if (!is.null(species)) body$species <- species
  if (!is.null(ortholog_map)) body$ortholog_map <- ortholog_map
  if (!is.null(layer)) body$layer <- layer
  response <- httr2::request(paste0(sub("/$", "", base_url), "/annotate")) |>
    httr2::req_method("POST") |>
    httr2::req_body_json(body, auto_unbox = TRUE) |>
    httr2::req_perform()
  httr2::resp_body_json(response, simplifyVector = FALSE)
}
