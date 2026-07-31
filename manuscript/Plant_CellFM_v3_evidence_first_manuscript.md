# Plant-CellFM: protocol-aware cross-species annotation and target-species adaptation for plant single-cell transcriptomics

## Abstract

Plant single-cell atlases are expanding quickly, but cell annotations remain difficult to transfer across species, organs and experimental collections. The difficulty is not only a representation-learning problem: an annotation label may be absent from the source label space, target species may have highly uneven public data support, and a deployment annotation head is often evaluated under a different information boundary from a strict zero-shot transfer method. We present Plant-CellFM, a reproducible plant single-cell expression framework that makes these boundaries explicit. The frozen current corpus contains 272,732 cells, 209,405 genes, five species, nine datasets, 31 samples and 34 annotated cell labels. Plant-CellFM combines a 256-dimensional four-layer expression encoder, gene-identifier/ortholog transfer contract, adapter-resolution interface, hierarchical annotation routes and a runtime annotation head. On 3,964 cells from eight held-out species, a nested source-species selection protocol achieved 39.96% exact all-cell accuracy, 71.48% accuracy on labels represented in the source training space, 0.2817 known-label macro-F1 and 55.90% source-label coverage. This strict result is deliberately separated from an exploratory global-context sensitivity analysis, from few-shot adaptation, and from full-vocabulary runtime evaluation. With 8, 16, 32 and 64 randomly labelled support cells per target species, mean query all-cell accuracy reached 59.21%, 67.34%, 72.30% and 75.89%, respectively, across ten independent support draws with support/query nonoverlap. A root-cell case study supplies an identity taxonomy and marker-candidate resource, while a runtime confidence analysis quantifies the operational trade-off between accepted-cell fraction, selective accuracy and rejected-error capture. Plant-CellFM therefore provides an evidence-traceable route for plant atlas annotation and target-species adaptation, with every main quantitative panel linked to frozen source data and an explicit evaluation protocol.

## Introduction

Single-cell and single-nucleus RNA sequencing are changing the resolution at which plant development, stress responses and specialised cell states can be studied. The growing volume of plant atlases makes annotation transfer a central practical problem: a reference labelled in one species or organ is often used to label cells in a taxonomically distant species, despite shifts in gene identifiers, orthology, tissue composition and the available cell-state vocabulary. Resources such as scPlantDB provide a valuable basis for systematic cross-species analysis by collating plant cell atlases and marker information [1]. General-purpose plant analysis frameworks have also made it easier to inspect and process individual atlases [2]. However, a reusable annotation framework must do more than expose a reference: it must declare whether an evaluation permits target labels, whether the target label exists in the training vocabulary, and whether an inference-time classifier has already learned that label.

Recent single-cell foundation models have shown that large-scale expression representations can transfer across tasks. scGPT demonstrated generative pretraining for single-cell multi-omics [3], scFoundation scaled expression modelling to large human single-cell corpora [4], and SATURN introduced cross-species integration through protein-informed representations [5]. More recently, UCE and Nicheformer have expanded the conceptual reach of cellular foundation models across genomes, tissues and spatial contexts [6,7]. These advances establish an important precedent, but plant transfer has a distinct combination of biological and data-engineering constraints. Gene symbols and reference genomes vary substantially between species, labelled cell states are sparsely shared, and public plant datasets often have strong species and tissue imbalance. A single headline accuracy can therefore be misleading if it silently removes novel target labels or mixes strict transfer with a deployment classifier.

Plant-CellFM was designed around this reporting problem. The framework contains an expression encoder, a gene-identifier/ortholog transfer contract, adapter-resolution interface, hierarchical annotation paths, marker-candidate ranking and a runtime annotation head. Its contribution is not a claim that one frozen model already annotates every plant species with uniformly high accuracy. Instead, Plant-CellFM establishes a reproducible experimental and operational system in which four different questions are measured separately: (i) strict leave-species transfer without target labels; (ii) sensitivity of a globally selected context gate; (iii) few-shot adaptation with labelled support cells that are excluded from query scoring; and (iv) runtime annotation with a trained full-vocabulary head.

Here we first construct a traceable frozen plant corpus and evaluate the shared embedding space. We then apply nested source-species selection to strict leave-species transfer and expose the exact-label open-set denominator rather than removing unsupported labels. We benchmark the frozen Plant-CellFM v9 checkpoint against the frozen v3 checkpoint only on matched grouped splits, retain heterogeneous external tools as an evidence-closure audit until official predictions are available, quantify few-shot target-species adaptation, and present an Arabidopsis root marker-candidate resource. Finally, we show how the runtime head can be controlled by confidence thresholds while remaining explicitly separate from the strict zero-shot claim.

