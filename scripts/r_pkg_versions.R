pkgs <- c(
  "Seurat",
  "SeuratObject",
  "spatstat",
  "spatstat.core",
  "spatstat.data",
  "spatstat.explore",
  "spatstat.geom",
  "spatstat.random",
  "spatstat.sparse",
  "spatstat.utils",
  "RcppAnnoy",
  "remotes",
  "devtools",
  "Matrix"
)

cat("R.version=", R.version.string, "\n", sep = "")
cat(".libPaths=", paste(.libPaths(), collapse = " | "), "\n", sep = "")
ip <- installed.packages()
for (p in pkgs) {
  cat("PKG\t", p, "\t", sep = "")
  if (p %in% rownames(ip)) {
    cat(ip[p, "Version"], "\t", ip[p, "LibPath"], "\n", sep = "")
  } else {
    cat("MISSING\t\n", sep = "")
  }
}
