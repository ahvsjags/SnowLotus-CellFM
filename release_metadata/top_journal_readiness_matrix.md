# Plant-CellFM v9 Publication Target Readiness Matrix

Generated: 2026-07-30 Asia/Shanghai

This matrix is a current-state submission audit for the frozen v9 package. The current model card uses NVIDIA GeForce RTX 4090, 24 GB VRAM, and the current scientific scope is Plant-CellFM as a plant-general single-cell annotation foundation model with an all-plant adapter layer.

## Readiness Summary

| Target tier | Current status | Submission stance |
| --- | --- | --- |
| Plant-focused methods/resource journal | READY | Strongest current path. Submit as a plant single-cell method/resource with public corpus, adapter framework, benchmark evidence and Arabidopsis root case. |
| Genome Biology / genomics computational-method target | READY_WITH_MAJOR_REVISION_RISK | Plausible if framed around reproducible genomics resource, strict benchmark, open-set calibration, third-party benchmark contracts and multi-species public-data biology. |
| Communications Biology / broad biology target | POSSIBLE_WITH_CONSERVATIVE_FRAMING | Usable if the manuscript emphasizes concrete plant biology utility and avoids universal high-accuracy claims. |
| Nature Methods | PRESUBMISSION_INQUIRY_READY_STRETCH | v14 context-aware zero-shot STC now crosses the 40% strict leave-species threshold, but full submission still needs official third-party numerical closure and stronger independent validation. |
| Nature Plants | STRETCH_AFTER_BIOLOGY_VALIDATION | Needs stronger independent plant biological discovery or validation beyond the current computational case. |

## Current Gate Matrix

