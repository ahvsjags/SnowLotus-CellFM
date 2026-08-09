# PlantCell-Agent addendum for the Plant Methods submission

## Methods: evidence-aware annotation agent

We implemented PlantCell-Agent as a deterministic plan-act-verify layer around
the frozen Plant-CellFM checkpoint. Each run first audits matrix dimensions,
gene and cell identifier uniqueness, detected genes per cell, library size,
species metadata and available tissue fields. The agent then resolves a
registered species adapter or materializes a runtime general-plant adapter and
selects one of four declared routes: registered-adapter inference,
ortholog-projected transfer, universal open-set inference or support-prototype
calibration.

The support route requires at least eight labelled cells. It does not update
checkpoint weights. Instead, it computes normalized class centroids in the
frozen embedding space and assigns each query to the highest cosine-similarity
centroid. The original checkpoint output is retained beside the calibrated
output. A confidence threshold then separates accepted cells from the review
queue; labels recognized as open-set are always retained for review. Finally,
the agent exports predicted-label marker candidates and a JSONL trace of every
plan, action and verification event.

The upgrade makes the route choices executable specialist agents rather than
adapter aliases. The central model is registered as
`plant_cellfm.central_model`; route specialists include registered species
adapters, organ-context routing, orthology transfer, support-prototype
calibration and open-set detection. Every specialist has an `agent_id`, role,
scope, required inputs, outputs, evidence requirements and a fallback chain.
The evidence-verification agent checks prediction columns, cell-row counts,
unique identifiers, confidence bounds and embedding shape. A failed contract
does not silently substitute another prediction: the Review Agent is activated
and the complete prediction table is sent to review.

For the evidence audit, the accept-all direct output is retained as the baseline
and the Agent is evaluated at thresholds 0.50-0.90. Coverage--accuracy,
selective risk, ten-bin calibration and error capture are calculated on the full
matched denominator. At the prespecified 0.70 threshold, a release gate checks
that the review branch has higher reference error than the automatically accepted
branch in every audited case.

## Results: operational reliability

The Agent adds a reproducible operational layer to the Plant-CellFM workflow.
For a direct run, the output includes the unchanged model predictions together
with an explicit review queue. When labelled support is available, the
prototype route is invoked automatically and its effect can be inspected by
comparing `predictions_direct.csv` with `predictions.csv`. Thus the workflow
separates model discrimination from downstream acceptance policy and makes
open-set cells visible instead of forcing an unsupported label.

## Supplementary material

Supplementary Fig. S12 summarizes the central model, orchestrator, specialist
agent ecosystem, evidence verification and review loop. Supplementary Fig. S13 reports coverage--accuracy,
selective risk, calibration and reference-backed accepted-versus-review audits
for the strict 3,964-cell locked bundle and three end-to-end replays.
Supplementary Table S28 defines the route triggers, replay outcomes and output
artifacts; Table S29 defines the evidence tables and blinded expert worksheet.
The strict raw H5AD is unavailable, so the 3,964-cell result is labelled a
locked-output replay. The public worksheet hides the acceptance group and
reference label; an independent expert must complete it before an independent
expert-validation claim is made.
