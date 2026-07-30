# Plant-CellFM Frozen v9 Publication Readiness Audit

This file records the evidence behind the frozen v9 candidate. It is an engineering and submission audit, not a claim that peer review has been completed.

## Implemented

1. **General-plant model scope.** The service and adapter registry treat Snow Lotus as one species within a plant-general model. Unknown named species receive a runtime adapter record, while exact gene IDs and optional ortholog maps are resolved through the same inference contract.
2. **Public corpus construction.** The v9 corpus contains 56 validated manifest rows from 29 datasets and 21 species, with 13.78 million cells in the built corpus. Manifest paths, duplicate handling, source metadata and checksums are retained.
3. **GPU training.** The v9 LoRA candidate was trained on the RTX 4090 with a resolved YAML configuration, epoch checkpoints, progress logs, preprocessing statistics and a completion marker.
4. **Fair baseline comparison.** v9 and v3 were evaluated on the same v9 shared-gene benchmark under leave-dataset-out, leave-sample-out and leave-species-out protocols.
5. **Inference service.** The service exposes health, metadata, capability, adapter and annotation routes. A live health check reports `model_scope=plant_general`, 24 catalog adapters, dynamic all-plant resolution and `device=cuda`.
6. **Reproducible release.** The v9 package contains the checkpoint, configuration, manifest, benchmark subset, benchmark JSON, comparison report, training history, scripts and SHA256 manifest. The server-side checksum verification passed.
7. **Repository hygiene.** The public repository was scanned for tracked private keys, GitHub tokens, raw server credentials and key-like files before changing visibility to public.

## Frozen Results

| Protocol | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out | 0.3635 | 0.6882 | 0.5282 | 0.2897 | 0.1690 |

The internal held-out test reports fine accuracy 0.8113, coarse accuracy 0.8298 and fine macro-F1 0.3833. The known-label columns evaluate only cells whose reference labels occur in the training fold. The all-cell column counts an unseen reference label as an error, so the leave-species-out result is the stricter open-set estimate. The cross-group results above are the primary generalization evidence, and the 36.35% all-cell species-holdout accuracy rather than 52.82% conditional accuracy should be used as the headline number.

## Publication Positioning

The strongest current manuscript framing is a computational method/resource paper: a plant-specific foundation model, a species-adapter transfer layer, a public corpus construction protocol and a reproducible cross-species benchmark. The paper should make the leave-species-out result and the reproducibility package central, rather than presenting the internal held-out accuracy as universal plant accuracy.

## Journal Fit

- **First-choice stretch target: Nature Methods.** The work is within the journal's computational and single-cell methods scope, but the current evidence still needs a stronger comparison against established annotation and foundation-model tools plus a convincing biological application.
- **Strong methods target: Genome Biology.** The plant single-cell corpus, cross-species evaluation and open implementation fit the journal's genomics and computational-method readership. A complete external baseline panel and clearer biological discovery would materially strengthen the submission.
- **Plant-focused target: Plant Communications.** The model and public plant resource are directly within the journal's plant genomics, cellular biology and technical-resource scope. This is the best fit when the manuscript emphasizes plant utility and an accessible resource rather than broad AI novelty.
- **Broad biology target: Communications Biology.** The current work can fit as an innovative computational method if the paper demonstrates a concrete plant-biology use case and the conclusions are supported by strong evidence.
- **Stretch AI target: Nature Machine Intelligence or Nature Computational Science.** These venues require a larger methodological advance and broader significance than the current frozen evidence demonstrates; they are appropriate only after a substantially stronger algorithmic contribution and independent validation.

## Final Submission Package

The reviewer-facing package should contain the frozen v9 checkpoint, model card, data card, manifest and provenance audit, benchmark subset and JSON results, training configuration and history, service instructions, source repository and a manuscript whose numerical tables match the frozen JSON files. Do not describe the model as trained on all plant species or claim universal accuracy.