## Results

### A traceable corpus and a common plant expression contract

The current frozen H5AD profile comprises 272,732 measured cells and 209,405 genes across five species, nine dataset accessions, 31 samples, six tissues and 34 cell labels (Fig. 1a,b; Extended Data Fig. 1; Table S1). The largest contribution is *Arabidopsis thaliana*, followed by *Fragaria vesca*, *Catharanthus roseus*, *Brassica rapa* and *Gossypium bickii*. The distribution is intentionally retained rather than rebalanced for presentation: dataset scale and label frequency are part of the annotation problem, and the long-tailed cell-state abundance is directly reported in Extended Data Fig. 1c.

Plant-CellFM uses a 256-dimensional, four-layer expression encoder with LoRA adaptation. Inputs are resolved through exact gene identifiers where available; new species can enter through an ortholog map that is recorded with the inference or training job. This is a gene-transfer contract, not an assertion that every possible ortholog relation is known. The model emits a shared cell embedding, annotation outputs and ranked marker candidates. The implementation also exposes a runtime adapter-resolution path, permitting a named adapter or an unregistered-plant fallback to be materialised for a new input. The capability is operationally useful, but the evidence for a new species begins only after its input contract and held-out evaluation have been established.

The figure package makes the distinction between corpus and evaluation set visible. The current profiled corpus contains five species, whereas the strict evaluation uses 3,964 aligned cells from eight held-out species. The evaluation atlas contains callus, leaf, root and shoot-apex contexts in the shared embedding space (Fig. 1c). Plant-CellFM therefore separates the question of what has been profiled in the frozen training corpus from the question of what has been measured in the cross-species benchmark.

### Nested selection produces a conservative strict leave-species result

We evaluated strict cross-species transfer using a leave-species-out protocol in which the held-out target-species labels are not used for fitting, calibration or selection. For every outer held-out species, context-gate candidates are ranked only on inner source-species holdouts. The selected configuration is then applied to the outer test species. The candidate audit, including all inner candidate ranks and red-outlined selections, is shown in Extended Data Fig. 2 and Table S4. This procedure prevents the target fold from choosing its own preferred transfer rule.

The primary strict result is the nested v17 metadata gate. Across all 3,964 held-out cells, exact all-cell accuracy was 39.96% (Fig. 2b; Table S3). The source label space covered 55.90% of test cells; among those covered cells, accuracy was 71.48% and macro-F1 was 0.2817. The distinction between all-cell and known-label performance is central. The all-cell denominator includes target labels absent from the source training label space, whereas known-label accuracy conditions on labels that exist in the source vocabulary. We retain both quantities because reporting only the latter would hide the open-set difficulty.

Species-level outcomes were heterogeneous (Fig. 2c,e). The cell bootstrap distribution quantifies uncertainty conditional on the fixed 3,964-cell test set (Fig. 2d), while species-level results and label-space coverage are given separately. Extended Data Fig. 3 converts this accounting into a direct composition view: every strict test cell is counted as exactly correct, incorrect within the seen label space, or carrying a held-out label. This visualization also shows that label-space coverage, organ composition and species identity jointly structure the difficulty of the task. The strict protocol should consequently be interpreted as a transparent transfer benchmark rather than a universal high-accuracy annotation rate.

An earlier globally selected context gate reached 42.36% all-cell accuracy, 75.77% known-label accuracy and 0.3045 macro-F1 under the same broad frozen evidence set. Because its global configuration choice uses information aggregated across outer folds, we preserve it only as an exploratory sensitivity analysis (Fig. 2b; Table S2). It is not the primary strict headline. This separation is a deliberate design decision: a smaller, correctly nested estimate is more informative than a larger value whose selection boundary is ambiguous.

### Matched checkpoint comparisons show improvements without over-ranking external tools

We performed numerical comparisons only where the frozen v3 and Plant-CellFM v9 checkpoints share the same data contract and grouped split. On leave-dataset-out evaluation, all-cell accuracy increased from 20.21% for frozen v3 to 44.90% for Plant-CellFM v9. On leave-sample-out evaluation, accuracy increased from 41.55% to 62.00%; on a normalized leave-species-out split, it increased from 19.12% to 23.54% (Fig. 3a; source data accompanying Fig. 3). Known-label macro-F1 improved in parallel (Fig. 3b). These are matched checkpoint comparisons and are shown as such.

