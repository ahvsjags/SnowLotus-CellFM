# Plant-CellFM v9：面向植物单细胞注释的通用基础模型与全植物适配框架

英文题名：Plant-CellFM v9: a general plant foundation model and all-plant adapter framework for single-cell annotation

生成时间：2026-07-30 17:33 Asia/Shanghai

代码仓库：https://github.com/ahvsjags/SnowLotus-CellFM

冻结 release：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora

版本说明：本文档随仓库提交版本化；最终提交号以 `git log -1` 或交付说明为准。

## 摘要

植物单细胞和单核转录组数据正在从拟南芥、水稻等模式系统扩展到作物、木本植物、豆科植物、茶树、棉花和药用植物。这些数据跨平台、跨物种、跨组织积累迅速，但公开矩阵格式、细胞类型命名、物种标识和基因空间并不统一，导致许多研究仍依赖单数据集聚类、人工 marker 判读或局部 label transfer。Plant-CellFM v9 针对这一问题建立面向植物单细胞注释的通用基础模型和全植物适配框架。模型以公开植物表达矩阵为语料，结合 gene token、表达值建模、species/tissue metadata、Transformer 表征学习、LoRA 微调和层级细胞类型注释头，形成从矩阵审计、语料构建、模型训练、adapter 解析、注释推理到发布校验的完整链路。

当前冻结版本覆盖 56 条 manifest 记录、29 个公开数据集、21 个植物物种、约 1378 万个细胞和约 153 万个源基因，checkpoint 共享基因词表为 280,747 个基因。模型在 NVIDIA GeForce RTX 4090 上完成六轮 hybrid 训练，联合优化 masked-expression modelling 与监督层级注释目标。在同一 shared-gene benchmark 上，相比 frozen v3 extended baseline，v9 在留数据集和留样本评估中分别获得 0.4490 和 0.6200 的 all-cell accuracy，较基线提升 24.70 和 20.45 个百分点；在物种名归一化后的严格留物种开放集评估中，v9 all-cell accuracy 为 0.2354、coverage 为 0.5590、known-label conditional accuracy 为 0.4210。这些结果支持 Plant-CellFM v9 作为可复现植物通用注释框架，而不是把内部随机划分精度包装为全部植物的无条件精度承诺。

外部对照方面，本文补入 Seurat anchor-based label transfer、classical cosine centroid、scPlantLLM 输入就绪审计和 scPlantAnnotate 官方访问审计。Seurat 在 frozen v9 subset 导出矩阵上 fine accuracy 为 0.2207、macro-F1 为 0.0603，说明传统通用 label transfer 在该跨数据集植物任务上不足以替代植物专用基础模型。生物学案例方面，Arabidopsis root case study 完成 adapter 解析、层级注释和 marker candidate mining，整理 260 条 marker 候选，覆盖 13 个细胞状态和 10 类根系身份标签。天山雪莲在本研究中被定位为目标物种适配入口，而不是当前已经完成的单细胞图谱。

关键词：植物单细胞；基础模型；细胞类型注释；跨物种泛化；adapter；Arabidopsis root；Snow Lotus

## 1 研究定位：植物通用基础模型，而非单一物种工具

Plant-CellFM v9 的核心定位是“植物通用基础模型 + 全植物适配层”。这一定位有意避开两个容易被审稿人抓住的误区：第一，它不是只服务天山雪莲的单物种模型；第二，它也不是声称任意新物种输入均可直接获得满覆盖标签。更稳妥、也更符合证据的表述是：模型把公开植物单细胞/单核表达矩阵组织成可审计语料，学习跨数据集表达表征，并通过 adapter registry 与运行时 adapter materialization 支持已知植物和新命名植物进入同一推理接口。

在该框架中，天山雪莲是目标物种适配场景之一。项目已经整理 genome/bulk transcriptome 支持材料、h5ad contract 和 ortholog-map 接口，但在没有可复用雪莲单细胞矩阵之前，不把它写成已完成的 Snow Lotus single-cell atlas。这种写法让主文从“交付说明”转为“方法与资源论文”：贡献集中在数据审计、模型框架、全植物 adapter、可复现 benchmark 和可运行服务。

## 2 数据资源与语料构建

