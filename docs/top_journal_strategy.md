# SnowLotus-CellFM 顶刊级研发方案

## 一句话定位

SnowLotus-CellFM 不是普通细胞注释器，而是面向植物跨物种单细胞图谱的基础模型，并以天山雪莲（Saussurea involucrata）作为高寒药用植物验证场景。核心科学问题是：

1. 植物细胞类型的跨物种共性表示能否被基础模型稳定学习。
2. 天山雪莲的组织细胞组成、次生代谢和高寒/低压适应是否存在可解释的细胞类型特异程序。
3. 模型能否优于 marker-based、Seurat label transfer、scPlantLLM、scPlantAnnotate 等基线，并产出可实验验证的新基因/细胞状态发现。

## 已核对的领域坐标

- scPlantDB 汇总大量植物单细胞数据，是公开植物 scRNA 数据发现入口。
- scPlantLLM 是植物单细胞基础模型参照，强调 masked language modeling、zero-shot、batch integration、cell type annotation 和 GRN inference。
- scPlantAnnotate 是 transformer 注释基线，强调 Arabidopsis、maize、rice、soybean 以及 leave-one-dataset-out 评估。
- Brassicaceae multi-species root atlas（GSE268881）适合作为跨物种 root cell-type transfer 和 stress adaptation 外部验证。
- Rice soil-stress root atlas（GSE251706）适合作为环境胁迫、根部细胞状态和空间验证对照。
- Rice root tip atlas（GSE146034）适合作为体量适中的单子叶根尖验证数据集。
- Arabidopsis life-cycle/spatial atlas（GSE226097）适合作为跨器官和空间 marker 验证目标。
- Wheat root atlas（GSE270342）和 Arabidopsis secondary root atlas（GSE270140）适合作为小体量、标准 10x H5 的快速增量验证集。

## 数据策略

### 公开预训练语料

优先纳入：

1. scPlantLLM benchmark subset：用于 smoke-to-public-data 过渡。
2. GSE268881 Brassicaceae root atlas：跨物种 root/stress benchmark。
3. GSE152766 Arabidopsis root atlas：经典 Arabidopsis root 注释 benchmark。
4. GSE270342 wheat soil-grown root atlas：单子叶 cereal transfer。
5. GSE270140 Arabidopsis secondary root atlas：独立 Arabidopsis developmental root validation。
6. GSE146034 rice root tip atlas：紧凑型 monocot root-tip validation。
7. GSE251706 rice soil-stress root atlas：stress root biology comparator。
8. GSE226097 Arabidopsis life-cycle/spatial atlas：空间和跨器官验证候选，目前先作为 metadata/策略位点。

所有公开数据进入同一层级：

- raw files: `data/public/<accession>_*`
- converted sparse NPZ: `data/public/<accession>_npz`
- manifest: `data/corpus_manifest.<accession>.tsv`
- available corpus: `data/plant_foundation_corpus_public_mlm_available.h5ad`
- full corpus: `data/plant_foundation_corpus_public_mlm.h5ad`

### 天山雪莲核心数据

真正支撑顶刊主张的硬条件仍是：

- `data/saussurea_involucrata.h5ad`
- 推荐组织：叶、根、茎、花序、愈伤/分生组织；若目标是高寒适应，加入常压、低压、低温、强 UV 或低氧处理。
- 必需 obs 字段：`cell_type`, `cell_type_coarse`, `sample_id`, `species`, `tissue`, `batch`, `cell_id`。
- 最低实验版：每个组织/处理 2-3 个 biological replicate；每个样本 5k-20k cells/nuclei。

### 同源基因与标签本体

- 用 OrthoFinder/Ensembl Plants/PLAZA 构建 `source_gene -> target_gene`。
- 训练 token 优先采用 orthogroup 或一对一同源基因，避免跨物种 gene ID 不可比。
- 标签采用两层体系：粗类 `dermal/vascular/ground/meristem/reproductive/stress_response/secretory`，细类保留原始注释。