External tools require a different standard. A cosine-centroid baseline and Seurat label transfer have reproducible results under their own recorded protocols. The scPlantLLM input contract is prepared but an official frozen-checkpoint prediction has not yet been obtained, and scPlantAnnotate requires authenticated or exported official output. Figure 3d and Table S8 therefore display these methods as an evidence-closure audit rather than placing them in a visually persuasive but protocol-incompatible performance ranking. This policy makes the current comparative statement narrower but reproducible: Plant-CellFM v9 improves over the frozen v3 checkpoint under matched grouped splits; external numerical superiority is not claimed until the official inference outputs can be evaluated on an identical frozen input and split.

### Small target-species support produces a monotonic adaptation response

Strict zero-shot transfer is not the only practical use of a plant expression model. In many atlas projects, a modest set of target-species cells can be labelled before the remaining cells are annotated. We therefore evaluated target-species adaptation with randomly sampled support cells and a disjoint query set. No support cell is included in query scoring (Fig. 4a). For each support budget, ten independent support draws were evaluated.

With eight labelled support cells per target species, mean query all-cell accuracy was 59.21%. The mean increased to 67.34%, 72.30% and 75.89% for 16, 32 and 64 support cells per target species, respectively (Fig. 4b; Table S6). Query macro-F1 increased with the support budget as well (Fig. 4c). The benefit was not uniform across species, which is why representative per-species outcomes and support-label diversity are shown in Fig. 4d and Extended Data Fig. 4. The adaptation result is not substituted for the strict zero-shot benchmark: it answers a different, operationally useful question about how much target annotation is needed to calibrate a new species.

### An Arabidopsis root resource connects annotation states to marker candidates

To demonstrate the biological output layer, we analysed an *Arabidopsis thaliana* root case. Ten root-related identity labels were organised across root-cap, epidermal, ground-tissue and vascular compartments: columella root cap, lateral root cap, root cap, root hair, non-hair, root cortex, root endodermis, root stele, phloem and xylem (Fig. 5a). For each identity, the figure shows five leading marker candidates and their log2 fold-change values (Fig. 5b), complemented by an effect-size/detection-separation landscape (Fig. 5c) and a summary marker-strength panel (Fig. 5d).

The candidate table contains the underlying ranked genes, effect sizes, detection fractions and cell counts (Table S9). The root identity taxonomy is literature-aligned, and the output is designed to support experimental follow-up or atlas curation. The present analysis treats these rows as computational marker candidates rather than claiming wet-lab validation. This distinction allows the biological case to be useful now while keeping the status of future validation unambiguous.

### Runtime confidence controls expose the deployment operating curve

Annotation systems are often deployed with a trained full-vocabulary head rather than under the strict source-label boundary. We analysed this operating mode separately on the aligned 3,964-cell evaluation set (Fig. 6). At full acceptance, the runtime head reached 66.25% all-cell accuracy. When only the top 30% most confident calls were accepted, selective accuracy was 96.64% and the rejected set captured 97.01% of runtime errors. As the accepted-cell fraction increased, selective accuracy decreased smoothly while rejected-error capture decreased in the opposite direction (Fig. 6b; source data accompanying Fig. 6).

The runtime result is accompanied by species-specific accuracy and explicit label-space composition (Fig. 6c,d). This exposes the operational envelope rather than presenting the mean as a guarantee for every species. Most importantly, the runtime head is labelled as a full-vocabulary deployment analysis throughout the figure and manuscript. It is not combined with the v17 strict result, because the two workflows have different access to annotation vocabulary and answer different biological and engineering questions.

## Methods

### Frozen corpus profile and provenance

We profiled `data/plant_foundation_corpus_current_scplantdb_v2.h5ad` using `scripts/profile_h5ad_corpus.py`, which reads the H5AD structure directly and exports species-by-dataset, species-by-tissue and species-by-cell-type source tables. The profile was frozen for the v3 figure package and records 272,732 cells, 209,405 genes, five species, nine datasets, 31 samples and 34 labels. All corpus-composition panels are generated from these TSVs rather than from hand-entered summary values.

### Model and input contract

Plant-CellFM uses a four-layer expression encoder whose exported cell representation has 256 dimensions. LoRA adapters are used for adaptation paths. The input contract accepts a cells-by-genes expression matrix, resolves known gene identifiers to the checkpoint vocabulary and supports ortholog-map based preprocessing for new species. The runtime service can emit embeddings, annotations and metadata. The model card in `release_metadata/plant_cellfm_model_card_v3.json` distinguishes implemented capabilities from validated species-level performance.

### Strict leave-species evaluation

