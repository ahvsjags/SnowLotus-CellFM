# Plant-CellFM v9 当前开发与提交方案

## 当前目标

Plant-CellFM v9 的提交目标是构建一套面向植物单细胞和单核表达矩阵的通用基础模型，而不是单独服务天山雪莲的物种专用工具。当前冻结版采用“植物通用基础模型 + 全植物 adapter 层 + 目标物种接入契约”的结构：公开植物数据用于训练和评估共享模型，已知植物通过 adapter registry 接入，新命名植物通过运行时 adapter materialization 接入，天山雪莲作为目标物种适配入口之一进入同一系统。

当前提交版以 NVIDIA GeForce RTX 4090 训练和服务环境为准。早期文件名或历史脚本中保留的 `5090` 字样只代表项目早期规划和路径命名，不作为本版硬件声明。

## 数据路线

1. 公开植物单细胞和单核数据作为主语料，覆盖拟南芥、水稻、番茄、玉米、棉花、茶树、杨树、豆科植物等多类植物来源。
2. v9 冻结语料包含 56 条 manifest 记录、29 个公开数据集、21 个植物物种和约 1378 万细胞。
3. 每条数据记录保留数据集编号、物种、组织、样本字段、标签字段、转换路径和校验信息，方便编辑和审稿人复核。
4. 基因空间通过 shared checkpoint vocabulary、exact-gene transfer 和 optional ortholog TSV 入口统一处理，避免模型被限定在单一物种基因命名体系。
5. 天山雪莲当前以 genome/bulk transcriptome 支持材料、h5ad contract 和 ortholog-map 接口形式接入，不写作已完成的天山雪莲单细胞图谱。

## 模型路线

当前实现为植物表达 Transformer + LoRA 适配框架：

- gene token embedding：表示输入细胞中的基因身份。
- expression value embedding/projection：同时处理表达值离散桶和连续表达强度。
- species/tissue metadata：保留物种和组织信息，支持跨数据集迁移。
- transformer encoder：学习细胞级表达上下文表示。
- hierarchical annotation heads：输出 fine/coarse 层级细胞状态。
- adapter registry：保存 24 个已知 adapter，并支持新植物名称在推理时生成 adapter 记录。
- ortholog transfer contract：为非模式植物、药用植物和目标物种接入保留同源映射入口。

## 训练与冻结

v9 候选模型在 RTX 4090 上完成六轮 hybrid 训练，联合优化 masked-expression modelling 和监督层级注释目标。冻结 checkpoint 为 `SnowLotus-CellFM-v9-lora-4090-best.pt`，服务端路径为 `/root/snowlotus_cellfm_v9_lora_shared_4090/best.pt`。冻结包保留 resolved config、训练日志、history、benchmark JSON、模型卡、数据卡、SHA256 校验和服务脚本。

## 评估口径

当前提交版采用三类主评估：

| 协议 | v9 all-cell accuracy | coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |

新增 STC 物种迁移校准层在同一 frozen runtime embedding 和同一 leave-species split 上实现真实 classifier-side 提升：`knn_cosine_k9` 将 all-cell accuracy 从 centroid 0.2364 提高到 0.3010，known-label accuracy 从 0.4228 提高到 0.5384，known-label macro-F1 从 0.1922 提高到 0.2663。coverage 保持 0.5590，因此该结果作为真实校准增益报告，不替代 frozen v9 主 benchmark，也不写成全植物满覆盖高精度。

论文主张以开放集口径为准：all-cell accuracy 把训练折未见标签计为错误，coverage 说明测试集中可被训练标签覆盖的比例，known-label 指标只解释可评估标签子集。当前稳妥结论是 Plant-CellFM v9 在同一 shared-gene benchmark 上优于 v3 extended baseline，并提供可复现的植物通用注释框架；不把内部 held-out accuracy 写成所有植物物种的无条件精度。

## 横向对照与生物学案例

- v3 extended baseline：三类交叉组协议均已完成。
- Classical centroid baseline：group-random 和 SRP169576 sample-holdout 已完成。
- Seurat label transfer：已完成，fine accuracy 0.2207，macro-F1 0.0603。
- scPlantLLM：输入和预处理路径已审计，正式数值需官方 checkout 和权重在本地可执行后再冻结。
- scPlantAnnotate：官方 web/API 路径已审计，匿名脚本化 benchmark 需认证后执行。
- Arabidopsis root case：已形成 260 条 marker-candidate 记录，覆盖 13 个细胞状态和 10 类根系身份标签。

## 当前提交包

编辑和审稿人应优先查看：

- `SUBMISSION_INDEX_v9.md`
- `README.md`
- `release_metadata/plant_cellfm_v9_model_card.md`
- `release_metadata/v9_submission_stability_audit.md`
- `release_metadata/external_benchmark_panel_v9.md`
- `release_metadata/plant_biology_case_study_v9.md`
- `docs/publication_readiness_v9.md`
- `manuscript/Plant_CellFM_v9_完整主文_稳健方法版_v1.md`

旧版 `SnowLotus_CellFM_*v0_*` 文稿、早期 `rtx5090` 配置和历史 pipeline 脚本保留为开发记录，不代表当前 v9 冻结提交口径。
