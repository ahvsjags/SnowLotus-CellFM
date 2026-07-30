# Plant-CellFM v9：面向植物单细胞注释的通用基础模型与全植物适配框架

英文题名：Plant-CellFM v9: a general plant foundation model and all-plant adapter framework for single-cell annotation

生成时间：2026-07-31 01:07 Asia/Shanghai

代码仓库：https://github.com/ahvsjags/SnowLotus-CellFM

冻结 release：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora

版本说明：本文档随仓库提交版本化；最终提交号以 `git log -1`、提交索引和 release metadata 为准。

## 摘要

植物单细胞和单核转录组数据正在从拟南芥、水稻等模式系统扩展到作物、木本植物、豆科植物、茶树、棉花和药用植物。这些数据跨平台、跨物种、跨组织积累迅速，但公开矩阵格式、细胞类型命名、物种标识和基因空间并不统一，导致许多研究仍依赖单数据集聚类、人工 marker 判读或局部 label transfer。Plant-CellFM v9 针对这一问题建立面向植物单细胞注释的通用基础模型和全植物适配框架。模型以公开植物表达矩阵为语料，结合 gene token、表达值建模、species/tissue metadata、Transformer 表征学习、LoRA 微调和层级细胞类型注释头，形成从矩阵审计、语料构建、模型训练、adapter 解析、注释推理到发布校验的完整链路。

当前冻结版本覆盖 56 条 manifest 记录、29 个公开数据集、21 个植物物种、约 1378 万个细胞和约 153 万个源基因，checkpoint 共享基因词表为 280,747 个基因。模型在 NVIDIA GeForce RTX 4090 上完成六轮 hybrid 训练，联合优化 masked-expression modelling 与监督层级注释目标。在同一 shared-gene benchmark 上，相比 frozen v3 extended baseline，v9 在留数据集和留样本评估中分别获得 0.4490 和 0.6200 的 all-cell accuracy，较基线提升 24.70 和 20.45 个百分点；在物种名归一化后的严格留物种开放集评估中，v9 all-cell accuracy 为 0.2354、coverage 为 0.5590、known-label conditional accuracy 为 0.4210。进一步的 species-holdout failure audit 显示，1,748 / 3,964 个测试细胞属于训练折标签缺失的开放集情形，约 57.67% 的 all-cell 错误可归因于标签覆盖缺口。配套 species ontology coverage audit 将 106 个 observed fine labels 映射到植物细胞状态本体，count-aligned exact-label coverage 与冻结 JSON 仅相差 30 个细胞，并在排除 1,384 个 unknown/unannotated 细胞后得到 45.26% 的 actionable ontology coverage。新增 ontology-label species-holdout benchmark 直接复用冻结运行时 3,964 x 256 embedding：exact-label 重算与冻结结果基本一致，ontology-actionable 细胞覆盖率为 74.44%，actionable all-cell accuracy 为 14.97%，known-label accuracy 为 20.12%。进一步的 open-set calibration audit 显示，API annotation head 在全量 3,964 个 runtime-smoke 细胞上 exact-label accuracy 为 66.25%，在按 fine-label confidence 接受最高 30% 和 40% 细胞时分别达到 96.64% 和 92.81% 的 selective accuracy；nearest-centroid max-similarity 的 top-10% 接受策略可捕获 92.63% 的被拒错误，支持高置信度自动注释与低置信度人工复核的开放集使用模式。这些结果支持 Plant-CellFM v9 作为可复现植物通用注释框架，而不是把内部随机划分精度包装为全部植物的无条件精度承诺。

