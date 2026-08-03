# Plant-CellFM: coverage-aware cross-species annotation and sparse adaptation across plant species

**Article type:** Methodology

**Authors:** Author details to be supplied by the submitting author

**Affiliations:**

1. Author affiliations to be supplied in the journal submission system

**Corresponding author:** To be supplied by the submitting author

## Abstract

### Background

Plant single-cell atlases increasingly span model species and crops, yet transferring cell identities between species remains difficult. Gene identifiers and orthology relations differ among genomes, tissues contain different state compositions, and target atlases often include identities that are absent from the reference vocabulary. These unsupported-label conditions are obscured when source-only transfer and target-supervised adaptation are reported as the same annotation task.

### Results

We developed Plant-CellFM, a gene-set transformer that combines a shared plant expression representation with explicit orthology mapping, phylogeny-organ calibration and rank-8 low-rank adaptation. The training corpus comprised 272,732 cells from five species; evaluation used 3,964 cells from eight held-out species or species-groups. In nested leave-species decoder transfer on a fixed pre-trained embedding, downstream decoder fitting and selection excluded the outer target labels and yielded 39.96% all-cell accuracy. Only 55.90% of held-out cells had labels represented in the corresponding source folds; accuracy within this covered subset was 71.48%, showing that absent reference states accounted for a substantial component of cross-species error. A label-independent phylogeny-organ gate increased all-cell accuracy to 42.36% in a separately designated sensitivity analysis. With labelled target support, mean query accuracy rose from 59.21% with eight cells per species to 75.89% with 64 cells. Rank-8 adapters reached 62.25% accuracy on 1,433 held-out wheat root cells and 76.02% across 27 states in a sealed *Sorghum* library. On 3,549 *Sorghum* cells with compatible broad identities, adaptation increased accuracy from 14.79% to 84.98%.

### Conclusions

Plant-CellFM identifies the label-coverage limit of cross-species plant annotation and provides a parameter-efficient route for recovering species- and study-specific cell states. Reporting source-only recognition and target-supervised recovery as separate endpoints yields a practical framework for annotating new plant atlases without masking unsupported-label failure.

**Keywords:** plant single-cell transcriptomics; cell-type annotation; cross-species transfer; label coverage; LoRA; orthology; species adaptation

## Background

Single-cell RNA sequencing and single-nucleus RNA sequencing have resolved developmental, stress-responsive and lineage-specific transcriptional states in plants [1,2]. *Arabidopsis* root atlases established detailed anatomical and developmental vocabularies [3,4], and crop studies have extended these analyses to larger and polyploid genomes [5]. Reusing such atlases as references requires more than within-study classification: the target experiment may use a different genome annotation, contain a different mixture of tissues and developmental states, or distinguish identities that have no counterpart in the reference.

These differences create two separable sources of error. Expression from a conserved cell identity may fail to align because source and target genes are incompletely mapped or because the relevant state occupies a different transcriptional context. Alternatively, the target identity may be genuinely unavailable to the source classifier. The second case cannot be corrected by choosing a stronger closed-set decoder. It requires explicit coverage accounting, rejection or expansion of the target vocabulary. Placeholder annotations such as unknown, unannotated and experiment-specific cluster names further complicate evaluation because removing them changes both the test denominator and the apparent label space.

Large single-cell models such as scGPT, scFoundation, SATURN and universal cell embeddings demonstrate that learned representations can support transfer across datasets and species [6-9]. Plant-focused resources, including scPlant, scPlantDB, scPlantLLM and scPlantAnnotate, add plant gene dictionaries, reference atlases and dedicated annotation models [10-13]. Their reported accuracies nevertheless address different tasks. Some evaluations transfer labels without target annotation, whereas others fit a new classifier or backbone on target-labelled cells. Gene mapping and target-label coverage are also reported inconsistently, making it difficult to determine whether an error reflects representation failure, an unsupported cell identity or an incompatible input vocabulary.

Plant-CellFM addresses this problem with a shared gene-set encoder and three annotation regimes. Frozen-encoder leave-species decoder transfer measures recognition without target labels in the downstream classifier. A context gate uses label-independent species-family and organ metadata to route cells among labels represented in the source data. When target states remain unresolved, low-rank species adapters learn a study-specific vocabulary from a small labelled support set. Exact gene matching and declared orthology projection provide a common input layer for these regimes.

We tested whether these regimes separate label-space failure from recoverable transfer error. The analysis first quantifies strict leave-species performance on the complete test denominator, then measures the effect of source-derived context and increasing target-label support. Independent root datasets from *Arabidopsis*, allopolyploid wheat and *Sorghum* examine marker coherence, orthology-aware adaptation and library-level generalization. These experiments define when a shared plant representation is sufficient and when a species-specific adapter is required.

## Methods

### Study design and annotation tasks

Six tasks were evaluated according to the target information available at prediction time. Nested leave-species decoder transfer used a fixed pre-trained encoder and excluded all outer target labels from downstream decoder fitting, decoder selection and calibration. Context sensitivity additionally used organ metadata and phylogenetic family assignments derived independently of cell labels. Few-shot experiments supplied labelled support cells but evaluated disjoint query cells. Blind external inference assessed expression coherence when expert identities were unavailable. The wheat and Sorghum studies used labelled training and validation cells with held-out test sets. Table 1 defines the endpoint and interpretation for each task.

**Table 1. Annotation tasks and permitted target information**

| Task | Target labels used for fitting or selection | Test unit | Primary interpretation |
| --- | --- | --- | --- |
| Nested leave-species decoder transfer | No target labels for downstream decoder fitting or selection; fixed pre-trained encoder | 3,964 cells from eight held-out species or species-groups | Source-only transfer with complete denominator |
| Context-gated sensitivity | No target labels; source metadata only | Same 3,964 cells | Mechanistic sensitivity analysis |
| Sparse target adaptation | Support cells only | Disjoint query cells over ten draws | Label-efficient species calibration |
| Blind Arabidopsis marker analysis | No expert labels available | 6,566 external cells | Marker coherence |
| Wheat matched benchmark | Training and validation labels | 1,433 identical locked barcodes | Same-study adaptation reference |
| Sorghum sealed-library adaptation | Three non-test libraries | 4,150 cells from one sealed library | Library-held-out target adaptation |