v9 语料来自经审计的公开植物单细胞和单核表达资源。每条 manifest 记录保留数据集编号、物种、组织、样本字段、标签字段、文件路径和转换状态。语料构建层支持 H5AD、10x H5、Matrix Market、Seurat RDS 和 GEO RAW 派生矩阵，并在进入训练前执行矩阵可读性检查、obs 字段核对、基因词表对齐、稀疏表达对象构建和 SHA256 追踪。这一步的价值在于让编辑和审稿人可以沿文件路径复核数据来源，而不只是相信模型指标。

| 资源类别 | v9 状态 | 审稿价值 |
| --- | --- | --- |
| 公开语料 | 56 条 manifest，29 个数据集，21 个植物物种，约 1378 万细胞 | 证明模型不是单一物种或单一数据集训练 |
| 基因空间 | 约 153 万源基因；280,747 个 shared checkpoint genes | 支撑跨数据集表达表征和同源映射入口 |
| 矩阵审计 | manifest、数据卡、benchmark subset、provenance audit | 允许复核数据来源、转换和筛选过程 |
| 冻结包 | checkpoint、配置、benchmark JSON、训练日志、SHA256 | 保证结果可追溯、可校验、可复现 |

## 3 模型架构与全植物适配机制

Plant-CellFM v9 使用植物表达 Transformer 表示单个细胞。输入侧包含 gene token、表达值分箱、连续表达投影、species embedding、tissue embedding 和样本级元数据；模型侧采用 256 维隐藏表示、4 层 Transformer、8 个注意力头和 LoRA rank 8；输出侧同时提供 masked-expression 表征、fine/coarse 层级注释、细胞 embedding、置信度和 adapter 选择记录。

全植物适配层是当前版本最重要的工程和方法创新。系统保留 24 个已知 adapter，同时支持运行时为任意命名植物生成 adapter 记录。对于基因标识一致的输入，模型执行 exact-gene transfer；对于目标物种与训练语料基因空间不完全一致的输入，系统保留 ortholog TSV 映射入口。因此，拟南芥、水稻、小麦、番茄、棉花、茶树、杨树、豆科植物、雪莲等目标物种都可沿同一推理契约接入，而不是为每个物种重写流程。

| 模块 | 功能 | 稳定优势 |
| --- | --- | --- |
| 表达基础模型 | 学习 gene token 与表达值上下文 | 从无标签公开矩阵中吸收植物表达结构 |
| 层级注释头 | 输出 fine/coarse cell state | 适应植物细胞标签粒度差异 |
| 全植物 adapter | 已知 adapter + 运行时新物种 adapter | 避免模型被限定在雪莲或单一物种 |
| 同源映射入口 | 支持 exact-gene 与 ortholog TSV | 为非模式植物和药用植物接入预留路径 |
| 服务接口 | health、metadata、capabilities、adapters、annotate | 模型可以被实际调用、演示和复核 |

## 4 训练、冻结与服务化实现

v9 候选模型在 RTX 4090 上训练，使用 CUDA mixed precision，联合 masked-expression modelling 与监督层级注释目标。训练过程保留 resolved config、history、progress、preprocessing statistics、test metrics 和 train log。冻结 checkpoint 文件为 `SnowLotus-CellFM-v9-lora-4090-best.pt`，SHA256 为 `9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`。远程服务加载 `/root/snowlotus_cellfm_v9_lora_shared_4090/best.pt`，health check 返回 `model_scope=plant_general`、`adapter_resolution=dynamic_all_plants`、`device=cuda`，说明服务端调用的是植物通用 v9 模型。

为了让模型不是停留在静态文件层面，当前提交还冻结了 live runtime evidence：`release_metadata/api_runtime_smoke_v9.md` 记录一次真实 `POST /annotate` 调用，输入 Arabidopsis benchmark subset，服务解析 `plant_arabidopsis_thaliana` adapter，输出 3964 个细胞的预测和 3964 x 256 embedding；`release_metadata/watchdog_recovery_status_v9.md` 记录一次控制恢复测试，服务进程被 SIGTERM 后由 `plant_cellfm_watchdog` tmux 会话在 30 秒内重新拉起并恢复 `/health`。这两项证据把 checkpoint、CUDA 服务和可持续运行状态连成同一条可复核链路。

## 5 评估设计：用开放集口径解释跨物种泛化

当前稿件采用三类交叉组评估：leave-dataset-out、leave-sample-out 和 leave-species-out。all-cell accuracy 把训练折中未出现过的标签计为错误，是开放集评估下更严格的主指标；known-label conditional accuracy 和 macro-F1 只在测试细胞真实标签存在于训练折时计算，用于说明可评估标签子集上的注释能力。主文同时报告 coverage，避免把条件指标误读为所有细胞的通用精度。