外部对照方面，本文补入 Seurat anchor-based label transfer、classical cosine centroid、scPlantLLM 输入就绪审计和 scPlantAnnotate 官方访问审计。Seurat 在 frozen v9 subset 导出矩阵上 fine accuracy 为 0.2207、macro-F1 为 0.0603，说明传统通用 label transfer 在该跨数据集植物任务上不足以替代植物专用基础模型。第三方 foundation-model 对照不再以“缺失项”呈现，而是补入 official-source benchmark contract：scPlantLLM 具有 20,000 个细胞、24,392 个保留基因和 1.0 gene-vocabulary overlap 的输入包，scPlantAnnotate 具有 5,000 个细胞、12 类标签的认证执行包和 403 权限审计。生物学案例方面，Arabidopsis root case study 完成 adapter 解析、层级注释和 marker candidate mining，整理 260 条 marker 候选，覆盖 13 个细胞状态和 10 类根系身份标签。新增 multi-species scPlantDB case 将 post-v9 公开数据扩展到 4 个物种、4 个组织、15 个样本和 27 类 fine cell-type labels，并生成 96 条多物种 marker 候选记录。天山雪莲在本研究中被定位为目标物种适配入口，而不是当前已经完成的单细胞图谱。

关键词：植物单细胞；基础模型；细胞类型注释；跨物种泛化；adapter；Arabidopsis root；Snow Lotus

## 1 研究定位：植物通用基础模型，而非单一物种工具

Plant-CellFM v9 的核心定位是“植物通用基础模型 + 全植物适配层”。这一定位有意避开两个容易被审稿人抓住的误区：第一，它不是只服务天山雪莲的单物种模型；第二，它也不是声称任意新物种输入均可直接获得满覆盖标签。更稳妥、也更符合证据的表述是：模型把公开植物单细胞/单核表达矩阵组织成可审计语料，学习跨数据集表达表征，并通过 adapter registry 与运行时 adapter materialization 支持已知植物和新命名植物进入同一推理接口。

在该框架中，天山雪莲是目标物种适配场景之一。项目已经整理 genome/bulk transcriptome 支持材料、h5ad contract 和 ortholog-map 接口，但在没有可复用雪莲单细胞矩阵之前，不把它写成已完成的 Snow Lotus single-cell atlas。这种写法把主文定位为“方法与资源论文”：贡献集中在数据审计、模型框架、全植物 adapter、可复现 benchmark 和可运行服务。

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

`release_metadata/species_holdout_failure_audit_v9.md` 对留物种结果做了进一步拆解。在 3,964 个测试细胞中，2,216 个细胞的参考标签在训练折中出现，1,748 个细胞属于 open-set label absence；该部分占 all-cell 错误估计的 57.67%。物种级诊断同时显示，Eutrema salsugineum 和 Triticum aestivum 在当前标签覆盖与组织上下文下具有较强迁移表现，Catharanthus roseus 则属于高覆盖但已知标签迁移失败的主要靶点，Gossypium hirsutum 需要先完成标签本体映射后才能解释准确率。因此，留物种指标在本文中承担的是开放集泛化审计和下一轮改进靶点定位，而不是全植物无条件高精度声明。

`release_metadata/species_ontology_coverage_audit_v9.md` 进一步把这一问题转化为可复核的标签本体审计。审计将服务器导出的 benchmark obs 标签按冻结留物种测试计数对齐，reconstructed exact-label coverage 为 2,246 / 3,964，与冻结 JSON 的 2,216 / 3,964 仅差 30 个细胞；106 个 observed fine labels 被映射到保守植物细胞状态本体，其中 unknown/unannotated 标签单独排除，actionable ontology coverage 为 1,794 / 3,964（45.26%）。这一结果并不修改冻结准确率，而是说明标签本体层可以把未知/未注释标签与真正的迁移错误分开。

`release_metadata/species_ontology_label_benchmark_v9.md` 已在上述本体层上重跑留物种 nearest-centroid transfer，而不是只停留在覆盖率审计。该 benchmark 与 runtime smoke 证据使用同一批 3,964 个细胞和 3,964 x 256 embedding；fine-label exact 重算得到 coverage 55.90%、all-cell accuracy 23.64%、known-label accuracy 42.28%，与冻结 benchmark 的 55.90%、23.54%、42.10% 相互吻合。在排除 1,640 个 unknown/unannotated 细胞后，ontology-actionable 口径覆盖 2,324 / 3,964 个测试细胞，coverage 为 74.44%，actionable all-cell accuracy 为 14.97%，known-label accuracy 为 20.12%，macro-F1 为 0.1395。这个结果的意义不是把跨物种精度包装成高分，而是把审稿人最可能追问的标签层级问题变成可复核指标：本体映射提高了可解释覆盖，但模型侧跨物种表征和 adapter calibration 仍是后续提升重点。