### Training corpus and public data provenance

The training corpus was assembled from public plant single-cell and single-nucleus expression matrices and profiled from the versioned H5AD object used for this study. It contains 272,732 cells, 209,405 genes, five species, nine datasets and 31 samples. Supplementary Table S1 reports dataset identifiers, source URLs, sample names, species aliases, tissues and file checksums. Larger development collections and resources assembled after checkpoint training were excluded from the corpus totals and all model-performance analyses.

The leave-species transfer panel contains 3,964 aligned cells from eight held-out species or species-groups after normalization of aliases such as *Arabidopsis thaliana* and Arabidopsis_thaliana. The panel includes *Arabidopsis thaliana*, *Brassica rapa*, *Catharanthus roseus*, *Eutrema salsugineum*, *Fragaria vesca*, *Gossypium bickii*, *Gossypium hirsutum* and *Triticum aestivum*. The encoder was kept fixed rather than retrained for each outer species; the held-out exclusion applies to downstream decoder fitting, decoder selection and calibration. All cells contributed to all-cell accuracy, including those whose reference label was absent from the corresponding source fold.

External analyses used GSE152766/GSM4626007 for blind *Arabidopsis* root inference, GSE270140/GSM8335426 for supervised secondary-root adaptation, GSE270342 for the wheat-root comparison and GSE297576 for *Sorghum* root adaptation [14-17]. Source objects, conversion procedures and cell identifiers were fixed before model scoring. No human or animal data were used.

### Gene representation and orthology projection

Let \(c_{ig}\) denote the raw count for gene \(g\) in cell \(i\), and let \(L_i\) be the corresponding library size. Counts were normalized to 10,000 per cell and transformed as

<!-- equation:main-1 -->
$$\widetilde{x}_{ig}=\log\!\left(1+\frac{10^{4}c_{ig}}{L_i}\right),\qquad L_i=\sum_{h}c_{ih}. \tag{1}$$

Only expressed genes were eligible for tokenization. The retained set was

<!-- equation:main-2 -->
$$G_i=\mathrm{TopK}\!\left(\{g:\widetilde{x}_{ig}>0\},K\right). \tag{2}$$

The v9 plant-general checkpoint used \(K=512\) and 32 expression bins. The independently trained Arabidopsis, wheat and Sorghum root adapters used the same encoder family with \(K=1{,}024\) and 64 bins; these settings are reported separately because the adapter experiments were initialized from the pretrained root checkpoint rather than the v9 strict-transfer checkpoint.

Exact identifiers were matched directly to the relevant checkpoint vocabulary. When identifiers differed, a versioned map assigned each source gene \(g\) a target set \(M(g)\). The primary rule retained the first declared target; the sensitivity rule distributed a source count equally over all declared targets. Both are represented by projection weights \(P_{gt}\), with projected counts

<!-- equation:main-3 -->
$$c^{\mathrm{proj}}_{it}=\sum_g c_{ig}P_{gt},\qquad P_{gt}=\mathbf{1}\{t=\mathrm{first}\,M(g)\}\ \text{or}\ \frac{\mathbf{1}\{t\in M(g)\}}{|M(g)|}. \tag{3}$$

Unmapped genes were discarded. Feature coverage and count retention were calculated before normalization of the projected matrix:

<!-- equation:main-4 -->
$$C_{\mathrm{feat}}=\frac{\sum_g\mathbf{1}\{|M(g)|>0\}}{|G_{\mathrm{source}}|},\qquad C_{\mathrm{count}}=\frac{\sum_{i,g}c_{ig}\mathbf{1}\{|M(g)|>0\}}{\sum_{i,g}c_{ig}}. \tag{4}$$

Wheat features were transferred with the author-provided PLAZA orthogroup relation. The deterministic primary projection used the first declared target, and a count-conserving mean projection provided a sensitivity analysis. For *Sorghum*, the author-maintained ten-species orthogroup resource was converted to a *Sorghum*-to-*Arabidopsis* mapping. Of 25,464 author genes, 15,940 mapped to an orthogroup target and 10,325 were represented in the pretrained checkpoint after preprocessing.

### Model architecture and objectives

Plant-CellFM is a position-free transformer over expressed gene sets. For token \(g\) in cell \(i\), the normalized value was scaled to \(s_{ig}\in[0,1]\), assigned to expression bin \(b_{ig}\), and combined with gene, bin, continuous-value, species and tissue embeddings:

<!-- equation:main-5 -->
$$s_{ig}=\mathrm{clip}\!\left(\frac{\widetilde{x}_{ig}}{\log(10001)},0,1\right),\quad b_{ig}=\left\lfloor(B-1)s_{ig}\right\rfloor,\quad z^{(0)}_{ig}=\text{LN}\!\left(e_g+e^{\mathrm{bin}}_{b_{ig}}+\phi(s_{ig})+\gamma(e^{\mathrm{sp}}_{s_i}+e^{\mathrm{tis}}_{t_i})\right). \tag{5}$$

Here \(\phi\) is a two-layer learned projection and \(\gamma\) is a learned scalar. No positional encoding was added. Four pre-normalized transformer blocks, each with eight-head set self-attention and a SwiGLU feed-forward module of width 768, produced token states of dimension 256. Padding keys and outputs were masked. The cell representation was the final state of the prepended classification token, not a mean over genes:

<!-- equation:main-6 -->
$$Z_i^{(\ell)}=\mathrm{Block}_{\ell}\!\left(Z_i^{(\ell-1)},m_i\right),\ \ell=1,\ldots,4;\qquad h_i=\text{LN}\!\left(Z_i^{(4)}\right)_{\mathrm{CLS}}\in\mathbb{R}^{256}. \tag{6}$$

