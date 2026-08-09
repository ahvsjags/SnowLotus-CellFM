# Supporting Information for Plant-CellFM

## Plant-CellFM: coverage-aware cross-species annotation and sparse adaptation across plant species

**Authors:** Author details to be supplied by the submitting author

**Corresponding author:** To be supplied by the submitting author

## Contents

1. Supplementary Methods
2. Supplementary Results
3. Supplementary Figure Legends S1-S13
4. Supplementary Table Descriptions S1-S29
5. Data and code availability

## Supplementary Methods

### S1. Data acquisition and provenance

For each dataset, we recorded the source accession, downloaded file, checksum, matrix orientation, cell-identifier field, gene-identifier field and relevant author annotation columns. Public matrices were converted to H5AD without changing cell order. When the processed source was an R or Seurat object, RNA counts, cell metadata and author embeddings were exported separately and matched by barcode before assembly.

The versioned training H5AD contains 272,732 cells, 209,405 genes, five species, nine datasets and 31 samples. A larger development collection and the later multi-species scPlantDB marker analysis were not used to train the checkpoint evaluated in this article.

Species names were canonicalized before group splitting. Punctuation, underscores and repeated whitespace were normalized, and recognized aliases were mapped to one binomial name. This procedure reduced nine raw strings to eight held-out species; Supplementary Table S1 retains both original and canonical names.

### S2. Expression preprocessing and gene projection

For cell \(i\) and gene \(g\), \(c_{ig}\) denotes the raw count, \(L_i=\sum_hc_{ih}\) the library size and \(\widetilde{x}_{ig}\) the normalized value. Cells and genes failing the declared dataset-specific detection filters were removed before normalization. The transformation was

<!-- equation:supp-1 -->
$$\widetilde{x}_{ig}=\log\!\left(1+\frac{10^{4}c_{ig}}{\sum_hc_{ih}}\right). \tag{S1}$$

The expressed-gene token set was selected deterministically by value rank:

<!-- equation:supp-2 -->
$$G_i=\mathrm{argsort}_{g:c_{ig}>0}\!\left(\widetilde{x}_{ig};\ \mathrm{descending}\right)_{1:K}. \tag{S2}$$

The v9 strict-transfer checkpoint used \(K=512\); the root-adapter experiments used \(K=1{,}024\). A classification token was prepended and all remaining positions were filled with the padding identifier, giving sequence length \(K+1\). Padding positions were explicitly masked in attention and at every residual output.

Exact identifiers were used when they occurred in the checkpoint vocabulary. Otherwise, an orthology table specified a target set \(M(g)\) for source gene \(g\). The sparse projection matrix was

<!-- equation:supp-3 -->
$$P_{gt}=\begin{cases}\mathbf{1}\{t=\mathrm{first}\,M(g)\},&\text{first-target rule},\\|M(g)|^{-1}\mathbf{1}\{t\in M(g)\},&\text{mean rule},\end{cases}\qquad C^{\mathrm{proj}}=CP. \tag{S3}$$

The mean rule conserves each mapped source gene's total count across its targets. Multiple source genes resolving to the same target were summed by sparse matrix multiplication. Unmapped genes were dropped. With source-gene set \(G\), feature coverage and count retention were

<!-- equation:supp-4 -->
$$C_{\mathrm{feat}}=|G|^{-1}\sum_{g\in G}\mathbf{1}\{|M(g)|>0\},\qquad C_{\mathrm{count}}=\frac{\sum_{i,g}c_{ig}\mathbf{1}\{|M(g)|>0\}}{\sum_{i,g}c_{ig}}. \tag{S4}$$

For GSE270342, the author PLAZA mapping is many-to-many. The primary first-target rule selected a deterministic target for every source gene, and a mean projection provided a count-conserving sensitivity result. For GSE297576, the author ten-species orthogroup table was filtered to Sorghum and Arabidopsis genes. Of 25,464 source genes, 15,940 resolved to orthogroup targets and 10,325 checkpoint-compatible targets remained after preprocessing.

### S3. Plant-CellFM implementation

Plant-CellFM uses a transformer encoder without positional encoding because expressed genes are treated as a set rather than a biological sequence. Let \(B\) be the number of expression bins, \(s_i\) and \(t_i\) the source-species and tissue indices, \(\gamma\) a learned scalar and \(\phi\) a two-layer GELU projection. Token initialization was