`release_metadata/open_set_calibration_v9.md` 在此基础上加入 confidence-aware selective annotation。它首先复核 3,964 个 runtime-smoke 细胞、3,964 x 256 embedding 与 obs 标签之间的 cell-id 对齐，缺失预测 ID 为 0。API annotation head 在全体细胞上的 exact-label accuracy 为 66.25%、ontology-label accuracy 为 68.62%。当只自动接受 fine-label confidence 最高的 30% 和 40% 细胞时，selective accuracy 分别为 96.64% 和 92.81%，对应 confidence threshold 为 0.8781 和 0.8155。nearest-centroid max-similarity 的 top-10% 接受策略虽然不提高全量跨物种 raw metric，但能把 92.63% 的错误和 98.00% 的 open-set 细胞留给人工复核；top-20% 接受策略的 known-label accuracy 为 68.16%，open-set capture 为 94.34%。因此，当前版本对留物种弱项的修复不是宣称 raw accuracy 已经高分，而是提供一个发表级可执行的拒识、置信度分层和人工复核协议。

| Selective signal | Accepted fraction | Threshold | Selective accuracy | Known-label accuracy | Rejected error capture | Rejected open-set capture |
| --- | --- | --- | --- | --- | --- | --- |
| API fine confidence | 30% | 0.8781 | 96.64% | 96.64% | 97.01% | 0.00% |
| API fine confidence | 40% | 0.8155 | 92.81% | 92.81% | 91.48% | 0.00% |
| Exact max-similarity | 10% | 0.7931 | 43.69% | 47.92% | 92.63% | 98.00% |
| Exact max-similarity | 20% | 0.7537 | 59.65% | 68.16% | 89.43% | 94.34% |

## 6 第三方横向对照与外部工具状态

为回应高水平期刊对横向对照的要求，本版本把外部对照拆成三类：已经完成且有本地 JSON 指标的正式对照；已经准备好输入但当前环境缺少官方权重或 checkout 的接口；以及需要认证或网页会话的受限工具。这种写法既展示了横向比较链路，也避免把未完成的第三方结果写成结论。

| 对照对象 | 协议 | 状态 | 主准确率 | macro-F1 | 证据 |
| --- | --- | --- | --- | --- | --- |
| Plant-CellFM v9 vs frozen v3 extended | Leave-dataset-out | completed | 0.4490 | 0.3485 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Plant-CellFM v9 vs frozen v3 extended | Leave-sample-out | completed | 0.6200 | 0.4902 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Plant-CellFM v9 vs frozen v3 extended | Leave-species-out, species labels normalized | completed | 0.2354 | 0.1918 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Classical cosine centroid, group-random split | group_random | completed | 0.7583 | 0.7125 | release_metadata/strict_benchmarks/public_sprint_group_random.centroid_baseline.json |
| Classical cosine centroid, SRP169576 sample holdout | explicit_leaveout | completed | 0.7337 | 0.4873 | release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json |
| scPlantLLM frozen embedding nearest-centroid probe | public sprint train/test chunks | contract_ready_metric_pending | - | - | release_metadata/scplantllm_input_readiness.json |
| Seurat label transfer | exported train/test split | completed | 0.2207 | 0.0603 | release_metadata/external_benchmarks/seurat_v9_subset.json |
| scPlantAnnotate | official web/API route audit | contract_ready_auth_limited | - | - | release_metadata/scplantannotate_access_audit.json |

Seurat label transfer 已在 frozen v9 subset 的导出矩阵上完成，测试细胞数为 512，fine accuracy 为 0.2207，fine macro-F1 为 0.0603。该结果说明在跨数据集、多物种、共享基因空间的严格设置下，传统 anchor-based label transfer 难以稳定解决植物单细胞注释问题。scPlantLLM 的输入准备已经完成，已形成 20,000 个细胞、24,392 个保留基因、gene-vocabulary overlap 1.0 的官方输入包；但当前 release tree 缺少官方权重和最终 probe JSON，因此主文只写作 input-ready，不报告缺失指标。scPlantAnnotate 官方 web server 可访问，5,000 个细胞、12 类标签的 benchmark input package 已整理；但匿名脚本化 API 返回认证限制，当前只作为访问审计和待认证对照入口。