## 模型路线

当前已实现：

- gene set Transformer，适合每个细胞 top expressed genes。
- gene token + 表达量离散桶 + 连续表达投影。
- species/tissue embedding。
- fine/coarse 层级注释头。
- masked gene/value reconstruction。
- full/head/last_n/LoRA 微调。
- strict split audit、centroid baseline、marker candidate mining。

下一轮增强：

1. ortholog-aware embedding：同源组共享 embedding，物种特异 paralog 加 residual adapter。
2. contrastive alignment：同一粗类跨物种拉近，不同粗类推远。
3. leave-species-out / leave-dataset-out 训练器：对标 scPlantAnnotate 严格评估。
4. marker interpretability：attention/gradient/one-vs-rest marker ranking 与 scPlantDB marker、实验 marker 对照。
5. GRN candidate mining：用细胞类型特异 embedding 与 mask perturbation 找调控候选基因。

## 训练路线

1. Smoke: `configs/smoke.yaml`。
2. Base corpus: `snowcell build-corpus --manifest data/corpus_manifest.tsv --output data/plant_foundation_corpus.h5ad`。
3. Foundation pretrain: `configs/foundation_5090_pretrain.yaml`。
4. Available public MLM expansion: `configs/foundation_5090_mlm_public_available_expansion.yaml`。
5. Full public MLM expansion: `configs/foundation_5090_mlm_public_expansion.yaml`。
6. 天山雪莲 LoRA 微调: `configs/saussurea_lora_finetune.yaml`。
7. Ablation: 去 ortholog、去 species/tissue embedding、去 MLM、去 hierarchy loss。
8. Benchmark: Seurat label transfer、Scanpy ingest、scPlantLLM、scPlantAnnotate、marker rules。

严格拆分使用 `data.split_strategy=explicit_leaveout`，通过 `scripts/create_leaveout_config.py` 派生 leave-dataset-out、leave-species-out 和 snow lotus holdout 配置。

## 顶刊级结果矩阵

主图至少需要：

1. 数据与模型总览：物种、组织、细胞数、模型架构、训练任务。
2. 跨物种 embedding：按细胞类型聚类，而不是按物种/批次聚类。
3. 严格 benchmark：random split、leave-dataset-out、leave-species-out、snow lotus holdout。
4. 天山雪莲细胞图谱：组织 UMAP、粗/细类注释、marker heatmap。
5. 高寒/药用机制：黄酮、萜类、抗氧化、低压响应基因在细胞类型中的富集。
6. 可解释模型发现：模型 marker 与公开 marker、差异表达、同源基因证据交叉验证。
7. 实验验证：RNA in situ、smFISH、qPCR 或 reporter，至少验证 3-5 个细胞类型特异 marker 或调控候选。

## 服务器执行

安装依赖：

```bash
cd /mnt/snowlotus_cellfm
bash scripts/install_server_dependencies.sh
```

后台全流程：

```bash
cd /mnt/snowlotus_cellfm
tmux new -s snowlotus_top
bash scripts/top_journal_pipeline.sh 2>&1 | tee logs/top_journal_pipeline.log
```

公开数据和 public MLM 自动接力：

```bash
cd /mnt/snowlotus_cellfm
bash scripts/ensure_public_data_jobs.sh
bash scripts/queue_public_mlm_expansion.sh
```

## 当前硬缺口

1. 缺真实天山雪莲 scRNA/snRNA 数据：`data/saussurea_involucrata.h5ad`。
2. 缺雪莲基因注释和高质量同源基因映射。
3. 公开数据还在下载/转换，full corpus 尚未完全闭合。
4. 与 scPlantLLM/scPlantAnnotate 的公平外部 benchmark 尚未完成。
5. 纯算法结果不足以支撑雪莲生物学顶刊故事，仍需要独立实验或独立数据验证。