<!-- equation:supp-5 -->
$$v_{ig}=\mathrm{clip}\!\left(\frac{\widetilde{x}_{ig}}{\log(10001)},0,1\right),\quad b_{ig}=\lfloor(B-1)v_{ig}\rfloor,\quad z_{ig}^{(0)}=\mathrm{Dropout}\!\left[\text{LN}\!\left(e_g+e_{b_{ig}}^{\mathrm{bin}}+\phi(v_{ig})+\gamma(e_{s_i}^{\mathrm{sp}}+e_{t_i}^{\mathrm{tis}})\right)\right]. \tag{S5}$$

Thus, context embeddings were added to every non-padding token through the same learned scale; they were not concatenated after cell pooling. For encoder layer \(\ell\), eight-head scaled dot-product attention was

<!-- equation:supp-6 -->
$$Q^{(\ell)},K^{(\ell)},V^{(\ell)}=Z^{(\ell-1)}W_{QKV}^{(\ell)},\qquad \mathrm{Attn}(Z)=\mathrm{softmax}\!\left(\frac{QK^{\mathsf{T}}}{\sqrt{d_h}}+A_m\right)V, \tag{S6}$$

where \(A_m\) assigns negative infinity to padding keys. The feed-forward transformation was a SwiGLU module,

<!-- equation:supp-7 -->
$$\mathrm{FFN}(z)=W_{\mathrm{down}}\!\left[\mathrm{SiLU}(W_{\mathrm{gate}}z)\odot(W_{\mathrm{up}}z)\right], \tag{S7}$$

with pre-layer normalization and residual dropout around both attention and feed-forward branches.

Both evaluated configurations contain four encoder blocks, hidden dimension 256, eight attention heads, feed-forward dimension 768 and dropout 0.10. The v9 checkpoint used 32 expression bins and the root-adapter checkpoint used 64. Gated feed-forward layers and attention projections expose low-rank update points. The final classification-token state, rather than mean pooling, is the cell embedding:

<!-- equation:supp-8 -->
$$h_i=\text{LN}\!\left(Z_i^{(4)}\right)_{\mathrm{CLS}},\qquad p_i^{q}=\mathrm{softmax}\!\left(W_{2}^{q}\mathrm{Dropout}\!\left[\mathrm{GELU}(W_{1}^{q}\text{LN}(h_i))\right]\right),\ q\in\{\mathrm{fine},\mathrm{coarse}\}. \tag{S8}$$

The masked-gene decoder tied its output matrix to the gene-embedding matrix, while a separate linear decoder predicted continuous normalized values.

Let \(a(k)\) map fine class \(k\) to a coarse class. The hierarchy probability and loss were

<!-- equation:supp-9 -->
$$\bar p_{ic}=\sum_{k:a(k)=c}p_{ik}^{\mathrm{fine}},\qquad \mathcal{L}_{\mathrm{hier}}=-|V|^{-1}\sum_{i\in V}\log(\bar p_{i,y_i^{\mathrm{coarse}}}+10^{-8}). \tag{S9}$$

For masked positions \(\Omega\), the self-supervised terms were

<!-- equation:supp-10 -->
$$\mathcal{L}_{\mathrm{gene}}=-|\Omega|^{-1}\sum_{(i,g)\in\Omega}\log p(g\mid Z_{ig}),\qquad \mathcal{L}_{\mathrm{value}}=|\Omega|^{-1}\sum_{(i,g)\in\Omega}\mathrm{SmoothL1}(\widehat{x}_{ig},\widetilde{x}_{ig}). \tag{S10}$$

The v9 hybrid objective used

<!-- equation:supp-11 -->
$$\mathcal{L}=\mathcal{L}_{\mathrm{fine}}+0.35\mathcal{L}_{\mathrm{coarse}}+0.10\mathcal{L}_{\mathrm{hier}}+0.35\mathcal{L}_{\mathrm{gene}}+0.10\mathcal{L}_{\mathrm{value}}. \tag{S11}$$

