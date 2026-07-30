# Plant-CellFM v9 Publication Target Readiness Matrix

Generated: 2026-07-30 Asia/Shanghai

This matrix is a current-state submission audit for the frozen v9 package. It replaces earlier 5090/SnowLotus-centered planning language. The current model card uses NVIDIA GeForce RTX 4090, 24 GB VRAM, and the current scientific scope is Plant-CellFM as a plant-general single-cell annotation foundation model with an all-plant adapter layer.

## Readiness Summary

| Target tier | Current status | Submission stance |
| --- | --- | --- |
| Plant-focused methods/resource journal | READY | Strongest current path. Submit as a plant single-cell method/resource with public corpus, adapter framework, benchmark evidence and Arabidopsis root case. |
| Genome Biology / genomics computational-method target | NEAR_READY_WITH_MAJOR_REVISION_RISK | Plausible if framed around reproducible genomics resource and strict benchmark; stronger official third-party comparator would improve the case. |
| Communications Biology / broad biology target | POSSIBLE_WITH_CONSERVATIVE_FRAMING | Usable if the manuscript emphasizes concrete plant biology utility and avoids universal high-accuracy claims. |
| Nature Methods | STRETCH_NOT_YET_FULLY_CLOSED | Needs stronger method novelty, official third-party model benchmarks and broader biological validation before being a robust target. |
| Nature Plants | STRETCH_AFTER_BIOLOGY_VALIDATION | Needs stronger independent plant biological discovery or validation beyond the current computational case. |

## Current Gate Matrix

