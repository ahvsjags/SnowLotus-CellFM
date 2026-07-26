# Editor cover note for SnowLotus-CellFM v0.3

Generated 2026-07-26 03:38 UTC

Dear Editor,

We are submitting SnowLotus-CellFM as an editor-facing v0.3 snapshot of an audited plant single-cell foundation-model resource. The package is designed to be inspectable immediately. It includes source code, training configurations, manuscript files, release metadata, data-integrity audits, model cards, checkpoint manifests, frozen model assets and SHA256 checksums.

The main contribution is a reproducible framework for plant single-cell target-species transfer under realistic public-data constraints. The current audit covers 70 manifest files, 240 readable matrix files and 4,544,570 referenced cells, with 0 missing and 0 unreadable matrices. The frozen embedding checkpoint is the v0.3 validation-best asset from epoch 7 with eval loss 7.1917; the supervised annotation checkpoint carries macro-F1 evidence of 0.8121.

We have deliberately kept the Snow Lotus claim bounded. The current public audit did not identify a directly reusable *Saussurea involucrata* single-cell matrix. The manuscript therefore presents Snow Lotus as a target-species transfer case and data-gap motivation, not as a completed primary atlas. This boundary is stated in the abstract, results and limitations.

Background training and public-data promotion are continuing on the RTX 5090 server. Those activities are not required to inspect the present submission, because the v0.3 assets are frozen and checksummed in the release package. A subsequent revision can replace or supplement the frozen embedding checkpoint after the active run and benchmark refreshes pass audit.

Sincerely,

SnowLotus-CellFM authors
