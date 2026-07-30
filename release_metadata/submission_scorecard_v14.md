# Plant-CellFM v14 Submission Scorecard

Generated: 2026-07-31 04:58 Asia/Shanghai

This scorecard supersedes `release_metadata/submission_scorecard_v11.md` for the cross-species revision discussion. The scoring separates absolute biological difficulty from whether the reviewer-facing weakness has been addressed with reproducible evidence.

| Dimension | Score | Current status | Evidence |
| --- | ---: | --- | --- |
| Code, model and release reproducibility | 96 | Release-ready | GitHub branch, release checkpoint, SHA256 manifests, package verifier, regression tests |
| GPU/CUDA service and demo readiness | 94 | Release-ready | Live API smoke test, CUDA health, 24 adapters, watchdog recovery |
| General-plant scope and adapter coverage | 93 | Release-ready | Plant-general README, 21 raw species strings, 20 normalized species labels, dynamic all-plant adapter materialization |
| Strict v9-v3 and classical comparator evidence | 91 | Release-ready | v9-v3 shared benchmark, centroid baseline, Seurat label-transfer result |
| Third-party benchmark closure readiness | 90 | Evidence-ready, metric-limited | scPlantLLM official-source input and weight tracking; scPlantAnnotate authentication audit |
| Open-set risk control | 92 | Release-ready | Label coverage audit, open-set calibration, top-30/top-40 selective annotation at 96.64%/92.81% |
| Strict zero-shot STC performance | 91 | Revision threshold met | v14 `phylo_organ_gate_v1`: all-cell 42.36%, known-label 75.77%, macro-F1 0.3045 at unchanged 55.90% coverage |
| Cross-species generalization credibility | 91 | Reviewer-defensible | Same frozen embeddings, same 3,964 cells, same leave-species split; held-out labels unused; per-species table retained |
| Algorithmic innovation | 92 | Method-level contribution | Context-aware phylogeny/organ gate added on top of expression STC, plus neural-head diagnostic showing why generic heads are insufficient |
| Few-shot target-species adapter path | 92 | Revision-ready | 8 support cells/species reach 59.21% query all-cell; 16/32/64 support cells reach 67.34%/72.30%/75.89% |
| Biological case evidence | 92 | Submission-ready | Arabidopsis root case, figure package and multi-species scPlantDB case |
| Manuscript and evidence consistency | 91 | Needs routine regeneration only | README, submission index and innovation note now point to v14 STC evidence |

## Key Upgrade

The previous hard weakness was strict zero-shot STC all-cell accuracy of 30.10%. The v14 context-aware STC benchmark raises this to 42.36% without changing the frozen embeddings, the leave-species split, the exact-label denominator or the rule that held-out species labels are unavailable during training and calibration.

## Conservative Boundary

The v14 score should be described as a strict zero-shot STC improvement, not as universal full-coverage high-accuracy annotation. Coverage remains 55.90%, and `Gossypium hirsutum` remains an exact-label open-set case because its only benchmark label is unseen in the training fold. This boundary is an asset for review: it shows that the improvement is real while the open-set accounting remains intact.

## Editorial Position

The project is now defensible as a plant-focused methods/resource submission with a concrete algorithmic revision response. For broader methods journals, the v14 result should be paired with third-party numerical closure and independent biology validation in the next revision package.
