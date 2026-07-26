pkgs <- c(
  "Seurat",
  "SeuratObject",
  "spatstat.core",
  "spatstat.geom",
  "spatstat.explore",
  "spatstat.random",
  "RcppAnnoy",
  "Matrix"
)

for (p in pkgs) {
  cat("PKG", p, "\n")
  cat("version=")
  if (requireNamespace(p, quietly = TRUE)) {
    cat(as.character(packageVersion(p)), "\n")
  } else {
    cat("MISSING\n")
  }
  cat("load=")
  print(tryCatch({
    suppressPackageStartupMessages(library(p, character.only = TRUE))
    "OK"
  }, error = function(e) paste("ERR", conditionMessage(e))))
}