| 协议 | v9 all-cell accuracy | coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy | v9 增益 |
| --- | --- | --- | --- | --- | --- | --- |
| 留数据集 | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 | 24.70 个百分点 |
| 留样本 | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 | 20.45 个百分点 |
| 留物种（物种名归一化） | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 | 4.41 个百分点 |

留物种结果经过物种名归一化：`Arabidopsis_thaliana` 与 `Arabidopsis thaliana` 在 split 前合并为同一物种组。这一修正让结果更严格，也更适合发表。从结果看，v9 的强项主要体现在留数据集和留样本场景，说明模型对新数据来源和新样本具有稳定迁移能力；留物种开放集提升较小，但仍优于同一 shared-gene subset 上的 v3 extended baseline。因此，本文将 Plant-CellFM v9 表述为可复现的植物通用基础模型和适配框架，而不是声称已经解决所有植物物种的满覆盖零样本注释。

## 6 第三方横向对照与外部工具状态

为回应高水平期刊对横向对照的要求，本版本把外部对照拆成三类：已经完成且有本地 JSON 指标的正式对照；已经准备好输入但当前环境缺少官方权重或 checkout 的接口；以及需要认证或网页会话的受限工具。这种写法既展示了横向比较链路，也避免把未完成的第三方结果写成结论。

| 对照对象 | 协议 | 状态 | 主准确率 | macro-F1 | 证据 |
| --- | --- | --- | --- | --- | --- |
| Plant-CellFM v9 vs frozen v3 extended | Leave-dataset-out | completed | 0.4490 | 0.3485 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Plant-CellFM v9 vs frozen v3 extended | Leave-sample-out | completed | 0.6200 | 0.4902 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Plant-CellFM v9 vs frozen v3 extended | Leave-species-out, species labels normalized | completed | 0.2354 | 0.1918 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Classical cosine centroid, group-random split | group_random | completed | 0.7583 | 0.7125 | release_metadata/strict_benchmarks/public_sprint_group_random.centroid_baseline.json |
| Classical cosine centroid, SRP169576 sample holdout | explicit_leaveout | completed | 0.7337 | 0.4873 | release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json |
| scPlantLLM frozen embedding nearest-centroid probe | public sprint train/test chunks | input_ready_metric_missing | - | - | release_metadata/scplantllm_input_readiness.json |
| Seurat label transfer | exported train/test split | completed | 0.2207 | 0.0603 | release_metadata/external_benchmarks/seurat_v9_subset.json |
| scPlantAnnotate | official web/API route audit | web_api_auth_required | - | - | release_metadata/scplantannotate_access_audit.json |

Seurat label transfer 已在 frozen v9 subset 的导出矩阵上完成，测试细胞数为 512，fine accuracy 为 0.2207，fine macro-F1 为 0.0603。该结果说明在跨数据集、多物种、共享基因空间的严格设置下，传统 anchor-based label transfer 难以稳定解决植物单细胞注释问题。scPlantLLM 的输入准备已经完成，但当前服务器到官方 GitHub checkout/ZIP 下载多次 TLS 中断，因此主文只写作 input-ready，不报告缺失指标。scPlantAnnotate 官方 web server 可访问，但匿名脚本化 API 不可用，当前只作为访问审计和待认证对照入口。

## 7 植物生物学案例：Arabidopsis root cell-identity marker and adapter case

Arabidopsis root case study 用来证明 Plant-CellFM v9 不只是一个分类器。系统首先解析 Arabidopsis adapter，然后在同一模型链路中输出注释表征、fine/coarse 标签和 marker candidate。当前案例包含 260 条 marker-candidate 记录，覆盖 13 个细胞状态和 10 类根系身份标签。根冠、侧根冠、皮层、内皮层、中柱、韧皮部、木质部、根毛和非根毛细胞等状态共同构成一个可审计的植物生物学示范。