Separate nonlinear heads returned fine and coarse posterior probabilities:

<!-- equation:main-7 -->
$$p_i^{\mathrm{fine}}=\mathrm{softmax}\!\left(H_{\mathrm{fine}}(h_i)\right),\qquad p_i^{\mathrm{coarse}}=\mathrm{softmax}\!\left(H_{\mathrm{coarse}}(h_i)\right). \tag{7}$$

For a known fine-to-coarse map \(a(k)\), fine probabilities were aggregated into the coarse vocabulary. Hierarchical consistency was the negative log probability assigned to the observed coarse class:

<!-- equation:main-8 -->
$$\bar p_{ic}^{\mathrm{coarse}}=\sum_{k:a(k)=c}p_{ik}^{\mathrm{fine}},\qquad \mathcal{L}_{\mathrm{hier}}=-\frac{1}{|V|}\sum_{i\in V}\log\!\left(\bar p_{i,y_i^{\mathrm{coarse}}}^{\mathrm{coarse}}+10^{-8}\right). \tag{8}$$

The hybrid training objective combined label-smoothed fine and coarse cross-entropy, the hierarchy term, masked-gene identity cross-entropy and Smooth-L1 reconstruction of the masked normalized value:

<!-- equation:main-9 -->
$$\mathcal{L}=\mathcal{L}_{\mathrm{fine}}+0.35\mathcal{L}_{\mathrm{coarse}}+0.10\mathcal{L}_{\mathrm{hier}}+0.35\mathcal{L}_{\mathrm{gene}}+0.10\mathcal{L}_{\mathrm{value}}. \tag{9}$$

Fifteen per cent of eligible non-CLS tokens were masked in hybrid training. The v9 checkpoint was trained for six epochs with bfloat16 CUDA mixed precision on an NVIDIA RTX 4090.

For each cell, the model returns fine and coarse labels, prediction confidence, a 256-dimensional embedding and ranked marker candidates. Twenty-four named adapter entries and a shared fallback use the same encoder interface. If a species-specific adapter is unavailable, the software reports fallback use rather than implying that species-specific weights were applied.

### Low-rank species adaptation

Parameter-efficient adaptation added low-rank updates to the query-key-value, attention-output and SwiGLU linear transformations [18]. For a frozen base matrix \(W\in\mathbb{R}^{d_{\mathrm{out}}\times d_{\mathrm{in}}}\), the adapted transformation was

<!-- equation:main-10 -->
$$y=Wx+\frac{\alpha}{r}BA\,\mathrm{Dropout}(x),\qquad A\in\mathbb{R}^{r\times d_{\mathrm{in}}},\quad B\in\mathbb{R}^{d_{\mathrm{out}}\times r}. \tag{10}$$

The configuration used \(r=8\), \(\alpha=16\) and adapter dropout 0.05. The shared backbone was initialized from the pretrained root checkpoint, while low-rank matrices, normalization parameters, input embeddings and fine and coarse annotation heads were optimized with class-balanced supervision. Wheat and Sorghum models used learning rates of 5 x 10^-5 for non-head trainable parameters and 2 x 10^-4 for annotation heads, weight decay of 0.02, label smoothing of 0.03 and bfloat16 mixed precision. Validation macro-F1 selected one checkpoint from a maximum of ten epochs; test labels were not used for selection.

### Nested leave-species evaluation

Let \(\mathcal{S}\) be the set of canonical species and \(D_s\) the cells of species \(s\). For each outer species, candidate decoder \(r\in\mathcal{R}\) was selected only from inner source-species holdouts:

<!-- equation:main-11 -->
$$r_s^{*}=\underset{r\in\mathcal{R}}{\mathrm{argmax}}\ \frac{1}{|\mathcal{S}\setminus\{s\}|}\sum_{u\in\mathcal{S}\setminus\{s\}}M\!\left(r;D_{\mathcal{S}\setminus\{s,u\}},D_u\right),\qquad \widehat y_i=r_s^{*}(h_i),\ i\in D_s. \tag{11}$$

The outer species contributed no labels to encoder fitting, decoder selection, calibration or error correction. Let \(\mathcal{Y}_{-s}\) be the label vocabulary observed outside species \(s\), and \(I_i=\mathbf{1}\{y_i\in\mathcal{Y}_{-s}\}\). Three denominators were reported explicitly:

<!-- equation:main-12 -->
$$\text{Acc}_{\mathrm{all}}=\frac{1}{N}\sum_{i=1}^{N}\mathbf{1}\{\widehat y_i=y_i\}. \tag{12}$$

<!-- equation:main-13 -->
$$\text{Coverage}=\frac{1}{N}\sum_{i=1}^{N}I_i. \tag{13}$$

<!-- equation:main-14 -->
$$\text{Acc}_{\mathrm{covered}}=\frac{\sum_{i=1}^{N}I_i\mathbf{1}\{\widehat y_i=y_i\}}{\sum_{i=1}^{N}I_i}. \tag{14}$$

Macro-F1 was averaged over the \(C\) represented reference classes in the covered subset:

<!-- equation:main-15 -->
$$F_{1,\mathrm{macro}}=\frac{1}{C}\sum_{c=1}^{C}\frac{2\,\mathrm{Prec}_c\mathrm{Rec}_c}{\mathrm{Prec}_c+\mathrm{Rec}_c}. \tag{15}$$

A companion analysis treated labels beginning with unknown, unknow or unannotated as placeholders and quantified their influence on class composition. The complete all-cell analysis remained primary. Species-level estimates and cell-bootstrap intervals are reported in Supplementary Tables S3-S7.

### Context-aware species-transfer calibration

Species-transfer calibration compared four decoders on the same pretrained embeddings: nearest centroid, expression-neighbour transfer, a neural calibration head and a deterministic phylogeny-organ gate. Expression transfer used cosine \(k\)-nearest neighbours with \(k=9\). For target species \(s\), organ \(o_i\) and botanical family \(F(s)\), let \(N_F(s)\) be the number of informative source cells from that family. The gate was

