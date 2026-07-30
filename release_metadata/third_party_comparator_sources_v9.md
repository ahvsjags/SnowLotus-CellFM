# Plant-CellFM v9 Third-Party Comparator Source Audit

This note records the source-level status of third-party plant single-cell comparators used or audited for the frozen v9 methods panel.

| Comparator | Official source | Paper / DOI | Current v9 status |
| --- | --- | --- | --- |
| scPlantLLM | https://github.com/compbioNJU/scPlantLLM | Genomics, Proteomics & Bioinformatics 2025, DOI `10.1093/gpbjnl/qzaf024` | Input-ready; metric not reported because the current Matpool host could not complete the official GitHub checkout or ZIP download during this audit. |
| scPlantAnnotate | https://scplantannotate.missouri.edu/ | Journal of Advanced Research 2026, DOI `10.1016/j.jare.2026.01.035` | Web/API reachable; anonymous scriptable benchmark execution is not available in the current audit. |
| Seurat label transfer | https://satijalab.org/seurat/ | Satija Lab Seurat reference-mapping workflow | Completed on the frozen v9 subset export; result in `outputs/external_benchmarks/seurat_v9_subset.json`. |

The frozen release should report completed metrics only for comparisons with local JSON outputs. Input-ready or access-limited tools should be described as audited interfaces until a reproducible checkpoint, CLI, authenticated API, or author-provided result export is available.