The fine and coarse terms were label-smoothed cross-entropies, and 15% of eligible non-CLS tokens were masked. Supervised adaptation disabled the two masked-token terms and optimized the available fine, coarse and hierarchy terms.

### S4. Adapter selection and runtime output

Each of the 24 adapter entries specifies an identifier, canonical species, aliases, source tissue, checkpoint path and label vocabulary. A species without trained adapter weights is processed by the shared fallback, and the output explicitly records that fallback status.

For each adapted linear map, the implementation evaluated

<!-- equation:supp-12 -->
$$f(x)=Wx+\frac{\alpha}{r}BA\,\mathrm{Dropout}(x),\qquad r=8,\ \alpha=16. \tag{S12}$$

with \(B\) initialized to zero so that adaptation began exactly at the base transformation. In LoRA mode, trainable parameters comprised the low-rank matrices, normalization layers, gene/value/species/tissue embeddings, the context scale and both annotation heads; the remaining base linear weights stayed fixed.

Cell-level output includes the selected adapter, fallback status, orthology map and aggregation rule, prediction probabilities, fine and coarse labels, 256-dimensional embeddings and ranked marker candidates. The same output schema is used by command-line and CUDA inference.

### S4a. Evidence-aware PlantCell-Agent

PlantCell-Agent is an optional, deterministic workflow layer around the Plant-CellFM inference interface. It does not retrain the model, modify a checkpoint or change the denominator of any primary benchmark. The input audit records the expression layer, matrix dimensions, identifier overlap, metadata fields, canonical species, tissue context and available support labels. The central model produces the shared embedding and direct prediction, after which the orchestrator selects a capability-scoped specialist agent: a registered species adapter, organ-context agent, orthology-transfer agent, support-prototype agent or universal open-set agent. Each specialist declares required inputs, outputs, evidence requirements and an explicit fallback chain in `plantcell_specialist_agents_v1.json`. The post-inference evidence agent validates confidence, coverage, artifact integrity, open-set and ontology signals, exports ranked marker evidence, and writes a review table for cells that fail the declared acceptance contract. For orthology-routed runs, the only retry is an alternate declared aggregation rule; it is retained only if accepted coverage and accepted confidence both improve. The complete state trace is stored as JSONL, and the direct prediction file is preserved beside the final prediction file.

The replay contract was evaluated on Arabidopsis secondary root, wheat root and Sorghum root objects. The agent selected the expected registered-adapter, registered-adapter and orthology-STC routes, respectively. Exact SHA-256 matches were obtained for direct predictions, final predictions and embeddings across independent repeats. A strict held-out replay was marked unavailable because the declared 3,964-cell H5AD object was not present in the execution workspace; no substitute object was used.

### S5. Nested strict evaluation

Let \(\mathcal{S}\) be the canonical species set, \(D_s\) the outer target cells and \(\mathcal{R}\) the candidate decoders. The source-only selector was

<!-- equation:supp-13 -->
$$r_s^{*}=\underset{r\in\mathcal{R}}{\mathrm{argmax}}\ |\mathcal{S}\setminus\{s\}|^{-1}\sum_{u\ne s}M\!\left(r;D_{\mathcal{S}\setminus\{s,u\}},D_u\right). \tag{S13}$$

The selected decoder was applied once to the untouched outer species. The encoder was a fixed pre-trained multispecies representation; target labels from the outer species were unavailable to downstream decoder fitting, decoder selection, thresholding and calibration.

Let \(I_i=\mathbf{1}\{y_i\in\mathcal{Y}_{-s_i}\}\) indicate that cell \(i\)'s reference label occurred in its source fold. All-cell accuracy, source-label coverage and covered-label accuracy were

<!-- equation:supp-14 -->
$$A_{\mathrm{all}}=N^{-1}\sum_i\mathbf{1}\{\widehat y_i=y_i\},\quad C=N^{-1}\sum_iI_i,\quad A_{\mathrm{covered}}=\frac{\sum_iI_i\mathbf{1}\{\widehat y_i=y_i\}}{\sum_iI_i}. \tag{S14}$$

Unsupported target labels therefore remained errors in all-cell scoring. For represented reference classes \(\mathcal{C}\),