| Gate | Status | Evidence | Interpretation |
| --- | --- | --- | --- |
| SSH and server execution | READY | `ssh matpool-px1-jcy`; server package under `/mnt/snowlotus_cellfm` | Remote execution and package synchronization are working. |
| GPU/CUDA service | READY | `release_metadata/api_runtime_smoke_v9.md`; service health reports `device=cuda` | The frozen model is served as a callable CUDA service. |
| Hardware statement | READY | `release_metadata/plant_cellfm_v9_model_card.md` | Current submission uses RTX 4090, not historical 5090 planning. |
| GitHub synchronization | READY | branch `agent/remote-pipeline-20260728`; final package manifest source commit `eed1005dec5d7d747b66afaa21e01505b096a381` | Repository, package and server evidence are aligned. |
| Public plant corpus | READY_FOR_V9 | `release_metadata/v9_data_card.md` | Supports plant-general framing for the frozen v9 candidate. |
| Frozen model asset | READY | GitHub release asset and SHA256 in model card | Checkpoint is externally addressable and checksum-pinned. |
| v9-v3 strict benchmark | READY | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` | Fair same-subset comparison exists. |
| Species-holdout interpretation | READY_WITH_OPEN_SET_BOUNDARY | `release_metadata/species_holdout_failure_audit_v9.md` | Low leave-species result is decomposed into label coverage and transfer errors; do not claim universal high accuracy. |
| Seurat comparator | READY | `release_metadata/external_benchmarks/seurat_v9_subset.json` | Traditional label transfer baseline is complete. |
| scPlantLLM comparator | INPUT_READY_METRIC_MISSING | `release_metadata/scplantllm_input_readiness.md`; `release_metadata/scplantllm_preprocess_probe_readiness.md` | Keep as auditable entry point until official checkout/weights are available. |
| scPlantAnnotate comparator | ACCESS_LIMITED | `release_metadata/scplantannotate_access_audit.md` | Official route is reachable, but anonymous scriptable benchmark execution is not available. |
| Arabidopsis root biological case | READY_COMPUTATIONAL_CASE | `release_metadata/plant_biology_case_study_v9.md`; `release_metadata/arabidopsis_root_case_figure_v9.md` | Demonstrates adapter resolution and marker-candidate mining on public data. |
| Snow Lotus atlas claim | NOT_READY_BY_DESIGN | `release_metadata/saussurea_h5ad_contract.md`; `docs/saussurea_evidence_plan.md` | Snow Lotus remains a target-species entry point until a reusable single-cell matrix is supplied. |
| Final editor package | READY | `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip` | Zip package is checksum-verified on the server and includes 64 assets. |

## Headline Evidence

| Evidence item | Frozen v9 value |
| --- | --- |
| GitHub branch | `https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728` |
| Final source commit | `eed1005dec5d7d747b66afaa21e01505b096a381` |
| Final package SHA256 | `75ae45ee6e0f9a3b085953ec071d36e4fa05b4020742cb72cc7cd03b1c9c416c` |
| Adapter count | 24 catalog adapters plus runtime all-plant adapter materialization |
| Leave-dataset-out all-cell accuracy | 0.4490, v3 baseline 0.2021 |
| Leave-sample-out all-cell accuracy | 0.6200, v3 baseline 0.4155 |
| Normalized leave-species-out all-cell accuracy | 0.2354, v3 baseline 0.1912 |
| Normalized leave-species-out coverage | 0.5590 |
| Normalized leave-species-out known-label accuracy | 0.4210 |
| Seurat frozen-subset fine accuracy | 0.2207 |
| Arabidopsis root case | 260 marker candidates, 13 cell states, 10 root identity states |

## Venue-Specific Decision Rules

| Venue path | Submit now? | What to emphasize | What must not be overclaimed |
| --- | --- | --- | --- |
| Plant Communications or similar plant resource venue | Yes | Plant utility, public corpus, adapter resolution, root marker case, reproducibility | Do not present Snow Lotus as a completed atlas. |
| Genome Biology | Yes, with major-revision risk | Genomics resource, benchmark transparency, public-data workflow, open implementation | Do not claim scPlantLLM/scPlantAnnotate superiority without official metrics. |
| Communications Biology | Yes, if framed conservatively | Biological utility and technically sound computational method | Do not lead with top-tier AI novelty if biological advance is limited. |
| Nature Methods | Presubmission inquiry only | New reusable method, detailed software usability, validation and benchmark comparison | Do not submit as universal plant annotator without stronger validation. |
| Nature Plants | Later revision | Plant biological insight, independent species/tissue case and validation | Do not rely only on computational Arabidopsis public-data case. |

## Required Upgrades For A Higher-Tier Revision

| Priority | Upgrade | Acceptance evidence |
| --- | --- | --- |
| P1 | Complete one official third-party foundation-model comparator, preferably scPlantLLM. | Frozen metric JSON, exact official checkout/weights, input manifest, command log and reproducible environment file. |
| P1 | Add one independent non-Arabidopsis biological case. | Separate public dataset or new matrix, adapter record, marker table, literature anchor and figure panel. |
| P1 | Improve species-holdout ontology coverage. | Label ontology mapping table and before/after coverage plus all-cell accuracy audit. |
| P2 | Add English manuscript package. | English `.docx` or `.tex`, figure captions, supplement index and data/code availability statement. |
| P2 | Add model usability supplement. | Installation guide, API example, expected input contract, output schema and minimal demo data. |
| P3 | Add Snow Lotus single-cell matrix if available. | `data/saussurea_involucrata.h5ad` with required obs fields, raw/processed deposition and validation markers. |

## Claim Boundary For Editors

Submission-safe claim: Plant-CellFM v9 is a reproducible plant-general single-cell expression foundation-model and adapter framework with a frozen RTX 4090 LoRA checkpoint, strict v9-v3 benchmark, completed Seurat and centroid baselines, species-holdout failure audit, Arabidopsis root computational biology case, GitHub release and live CUDA service evidence.

Unsafe claim: Plant-CellFM v9 universally annotates every plant species at high accuracy, completes a Snow Lotus single-cell atlas, or has already beaten scPlantLLM/scPlantAnnotate in official executable benchmarks.

## Source Scope Pages Checked

- Nature Methods aims and scope: https://www.nature.com/nmeth/submission-guidelines/about/aims
- Genome Biology journal page: https://link.springer.com/journal/13059
- Plant Communications journal page: https://www.sciencedirect.com/journal/plant-communications
- Communications Biology aims and scope: https://www.nature.com/commsbio/aims
- Nature Plants aims and scope: https://www.nature.com/nplants/aims
