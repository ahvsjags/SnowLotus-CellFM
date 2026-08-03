3 August 2026

Editor-in-Chief
Plant Methods

Dear Editor,

We submit the Methodology manuscript entitled **"Plant-CellFM: coverage-aware cross-species annotation and sparse adaptation across plant species"** for consideration in Plant Methods.

Plant single-cell annotation is limited by cross-species gene mapping, incomplete reference label spaces and the amount of target annotation available. Plant-CellFM addresses these problems with explicit orthology projection, a shared plant expression encoder, phylogeny-organ calibration and rank-8 species adapters. We evaluated the method through nested frozen-encoder leave-species decoder transfer, repeated sparse-support experiments, blind Arabidopsis root analysis, a matched allopolyploid wheat comparison and a library-held-out Sorghum study.

The study provides a practical method for deciding when a shared representation can transfer a plant cell identity and when target-specific adaptation is needed. Nested decoder evaluation retains every held-out cell, including labels absent from the source vocabulary, and excludes outer target labels from downstream fitting and selection. Source-label coverage was 55.90%, and accuracy among covered cells was 71.48%, revealing the contribution of unsupported target states. A separate source-context analysis reached 42.36% all-cell accuracy without target labels for routing, while increasing support from 8 to 64 labelled cells per species raised mean query accuracy from 59.21% to 75.89%. Plant-CellFM LoRA achieved 62.25% accuracy and 0.6660 macro-F1 on 1,433 held-out wheat cells and 76.02% accuracy across 27 states in a held-out Sorghum library.

The manuscript is not under consideration elsewhere and has not been published previously. All authors will read and approve the final uploaded version. The authors declare no competing interests. The study uses public plant transcriptomic data and does not involve human participants or animals. Software, configurations, model cards, cell-level results and figure source data are available through the public project repository. A frozen article tag is reported in the data availability statement; the persistent archive DOI will be added when the public archive record is issued.

Potential reviewers will be supplied in the submission system after conflict checks.

Thank you for considering our work.

Sincerely,

Submitting author
Corresponding author details to be supplied in the journal submission system