<!-- equation:main-16 -->
$$\widehat y_i^{\mathrm{gate}}=\begin{cases}\widehat y_i^{\mathrm{kNN}},&F(s)\ \text{known},\ o_i=\mathrm{leaf},\ N_F(s)\ge128,\\\underset{y}{\mathrm{argmax}}\sum_{j:s_j\ne s}\mathbf{1}\{o_j=o_i,\ y_j=y\},&\text{otherwise}.\end{cases} \tag{16}$$

Target cell labels were not used to construct either prediction. The family-support threshold and routing rule were selected after examining aggregate outer-fold behavior, so this analysis was reported as sensitivity rather than as the nested primary estimate.

### Sparse target-labelled adaptation

Few-shot adaptation simulated manual annotation of a small target subset. For draw \(t\) and budget \(b\), support set \(S_{s,b}^{(t)}\subset D_s\) and query set \(Q_{s,b}^{(t)}=D_s\setminus S_{s,b}^{(t)}\) were disjoint. Budgets of 8, 16, 32 and 64 cells per species were evaluated over \(T=10\) independent draws. Mean query accuracy was

<!-- equation:main-17 -->
$$\overline{A}_b=\frac{1}{T}\sum_{t=1}^{T}\frac{1}{|Q_{s,b}^{(t)}|}\sum_{i\in Q_{s,b}^{(t)}}\mathbf{1}\{\widehat y_i^{(t,b)}=y_i\}. \tag{17}$$

Separate allocations sampled support by target label to distinguish the effect of state diversity from total cell count. We report \(\overline{A}_b\), its between-draw standard deviation, query macro-F1 and species-resolved values.

### *Arabidopsis* root analyses

The pretrained root checkpoint was applied to GSE152766/GSM4626007, for which no expert cell-identity field was available. The matrix contained 6,566 cells and 25,171 TAIR10 identifiers. Before inspecting predictions, we specified six marker-identity pairs from published *Arabidopsis* root atlases: APL for phloem, COBL9 for root hair, GL2 and WER for non-hair epidermis, CASP1 for endodermis and MYB46 for xylem [3,4]. For predicted identity \(k\) with cell set \(C_k\), marker \(m\) was summarized by

<!-- equation:main-18 -->
$$\mu_{mk}=\frac{1}{|C_k|}\sum_{i\in C_k}\widetilde{x}_{im},\qquad d_{mk}=\frac{1}{|C_k|}\sum_{i\in C_k}\mathbf{1}\{c_{im}>0\}. \tag{18}$$

Mean normalized expression \(\mu_{mk}\) and detection fraction \(d_{mk}\) were compared between the expected predicted group and all remaining cells. Without expert identities, marker coherence was the prespecified endpoint.

GSE270140/GSM8335426 was used as a separate author-labelled adaptation case. Unique cell identifiers were assigned to a fixed 80/10/20 split containing 8,232 training, 1,176 validation and 2,352 locked test cells. Epoch 7 was selected by validation macro-F1. A three-state semantic map to phloem, xylem and stele was declared before test inference.

### Matched wheat-root benchmark

The GSE270342 author object contained 7,388 cells. Exact barcode comparison against an earlier exploratory record identified 224 overlapping cells; all were excluded before adaptation, leaving 7,164 cells. A fixed split assigned 5,014 cells to training, 717 to validation and 1,433 to the locked test. Epoch 8 was selected using validation macro-F1 only.

The official scPlantLLM checkpoint was evaluated on the same prepared object, author first-target orthogroup mapping and exact test barcodes. We tested a pretrained encoder with a train-only centroid readout, final-block adaptation with a new head and full-backbone adaptation with a new head. Official weights loaded with zero missing or unexpected state keys, and regenerated cell-level predictions reproduced the reported metrics. Because trainable parameter scope and compute were not matched, this experiment was interpreted as a same-study reference rather than a universal model ranking.

### Sealed-library *Sorghum* evaluation

The GSE297576 author object contained 19,316 cells, 25,464 genes, four libraries and 27 author states. Pretrained inference was completed before author labels were joined for scoring. For adaptation, OUGHX and OWGSC were used for fitting, OWGSB for validation-only epoch selection and OUGHW as the held-out test library. OUGHW contained 4,150 cells. Fine-state performance used all 27 author labels. Broad-root recovery used the 3,549 cells with a predefined compatible identity mapping so that pretrained and adapted predictions were compared on identical cells.

### Statistics and reproducibility

Accuracy, macro-F1 and weighted-F1 were computed from cell-level predictions. For metric \(M\), fixed-seed nonparametric bootstrap resampling drew \(B\) cell samples with replacement and reported the percentile interval

<!-- equation:main-19 -->
$$\text{CI}_{0.95}(M)=\left[Q_{0.025}\!\left(M^{(1)},\ldots,M^{(B)}\right),\ Q_{0.975}\!\left(M^{(1)},\ldots,M^{(B)}\right)\right]. \tag{19}$$

The Sorghum broad-root comparison used \(B=3{,}000\). These intervals quantify uncertainty conditional on the evaluated cells and do not represent biological-replicate inference. Few-shot variation was summarized across ten independent support-query draws. No test labels were used for epoch selection. The source-only Arabidopsis-to-wheat transfer experiment was retained as a negative control.

Tab-separated source data are provided for every quantitative figure panel. The software implements command-line training and annotation, CUDA inference, adapter inspection and export of cell-level predictions with model, mapping and task metadata.

### Use of language and coding assistance

An LLM-based coding assistant was used during software refactoring, figure-script development and English-language editing. The authors verified all numerical results, references, code changes and scientific claims against the versioned source data. The assistant is not listed as an author and did not determine study conclusions.

## Results

### A shared plant representation supports distinct transfer and adaptation tasks

Plant-CellFM was trained on 272,732 cells from five species and evaluated on a separate panel of 3,964 cells from eight held-out species (Fig. 1). The model maps exact or orthology-projected genes to a shared 256-dimensional cell representation and returns hierarchical identities, confidence scores and marker candidates. Rank-8 adapters update this representation for target studies while retaining a common input and output interface.