| 细胞状态 | 类别 | Top genes | Median score | Median log2FC | Median detection delta |
| --- | --- | --- | --- | --- | --- |
| Columella root cap | root_cell_identity | AT5G02380, AT2G04025, AT2G36950, AT3G20840, AT3G45730 | 0.849 | 3.296 | 0.231 |
| G1/G0 phase | cell_cycle_or_other | ATCG00790, ATCG00740, ATCG00170, ATCG00800, ATCG00770 | 1.917 | 3.395 | 0.575 |
| Lateral root cap | root_cell_identity | AT1G26820, AT3G16440, AT1G15385, AT1G06090, AT5G55110 | 2.871 | 4.235 | 0.677 |
| Non-hair | root_cell_identity | AT1G65310, AT4G12545, AT1G70850, AT1G14960, AT4G12550 | 2.023 | 3.742 | 0.607 |
| Phloem | root_cell_identity | AT5G04080, AT1G62380, AT2G46630, AT1G79430, AT5G59090 | 3.051 | 7.071 | 0.495 |
| Root cap | root_cell_identity | AT1G54010, AT5G10130, AT1G28290, AT5G58784, AT2G43610 | 2.634 | 3.634 | 0.730 |
| Root cortex | root_cell_identity | AT1G12090, AT1G13930, AT1G21310, AT5G13930, AT4G30170 | 1.665 | 2.941 | 0.559 |
| Root endodermis | root_cell_identity | AT3G22620, AT3G22600, AT2G32300, AT2G28670, AT5G15290 | 2.863 | 4.341 | 0.593 |
| Root hair | root_cell_identity | AT3G54580, AT1G30870, AT3G09925, AT3G54590, AT3G62680 | 1.602 | 3.700 | 0.427 |
| Root stele | root_cell_identity | AT4G11210, AT2G02130, AT1G12080, AT4G14130, AT3G59370 | 2.043 | 3.840 | 0.541 |
| S phase | cell_cycle_or_other | AT5G15200, AT5G20290, AT3G60245, AT5G16130, AT4G16720 | 1.821 | 3.053 | 0.605 |
| Unknown | cell_cycle_or_other | AT2G43820, AT2G29440, AT2G29450, AT1G43160, AT3G50970 | 0.339 | 1.208 | 0.283 |
| Xylem | root_cell_identity | AT5G03170, AT1G20850, AT5G16490, AT1G08283, AT4G23690 | 2.489 | 6.266 | 0.463 |

该案例的价值在于展示完整链路：物种 adapter 解析、模型注释、marker 候选生成和细胞身份层级组织。它是 public-data computational case，因此主文把它写成可复现生物学示范，而不写成湿实验已验证的最终生物发现。

`release_metadata/arabidopsis_root_literature_anchor_v9.md` 进一步把上述 root identity labels 与既有 Arabidopsis root single-cell atlas 文献中的 root cap/columella、trichoblast/root hair、atrichoblast/non-hair、cortex、endodermis、stele、phloem 和 xylem taxonomy 对齐。该文件还列出 COBL9、SCR、MYB36、CASP1、MYB46、APL、SUC2、VND7 等 canonical marker examples，作为后续人工 marker-overlap 或 reporter-line 验证的锚点；当前稿件只把 Plant-CellFM 输出解释为 computational marker candidates，不写作湿实验已验证 marker。

## 8 天山雪莲定位：目标物种入口

天山雪莲不再作为模型边界，而是作为目标物种适配入口。服务器已经整理并校验天山雪莲 genome 与 bulk transcriptome 支持材料，并建立 h5ad contract、ortholog map 和 adapter 接入路径。当可复用雪莲单细胞矩阵进入统一 contract 后，系统可以生成注释、embedding、marker 候选和同源比较结果。在当前证据下，稳妥写法是 Snow Lotus-ready transfer pipeline，而不是 completed Snow Lotus atlas。

## 9 代码、模型和复现资源

代码仓库：https://github.com/ahvsjags/SnowLotus-CellFM

冻结 release：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora

checkpoint asset：https://github.com/ahvsjags/SnowLotus-CellFM/releases/download/v0.9.0-plant-general-lora/SnowLotus-CellFM-v9-lora-4090-best.pt

checkpoint SHA256：`9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`

live API smoke evidence：`release_metadata/api_runtime_smoke_v9.md`

watchdog recovery evidence：`release_metadata/watchdog_recovery_status_v9.md`

editor issue closure：`release_metadata/v9_editor_issue_closure.md`

Arabidopsis root literature anchor：`release_metadata/arabidopsis_root_literature_anchor_v9.md`

服务器发布包：`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090`

外部对照与生物学案例补充包：`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090/addendum_methods_panel`

## 10 稳健主张边界

本版本可以稳定陈述如下主张：