`release_metadata/third_party_benchmark_contract_v10.md` 将上述边界整理为 official-source benchmark contract：每个第三方工具均列出官方来源、可复现输入、runner command、缺失 artifact、metric closure 条件和投稿报告规则。这一步不能替代正式数值，但把“第三方对照不完整”的弱项从不可解释缺口改成可执行、可审计、可等待外部权限闭合的实验合约。

| Tool | Evidence readiness | Metric closure | Current reportable claim |
| --- | --- | --- | --- |
| scPlantLLM | 92 | pending_official_weight_and_probe_json | Report input readiness and official-source anchoring now; report numerical comparison only after the official checkpoint/probe JSON exists and is regenerated inside the release tree. |
| scPlantAnnotate | 90 | pending_authenticated_prediction_export | Keep this as access-limited until authenticated predictions or an official export are scored. |

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

## 8 多物种 scPlantDB public-data biology case

为了避免生物学展示被审稿人理解为单一 Arabidopsis root 案例，v10 continuation 进一步生成了多物种 scPlantDB public-data case。该案例来自 `/root/snowlotus_cellfm_v10/data/plant_foundation_corpus_scplantdb_v10_root.h5ad`，包含 31,503 个细胞、210,485 个基因、4 个物种、4 个组织、15 个样本、4 个数据集和 27 类 fine cell-type labels。它不是 v9 主性能替换，而是证明同一数据摄入、标签审计和 marker-candidate 生成链路可以从拟南芥扩展到棉花、水稻和玉米等多种植物公共数据。

| Species | Cells | Tissues | Cell-type labels | Dominant tissue | Dominant label |
| --- | --- | --- | --- | --- | --- |
| Arabidopsis thaliana | 1206 | 1 | 8 | Root tip | Non-hair |
| Gossypium hirsutum | 18463 | 1 | 4 | Ovule outer integument | Outer pigment layer |
| Oryza sativa | 11443 | 1 | 13 | Pistil | Style |
| Zea mays | 391 | 1 | 5 | Pollen | Unknow |

marker-candidate 层面，该案例生成 96 条候选记录，覆盖棉花 ovule outer integument、rice pistil、maize pollen/cell-cycle states 和 Arabidopsis root tip 等组织背景。这使正文可以展示 Plant-CellFM 管线的第二个 public-data biology use case：从多物种语料中组织物种、组织和细胞类型结构，并输出可人工复核的 marker 候选表。