<!-- equation:supp-15 -->
$$F_{1,\mathrm{macro}}=|\mathcal{C}|^{-1}\sum_{c\in\mathcal{C}}\frac{2\,TP_c}{2\,TP_c+FP_c+FN_c}. \tag{S15}$$

A companion analysis identified labels beginning with unknown, unknow and unannotated using a predefined regular expression. These cells were excluded from identity-only fitting and scoring but remained in the primary all-cell analysis.

### S6. Context-aware species-transfer calibration

Four decoders were compared on the same pretrained embeddings. The centroid baseline selected the closest source-label centroid by cosine distance. Expression STC used nine cosine-nearest source cells. Neural STC fitted a z-scored linear classification head on source species. The phylogeny-organ gate combined the expression decoder with an organ-level majority prior.

For a target species \(s\), \(N_F(s)\) was the number of informative source cells from the same botanical family. With nine-neighbour expression transfer \(\widehat y_i^{\mathrm{kNN}}\), the implemented gate was

<!-- equation:supp-16 -->
$$\widehat y_i=\begin{cases}\widehat y_i^{\mathrm{kNN}},&F(s)\ne\varnothing,\ o_i=\mathrm{leaf},\ N_F(s)\ge128,\\\underset{y}{\mathrm{argmax}}\sum_{j:s_j\ne s}\mathbf{1}\{o_j=o_i,\ y_j=y\},&\mathrm{otherwise}.\end{cases} \tag{S16}$$

Species identity and organ metadata were available to the gate, but target cell labels were not.

The gate predicts only labels observed in the source fold, so cells with unsupported reference states remained unsupported-label errors. All four decoders used the same cells, denominator and 55.90% source-label coverage. Because the threshold and routing rule were selected from aggregate outer-fold behavior, the gate result is a sensitivity analysis; nested leave-species decoder transfer remains primary.

### S7. Few-shot target adaptation

Support and query cells were non-overlapping. For draw \(t\), species \(s\) and budget \(b\in\{8,16,32,64\}\), \(S_{s,b}^{(t)}\cap Q_{s,b}^{(t)}=\varnothing\) and \(S_{s,b}^{(t)}\cup Q_{s,b}^{(t)}=D_s\). Ten random draws were performed per budget. The reported mean and between-draw standard deviation were

<!-- equation:supp-17 -->
$$\bar A_b=T^{-1}\sum_{t=1}^{T}A_b^{(t)},\qquad \text{SD}(A_b)=\sqrt{(T-1)^{-1}\sum_{t=1}^{T}(A_b^{(t)}-\bar A_b)^2},\quad T=10. \tag{S17}$$

Model parameters were estimated from support cells and evaluated only on query cells. Species-resolved outcomes were calculated before aggregation.

Label-stratified allocations sampled one, three or five cells per available target label where possible. These experiments distinguished the effect of total annotation count from label diversity. The support allocation and all random seeds are included in Tables S8-S10.

### S8. Arabidopsis root analyses

For the label-free GSE152766 matrix, only model outputs and expression values were used. Six marker-to-identity expectations were fixed from Jean-Baptiste et al. and Shahan et al. before group-level contrasts. For marker \(m\) and predicted group \(C_k\),

<!-- equation:supp-18 -->
$$\mu_{mk}^{\mathrm{in}}=|C_k|^{-1}\sum_{i\in C_k}\widetilde{x}_{im},\quad d_{mk}^{\mathrm{in}}=|C_k|^{-1}\sum_{i\in C_k}\mathbf{1}\{c_{im}>0\};\qquad \Delta\mu_{mk}=\mu_{mk}^{\mathrm{in}}-\mu_{mk}^{\mathrm{out}}. \tag{S18}$$

Detection contrasts were defined analogously. Group ranks by mean expression and detection were also reported.

The GSE270140 secondary-root adapter used 11,760 author-labelled cells and 14 classes. The fixed seed 20260801 assigned 8,232 cells to training, 1,176 to validation and 2,352 to the locked test. LoRA rank was 8. The best epoch was selected by validation fine macro-F1. A three-state anatomical mapping was predeclared before test inference, and compatible test cells were scored without changing the mapping.

### S9. Wheat benchmark and comparator execution

