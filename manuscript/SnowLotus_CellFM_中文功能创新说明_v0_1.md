# SnowLotus-CellFM 天山雪莲与植物单细胞注释大模型功能创新说明

生成时间：2026-07-26 15:25 Asia/Shanghai

GitHub 仓库：https://github.com/ahvsjags/SnowLotus-CellFM

GitHub Release tag：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3

当前同步 commit：088cd8a6b6fce2eadcfff01dbd3e6ecd402c5cf6

## 一句话定位

SnowLotus-CellFM 是一个面向植物跨物种单细胞/单核表达数据的注释与表征基础模型工程。它不是单个分类脚本，而是覆盖公开数据发现、矩阵审计、语料构建、Transformer 训练、层级注释、外部 benchmark、模型发布与远程持续训练的一套完整系统；天山雪莲被定位为高寒药用植物的目标迁移与实验验证场景。

## 核心功能创新矩阵

| 功能创新 | 解决的问题 | 当前实现证据 |
| --- | --- | --- |
| 植物单细胞专用基础模型 | 不是把通用单细胞模型硬套到植物，而是围绕植物跨物种、跨组织、跨数据格式的表达矩阵重新设计训练与审计流程。 | 已实现 `snowcell train/build-corpus/predict`、公开语料构建、模型 checkpoint 与 SHA256 冻结。 |
| gene set Transformer 输入范式 | 每个细胞以高表达基因集合、表达值分桶、连续表达投影共同表示，天然适合不同测序平台和不同物种的 gene set 表达结构。 | 模型含 gene token、value bins、value projection、species/tissue embedding 和层级注释头。 |
| 层级注释输出 | 同时预测细胞细类与粗类，降低跨数据集标签粒度不一致造成的评估噪声。 | 训练中包含 fine/coarse 分类、hierarchy loss、macro-F1/accuracy 评估。 |
| 自监督与监督混合训练 | 用 masked gene modelling 学习植物表达结构，用标签任务保持可解释注释能力。 | 当前公开 MLM 长训 48,558,596 trainable parameters，epoch 1 已出 eval loss 9.1896。 |
| 天山雪莲转移框架 | 诚实区分“已有公开植物训练语料”和“尚待获得的雪莲单细胞矩阵”，把雪莲定位为高寒药用植物目标迁移场景。 | 已写入 Saussurea 数据需求、h5ad contract、同源基因和 marker 验证路线。 |

## 全链路功能模块

| 模块 | 代表组件 | 功能说明 |
| --- | --- | --- |
| 数据发现 | NCBI/GEO/scPlantDB/scPlantLLM | 发现、筛选、下载候选公开植物单细胞/单核表达数据。 |
| 数据审计 | manifest + integrity audit | 逐行检查矩阵是否存在、可读、是否具备训练所需 obs 字段。 |
| 语料构建 | H5AD/NPZ/10x/Seurat RDS 转换 | 合并成公开 plant foundation corpus，记录可用与不可用边界。 |
| 模型训练 | hybrid/pretrain/fine-tune | 支持 CUDA、bf16、gradient checkpointing、LoRA/last-n/head-only 等模式。 |
| 模型应用 | predict/annotation bundle/embedding export | 输出细胞类型、置信度、embedding、预测 CSV 和审计报告。 |
| 对照评估 | centroid baseline、Seurat、scPlantLLM、scPlantAnnotate | 已搭好外部 benchmark 输入与审计，scPlantAnnotate 需要授权后执行。 |
| 发布交付 | GitHub + editor zip + SHA256 | 源码、模型说明、状态页、远程审计、校验和统一归档。 |

## 当前可展示证据

| 证据类别 | 当前状态 |
| --- | --- |
| 远程执行 | SSH 新端口已恢复，别名 `matpool-px1-jcy` 指向 `px2-jcy.matpool.com:29153`。 |
| 硬件状态 | 替换服务器实测为 NVIDIA GeForce RTX 4090 24GB；CUDA 可用，GPU 长训正在运行。 |
| 代码链路 | 远程 pytest 已通过核心测试、on-disk corpus builder 测试、端口探测测试。 |
| 公开语料 | 恢复后公开 MLM corpus 为 71,330 cells x 49,106 genes，含 scPlantLLM SRP169576 与 scPlantDB SRP169576。 |
| 真实训练 | scPlantDB smoke train 已完成：fine accuracy 0.5991，fine macro-F1 0.5908，coarse accuracy 0.5993。 |
| 长训状态 | 当前 public MLM run 已输出 epoch 1：train loss 9.4579，eval loss 9.1896，184 个 validation batches。 |
| 模型资产 | 冻结 annotation checkpoint 与 embedding checkpoint 均有 SHA256；完整模型包本地与远程一致。 |
| GitHub 同步 | 仓库 main 与 editor-v0.3 tag 已同步到 commit 088cd8a6b6fce2eadcfff01dbd3e6ecd402c5cf6。 |

## 可写入稿件的创新点

| 编号 | 创新点 | 可写法 |
| --- | --- | --- |
| 创新 1 | 把“植物单细胞注释”从脚本级流程升级为基础模型工程 | 不仅能训练，还能构建 corpus、导出预测、生成数据卡、审计矩阵、维护模型 release。 |
| 创新 2 | 数据可用性审计前置 | 在训练前明确哪些 GEO/scPlantDB 数据可读、哪些只是元数据或不兼容，避免论文中虚增数据规模。 |
| 创新 3 | 跨物种表达表示 | 通过 species/tissue embedding、同源基因路线和 gene set Transformer，为 Arabidopsis/rice/maize/wheat/tomato 等跨物种迁移预留机制。 |
| 创新 4 | 层级标签鲁棒性 | 细类和粗类双头减少不同数据集注释体系不一致带来的泛化问题。 |
| 创新 5 | 面向雪莲的可落地转化 | 当前不伪造雪莲单细胞结果，而是准备好 h5ad contract、同源映射、marker 发现、LoRA 微调和实验验证清单。 |
| 创新 6 | 持续训练与可审计交付并行 | 编辑可先拿到固定版本，同时服务器后台继续训练；每个版本通过 SHA256、状态页和远程审计追踪。 |

## 当前边界与处理方式

| 边界/风险 | 事实 | 处理方式 |
| --- | --- | --- |
| 雪莲公开单细胞矩阵 | 当前未确认有可复用公开 Snow Lotus scRNA/snRNA matrix。 | 不把雪莲写成已完成 atlas；定位为目标迁移与实验验证框架。 |
| 外部强基线 | scPlantAnnotate 等工具需要授权或特定环境。 | 保留 authenticated benchmark 脚本与输入包，获得授权后补齐指标。 |
| 新服务器硬件 | 用户原期望 5090，但替换端口当前实测为 4090 24GB。 | 状态页已改为实测硬件，不再沿用旧服务器表述。 |
| 公开数据迁移 | 旧服务器部分 GEO 矩阵未完全迁入新机器。 | 已恢复核心公共语料，并继续修复 manifest ready 判定和数据队列。 |

## 可以直接对外说的结论

SnowLotus-CellFM 已经从方案推进到可运行、可训练、可审计、可交付的植物单细胞基础模型工程。当前版本足以展示功能创新和工程完成度；后续顶刊级强化重点是更大公开语料、强外部 benchmark 和真实雪莲单细胞矩阵接入。