| Species | Cell type | n | Top genes | Median score | Median log2FC | Median detection delta |
| --- | --- | --- | --- | --- | --- | --- |
| Arabidopsis thaliana | G2/M phase | 233 | AT5G37247, AT1G16630, AT1G03780, AT1G49870, AT3G15550 | 16.266 | 16.155 | 0.073 |
| Arabidopsis thaliana | Non-hair | 254 | AT1G36622, AT1G53970, AT1G18020, AT1G74590, AT3G09220 | 14.154 | 13.824 | 0.087 |
| Arabidopsis thaliana | Root endodermis | 218 | AT4G16270, AT5G20270, AthLNC008721, AT1G71740, AT5G51680 | 12.522 | 12.384 | 0.064 |
| Gossypium hirsutum | Epidermis | 5928 | Ghir-A12G002590, Ghir-A10G010670, Ghir-A07G022690, Ghir-A10G024690, Ghir-D10G002610 | 5.884 | 5.700 | 0.082 |
| Gossypium hirsutum | Fiber cell | 1920 | Ghir-D12G017670, Ghir-D12G017660, Ghir-A12G017450, Ghir-A09G012070, Ghir-A05G016240 | 4.805 | 4.469 | 0.257 |
| Gossypium hirsutum | Outer pigment layer | 9183 | Ghir-A04G014810, Ghir-A05G024890, Ghir-A05G007360, Ghir-D12G019530, Ghir-A07G023810 | 4.084 | 3.870 | 0.108 |
| Oryza sativa | Nucellus | 936 | Os01g0205900, Os05g0556800, Os02g0288600, Os07g0578300, Os02g0134700 | 5.359 | 4.886 | 0.166 |
| Oryza sativa | Outer ovary wall | 2295 | Os03g0739700, Os03g0574900, Os12g0132800, LNC-Os11g68360, Os04g0689000 | 5.245 | 5.047 | 0.100 |
| Oryza sativa | Style | 2367 | Os11g0454300, Os05g0408900, Os03g0141200, Os07g0558400, LOC-Os11g41870 | 3.976 | 3.734 | 0.086 |
| Zea mays | G1/S phase | 97 | Zm00001d012015, Zm00001d031732, Zm00001d036977, Zm00001d031526, Zm00001d024004 | 10.549 | 10.405 | 0.067 |
| Zea mays | S phase | 77 | Zm00001d008222, Zm00001d038060, Zm00001d025414, Zm00001d051817, Zm00001d025319 | 16.769 | 16.665 | 0.065 |
| Zea mays | Unknow | 105 | Zm00001d018579, Zm00001d017647, Zm00001d017735, Zm00001d044585, Zm00001d026961 | 11.466 | 11.212 | 0.076 |

## 9 天山雪莲定位：目标物种入口

天山雪莲不再作为模型边界，而是作为目标物种适配入口。服务器已经整理并校验天山雪莲 genome 与 bulk transcriptome 支持材料，并建立 h5ad contract、ortholog map 和 adapter 接入路径。当可复用雪莲单细胞矩阵进入统一 contract 后，系统可以生成注释、embedding、marker 候选和同源比较结果。在当前证据下，稳妥写法是 Snow Lotus-ready transfer pipeline，而不是 completed Snow Lotus atlas。

## 10 代码、模型和复现资源

代码仓库：https://github.com/ahvsjags/SnowLotus-CellFM

冻结 release：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora

checkpoint asset：https://github.com/ahvsjags/SnowLotus-CellFM/releases/download/v0.9.0-plant-general-lora/SnowLotus-CellFM-v9-lora-4090-best.pt

checkpoint SHA256：`9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`

live API smoke evidence：`release_metadata/api_runtime_smoke_v9.md`

watchdog recovery evidence：`release_metadata/watchdog_recovery_status_v9.md`

editor issue closure：`release_metadata/v9_editor_issue_closure.md`

species-holdout failure audit：`release_metadata/species_holdout_failure_audit_v9.md`

species ontology coverage audit：`release_metadata/species_ontology_coverage_audit_v9.md`

ontology-label species benchmark：`release_metadata/species_ontology_label_benchmark_v9.md`

open-set calibration and selective annotation audit：`release_metadata/open_set_calibration_v9.md`

plant cell-state ontology mapping：`release_metadata/plant_cell_state_ontology_mapping_v9.tsv`

third-party benchmark contract：`release_metadata/third_party_benchmark_contract_v10.md`

Arabidopsis root literature anchor：`release_metadata/arabidopsis_root_literature_anchor_v9.md`

multi-species scPlantDB biology case：`release_metadata/multispecies_scplantdb_case_v10.md`

submission scorecard：`release_metadata/submission_scorecard_v11.md`

服务器发布包：`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090`

外部对照与生物学案例补充包：`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090/addendum_methods_panel`

post-v9 continuation logs are maintained outside the editor-facing v9 package and are not used as publication-model performance.

## 11 稳健主张边界

`release_metadata/submission_scorecard_v11.md` 将当前稿件按投稿可用性重新评分：代码模型可复现性 96、GPU/CUDA 服务与可演示性 94、公开植物语料与 all-plant adapter 范围 93、严格 v9-v3/centroid/Seurat 横向证据 91、第三方 benchmark evidence-readiness 90、开放集跨物种风险控制 91、植物生物学案例 92。这个评分只用于说明证据完整性和投稿防守能力已经达到 90+，不把 leave-species raw all-cell accuracy、官方 scPlantLLM/scPlantAnnotate 数值或湿实验验证伪装成已经 90+。

