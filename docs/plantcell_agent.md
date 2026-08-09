# PlantCell-Agent

PlantCell-Agent is an evidence-aware orchestration layer around the frozen
Plant-CellFM checkpoint. The architecture has a shared central model and
capability-scoped specialist agents. It is designed for plant single-cell
annotation runs in which the input species, gene namespace and unknown-cell
fraction are not known in advance.

## Why it is useful

The base model already produces labels and embeddings. The practical gap is
deciding whether a result should be accepted, recalibrated from a small
labelled support set, or sent to review. PlantCell-Agent turns that decision
into a reproducible state machine with an explicit trace. It improves workflow
reliability and auditability without claiming that a wrapper changes the
locked all-cell benchmark accuracy.

## Execution contract

```text
matrix -> input audit -> Plant-CellFM central model
       -> PlantCell-Agent orchestrator -> specialist agent
       -> evidence verification -> automatic release or Review Agent
       -> trace and reproducible evidence bundle
```

The central model is the shared 256-dimensional expression encoder and direct
prediction service. Specialist agents are executable route contracts, not
renamed adapter files. Their capability declarations include scope, required
inputs, outputs, evidence requirements and fallback chains. The versioned
manifest is `release_metadata/plantcell_specialist_agents_v1.json`.

Routes are deterministic:

| Condition | Route | Model action |
|---|---|---|
| At least 8 labelled support cells | `fewshot_adapter` | Frozen embeddings plus cosine class prototypes |
| Registered species adapter | `registered_adapter` | Existing checkpoint inference |
| Explicit ortholog map | `ortholog_stc` | Existing inference with ortholog projection |
| Otherwise | `universal_open_set` | Existing inference plus open-set review |

The few-shot route is prototype calibration, not gradient-based fine-tuning.
The direct predictions are always retained as `predictions_direct.csv` so that
the calibrated output can be compared cell by cell.

The orchestrator always keeps the Evidence Agent and Review Agent available.
The Evidence Agent validates output rows, cell identifiers, confidence bounds
and embedding shape. A failed specialist contract forces review of the complete
prediction table; it never silently promotes a fallback prediction.

## CLI

```bash
snowcell agent-annotate \
  --checkpoint models/Plant_CellFM_checkpoint.pt \
  --data input.h5ad \
  --output-dir outputs/plantcell_agent_run \
  --species "Arabidopsis thaliana" \
  --support-labels support.tsv \
  --device cuda
```

The support table requires `cell_id` and one of `fine_label`, `label` or
`cell_type`. With no support table, the Agent still performs audit, routing,
open-set review, marker evidence export and reporting.

## Output contract

| Artifact | Purpose |
|---|---|
| `predictions.csv` | Final direct or support-calibrated labels |
| `predictions_direct.csv` | Frozen-checkpoint output before optional calibration |
| `embeddings.npy` | Cell representations from the frozen checkpoint |
| `agent_plan.json` | Planned steps and policy thresholds |
| `route_decision.json` | Adapter, route and metadata consistency decision |
| `specialist_capabilities.json` | Central model and specialist capability manifest |
| `specialist_plan.json` | Primary specialist, auxiliary agents and fallback chain |
| `evidence_verification.json` | Output-contract checks and fallback decision |
| `agent_trace.jsonl` | Timestamped plan/act/verify events |
| `uncertainty_review.tsv` | Low-confidence and open-set cells |
| `marker_evidence.tsv` | Exploratory marker candidates for predicted labels |
| `annotation_metadata.json` | Existing metadata plus Agent provenance |
| `agent_report.md` | Human-readable run summary |

## Reporting rule

Agent quality is reported with accepted coverage, review fraction, confidence,
open-set fraction and, when reference labels are available, accuracy and
macro-F1 computed by the benchmark scripts. Selective coverage is not used as
an all-cell accuracy substitute. Every manuscript result must retain the
direct-vs-Agent distinction and the locked species split.
