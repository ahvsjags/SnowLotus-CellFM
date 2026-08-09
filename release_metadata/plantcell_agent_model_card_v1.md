# PlantCell-Agent model card v1

## Scope

PlantCell-Agent is the reproducible execution layer for Plant-CellFM plant
single-cell annotation. It adds input quality control, adapter-aware route
selection, optional labelled-support prototype calibration, uncertainty triage,
predicted-marker evidence and a machine-readable execution trace.

## What is unchanged

- The Plant-CellFM checkpoint and its weights are unchanged.
- Existing strict benchmark denominators and labels are unchanged.
- Direct model outputs are preserved for every Agent run.
- No new species performance claim is inferred from runtime adapter creation.

## New measurable endpoints

1. Accepted-cell coverage at a configured confidence threshold.
2. Manual-review fraction and open-set fraction.
3. Route correctness against the declared species/orthology contract.
4. Direct versus prototype-calibrated output agreement.
5. Trace completeness and runtime reproducibility.

## Recommended interpretation

The Agent is most valuable for repeated annotation operations and open-set
plant datasets: it makes failure modes visible and directs ambiguous cells to a
review table. It should be presented as a reliability and reproducibility
contribution around the foundation model, not as an unvalidated replacement for
held-out species benchmarking.

## Reproducibility

The implementation is in `src/snowcell/agent.py`, `agent_policy.py`,
`agent_tools.py`, `agent_schema.py`, `agent_report.py` and
`specialist_agents.py`. The public command is
`snowcell agent-annotate`. Unit tests cover route precedence, input auditing,
selective review and CLI argument forwarding.

## Release replay

The replay manifest is `release_metadata/plantcell_agent_replay_v1.json`, and
the compact source table is `release_metadata/plantcell_agent_table_s28.tsv`.
The Agent preserved the direct all-cell outputs while exposing a selective
acceptance partition:

| Object | Route | All-cell accuracy | Macro-F1 | Accepted coverage | Accepted-cell accuracy | Review fraction | Repeatability |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Arabidopsis secondary root | registered adapter | 0.8664 | 0.8740 | 0.8417 | 0.9241 | 0.1583 | exact hash match |
| Wheat root | registered adapter | 0.6471 | 0.6935 | 0.4136 | 0.8289 | 0.5864 | exact hash match |
| Sorghum root | orthology STC | 0.8219 | 0.8322 | 0.7758 | 0.9082 | 0.2242 | exact hash match |

The strict held-out raw-input replay remains explicitly marked
`NOT_REPLAYED_INPUT_MISSING` because its declared H5AD object was unavailable in
the execution workspace. A separate complete 3,964-row locked prediction and
embedding replay is released in the selective-evidence package; it is labelled
`locked_bundle_replay` and is not presented as an end-to-end input replay.

## Selective reliability and audit

The strict locked 3,964-cell output replay and three end-to-end H5AD replays are
summarized in `release_metadata/plantcell_agent_evidence_audit_v1.md`. At the
0.70 review threshold, the strict case accepted 56.48% of cells at 85.71%
reference accuracy; the review group had 59.01% error versus 14.29% in the
accepted group. The corresponding accepted accuracies were 92.41% for
Arabidopsis, 82.89% for wheat and 90.82% for Sorghum. Direct and final labels
agreed for every cell in all four cases.

`plantcell_agent_expert_audit_template_v2.tsv` is the blinded worksheet. The
scoring key is retained only at
`outputs/internal/plantcell_agent_expert_audit_key_v2.tsv` and is not shipped in
the public release. The current reference-backed separation uses existing author
labels; it must not be called independent expert validation until a reviewer
completes the blinded worksheet.

## Central model and specialist-agent contract

The shared central model is registered as `plant_cellfm.central_model` and
returns the frozen 256-dimensional cell representation, hierarchical labels,
confidence and marker candidates. The orchestrator selects a capability-scoped
specialist rather than treating an adapter identifier as an agent name. The
release manifest is `release_metadata/plantcell_specialist_agents_v1.json`.

| Role | Responsibility | Required evidence |
| --- | --- | --- |
| Species Adapter Agent | Registered species/study vocabulary and adapter route | Adapter manifest, gene audit, prediction contract |
| Organ Context Agent | Tissue and phylogeny context used as routing evidence | Metadata key and context values |
| Orthology Transfer Agent | Explicit gene projection and aggregation retry | Mapped-gene fraction, count retention, aggregation rule |
| Support Prototype Agent | Few-shot label-space recovery in frozen embedding space | Support count, label count, disjoint-query contract |
| Open-set Agent | Unsupported-label detection and abstention | Label coverage, open-set fraction, confidence summary |
| Evidence Agent | Artifact, confidence, calibration and marker checks | Row count, unique IDs, confidence bounds, embedding shape |
| Review Agent | Manual review for low-confidence, open-set or failed-contract cells | Review threshold, reasons, blinded audit contract |

If a specialist fails its output contract, the orchestrator preserves the direct
prediction file and activates Review Agent for the complete affected table. The
fallback is observable and review-oriented rather than a silent model
substitution.