The experiments separate three uses of the representation. Frozen-encoder source-only transfer tests whether downstream decoders can assign labels to a held-out species group without using its labels. Context calibration asks whether organ and family information can correct errors among labels already observed in the source data. Sparse adaptation estimates how rapidly a target-specific vocabulary can be recovered after limited annotation. Blind Arabidopsis inference and held-out wheat and Sorghum datasets provide independent tests of biological coherence and study-level generalization.

This separation is necessary because the tasks have different attainable label spaces. A source-only decoder cannot predict an identity that is absent from its source vocabulary, whereas an adapter can learn that identity from target support cells. We therefore retained the complete all-cell denominator for frozen-encoder transfer and reported target-supervised adaptation on disjoint or sealed test sets.

Four features distinguish the framework from a closed-set annotation benchmark (Table 2). First, the leave-species protocol reports the complete denominator together with label coverage, preventing unsupported target states from being silently removed. Second, source-derived organ and family context is evaluated as a separate routing layer, so its benefit can be assigned to covered labels rather than to unavailable classes. Third, target-labelled support is treated as an explicit experimental variable, allowing annotation effort to be related to query accuracy and macro-F1. Fourth, external wheat and Sorghum experiments retain locked barcodes or locked libraries, giving adaptation results that can be audited independently of the training and validation splits.

**Table 2. Evidence controls supporting the main advantages of Plant-CellFM**

| Advantage | Evidence in this study | Boundary retained |
| --- | --- | --- |
| Coverage-aware transfer evaluation | 39.96% all-cell accuracy, 55.90% source-label coverage and 71.48% covered-label accuracy on the same 3,964-cell denominator | Frozen encoder; downstream decoder transfer only |
| Context routing without target labels | 42.36% all-cell accuracy and 75.77% covered-label accuracy in the phylogeny-organ sensitivity analysis | Global routing threshold; not the nested primary estimate |
| Label-efficient target recovery | Query accuracy increased from 59.21% to 75.89% as support rose from 8 to 64 cells per species | Target-supervised support with disjoint query cells |
| Independent external adaptation | 62.25% wheat accuracy on 1,433 locked cells and 76.02% Sorghum accuracy on a sealed 4,150-cell library | Not a compute-matched universal ranking |

### Open label vocabularies account for much of leave-species error

Nested leave-species evaluation yielded 39.96% exact accuracy across all 3,964 cells (Fig. 2). Source-label coverage was 55.90%; within these covered cells, accuracy was 71.48% and macro-F1 was 0.2817. Thus, 44.10% of the panel could not be correct under exact-label scoring because the corresponding target identity was absent from the source fold.

Coverage differed markedly among species. *Eutrema salsugineum* and *Triticum aestivum* were fully covered, whereas the *Gossypium hirsutum* reference labels had no exact counterpart in the source vocabulary. *Arabidopsis thaliana* contributed 2,366 cells and had 43.28% coverage. The panel also contained 1,640 unknown or unannotated records and 2,324 explicit identities. Treating those placeholders as ordinary biological classes, or removing them without reporting the denominator, changed the apparent difficulty of the task (Supplementary Fig. S1; Supplementary Tables S3-S7).

The current checkpoint improved matched internal transfer relative to the earlier v3 model: leave-dataset accuracy increased from 20.21% to 44.90%, leave-sample accuracy from 41.55% to 62.00% and label-normalized leave-species accuracy from 19.12% to 23.54%. The smaller gain for leave-species transfer indicates that scaling the representation alone did not resolve differences in target vocabularies and biological context.

### Phylogeny and organ context rescue transferable labels

We next tested whether source-derived context could improve decisions within the available label vocabulary. On the same embeddings, 3,964-cell denominator and 55.90% coverage, nearest-centroid decoding achieved 23.64% all-cell accuracy, expression-neighbour transfer achieved 30.10% and a neural calibration head achieved 31.84% (Fig. 3). The phylogeny-organ gate increased all-cell accuracy to 42.36% and covered-label accuracy to 75.77%; covered-label macro-F1 was 0.3045.

The gain was concentrated in species for which an organ-compatible source label existed. Relative to the centroid decoder, *Catharanthus roseus* improved by 69.14 percentage points and *Fragaria vesca* by 39.06 points. *Gossypium hirsutum* remained unresolved because none of its exact reference labels occurred in the source vocabulary. Cell-level transitions confirmed that the gate corrected covered-label errors but did not convert unsupported-label cells into exact matches.

The gate threshold and routing rule were selected from aggregate outer-fold behavior rather than inside each nested training loop. We therefore retain 39.96% as the primary leave-species estimate and report 42.36% as a sensitivity result that motivates fully nested calibration in future evaluations.

### Sparse target labels recover species-specific state vocabularies

Introducing labelled target support produced a monotonic adaptation response (Fig. 4). Across ten draws, eight support cells per species yielded 59.21% mean all-cell query accuracy. Accuracy increased to 67.34%, 72.30% and 75.89% with 16, 32 and 64 cells, respectively. The standard deviation decreased from 0.055 at eight cells to approximately 0.016 at 32 and 64 cells, while query macro-F1 increased from 0.2195 to 0.4619.

Label-stratified sampling showed that state coverage mattered in addition to the number of annotated cells. One support cell per represented label reached 56.84% query accuracy and 0.4724 macro-F1; three cells per label reached 68.73% and 0.5356. The larger macro-F1 gain under stratified sampling indicates that annotation distributed across rare states is more informative than the same effort concentrated in abundant classes.

### *Arabidopsis* roots link predicted identities to anatomical marker programs