| Gate | Status | Evidence | Interpretation |
| --- | --- | --- | --- |
| SSH and server execution | READY | `ssh matpool-px1-jcy`; server package under `/mnt/snowlotus_cellfm` | Remote execution and package synchronization are working. |
| GPU/CUDA service | READY | `release_metadata/api_runtime_smoke_v9.md`; service health reports `device=cuda` | The frozen model is served as a callable CUDA service. |
| Hardware statement | READY | `release_metadata/plant_cellfm_v9_model_card.md` | Current submission uses RTX 4090, 24 GB VRAM. |
| GitHub synchronization | READY | branch `agent/remote-pipeline-20260728`; package status file records source commit and origin head | Repository, package and server evidence are aligned through the generated package manifest. |
| Public plant corpus | READY_FOR_V9 | `release_metadata/v9_data_card.md` | Supports plant-general framing for the frozen v9 candidate. |
| Frozen model asset | READY | GitHub release asset and SHA256 in model card | Checkpoint is externally addressable and checksum-pinned. |
| v9-v3 strict benchmark | READY | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` | Fair same-subset comparison exists. |
| Species-holdout interpretation | READY_WITH_OPEN_SET_BOUNDARY | `release_metadata/species_holdout_failure_audit_v9.md`; `release_metadata/species_ontology_coverage_audit_v9.md`; `release_metadata/species_ontology_label_benchmark_v9.md`; `release_metadata/open_set_calibration_v9.md` | Low leave-species result is decomposed into label coverage, ontology-actionable labels, unknown labels, transfer errors and confidence-aware selective annotation; do not claim universal high accuracy. |
| Species ontology mapping and benchmark | READY_DIAGNOSTIC | `release_metadata/plant_cell_state_ontology_mapping_v9.tsv`; `release_metadata/species_ontology_label_benchmark_v9.md` | 106 observed fine labels are mapped to plant cell-state categories; the frozen embedding ontology-label benchmark is complete and should be reported as a diagnostic, not as a high-accuracy replacement metric. |
| Species-transfer calibration layer | READY_MEASURED_IMPROVEMENT | `release_metadata/cross_species_classifier_benchmark_v10.md`; `release_metadata/algorithm_innovation_v10.md` | STC `knn_cosine_k9` improves frozen leave-species all-cell accuracy from 23.64% to 30.10% and known-label accuracy from 42.28% to 53.84% without using held-out species labels for training. |
| v13 neural zero-shot STC audit | READY_DIAGNOSTIC | `release_metadata/revision_v13_neural_zero_shot_stc.md` | Generic neural calibration reaches 31.84% all-cell and 56.95% known-label accuracy, showing that classifier capacity alone does not solve the bottleneck. |
| v14 context-aware zero-shot STC | READY_REVISION_THRESHOLD_MET | `release_metadata/revision_v14_context_stc_benchmark.md`; `release_metadata/algorithm_innovation_v14.md` | `phylo_organ_gate_v1` reaches 42.36% strict all-cell and 75.77% known-label accuracy at unchanged 55.90% coverage without held-out species labels. |
| v11 few-shot target adapter | READY_REVISION_UPGRADE | `release_metadata/revision_v11_fewshot_adapter_benchmark.md` | Under labeled target-species support calibration, 8 random support cells per held-out species reach 59.21% mean query all-cell accuracy; 16/32/64 support cells reach 67.34%/72.30%/75.89%. |
| v11 runtime-head cross-species benchmark | READY_PROTOCOL_AUDIT | `release_metadata/revision_v11_runtime_head_benchmark.md` | The deployed full-vocabulary runtime head reaches 66.25% all-cell accuracy on the same 3,964 aligned cells and decomposes covered-label versus open-set-label performance. |
| Open-set calibration and selective annotation | READY_90_PLUS_EVIDENCE | `release_metadata/open_set_calibration_v9.md`; `release_metadata/api_confidence_calibration_curve_v9.tsv` | API top-30/top-40 selective accuracy is 96.64%/92.81%; low-confidence cells are routed to review or adapter calibration. |
| Seurat comparator | READY | `release_metadata/external_benchmarks/seurat_v9_subset.json` | Traditional label transfer baseline is complete. |
| scPlantLLM comparator | CONTRACT_READY_METRIC_PENDING | `release_metadata/scplantllm_input_readiness.md`; `release_metadata/third_party_benchmark_contract_v10.md` | Official-source input and runner contract are ready; numerical metric awaits official weight/probe JSON. |
| scPlantAnnotate comparator | CONTRACT_READY_AUTH_LIMITED | `release_metadata/scplantannotate_access_audit.md`; `release_metadata/scplantannotate_benchmark_input_package.md`; `release_metadata/third_party_benchmark_contract_v10.md` | Official route and input package are ready; anonymous scriptable benchmark execution is auth-limited. |
| v11 third-party closure audit | IN_PROGRESS_TRACKED | `release_metadata/revision_v11_third_party_closure.md` | scPlantLLM official LFS weight download and expected SHA256/OID are tracked; scPlantAnnotate still requires authenticated/exported output before numerical reporting. |
| Arabidopsis root biological case | READY_COMPUTATIONAL_CASE | `release_metadata/plant_biology_case_study_v9.md`; `release_metadata/arabidopsis_root_case_figure_v9.md` | Demonstrates adapter resolution and marker-candidate mining on public data. |
| Multi-species scPlantDB biological case | READY_COMPUTATIONAL_CASE | `release_metadata/multispecies_scplantdb_case_v10.md`; `release_metadata/multispecies_scplantdb_marker_candidates_v10.tsv` | Adds a non-Arabidopsis-only public-data case with 31,503 cells, 4 species, 4 tissues and 96 marker-candidate records. |
| Submission scorecard | READY_90_PLUS_EVIDENCE | `release_metadata/submission_scorecard_v14.md` | Strict zero-shot STC performance, cross-species credibility and algorithmic innovation are now scored 90+ evidence-readiness while open-set coverage remains explicit. |
| Snow Lotus atlas claim | NOT_READY_BY_DESIGN | `release_metadata/saussurea_h5ad_contract.md`; `docs/saussurea_evidence_plan.md` | Snow Lotus remains a target-species entry point until a reusable single-cell matrix is supplied. |
| Final editor package | READY | `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip`; generated status JSON | Zip package is checksum-verified on the server; current asset count and SHA are recorded by the package status file. |
| Post-v9 continuation logs | SEPARATED_FROM_EDITOR_PACKAGE | internal refresh logs; `release_metadata/multispecies_scplantdb_case_v10.md` remains as a public-data biology case | Exploratory continuation checkpoints are not used as frozen v9 performance evidence. |

## Headline Evidence

| Evidence item | Frozen v9 value |
| --- | --- |
| GitHub branch | `https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728` |
| Final source commit | recorded in `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.json` |
| Final package SHA256 | recorded in `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.json` and `.zip.sha256` |
| Adapter count | 24 catalog adapters plus runtime all-plant adapter materialization |
| Leave-dataset-out all-cell accuracy | 0.4490, v3 baseline 0.2021 |
| Leave-sample-out all-cell accuracy | 0.6200, v3 baseline 0.4155 |
| Normalized leave-species-out all-cell accuracy | 0.2354, v3 baseline 0.1912 |
| Normalized leave-species-out coverage | 0.5590 |
| Normalized leave-species-out known-label accuracy | 0.4210 |
| STC leave-species all-cell accuracy | 0.3010, centroid baseline 0.2364 |
| STC leave-species known-label accuracy | 0.5384, centroid baseline 0.4228 |
| STC leave-species known-label macro-F1 | 0.2663, centroid baseline 0.1922 |
| v13 neural STC leave-species all-cell accuracy | 0.3184 |
| v14 context-aware STC leave-species all-cell accuracy | 0.4236 |
| v14 context-aware STC leave-species known-label accuracy | 0.7577 |
| v14 context-aware STC leave-species known-label macro-F1 | 0.3045 |
| v11 few-shot target adapter, 8 support cells/species | 0.5921 mean query all-cell accuracy |
| v11 few-shot target adapter, 16 support cells/species | 0.6734 mean query all-cell accuracy |
| v11 full-vocabulary runtime head | 0.6625 all-cell accuracy |
| v11 runtime head covered/open-set accuracy | covered-label 0.6286; open-set-label 0.7054 |
| Ontology-mapped actionable leave-species coverage audit | 0.4526, after excluding 1,384 unknown/unannotated cells |
| Ontology-label benchmark actionable coverage | 0.7444, after excluding 1,640 unknown/unannotated cells |
| Ontology-label benchmark actionable all-cell accuracy | 0.1497 |
| Ontology-label benchmark known-label accuracy | 0.2012 |
| Seurat frozen-subset fine accuracy | 0.2207 |
| API confidence top-30 selective accuracy | 0.9664 |
| API confidence top-40 selective accuracy | 0.9281 |
| Exact max-similarity top-10 rejected-error capture | 0.9263 |
| Arabidopsis root case | 260 marker candidates, 13 cell states, 10 root identity states |
| Multi-species scPlantDB case | 31,503 cells, 4 species, 4 tissues, 96 marker candidates |
| Submission evidence-readiness scorecard | v14 scorecard: all key evidence-readiness dimensions >= 90 |

## Venue-Specific Decision Rules

| Venue path | Submit now? | What to emphasize | What must not be overclaimed |
| --- | --- | --- | --- |
| Plant Communications or similar plant resource venue | Yes | Plant utility, public corpus, adapter resolution, root marker case, reproducibility | Do not present Snow Lotus as a completed atlas. |
| Genome Biology | Yes, with major-revision risk | Genomics resource, benchmark transparency, open-set calibration, public-data workflow, open implementation, multi-species case | Do not claim scPlantLLM/scPlantAnnotate superiority without official metrics. |
| Communications Biology | Yes, if framed conservatively | Biological utility and technically sound computational method | Do not lead with top-tier AI novelty if biological advance is limited. |
| Nature Methods | Presubmission inquiry only | New reusable method, STC species-transfer calibration, open-set/selective annotation layer, detailed software usability, validation and benchmark comparison | Do not submit as universal plant annotator without stronger validation. |
| Nature Plants | Later revision | Plant biological insight, independent species/tissue case and validation | Do not rely only on computational Arabidopsis public-data case. |

## Required Upgrades For A Higher-Tier Revision

| Priority | Upgrade | Acceptance evidence |
| --- | --- | --- |
| P1 | Complete one official third-party foundation-model comparator, preferably scPlantLLM. | Contract is ready; remaining evidence is frozen metric JSON, exact official checkout/weights, command log and reproducible environment file. |
| P1 | Strengthen the independent non-Arabidopsis biology case with literature anchors or replication. | Multi-species scPlantDB case is complete; higher tier needs marker literature anchors, figure panel or independent validation. |
| P1 | Improve model-side cross-species transfer under the explicit STC/ontology/open-set layer. | STC benchmark, coverage audit, 106-label mapping table, frozen ontology-label benchmark JSON, open-set calibration and v11 few-shot target-adapter benchmark are complete; the next evidence should come from official third-party closure, ortholog-aware tokenization or independent species replication. |
| P2 | Add English manuscript package. | English `.docx` or `.tex`, figure captions, supplement index and data/code availability statement. |
| P2 | Add model usability supplement. | Installation guide, API example, expected input contract, output schema and minimal demo data. |
| P3 | Add Snow Lotus single-cell matrix if available. | `data/saussurea_involucrata.h5ad` with required obs fields, raw/processed deposition and validation markers. |

## Claim Boundary For Editors

Submission-safe claim: Plant-CellFM v9 is a reproducible plant-general single-cell expression foundation-model and adapter framework with a frozen RTX 4090 LoRA checkpoint, strict v9-v3 benchmark, completed Seurat and centroid baselines, species-holdout failure audit, ontology coverage audit, ontology-label species benchmark, STC species-transfer calibration benchmark, v11 few-shot target-adapter benchmark, v11 runtime-head benchmark, open-set calibration/selective annotation audit, official-source third-party benchmark contracts and closure audit, Arabidopsis root and multi-species scPlantDB computational biology cases, GitHub release and live CUDA service evidence.

Unsafe claim: Plant-CellFM v9 universally annotates every plant species at high accuracy, completes a Snow Lotus single-cell atlas, or has already beaten scPlantLLM/scPlantAnnotate in official executable benchmarks.

## Source Scope Pages Checked

- Nature Methods aims and scope: https://www.nature.com/nmeth/submission-guidelines/about/aims
- Genome Biology journal page: https://link.springer.com/journal/13059
- Plant Communications journal page: https://www.sciencedirect.com/journal/plant-communications
- Communications Biology aims and scope: https://www.nature.com/commsbio/aims
- Nature Plants aims and scope: https://www.nature.com/nplants/aims
