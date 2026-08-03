# Claim-to-Figure Map

| Manuscript claim | Controlling value | Figure or table | Evidence boundary |
| --- | --- | --- | --- |
| Training corpus | 272,732 cells; 209,405 genes; 5 species; 9 datasets; 31 samples | Fig. 1; Table S1 | Checkpoint training data |
| Frozen-encoder leave-species decoder transfer | 39.96% all-cell; 55.90% coverage; 71.48% covered accuracy; 0.2817 covered macro-F1 | Fig. 2; Tables S3-S7 | Primary source-only downstream decoder result; encoder fixed |
| Context-aware transfer | 42.36% all-cell; 75.77% covered accuracy; 0.3045 covered macro-F1 | Fig. 3 | Global sensitivity, not nested primary |
| Sparse target adaptation | 59.21%, 67.34%, 72.30%, 75.89% at 8, 16, 32, 64 support cells/species | Fig. 4; Tables S8-S10 | Target-labelled support, disjoint query |
| Blind root coherence | 6,566 cells; 5/6 fixed markers top in expected group | Fig. 5; Tables S16-S17 | No expert-label accuracy claim |
| Secondary-root adaptation | 83.97% accuracy; 84.47% macro-F1 on 2,352 cells | Fig. 5; Tables S18-S19 | One-sample supervised adaptation |
| Wheat Plant-CellFM adapter | 62.25% accuracy; 0.6660 macro-F1 on 1,433 cells | Fig. 6; Table S20 | Same-study supervised adaptation |
| Wheat scPlantLLM full reference | 45.01% accuracy; 0.4588 macro-F1 on identical cells | Fig. 6; Table S24 | Not compute matched or universal ranking |
| Sorghum fine-state adaptation | 76.02% accuracy; 0.7535 macro-F1 on 4,150 cells | Fig. 7; Table S26 | Sealed-library supervised adaptation |
| Sorghum broad recovery | 14.79% to 84.98% accuracy on 3,549 matched cells | Fig. 7; Table S27 | Same-cell frozen-to-adapted comparison |
| Runtime selective annotation | 66.25% all-cell; 96.64% top-30%; 92.81% top-40% | Supplementary Fig. S2 | Deployment route, not leave-species decoder transfer |
