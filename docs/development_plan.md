# 天山雪莲与植物单细胞注释大模型方案

## 目标

构建 SnowLotus-CellFM：面向天山雪莲（Saussurea involucrata）和泛植物单细胞数据的注释基础模型。模型输入为单细胞表达矩阵，输出细胞粗类、细类、置信度和细胞嵌入，支持从多植物数据预训练、在天山雪莲数据上微调，以及对新样本批量注释。

## 数据路线

1. 天山雪莲自有数据：根、茎、叶、花、胁迫处理、发育阶段等 `.h5ad` 或 `.npz` 表达矩阵。
2. 泛植物参考数据：Arabidopsis、rice、maize、tomato、poplar 等公开 scRNA/snRNA 数据。
3. 基因命名统一：优先映射到正交基因或 OrthoFinder/EnsemblPlants 同源簇，降低跨物种 gene ID 不一致带来的迁移损失。
4. 标签层级：粗类如 dermal、vascular、ground、meristem、reproductive、stress_response；细类保留数据集原始注释并维护 `cell_type -> cell_type_coarse` 映射。
5. 防泄漏拆分：按 `sample_id/donor/batch` 分 train/validation/test，避免同一样本细胞同时出现在训练与测试中。

## 模型路线

当前实现采用无位置编码的基因集合 Transformer：

- gene token embedding：基因或正交基因 token。
- value embedding + value projection：表达量离散桶与连续投影共同表示表达强度。
- species/tissue embedding：物种和组织协变量，便于跨物种训练和特定组织泛化。
- set self-attention：不依赖输入顺序，适合 top expressed genes 集合。
- 多任务头：细胞细类分类、粗类分类、masked gene/value 重建。
- 微调方式：full、head-only、last-n-layers、LoRA。

## 训练阶段

1. Smoke test：合成数据验证代码、checkpoint、预测导出链路。
2. 天山雪莲监督基线：只用已有标注训练 `stage: supervised`，获得首版注释器。
3. 泛植物自监督预训练：用未标注植物单细胞数据训练 `stage: pretrain`，学习跨组织和跨物种表达结构。
4. 混合训练：用天山雪莲和公开标注数据训练 `stage: hybrid`，联合优化注释与 masked reconstruction。
5. 领域微调：用天山雪莲关键组织/处理条件做 LoRA 或 last-n 微调，减少小样本过拟合。

## RTX 5090 起步设置

推荐从 `configs/rtx5090_base.yaml` 开始：

- `max_genes: 1024`
- `d_model: 512`
- `n_layers: 12`
- `batch_size: 24`
- `gradient_accumulation_steps: 4`
- `mixed_precision: bf16`
- `gradient_checkpointing: true`

如果显存充足，可逐步升到 `d_model: 768, n_layers: 16, max_genes: 1536`。如果显存不足，优先降低 `batch_size`，再降低 `max_genes`。

## 评估指标

- 细胞细类：accuracy、macro-F1、per-class F1。
- 粗类：accuracy、macro-F1。
- 层级一致性：细类预测映射到粗类后是否与粗类头一致。
- 泛化：留组织、留样本、留物种测试。
- 生物学有效性：marker gene 富集、UMAP 嵌入分群、已知组织 marker 的表达一致性。

## 数据格式

`.h5ad` 需要：

- `adata.X` 或指定 `layer`：非负 counts/表达量。
- `adata.var_names`：基因 ID。
- `adata.obs["cell_type"]`：细胞细类标签，监督/混合训练需要。
- `adata.obs["cell_type_coarse"]`：粗类标签，监督/混合训练需要。
- `adata.obs["sample_id"]`：样本、植株、donor 或 batch 级别拆分键。
- 可选：`species`、`tissue`、`batch`、`cell_id`。

正交映射 TSV 默认列：

```text
source_gene	target_gene	confidence	evidence
SaussureaGene001	ORTHO_000001	0.92	orthofinder
```

## 运行流程

```bash
python -m pip install -e ".[singlecell,dev]"
snowcell make-demo --output data/demo.npz
snowcell train --config configs/smoke.yaml
snowcell predict \
  --checkpoint outputs/smoke/best.pt \
  --data data/demo.npz \
  --output outputs/smoke/predictions.csv
```

真实数据训练：

```bash
snowcell train --config configs/rtx5090_base.yaml --device cuda
```

新样本注释：

```bash
snowcell predict \
  --checkpoint outputs/rtx5090_base/best.pt \
  --data data/new_saussurea_sample.h5ad \
  --output outputs/new_saussurea_predictions.csv \
  --device cuda
```

## 近期里程碑

1. 跑通 smoke test 并保存 `outputs/smoke/best.pt`。
2. 整理第一批天山雪莲 `.h5ad`，统一 obs 字段。
3. 生成正交基因映射表，确认映射率大于 60%。
4. 训练天山雪莲监督基线，查看低 F1 类别。
5. 汇入公开植物数据做 hybrid/pretrain。
6. 输出模型卡、标签本体、marker gene 报告和预测 CSV。