Blind inference on GSE152766/GSM4626007 assigned 13 states across 6,566 cells (Fig. 5). Lateral root cap, cortex and stele were the largest predicted groups, and 530 cells were assigned to unknown. Five of six predefined markers reached both their highest mean expression and highest detection rate in the expected group. APL, COBL9, GL2, CASP1 and MYB46 supported phloem, root hair, non-hair epidermis, endodermis and xylem assignments, respectively. WER was enriched in non-hair cells but ranked below another group. Because the predicted phloem group contained only four cells, the APL contrast was interpreted as a marker-coherence observation rather than population-level validation.

An independent, author-labelled secondary-root dataset tested recovery of a different state vocabulary. The LoRA adapter achieved 83.97% fine-label accuracy and 84.47% macro-F1 on 2,352 held-out cells. Among 1,885 cells covered by a predefined phloem-xylem-stele map, semantic accuracy increased from 2.02% with the pretrained head to 90.93% after adaptation. The two Arabidopsis analyses therefore separate marker-supported blind inference from quantitative recovery of study-specific labels.

### Orthology-aware low-rank adaptation improves wheat root annotation

The allopolyploid wheat analysis tested adaptation when source genes could not be matched directly to the checkpoint vocabulary (Fig. 6). After removal of 224 barcodes shared with an exploratory record, 7,164 cells remained. The author-provided orthogroup map resolved 53.75% of source features while retaining 76.33% of UMI counts, indicating that the mapped genes captured most measured expression despite incomplete feature coverage.

On the identical 1,433-cell test set, the pretrained scPlantLLM representation with a train-only centroid readout achieved 21.07% accuracy and 0.2001 macro-F1. Partial adaptation increased performance to 34.26% and 0.2998, and full-backbone adaptation reached 45.01% and 0.4588. Plant-CellFM rank-8 LoRA achieved 62.25% accuracy and 0.6660 macro-F1. On the 964-cell direct-root subset, Plant-CellFM accuracy increased from 25.93% before adaptation to 56.22% afterwards.

Both models used the same author labels, orthology mapping and test barcodes, but their architectures, pretraining corpora and trainable parameter scopes differed. The result therefore supports the effectiveness of Plant-CellFM LoRA on this wheat dataset; it is not a compute-matched ranking of the two pretrained models.

### Library-held-out adaptation recovers 27 *Sorghum* root states

*Sorghum* was absent from the five-species training corpus and provided a direct test of target-specific recovery (Fig. 7). Across 14,909 comparable cells in the full atlas, the pretrained root head achieved 14.56% accuracy and 0.1083 macro-F1 and assigned 63.39% of cells to unknown. This failure established the starting point for adaptation rather than being excluded from evaluation.

The adapter was fitted on OUGHX and OWGSC, selected on OWGSB and evaluated once on OUGHW. Across all 4,150 test cells and 27 author states, it achieved 76.02% accuracy and 0.7535 macro-F1. Among 3,549 cells with compatible broad-root identities, accuracy increased from 14.79% (95% bootstrap interval, 13.67-15.98%) to 84.98% (83.80-86.17%), and macro-F1 increased from 0.1218 to 0.8362. Exchanging the validation and test libraries preserved substantial recovery (Supplementary Fig. S4), while the 27-state error atlas identified the states that remained sensitive to support size and transcriptional proximity (Supplementary Fig. S5).

The *Sorghum* experiment shows that poor source-only recognition does not preclude accurate recovery after limited target supervision. It also illustrates why the two endpoints must be reported separately: the adapted result measures generalization to a held-out library after exposure to *Sorghum* labels, whereas the pretrained result measures transfer to an unsupported species.

## Discussion

Plant-CellFM resolves cross-species annotation as a sequence of recognition, coverage accounting and recovery. A shared gene-set representation transfers identities that are present in the source vocabulary; label-independent organ and species-family context corrects a subset of transferable errors; and low-rank adaptation learns identities that require target annotation. Linking each model response to the information available for a new atlas prevents supervised recovery from being interpreted as source-only recognition.

The strict experiment identifies label availability as a major determinant of apparent model performance. All-cell accuracy was 39.96%, whereas accuracy among source-covered cells was 71.48%. The 44.10% coverage deficit reflects several phenomena that are common in plant atlases: inconsistent label granularity, placeholder annotations and valid target-specific states. *Gossypium hirsutum* illustrates the limiting case, because none of its exact reference labels occurred in the source fold. Improved embeddings may reduce errors among shared identities, but they cannot supply an absent output class. Cross-species evaluation should therefore report coverage together with accuracy and retain unsupported cells in the primary denominator.

Two results show how the remaining error can be addressed. First, the phylogeny-organ gate improved covered-label routing, particularly in *Catharanthus roseus* and *Fragaria vesca*, without adding target labels. Its globally selected threshold means that this gain requires confirmation under fully nested selection, but the species-resolved transitions localize where context is useful. Second, query accuracy increased steadily as target support grew from 8 to 64 cells per species. Label-stratified support produced a larger macro-F1 gain than unstructured sampling, indicating that annotation effort should prioritize state diversity rather than additional examples from already abundant classes.

The target-adaptation results extend this observation to distinct plant genomes and label systems. A secondary *Arabidopsis* root adapter recovered 14 author states, and the wheat experiment showed that feature coverage and retained expression carry different information: 53.75% of genes mapped, but those genes accounted for 76.33% of UMI counts. Plant-CellFM LoRA outperformed three scPlantLLM configurations on identical wheat cells, although the comparison was not compute matched. In *Sorghum*, separation by library showed that the 27-state recovery generalized beyond the libraries used for fitting and checkpoint selection. Rank-8 adapters therefore offer a compact way to preserve a shared representation while accommodating study-specific output vocabularies.

Plant-CellFM complements existing plant analysis ecosystems rather than replacing their atlas and marker resources. scPlant and scPlantDB provide broad analysis and reference functions [10,11], whereas scPlantLLM and scPlantAnnotate establish plant-specific transformer annotation [12,13]. The present work contributes a coverage-aware evaluation design, explicit gene projection and a shared-backbone adaptation strategy. A community comparison will require identical gene mappings, training-label access, test barcodes and computational budgets across tools; the current wheat result establishes a matched-data comparison but not a universal ranking.

