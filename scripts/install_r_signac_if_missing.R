options(timeout = as.integer(Sys.getenv("R_DOWNLOAD_TIMEOUT", unset = "900")))

repos <- Sys.getenv("CRAN_REPO", unset = "https://cloud.r-project.org")
options(repos = c(CRAN = repos))

install_if_missing <- function(package) {
  if (requireNamespace(package, quietly = TRUE)) {
    message(package, " already installed: ", as.character(utils::packageVersion(package)))
    return(invisible(TRUE))
  }
  message("Installing missing R package: ", package)
  utils::install.packages(package, repos = repos, dependencies = TRUE)
  if (!requireNamespace(package, quietly = TRUE)) {
    stop("Package still missing after installation: ", package, call. = FALSE)
  }
  message(package, " installed: ", as.character(utils::packageVersion(package)))
  invisible(TRUE)
}

install_if_missing("BiocManager")
install_if_missing("remotes")

bioc_packages <- c(
  "BiocGenerics",
  "S4Vectors",
  "IRanges",
  "GenomeInfoDb",
  "GenomicRanges",
  "Biostrings",
  "Rsamtools",
  "SummarizedExperiment",
  "TFBSTools",
  "motifmatchr",
  "BSgenome",
  "rtracklayer",
  "biovizBase"
)

message("Installing/checking Bioconductor dependencies")
try(
  BiocManager::install(bioc_packages, ask = FALSE, update = FALSE, Ncpus = 2),
  silent = FALSE
)

cran_packages <- c(
  "rlang",
  "RcppHNSW",
  "irlba",
  "RcppRoll",
  "future",
  "future.apply",
  "ggplot2",
  "patchwork",
  "hdf5r"
)

for (package in cran_packages) {
  try(install_if_missing(package), silent = FALSE)
}

install_signac <- function() {
  if (requireNamespace("Signac", quietly = TRUE)) {
    message("Signac already installed: ", as.character(utils::packageVersion("Signac")))
    return(invisible(TRUE))
  }

  message("Trying CRAN Signac first")
  try(utils::install.packages("Signac", repos = repos, dependencies = TRUE), silent = FALSE)
  if (requireNamespace("Signac", quietly = TRUE)) {
    message("Signac installed from CRAN: ", as.character(utils::packageVersion("Signac")))
    return(invisible(TRUE))
  }

  message("Trying Signac 1.7.0 for Seurat 4.x compatibility")
  remotes::install_version(
    "Signac",
    version = "1.7.0",
    repos = repos,
    dependencies = TRUE,
    upgrade = "never"
  )
  if (!requireNamespace("Signac", quietly = TRUE)) {
    stop("Package still missing after Signac installation attempts", call. = FALSE)
  }
  message("Signac installed: ", as.character(utils::packageVersion("Signac")))
  invisible(TRUE)
}

install_signac()