The GSE270342 object contained 7,388 cells. A barcode intersection with an earlier exploratory record identified 224 shared cells, which were removed before all preparation and scoring. The remaining 7,164 cells were assigned to 5,014 training, 717 validation and 1,433 test cells. The Plant-CellFM adapter used a fixed seed, rank-8 LoRA, class-balanced supervision and validation-only epoch selection.

The official scPlantLLM checkpoint was converted only to reconcile packed query-key-value parameters with the execution module. Six weight tensors and six bias tensors were converted; ten discriminator-prefixed keys not used by the encoder were omitted. The resulting encoder loaded with zero missing and zero unexpected keys. Pretrained, partial and full adaptation configurations used the same author object, orthology map and test barcodes as Plant-CellFM. Cell-level predictions regenerated from the saved checkpoints reproduced the reported metrics.

The experiment was not compute matched. Plant-CellFM adapted low-rank modules and a task head; the strongest scPlantLLM reference adapted the full backbone and a new task head. The comparison therefore supports matched-data reproducibility, not universal superiority.

### S10. Sorghum sealed-library design

The GSE297576 author object contained four independent libraries. OUGHX and OWGSC formed the training set, OWGSB was restricted to validation and OUGHW remained sealed until final evaluation. The test library contained 4,150 cells and 27 author states. The selected rank-8 adapter was evaluated once after epoch selection.

Fine-state performance used all test cells. Broad-root performance used a predefined semantic map and the 3,549 test cells compatible with both pretrained and author vocabularies. The same cells were used for pretrained and adapted predictions. Bootstrap intervals used 3,000 fixed-seed resamples. An exchanged-library analysis reversed the validation and test roles to assess whether recovery was specific to OUGHW; the original split remained primary.

### S11. Statistical analysis and quality control

Accuracy was the fraction of exact correct predictions. Macro-F1 was the unweighted mean of per-class F1 over represented reference classes. If \(n_c\) is class support, weighted-F1 was

<!-- equation:supp-19 -->
$$F_{1,\mathrm{weighted}}=\sum_{c\in\mathcal{C}}\frac{n_c}{\sum_{k\in\mathcal{C}}n_k}F_{1,c}. \tag{S19}$$

For confidence-selective annotation at acceptance fraction \(q\), let \(\tau_q\) be the corresponding confidence quantile. Selective accuracy and coverage were

<!-- equation:supp-20 -->
$$A_{\mathrm{sel}}(q)=\frac{\sum_i\mathbf{1}\{p_i\ge\tau_q\}\mathbf{1}\{\widehat y_i=y_i\}}{\sum_i\mathbf{1}\{p_i\ge\tau_q\}},\qquad C_{\mathrm{sel}}(q)=N^{-1}\sum_i\mathbf{1}\{p_i\ge\tau_q\}. \tag{S20}$$

For metric \(M\), the percentile bootstrap interval from \(B\) resamples was

<!-- equation:supp-21 -->
$$\text{CI}_{0.95}(M)=\left[Q_{0.025}\!\left(M^{(1:B)}\right),Q_{0.975}\!\left(M^{(1:B)}\right)\right]. \tag{S21}$$

Confidence intervals were nonparametric cell-level bootstrap intervals and should not be interpreted as biological replicate confidence intervals. The Sorghum broad-root comparison used \(B=3{,}000\).

Every quantitative figure panel was generated from a tab-separated source file. Cell-level predictions, summary statistics and plotting inputs are available with the code repository.

## Supplementary Results

### S1. Open-set labels explain most strict error

Source-label coverage was 55.90%, leaving 44.10% of cells with reference labels unavailable in the corresponding source fold. The 1,748 unsupported-label cells accounted for 57.67% of all errors. Gossypium hirsutum was entirely outside the exact source vocabulary. Catharanthus roseus had high coverage and therefore represented a transfer error that context routing could address.

### S2. Label-integrity analysis separates identities from placeholders

The label-integrity companion contained 2,324 explicit-identity cells and 1,640 unknown or unannotated records. Removing placeholders changed both coverage and class composition; the complete all-cell panel therefore remained primary.

### S3. Runtime confidence defines a selective-use regime