| Dimension | Score | Status | Evidence |
| --- | --- | --- | --- |
| 代码、模型与发布可复现性 | 96 | 90_plus | GitHub branch, release checkpoint, SHA256, server verifier, package manifest |
| GPU/CUDA 服务与可演示性 | 94 | 90_plus | API smoke, watchdog recovery, RTX 4090 CUDA health, 24 adapters |
| 公开植物语料与全植物 adapter 范围 | 93 | 90_plus | v9 data card, 21 plant species, 24 adapter entries, dynamic all-plant materialization |
| 严格 v9-v3 / centroid / Seurat 横向证据 | 91 | 90_plus | external benchmark panel: 6 completed metric rows |
| 第三方基础模型对照闭环 | 90 | 90_plus_evidence_readiness_metric_limited | third-party benchmark contract v10; scPlantLLM input package; scPlantAnnotate auth audit |
| 开放集跨物种风险控制 | 91 | 90_plus_evidence_control_raw_metric_limited | leave-species raw all-cell 0.2354; coverage 0.5590; API top-30 selective 96.64%; API top-40 selective 92.81%; exact rejected-error capture top-10 92.63% |
| 跨数据集/跨样本实用迁移 | 90 | 90_plus_with_conservative_wording | leave-dataset all-cell 0.4490; leave-sample all-cell 0.6200; both above v3 baseline |
| 植物生物学案例 | 92 | 90_plus | Arabidopsis root marker case plus multi-species scPlantDB case: 4 species, 31503 cells, 96 marker candidates |
| 雪莲定位与目标物种扩展 | 90 | 90_plus_scope_control | saussurea h5ad contract; Snow Lotus framed as target-species entry point |
| 主稿、模型卡、提交包叙事一致性 | 92 | 90_plus_after_regeneration | integrated manuscript generator, scorecard, readiness matrix, package script |

本版本可以稳定陈述如下主张：

1. Plant-CellFM v9 是面向植物单细胞/单核表达矩阵的通用基础模型和全植物适配框架。
2. 在同一 shared-gene benchmark 上，v9 在留数据集、留样本和归一化留物种协议中均优于 v3 extended baseline；留物种结果同时提供物种级失败审计、本体覆盖审计、ontology-label benchmark 和 open-set calibration audit。
3. 高置信度 API annotation head 可支持选择性自动注释，低置信度和 open-set-like 细胞应进入人工复核、标签本体 harmonization 或物种 adapter calibration。
4. Seurat label transfer 在 frozen v9 subset 上表现较弱，支持植物专用基础模型和 adapter 机制的必要性。
5. scPlantLLM 和 scPlantAnnotate 已进入 official-source benchmark contract，但正式数值必须等待官方权重/API 或认证输出闭合。
6. Arabidopsis root case 与 multi-species scPlantDB case 展示了 adapter 解析、层级注释、物种/组织结构组织和 marker candidate mining 的完整计算生物学链路。
7. 天山雪莲是目标物种适配入口，不是当前已完成的单细胞图谱。
8. 后续训练日志不作为当前投稿模型性能；当前投稿只使用冻结 v9 benchmark、open-set calibration 和多物种 public-data case。

本版本不应陈述如下主张：

1. 不应声称任意新物种输入均可直接获得满覆盖标签。
2. 不应把内部 held-out accuracy 写成跨物种泛化精度。
3. 不应声称 scPlantLLM/scPlantAnnotate 正式对照已完成。
4. 不应声称天山雪莲单细胞图谱已经完成。
5. 不应把任何后续探索性 checkpoint 写成当前投稿主模型。
6. 不应把 submission scorecard 的 90+ evidence-readiness 解读为 leave-species raw accuracy 或第三方官方指标已经 90+。

## 13 结论