The biological evidence is strongest for root tissues. Marker expression supported five of six predefined identities in the label-free *Arabidopsis* case, while the labelled *Arabidopsis*, wheat and *Sorghum* datasets quantified supervised recovery. These analyses do not establish a complete plant cell ontology, and marker candidates remain hypotheses until supported by independent spatial, genetic or perturbation evidence. The current training corpus contains five species, and frozen-encoder downstream transfer was evaluated in eight held-out species or species-groups; broader organs and taxonomic distances remain to be tested. scPlantAnnotate was not included in the numerical comparison because reproducible batch predictions were unavailable for the evaluated cells.

For practical use, exact gene identifiers should be matched whenever possible, and orthology projections should report both feature coverage and count retention. Predictions for a new species or study should be accompanied by label coverage and confidence. High-confidence calls can be accepted selectively: the full-vocabulary runtime head reached 96.64% accuracy in the highest-confidence 30% of cells and 92.81% in the highest-confidence 40% (Supplementary Fig. S2). Low-confidence or unsupported-label-like cells should instead be reviewed with marker evidence or used to define a label-diverse support set for adaptation.

## Conclusions

Plant-CellFM separates cross-species plant annotation into label recognition, context-guided routing and target-specific recovery. Frozen-encoder decoder evaluation showed that absent source labels explain a substantial fraction of leave-species error, while sparse rank-8 adaptation recovered study-specific states in *Arabidopsis*, wheat and *Sorghum*. The resulting workflow provides a reproducible basis for deciding when a shared plant representation is sufficient and when new target annotation is required.

## List of abbreviations

LoRA: low-rank adaptation; scRNA-seq: single-cell RNA sequencing; snRNA-seq: single-nucleus RNA sequencing; STC: species-transfer calibration; UMI: unique molecular identifier; UMAP: uniform manifold approximation and projection; F1: harmonic mean of precision and recall; GEO: Gene Expression Omnibus; API: application programming interface.

## Declarations

### Ethics approval and consent to participate

Not applicable. The study used publicly available plant transcriptomic datasets and did not involve humans or animals.

### Consent for publication

Not applicable.

### Availability of data and materials

All public datasets analysed in this study are available through the accessions listed in Supplementary Table S1, including GSE152766, GSE270140, GSE270342 and GSE297576. Source code, configuration files, model cards, cell-level results and figure source data are available at the Plant-CellFM repository [19]. The version analysed in this article is prepared for the public tag `plant-methods-submission-v1-20260803`; a persistent archive DOI will be added after the repository release is linked to an archive record.

### Competing interests

The authors declare that they have no competing interests.

### Funding

This research received no specific grant from any funding agency.

### Authors' contributions

Author-specific contribution initials will be completed by the submitting author after the author order is finalized. The submitted contribution statement will identify responsibility for study conception, model and software development, data curation, evaluation design, plant biological interpretation and manuscript writing. All listed authors will review and approve the final manuscript before journal upload.

### Acknowledgements

Not applicable.

### Authors' information

Not applicable.

## Additional files

**Additional file 1. DOCX. Plant-CellFM Supporting Information.** Supplementary Methods, Supplementary Results and descriptions of supplementary figures and tables.

**Additional file 2. PDF. Plant-CellFM Supplementary Figures.** Supplementary Figs. S1-S11 covering leave-species uncertainty, confidence-selective annotation, checkpoint comparison, Sorghum replication and state-level errors, Arabidopsis marker programs, secondary-root adaptation, wheat comparator results, source-only transfer and the multi-species marker resource.

**Additional file 3. XLSX. Plant-CellFM Supplementary Tables S1-S27.** Data provenance, task definitions, species-resolved results, nested selection, few-shot draws, comparator results, marker candidates and external analyses.

**Additional file 4. XLSX. Plant-CellFM Figure Source Data.** Quantitative source tables for the main and supplementary figures.

## Figure legends

**Fig. 1 Plant-CellFM architecture and annotation tasks.** a, Plant expression matrices enter through exact gene identifiers or a specified orthology map. b, A four-layer set transformer combines gene identity and expression values into a 256-dimensional cell representation. c, The model returns hierarchical identities, confidence scores and marker candidates. d, Rank-8 modules adapt the shared representation to species- or study-specific vocabularies. e, The training corpus and evaluation panels define explicit roles for each downstream protocol. f, Frozen-encoder transfer, context calibration, sparse support and study-level adaptation use different target information. Conceptual panels contain no quantitative data.

**Fig. 2 Coverage-aware leave-species decoder transfer.** a, Outer held-out species are excluded from downstream decoder fitting and selection while the encoder is kept fixed. b, Cell embeddings are coloured by correct, covered-error and unsupported-label outcomes. c, All-cell accuracy, source-label coverage and covered-label accuracy are reported together. d, Species-level metrics retain complete test denominators. e, Cell outcomes quantify the contribution of unsupported labels. f, Matched v3 and current-checkpoint comparisons use the same datasets, splits and labels. g-h, Bootstrap intervals summarize test-population uncertainty and confirm exclusion of target labels from downstream decoder selection.

**Fig. 3 Phylogeny-organ species-transfer calibration.** a, Expression neighbours, organ priors and same-family support determine context-gate routing. b, All decoders are evaluated on the same 3,964 cells and 55.90% source-label coverage. c, Context ablations quantify organ and family contributions. d, Species-level routing identifies the selected decoder. e, Outcomes separate all-cell accuracy, coverage and covered-label accuracy. f, Per-species changes are measured relative to centroid decoding. g, Cell transitions distinguish rescued, retained, lost, persistent-error and unsupported-label cells. h, The globally selected sensitivity result is shown separately from the nested primary estimate.

**Fig. 4 Sparse target-species adaptation.** a, Labelled support cells are excluded from query evaluation. b, Mean query accuracy rises with support size across ten draws. c, Query macro-F1 is shown separately. d, Species-by-budget values retain heterogeneous responses. e, Fixed budgets are compared with label-stratified allocation. f, Draw-level distributions show sampling variation. g, The target embedding illustrates support and query placement. The workflow panel contains no quantitative data.

