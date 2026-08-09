# PlantCell-Agent benchmark contract v1

The Agent replay must use the same frozen checkpoint and cell identifiers as the
existing locked analyses. Four replay groups are defined in
`release_metadata/plantcell_agent_replay_manifest_v1.json`:

| Group | Existing evidence path | Required comparison |
|---|---|---|
| Strict held-out species | `data/external_validation/v9_benchmark_subset_256_shared_genes.h5ad` | Direct vs Agent selective coverage, open-set review and trace completeness |
| Arabidopsis root | `outputs/external_validation/gse270140/GSM8335426_JWE03_author_annotated_secondary_root.h5ad` | Root identity route, marker evidence and literature-aligned labels |
| Wheat root | `outputs/external_validation/gse270342/GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad` | Direct vs Agent route and external matched-test metrics |
| Sorghum root | `outputs/external_validation/gse297576_bicolor_root/GSE297576_bicolor_root_author_atlas.h5ad` | Sealed-library route, review fraction and state recovery |

The replay report must record whether the original matrix and checkpoint are
available locally. Missing execution inputs are marked `NOT_REPLAYED`; no metric
is copied from a previous report and relabelled as an Agent result. Once an
input is available, each run must archive `agent_result.json`,
`predictions_direct.csv`, `predictions.csv`, `uncertainty_review.tsv` and
`agent_trace.jsonl`.

The current execution result is released in
`release_metadata/plantcell_agent_replay_v1.md`; the compact source table is
`release_metadata/plantcell_agent_table_s28.tsv`.

Selective-risk and calibration evidence is released in
`release_metadata/plantcell_agent_selective_metrics_v1.tsv` and
`release_metadata/plantcell_agent_calibration_curve_v1.tsv`. The
reference-backed accepted-versus-review audit is in
`release_metadata/plantcell_agent_reference_audit_v1.tsv`. The public expert
worksheet hides the acceptance group and reference label; its key is retained
separately for scoring after independent review.

The central-model and specialist-agent capability contract is released in
`release_metadata/plantcell_specialist_agents_v1.json`. Each run must copy the
manifest to `specialist_capabilities.json`, record its selected primary and
fallback agents in `specialist_plan.json`, and write
`evidence_verification.json` before automatic release. A failed specialist
contract forces the Review Agent path and preserves the direct prediction file.
