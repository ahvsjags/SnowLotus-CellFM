# SnowLotus-CellFM 已完成工作汇总（校稿版）

生成时间：2026-07-27 01:03 Asia/Shanghai

GitHub 仓库：https://github.com/ahvsjags/SnowLotus-CellFM

Release 标签：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3

当前 GitHub 状态：`editor-v0.3 tag points to the latest GitHub commit`

本文件只整理已经完成、可供编辑或合作者校稿的内容；仍在下载、训练、授权 benchmark 或远程端口恢复中的事项，均放在边界与待补强中，不作为已完成结果表述。

## 一句话定位

SnowLotus-CellFM 是一个面向植物跨物种单细胞/单核表达数据的注释与表征基础模型工程。当前版本已经完成从公开数据发现、矩阵审计、语料构建、Transformer 训练、层级注释、外部 benchmark 准备、模型冻结、GitHub 发布到编辑提交包整理的一条可复现链路；天山雪莲被明确定位为高寒药用植物的目标迁移与后续实验验证场景，而不是夸大为已经完成的雪莲单细胞图谱。

## 已完成且可校稿的核心结论

- 项目已经形成可运行代码仓库、训练脚本、数据审计脚本、模型 checkpoint、投稿说明和一键提交包。
- 当前可展示的模型资产包括冻结 annotation checkpoint 与 embedding checkpoint，并有 SHA256 校验、模型卡、release manifest 和编辑包记录。
- 公开植物单细胞数据链路已经能处理 H5AD、10x H5、Matrix Market、Seurat RDS、GEO RAW tar 等多种格式，并能区分可用矩阵、缺失矩阵和不兼容记录。
- 模型路线采用植物表达 gene-token / expression-value / species-tissue metadata 的 Transformer masked modelling，并保留 fine/coarse 层级注释头。
- 天山雪莲部分当前应写作“目标物种迁移框架与数据缺口已定义”，不应写作“雪莲单细胞图谱已经完成”。

## 可引用证据

- 模型规模：恢复服务器公开 MLM 长训记录为 48,558,596 trainable parameters。
- Embedding checkpoint：v0.3 epoch 7，eval loss 7.1917，SHA256 `00c1b0a1049c441585ecd7ee03e81d05704bd93100c692cc06f7bdc90f2c034a`。
- Annotation checkpoint：release evidence 记录 macro-F1 0.8121，SHA256 `ebc95ca58ffede9c9bfd2bb4f056c452b7dc43a0f799cbaf88ff77e4e9d3a4ef`。
- 恢复服务器训练：2026-07-26 审计时，RTX 4090 24GB 上 public MLM run 已到 epoch 6，eval loss 8.6741，GPU 接近满载。
- 编辑稿件记录当前审计包包含 70 manifest、240 readable matrix files、4,544,570 referenced cells。
- 本地已有 `SnowLotus-CellFM_editor-v0.3_submit-now.zip`、中文功能创新说明、稿件草稿、cover note、README 和模型校验信息。

## 建议摘要

我们已经完成 SnowLotus-CellFM 的第一版可复现研究发布。该项目面向植物单细胞和单核转录组数据，建立了从公开数据发现、矩阵级审计、语料构建、Transformer masked modelling、层级细胞类型注释、模型冻结、外部 benchmark 准备到 GitHub/编辑包交付的完整链路。当前版本冻结了可供审阅的 annotation 与 embedding checkpoint，保留 SHA256 校验和模型卡，并将天山雪莲明确作为目标物种迁移场景处理。现阶段不夸大为已经完成雪莲单细胞图谱，而是提供一个可立即审阅、可继续训练、可在获得雪莲单细胞矩阵后快速适配的植物单细胞基础模型框架。

## 边界

- 当前审计未确认可复用的公开 Snow Lotus scRNA/snRNA cell-by-gene matrix。
- 2026-07-27 当前 Matpool 端口返回 Connection refused，服务器端口需恢复或更换；这不影响本地提交包和 GitHub 已完成内容。
- scPlantAnnotate 需要授权或结果导出，当前不能写成完成指标。
- GitHub 给编辑/审稿人使用前，需要添加访问权限或切换为 public。