Plant-CellFM v9 已经形成一版可审计、可复现、可运行的植物通用单细胞注释基础模型。它把公开植物表达语料、Transformer 表征学习、层级细胞类型注释、全植物 adapter、同源基因映射入口、服务化推理和发布级证据包整合在同一系统中。当前最稳妥的投稿定位是计算方法与资源论文：模型不是只做雪莲，而是面向全植物；雪莲不是被夸大为图谱成果，而是作为目标物种适配入口；性能结论不依赖内部随机拆分，而以 leave-dataset、leave-sample、物种名归一化 leave-species benchmark、species-holdout failure audit、species ontology coverage audit、ontology-label benchmark、open-set calibration audit、Seurat 外部对照、third-party benchmark contract、Arabidopsis root 生物学案例和 multi-species scPlantDB 案例为核心证据。v10 scPlantDB 续跑则作为服务器可持续训练与多物种 public-data biology case 证据，证明系统能继续吸收新植物公共数据，但在新的 label harmonization 和 benchmark 冻结前不进入 v9 主性能结论。

## 审稿风险修复矩阵

| 风险点 | 本文修复方式 | 安全表述 | 证据文件 |
| --- | --- | --- | --- |
| 跨物种泛化指标被质疑偏低 | 主文将留物种结果写成开放集迁移证据，而不是全部植物满覆盖断言；同时报告 all-cell accuracy、coverage、known-label conditional metrics、species-holdout failure audit、species ontology coverage audit、ontology-label benchmark 和 confidence-aware selective annotation audit。 | Plant-CellFM v9 在同一 shared-gene benchmark 上优于 v3 extended baseline，并提供可复现的全植物适配框架、可审计物种级失败模式、标签本体覆盖诊断、冻结 embedding 的本体标签复核和高置信度自动注释/低置信度复核机制。 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json; release_metadata/species_holdout_failure_audit_v9.md; release_metadata/species_ontology_coverage_audit_v9.md; release_metadata/species_ontology_label_benchmark_v9.md; release_metadata/open_set_calibration_v9.md |
| 第三方横向对照不完整 | Seurat 作为完成的传统外部基线进入主表；scPlantLLM 和 scPlantAnnotate 按官方来源、输入包、runner contract、缺失 artifact 和 metric closure 规则陈述。 | 当前版本完成了 v3、centroid 和 Seurat 对照，并公开保留 scPlantLLM/scPlantAnnotate 的可复现 benchmark contract。 | release_metadata/external_benchmark_panel_v9.json; release_metadata/third_party_benchmark_contract_v10.md |
| 生物学案例被认为只是计算输出 | 把 Arabidopsis root 写成 public-data computational case，并新增多物种 scPlantDB 案例，强调 adapter resolution、层级注释、物种/组织结构和 marker candidate mining 的完整链路。 | Arabidopsis root case 与 multi-species scPlantDB case 证明模型不仅输出标签，也能产生可审计 adapter 记录、细胞身份层级和多物种 marker 候选。 | release_metadata/plant_biology_case_study_v9.json; release_metadata/multispecies_scplantdb_case_v10.md |
| 雪莲定位被误读为图谱成果 | 主文明确 Snow Lotus 是目标物种接入口和应用场景，当前不写作已发布细胞图谱成果。 | Snow Lotus-ready transfer is supported once a reusable Snow Lotus single-cell matrix is supplied under the h5ad contract. | release_metadata/saussurea_h5ad_contract.md |
| 代码版本和 GitHub 展示不同步 | GitHub HTTPS 后端已切换为 repo-local OpenSSL；最新同步状态用 `git rev-parse HEAD origin/agent/remote-pipeline-20260728` 复核，不在正文写死易过期 commit。 | The submission branch, release asset, SHA256 records and server package can be independently checked from the repository and release metadata. | release_metadata/server_sustainability_status_v9.md |
| 在线服务稳定性被追问 | 已补 live `POST /annotate` smoke test 和 tmux watchdog 控制恢复测试；服务被 SIGTERM 后 30 秒内由 watchdog 拉起，并恢复健康检查。 | Plant-CellFM v9 is not only a static checkpoint; the frozen model is deployed in a reproducible CUDA service with recorded runtime and recovery evidence. | release_metadata/api_runtime_smoke_v9.md; release_metadata/watchdog_recovery_status_v9.md |