The full-vocabulary runtime head achieved 66.25% exact-label accuracy on 3,964 aligned cells. Restricting acceptance to the highest-confidence 30% of cells increased selective accuracy to 96.64%; the highest-confidence 40% achieved 92.81%. These values describe selective runtime annotation, not leave-species decoder-transfer performance, because the runtime and source-fold vocabularies differ.

### S4. Internal checkpoint gains are protocol dependent

On matched data and labels, the current checkpoint improved leave-dataset, leave-sample and label-normalized leave-species accuracy over v3. The gain was largest for leave-dataset evaluation; the smaller leave-species improvement indicates that representation scaling alone did not resolve cross-species annotation.

### S5. Source-only adaptation did not improve wheat transfer

A GSE270140 Arabidopsis root adapter was transferred to a fixed three-state wheat evaluation without wheat labels. The pretrained root checkpoint achieved 0.4231 macro-F1, while the source adapter achieved 0.4036. Additional source-tissue adaptation therefore specialized the model without improving transfer to wheat (Supplementary Fig. S9; Table S21).

### S6. Multi-species marker resources extend interpretation without changing training scope

The separate scPlantDB analysis contains 31,503 cells from Arabidopsis thaliana, Gossypium hirsutum, Oryza sativa and Zea mays across root tip, ovule, pistil and pollen. It yielded 96 marker-candidate records across 27 author states. These data were assembled after checkpoint training and were used only to examine marker output across plant contexts.

### S7. Sorghum recovery is state dependent

The OUGHW adapter recovered most broad root layers, but fine-state F1 varied with state support and transcriptional proximity. Table S26 reports precision, recall and F1 for all 27 states, and Supplementary Fig. S5 shows broad-root confusion. Exchanging OWGSB and OUGHW preserved substantial recovery, indicating that performance was not restricted to a single favourable test library.

### S8. Third-party benchmark availability

Seurat transfer, centroid baselines and the matched scPlantLLM analysis were completed. Official scPlantLLM weights loaded on CUDA with zero missing or unexpected encoder keys, and saved predictions reproduced the reported results. scPlantAnnotate was accessible through an online service, but authenticated batch execution and cell-level prediction export were unavailable for the test set; no numerical comparison is therefore reported.

### S9. PlantCell-Agent replay and audit outputs

The replay manifest in `release_metadata/plantcell_agent_replay_v1.json` records the input paths, checkpoint paths, expected routes, preprocessing statistics, direct-versus-agent metrics, review decisions, retry outcomes, runtime and repeatability hashes. The three available end-to-end replays produced the following all-cell accuracy values: Arabidopsis secondary root, 0.8664; wheat root, 0.6471; and Sorghum root, 0.8219. The workflow layer leaves these direct values unchanged; its measurable output is accepted-cell coverage and the explicit review partition. The raw strict H5AD remains unavailable, but the complete 3,964-cell prediction/embedding bundle was replayed against cell-level author labels and is reported separately as `locked_bundle_replay` in Supplementary Fig. S13 and Table S29. This is not described as an end-to-end input replay.

## Supplementary Figure Legends

**Supplementary Fig. S1 Leave-species uncertainty.** Point estimates, cell-bootstrap intervals, label coverage, unsupported-label composition and held-out species sizes for nested evaluation.

**Supplementary Fig. S2 Confidence-selective runtime annotation.** Full-vocabulary accuracy, confidence-selective performance and teacher-rescue predictions shown separately from leave-species transfer.

**Supplementary Fig. S3 Matched internal checkpoint gain.** Pretrained v3 and current-checkpoint performance with shared data, splits, labels and gene mappings.

**Supplementary Fig. S4 Exchanged Sorghum library replication.** Fine-state performance after exchanging the validation and sealed-test libraries within the same source-pinned atlas.

**Supplementary Fig. S5 Sorghum state-resolved error atlas.** Precision, recall, F1, support and broad-root confusion for the sealed OUGHW library.

**Supplementary Fig. S6 Arabidopsis marker-candidate programs.** Computational marker candidates across ten root identities, including literature-fixed anchors. The panel is not wet-lab validation.

**Supplementary Fig. S7 Secondary-root adapter.** GSE270140 split, validation history, 14-class confusion matrix, per-class F1 and predeclared three-state semantic recovery.