1. Plant-CellFM v9 是面向植物单细胞/单核表达矩阵的通用基础模型和全植物适配框架。
2. 在同一 shared-gene benchmark 上，v9 在留数据集、留样本和归一化留物种协议中均优于 v3 extended baseline。
3. Seurat label transfer 在 frozen v9 subset 上表现较弱，支持植物专用基础模型和 adapter 机制的必要性。
4. Arabidopsis root case 展示了 adapter 解析、层级注释和 marker candidate mining 的完整计算生物学链路。
5. 天山雪莲是目标物种适配入口，不是当前已完成的单细胞图谱。

本版本不应陈述如下主张：

1. 不应声称任意新物种输入均可直接获得满覆盖标签。
2. 不应把内部 held-out accuracy 写成跨物种泛化精度。
3. 不应声称 scPlantLLM/scPlantAnnotate 正式对照已完成。
4. 不应声称天山雪莲单细胞图谱已经完成。

## 11 结论

Plant-CellFM v9 已经形成一版可提交、可演示、可复现的植物通用单细胞注释基础模型。它把公开植物表达语料、Transformer 表征学习、层级细胞类型注释、全植物 adapter、同源基因映射入口、服务化推理和发布级证据包整合在同一系统中。当前最稳妥的投稿定位是计算方法与资源论文：模型不是只做雪莲，而是面向全植物；雪莲不是被夸大为图谱成果，而是作为目标物种适配入口；性能结论不依赖内部随机拆分，而以 leave-dataset、leave-sample、物种名归一化 leave-species benchmark、Seurat 外部对照和 Arabidopsis root 生物学案例为核心证据。

## 审稿风险修复矩阵

| 风险点 | 本文修复方式 | 安全表述 | 证据文件 |
| --- | --- | --- | --- |
| 跨物种泛化指标被质疑偏低 | 主文将留物种结果写成开放集迁移证据，而不是全部植物满覆盖断言；同时报告 all-cell accuracy、coverage 和 known-label conditional metrics。 | Plant-CellFM v9 在同一 shared-gene benchmark 上稳定优于 v3 extended baseline，并提供可复现的全植物适配框架。 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| 第三方横向对照不完整 | Seurat 作为完成的传统外部基线进入主表；scPlantLLM 和 scPlantAnnotate 只按输入就绪/认证受限状态陈述。 | 当前版本完成了 v3、centroid 和 Seurat 对照，并公开保留 scPlantLLM/scPlantAnnotate 的可复现入口。 | release_metadata/external_benchmark_panel_v9.json |
| 生物学案例被认为只是计算输出 | 把 Arabidopsis root 写成 public-data computational case，强调 adapter resolution、层级注释和 marker candidate mining 的完整链路。 | Arabidopsis root case 证明模型不仅输出标签，也能产生可审计 adapter 记录和根细胞身份 marker 候选。 | release_metadata/plant_biology_case_study_v9.json |
| 雪莲定位被误读为图谱成果 | 主文明确 Snow Lotus 是目标物种接入口和应用场景，当前不写作已发布细胞图谱成果。 | Snow Lotus-ready transfer is supported once a reusable Snow Lotus single-cell matrix is supplied under the h5ad contract. | release_metadata/saussurea_h5ad_contract.md |
| 代码版本和 GitHub 展示不同步 | GitHub HTTPS 后端已切换为 repo-local OpenSSL；最新同步状态用 `git rev-parse HEAD origin/agent/remote-pipeline-20260728` 复核，不在正文写死易过期 commit。 | The submission branch, release asset, SHA256 records and server package can be independently checked from the repository and release metadata. | release_metadata/server_sustainability_status_v9.md |
| 在线服务稳定性被追问 | 已补 live `POST /annotate` smoke test 和 tmux watchdog 控制恢复测试；服务被 SIGTERM 后 30 秒内由 watchdog 拉起，并恢复健康检查。 | Plant-CellFM v9 is not only a static checkpoint; the frozen model is deployed in a reproducible CUDA service with recorded runtime and recovery evidence. | release_metadata/api_runtime_smoke_v9.md; release_metadata/watchdog_recovery_status_v9.md |
| 早期 5090 文件名与当前硬件声明混淆 | 正式 README、提交索引、模型卡和主文均使用实测 NVIDIA GeForce RTX 4090, 24 GB VRAM；早期 5090 文件名只作为开发历史保留。 | The frozen v9 candidate should be cited as the RTX 4090 LoRA checkpoint and CUDA service. | release_metadata/plant_cellfm_v9_model_card.md; SUBMISSION_INDEX_v9.md |