The strict benchmark aligns observation metadata with frozen embeddings and evaluates eight outer held-out species, for a total of 3,964 cells. Each outer species is scored using a configuration selected solely through inner source-species leave-species evaluation. Exact all-cell accuracy is calculated on every held-out cell. Source-label coverage is the fraction of held-out cells whose truth label occurs in the source training label space. Known-label accuracy and macro-F1 are calculated only on that covered subset. The v17 script writes the selected configurations, inner candidate rankings, per-species outer records and cell-level predictions to `release_metadata/` and `figure_data/v2_embeddings/`.

The v14 global context-gate result is retained as a sensitivity analysis. Its configuration is selected globally across outer folds and is consequently not used as the primary strict result. The distinction is declared in the model card, Table S2, Fig. 2 and Extended Data Fig. 2.

### Matched comparisons and external evidence audit

Frozen v3 and v9 comparisons are extracted from `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json`. Values are compared only when the protocol, data contract and grouped split are shared. Centroid and Seurat results are recorded with their own input/split information. scPlantLLM and scPlantAnnotate are listed as pending only where their official prediction output is not reproducibly available. No external method is assigned a numerical rank without an official output on a frozen compatible input.

### Few-shot adaptation and runtime confidence analysis

Few-shot target adaptation samples a specified number of labelled support cells per held-out species, excludes support cells from query scoring, and repeats the sampling ten times. Aggregate means and standard deviations are stored in `release_metadata/revision_v11_fewshot_adapter_benchmark.json`. The runtime-head confidence curve is derived from the trained full-vocabulary annotation head and reports accepted-cell fraction, selective accuracy and rejected-error capture. Runtime results are operational metrics and are always reported separately from strict zero-shot transfer.

### Root marker-candidate analysis

The root case uses the v9 root marker-candidate table and a literature-aligned identity taxonomy. Marker candidates are ranked per identity and summarised by log2 fold change, detection separation, score and number of in-state cells. Source data for the root figure and the full candidate table are exported with the v3 package.

### Statistics and visualisation

Figure 2 uses a nonparametric cell bootstrap conditional on the fixed strict test set. Few-shot values are mean plus standard deviation across ten independently sampled support draws. Point area is used only where explicitly described as proportional to evaluated cell count. Main and Extended Data figures are generated in non-interactive Matplotlib `Agg` mode as SVG, PDF, PNG and 600-dpi TIFF, and every numerical panel has a tab-separated source-data export.

## Data and Code Availability

The frozen corpus profile, v17 strict-evaluation record, source-data tables, v3 figure renderers and v3 supplementary tables are included in this repository. The code repository is available at [https://github.com/ahvsjags/SnowLotus-CellFM](https://github.com/ahvsjags/SnowLotus-CellFM). The reproducibility commands are:

```bash
python scripts/render_v3_data_first_main_figures.py
python scripts/render_v3_extended_data_suite.py
python scripts/write_submission_v3_supplementary_tables.py
```

The final archival commit identifier should be inserted here after the v3 source-data package has been pushed. The current source-data directories are `figures/plant_cellfm_submission_v3/source_data`, `figures/plant_cellfm_submission_v3/extended_data/source_data` and `supplementary_tables/submission_v3`.

## References

1. Chen, H. *et al.* scPlantDB: a comprehensive database for exploring cell types and markers of plant cell atlases. *Nucleic Acids Research* **52**, D1629-D1638 (2024). https://doi.org/10.1093/nar/gkad706
2. Zhai, J. *et al.* scPlant: a versatile framework for single-cell transcriptomic data analysis in plants. *Plant Communications* (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10504592/
3. Cui, H. *et al.* scGPT: toward building a foundation model for single-cell multi-omics using generative AI. *Nature Methods* **21**, 1470-1480 (2024). https://doi.org/10.1038/s41592-024-02201-0
4. Hao, M. *et al.* Large-scale foundation model on single-cell transcriptomics. *Nature Methods* **21**, 1481-1491 (2024). https://doi.org/10.1038/s41592-024-02305-7
5. Rosen, Y. *et al.* Toward universal cell embeddings: integrating single-cell RNA-seq datasets across species with SATURN. *Nature Methods* **21**, 1492-1500 (2024). https://doi.org/10.1038/s41592-024-02191-z
6. Theodoris, C. V. *et al.* Universal cell embedding provides a foundation model for cell biology. *Nature* (2026). https://doi.org/10.1038/s41586-026-10689-z
7. Lotfollahi, M. *et al.* Nicheformer: a foundation model for single-cell and spatial omics. *Nature Methods* **22**, 2525-2538 (2025). https://doi.org/10.1038/s41592-025-02814-z