**Supplementary Fig. S8 Matched scPlantLLM wheat reference.** Pretrained, partial and full scPlantLLM adaptation on the same GSE270342 object, first-target mapping and 1,433 test barcodes.

**Supplementary Fig. S9 Source-only Arabidopsis-to-wheat transfer.** Negative-control comparison of the pretrained root checkpoint and GSE270140 adapter on a fixed wheat evaluation.

**Supplementary Fig. S10 Multi-species scPlantDB resource.** Cell and marker-candidate coverage across four species and four tissues in a separately versioned post-training resource.

**Supplementary Fig. S11 Annotation-task topology.** Target information used in leave-species transfer, blind inference, target adaptation, library-held-out testing and matched-data comparison.

**Supplementary Fig. S12 Central Plant-CellFM model with specialist adapter agents.** Vector schematic (`figures/plantcell_agent/plantcell_agent_extended_data_fig1_v3.svg`) of the shared central model, PlantCell-Agent orchestrator, capability-scoped species/organ/orthology/support/open-set/marker agents, evidence verification, Review Agent and reproducible output bundle. The figure is a workflow specification; it contains no new performance estimate.

**Supplementary Fig. S13 Selective reliability of PlantCell-Agent.** Coverage--accuracy, selective risk, confidence calibration and review error-capture curves for the strict 3,964-cell locked bundle and three end-to-end H5AD replays. Squares mark the accept-all baseline; circles show Agent threshold policies. The strict panel is explicitly a locked-output replay because the raw H5AD object was unavailable.

## Supplementary Table Descriptions

**Table S1.** Training corpus datasets, species, cell counts and gene counts.

**Table S2.** Annotation tasks, permitted target information, denominators and interpretation.

**Table S3.** Nested strict v17 results for each held-out species.

**Table S4.** Identity-curated v18 companion results for each evaluable species.

**Table S5.** Identity labels and placeholder states in the strict panel.

**Table S6.** Inner-fold candidate selection records for the nested protocol.

**Table S7.** Selected decoder configuration for each outer species.

**Table S8.** Aggregate few-shot query metrics by support budget.

**Table S9.** Raw few-shot query metrics across repeated draws.

**Table S10.** Per-species few-shot outcomes for each draw and budget.

**Table S11.** Matched internal checkpoint comparison.

**Table S12.** External comparator availability and execution status.

**Table S13.** Arabidopsis root marker-candidate records.

**Table S14.** Figure source-data index.

**Table S15.** Reproducibility files and checksums.

**Table S16.** Literature-fixed Arabidopsis root marker concordance.

**Table S17.** GSE152766 blind external-root input and output summary.

**Table S18.** GSE270140 secondary-root adapter per-class metrics.

**Table S19.** GSE270140 predeclared semantic recovery.

**Table S20.** GSE270342 barcode exclusion, orthology mapping, split and adapter configuration.

**Table S21.** Source-only GSE270140-to-GSE270342 transfer sensitivity.

**Table S22.** scPlantLLM pretrained matched wheat embedding probe.

**Table S23.** scPlantLLM partial-adaptation wheat metrics.

**Table S24.** scPlantLLM full-backbone wheat metrics.

**Table S25.** GSE297576 pretrained Sorghum predictions.

**Table S26.** GSE297576 Sorghum adapter per-state metrics.

**Table S27.** Pretrained-to-adapted matched Sorghum broad-root recovery.

**Table S28.** PlantCell-Agent replay contract, route decisions, direct-versus-agent metrics, accepted-cell metrics, review fractions, runtime, GPU peak memory, retry outcomes and exact-repeat hashes.

**Table S29.** PlantCell-Agent selective-risk metrics, ten-bin calibration curves, expected calibration error, reference-backed accepted-versus-review audit and the blinded expert-audit worksheet/key contract.

## Data and code availability

Code, model configurations, processed data manifests and figure source tables are available from `https://github.com/ahvsjags/SnowLotus-CellFM`. Supplementary Figs. S1-S13 are provided in citation order, and Tables S1-S29 contain the data provenance, task definitions, species-resolved metrics, external analyses, Agent replay contract, selective-risk evidence and reproducibility information used in this study. The article version is prepared for the public tag `plant-methods-submission-v1-20260803`; a persistent archive DOI will be added after the repository release is linked to an archive record.