**Fig. 5 Arabidopsis root marker coherence and state adaptation.** a, Root anatomy provides the identity reference. b-c, Blind GSE152766 embeddings and predicted state composition are shown without expert labels. d, Six predefined markers are tested in their expected predicted groups. e, Marker-to-identity links distinguish concordant and non-top signals. f, The fixed GSE270140 split supports supervised secondary-root adaptation. g-i, Validation history, 14-state confusion and per-class F1 quantify held-out performance. The anatomy panel contains no quantitative data.

**Fig. 6 Orthology-aware wheat-root model comparison.** a, The allopolyploid wheat orthogroup map projects source features to the checkpoint vocabulary. b, Overlapping barcodes are removed before the fixed train-validation-test split. c, Plant-CellFM LoRA and three scPlantLLM configurations are evaluated on the same 1,433 cells. d, Bootstrap intervals summarize test accuracy and macro-F1. e, Per-state F1 differences identify complementary errors. f-g, Confusion matrices retain all 13 author labels. h, Prediction changes summarize resolved and persistent errors. The workflow panel contains no quantitative data.

**Fig. 7 Library-held-out Sorghum root adaptation.** a, Two libraries are used for training, one for validation and OUGHW for final testing. b, Author root layers and 27 states define the evaluation vocabulary. c, Pretrained and adapted broad-root predictions are compared on the same 3,549 cells. d, State-resolved performance is reported for the test library. e, Orthogroup projection maps 25,464 author genes to 15,940 orthogroup targets and 10,325 checkpoint-represented genes. f, Root-layer transitions show correct and off-diagonal predictions. g, State support is related to F1. h, Broad-root accuracy is shown by identity. The anatomy panel contains no quantitative data.

## References

1. Seyfferth C, Renema J, Wendrich JR, Eekhout T, Seurinck R, Vandamme N, et al. Advances and opportunities in single-cell transcriptomics for plant research. Annu Rev Plant Biol. 2021;72:847-866. doi:10.1146/annurev-arplant-081720-010120.
2. Wang J, Zheng S, Lu B, Jiang Y, Zhu Y, Liu Q, et al. Integrated experimental and computational workflows for single-cell transcriptomics in plants. Plant Methods. 2026;22:12. doi:10.1186/s13007-025-01490-6.
3. Jean-Baptiste K, McFaline-Figueroa JL, Alexandre CM, Dorrity MW, Saunders L, Bubb KL, et al. Dynamics of gene expression in single root cells of Arabidopsis thaliana. Plant Cell. 2019;31:993-1011.
4. Shahan R, Hsu CW, Nolan TM, Cole BJ, Taylor IW, Greenstreet L, et al. A single-cell Arabidopsis root atlas reveals developmental trajectories in wild-type and cell identity mutants. Dev Cell. 2022;57:543-560.e9.
5. Ke Y, et al. A single-cell and spatial wheat root atlas with cross-species annotations delineates conserved tissue-specific marker genes and regulators. Cell Rep. 2025;44:115240. doi:10.1016/j.celrep.2025.115240.
6. Cui H, Wang C, Maan H, Pang K, Luo F, Duan N, Wang B. scGPT: toward building a foundation model for single-cell multi-omics. Nat Methods. 2024;21:1470-1480.
7. Hao M, Gong J, Zeng X, Liu C, Guo Y, Cheng X, et al. Large-scale foundation model on single-cell transcriptomics. Nat Methods. 2024;21:1481-1491.
8. Rosen Y, Brbic M, Roohani Y, Swanson K, Li Z, Leskovec J. Toward universal cell embeddings: integrating single-cell RNA-seq datasets across species with SATURN. Nat Methods. 2024;21:1492-1500. doi:10.1038/s41592-024-02191-z.
9. Rosen Y, Roohani Y, Agrawal A, Samotorcan L, Tabula Sapiens Consortium, Quake SR, et al. Universal cell embedding provides a foundation model for cell biology. Nature. 2026. doi:10.1038/s41586-026-10689-z.
10. Zhai J, et al. scPlant: a versatile framework for single-cell transcriptomic data analysis in plants. Plant Commun. 2023;4:100477.
11. Chen H, et al. scPlantDB: a comprehensive database for exploring cell types and markers of plant cell atlases. Nucleic Acids Res. 2024;52:D1629-D1638.
12. Cao G, Chao H, Zheng W, Lan Y, Lu K, Wang Y, et al. Harnessing the foundation model for exploration of single-cell expression atlases in plants. Genomics Proteomics Bioinformatics. 2025:qzaf024. doi:10.1093/gpbjnl/qzaf024.
13. Lu C, Immadi MS, Chan YO, Dhakal S, Xu D, Libault M, Joshi T. scPlantAnnotate: an accurate and robust transformer-based model for plant cell type annotation. J Adv Res. 2026;S2090-1232(26)00060-3. doi:10.1016/j.jare.2026.01.035.
14. National Center for Biotechnology Information. Gene Expression Omnibus accession GSE152766. https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152766. Accessed 3 Aug 2026.
15. National Center for Biotechnology Information. Gene Expression Omnibus accession GSE270140. https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270140. Accessed 3 Aug 2026.
16. National Center for Biotechnology Information. Gene Expression Omnibus accession GSE270342. https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270342. Accessed 3 Aug 2026.
17. National Center for Biotechnology Information. Gene Expression Omnibus accession GSE297576. https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297576. Accessed 3 Aug 2026.
18. Hu EJ, Shen Y, Wallis P, Allen-Zhu Z, Li Y, Wang S, et al. LoRA: low-rank adaptation of large language models. In: International Conference on Learning Representations; 2022.
19. SnowLotus-CellFM Consortium. Plant-CellFM software and evidence repository. https://github.com/ahvsjags/SnowLotus-CellFM. Accessed 3 Aug 2026.
