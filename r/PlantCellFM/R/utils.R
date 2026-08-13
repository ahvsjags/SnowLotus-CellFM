.require_scalar <- function(value, name, allow_null = FALSE) {
  if (is.null(value) && allow_null) return(invisible(NULL))
  if (length(value) != 1L || is.na(value) || !is.character(value)) {
    stop(sprintf("%s must be one non-missing character value", name), call. = FALSE)
  }
  invisible(value)
}

.abs_path <- function(path, name, must_exist = FALSE) {
  .require_scalar(path, name)
  result <- normalizePath(path, winslash = "/", mustWork = must_exist)
  if (must_exist && !file.exists(result)) {
    stop(sprintf("%s does not exist: %s", name, result), call. = FALSE)
  }
  result
}

.pythonpath <- function(project_root) {
  src <- file.path(project_root, "src")
  old <- Sys.getenv("PYTHONPATH", unset = "")
  value <- c(src, if (nzchar(old)) strsplit(old, .Platform$path.sep, fixed = TRUE)[[1]])
  old_env <- Sys.getenv("PYTHONPATH", unset = NA_character_)
  Sys.setenv(PYTHONPATH = paste(unique(value), collapse = .Platform$path.sep))
  function() {
    if (is.na(old_env)) Sys.unsetenv("PYTHONPATH") else Sys.setenv(PYTHONPATH = old_env)
  }
}

.run_python <- function(python, args, project_root) {
  .require_scalar(python, "python")
  restore <- .pythonpath(project_root)
  on.exit(restore(), add = TRUE)
  output <- system2(python, args = args, stdout = TRUE, stderr = TRUE)
  status <- attr(output, "status")
  if (!is.null(status) && status != 0L) {
    message_text <- paste(as.character(output), collapse = "\n")
    stop(sprintf("Plant-CellFM Python command failed (status %s):\n%s", status, message_text), call. = FALSE)
  }
  invisible(as.character(output))
}

.as_json <- function(path) {
  if (!file.exists(path)) return(NULL)
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

.read_table <- function(path, sep = ",") {
  if (!file.exists(path)) return(NULL)
  utils::read.delim(path, sep = sep, header = TRUE, quote = "", comment.char = "", check.names = FALSE,
                    stringsAsFactors = FALSE)
}

.nullable_argument <- function(args, flag, value) {
  if (!is.null(value)) c(args, flag, as.character(value)) else args
}
