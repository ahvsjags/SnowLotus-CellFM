# Plant-CellFM v9 投稿分层与顶刊推进策略

Generated: 2026-07-30 Asia/Shanghai

本文件替代早期 SnowLotus-centered 顶刊方案。当前冻结稿的正式定位是 **Plant-CellFM 植物通用基础模型 + 全植物适配层**；天山雪莲是目标物种接入场景，不是当前完成的单细胞图谱。当前硬件声明统一为 NVIDIA GeForce RTX 4090, 24 GB VRAM。

## 当前一句话定位

Plant-CellFM v9 是一个面向植物单细胞/单核表达矩阵的可复现注释基础模型和 adapter 框架。它提供公开植物语料、共享基因 backbone、层级注释头、动态全植物 adapter、严格 cross-group benchmark、Species-Transfer Calibration（STC）层、open-set calibration、Seurat/centroid/v3 对照、第三方 benchmark contract、Arabidopsis root 与 multi-species scPlantDB 计算生物学案例、GitHub release、SHA256 固化包和服务器 CUDA 服务。

当前稿件可以稳妥主张：

1. 模型不是雪莲单物种工具，而是植物通用框架。
2. v9 在同一 shared-gene benchmark 上优于 frozen v3 extended baseline。
3. 留物种结果必须按开放集解释：23.54% all-cell accuracy、55.90% coverage、42.10% known-label conditional accuracy。
4. `release_metadata/species_holdout_failure_audit_v9.md` 已把留物种低分拆成标签覆盖缺口、已知标签迁移错误和物种级修订目标；`release_metadata/species_ontology_coverage_audit_v9.md` 进一步给出 106 个 fine label 的植物细胞状态本体映射和 unknown/unannotated 诊断；`release_metadata/species_ontology_label_benchmark_v9.md` 已用冻结 3964 x 256 embedding 重跑 ontology-label 留物种 benchmark。
5. `release_metadata/cross_species_classifier_benchmark_v10.md` 和 `release_metadata/algorithm_innovation_v10.md` 将留物种改进落实为 STC 层：同一 frozen embedding、同一 leave-species split 下，`knn_cosine_k9` 把 all-cell accuracy 从 23.64% 提升到 30.10%，known-label accuracy 从 42.28% 提升到 53.84%，macro-F1 从 0.1922 提升到 0.2663。
6. `release_metadata/open_set_calibration_v9.md` 将留物种弱项转化为可执行使用规则：API fine-confidence top 30% / 40% selective accuracy 为 96.64% / 92.81%，低置信度和 open-set-like 细胞进入人工复核或 adapter calibration。
7. `release_metadata/third_party_benchmark_contract_v10.md` 已把 scPlantLLM/scPlantAnnotate 处理为 official-source execution contract；当前不写正式数值，但输入、runner、缺失 artifact 和 metric closure 条件齐全。
8. Arabidopsis root 与 multi-species scPlantDB 案例展示 adapter 解析、层级注释、物种/组织结构组织和 marker-candidate mining，但仍是 public-data computational case。

当前稿件不应主张：

1. 任意植物新物种都能无条件高精度自动注释。
2. 天山雪莲单细胞图谱已经完成。
3. scPlantLLM/scPlantAnnotate 正式数值对照已经完成。
4. 硬件口径以当前模型卡为准：NVIDIA GeForce RTX 4090, 24 GB VRAM。

## 期刊分层依据

以下判断以官方 scope 页面和当前证据为依据：

| 目标 | 当前适配度 | 主要依据 | 当前风险 |
| --- | --- | --- | --- |
| Nature Methods | Stretch | 官方 scope 强调新方法、single-cell analysis、computational/machine-learning methods、强 validation、与可用方法比较和重要生物应用。 | 需要更强第三方模型闭环和独立生物应用验证。 |
| Genome Biology | Strong methods/resource target | 官方页面将其定位为 genomics/post-genomics 视角的 biology/biomedicine open-access journal，并有 plant single-cell/spatial omics 相关 collection。 | 需要把方法贡献、公开语料和可复现资源写得更完整，最好补一个官方 third-party model run。 |
| Plant Communications | Most stable plant-focused target | 官方 scope 接收植物科学原创研究、重要技术进展和有用资源，覆盖 plant cellular biology、genomics、development、metabolism 等方向。 | 需要突出植物用途、adapter resolution、marker discovery 和 Arabidopsis root 生物学解释。 |
| Communications Biology | Broad fallback | 官方 scope 接收 biological sciences 中的 secondary data analysis、innovative computational methods，并要求 strong evidence。 | 必须降低“顶刊 AI 模型”叙事，突出可靠证据和具体植物生物学用例。 |
| Nature Plants | High stretch plant venue | 官方 scope 覆盖 plant genomics、cell biology、development、metabolism、systems biology。 | 当前缺少湿实验或独立植物生物学发现；更适合作为后续强化目标。 |

官方 scope 链接：

- Nature Methods aims and scope: https://www.nature.com/nmeth/submission-guidelines/about/aims
- Genome Biology journal page: https://link.springer.com/journal/13059
- Plant Communications journal page: https://www.sciencedirect.com/journal/plant-communications
- Communications Biology aims and scope: https://www.nature.com/commsbio/aims
- Nature Plants aims and scope: https://www.nature.com/nplants/aims

## 当前证据矩阵

| 证据模块 | 状态 | 关键文件 | 投稿价值 |
| --- | --- | --- | --- |
| GitHub 同步 | completed | `SUBMISSION_INDEX_v9.md`; branch `agent/remote-pipeline-20260728` | 编辑可以直接复核代码、文档和证据包。 |
| 冻结 checkpoint | completed | `release_metadata/plant_cellfm_v9_model_card.md` | 模型 asset、SHA256、配置和训练硬件可核查。 |
| 服务器服务 | completed | `release_metadata/api_runtime_smoke_v9.md`; `release_metadata/watchdog_recovery_status_v9.md` | 证明不是静态说明，而是可调用 CUDA 服务。 |
| 公共植物语料 | completed for v9 | `release_metadata/v9_data_card.md` | 支撑植物通用而非单物种说法。 |
| v9-v3 公平对照 | completed | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` | 证明同 subset、同指标下 v9 有增益。 |
| Seurat 外部对照 | completed | `release_metadata/external_benchmarks/seurat_v9_subset.json` | 给出传统 label transfer 基线。 |
| scPlantLLM 对照 | evidence-readiness 92, metric pending | `release_metadata/scplantllm_input_readiness.md`; `release_metadata/third_party_benchmark_contract_v10.md` | 20,000 细胞输入、24,392 基因、1.0 vocab overlap 和 runner contract 已齐，当前不写数值结论。 |
| scPlantAnnotate 对照 | evidence-readiness 90, auth-limited | `release_metadata/scplantannotate_access_audit.md`; `release_metadata/scplantannotate_benchmark_input_package.md`; `release_metadata/third_party_benchmark_contract_v10.md` | 5,000 细胞、12 类标签输入包和认证执行命令已齐；匿名 API 受限。 |
| 留物种失败审计 | completed | `release_metadata/species_holdout_failure_audit_v9.md` | 把低分解释为开放集标签覆盖与迁移错误分解，而非包装成高精度。 |
| 留物种本体覆盖审计 | completed | `release_metadata/species_ontology_coverage_audit_v9.md`; `release_metadata/plant_cell_state_ontology_mapping_v9.tsv` | 给出 count-aligned exact coverage、actionable ontology coverage、unknown/unannotated 细胞占比和可重跑本体层。 |
| 留物种本体标签 benchmark | completed diagnostic | `release_metadata/species_ontology_label_benchmark_v9.md` | 复用冻结 runtime embedding；ontology-actionable coverage 为 74.44%，actionable all-cell accuracy 为 14.97%，用于定位跨物种迁移问题而非包装高分。 |
| STC 物种迁移校准层 | completed measured improvement | `release_metadata/cross_species_classifier_benchmark_v10.md`; `release_metadata/algorithm_innovation_v10.md` | 同一 frozen embedding 和同一 leave-species split 下，all-cell 23.64% -> 30.10%，known-label 42.28% -> 53.84%；创新性从工程整合提升为方法层。 |
| 开放集校准/选择性注释 | completed | `release_metadata/open_set_calibration_v9.md` | API top-30/top-40 selective accuracy 为 96.64%/92.81%，为低留物种 raw metric 提供可靠使用边界。 |
| Arabidopsis root 案例 | completed computational case | `release_metadata/plant_biology_case_study_v9.md`; `release_metadata/arabidopsis_root_case_figure_v9.md` | 展示生物学使用路径和 marker-candidate 输出。 |
| multi-species scPlantDB 案例 | completed computational case | `release_metadata/multispecies_scplantdb_case_v10.md` | 第二个 public-data biology case：31,503 细胞、4 物种、4 组织和 96 条 marker 候选。 |
| 投稿评分矩阵 | completed | `release_metadata/submission_scorecard_v11.md` | 所有可补强 evidence-readiness 模块达到 90+，并明确 raw metric 不虚假提分。 |
| 雪莲目标物种入口 | scoped | `release_metadata/saussurea_h5ad_contract.md`; `docs/saussurea_evidence_plan.md` | 说明接入条件，不夸大成已完成图谱。 |
| 后续训练日志隔离 | scoped outside editor package | internal continuation logs; current package keeps `release_metadata/multispecies_scplantdb_case_v10.md` only as a public-data biology case | 投稿包不使用探索性续训 checkpoint 作为性能证据，避免与冻结 v9 主张冲突。 |

## Revision v11 增强证据

下一轮 revision 已经有实证升级，而不只是计划。`release_metadata/revision_v11_fewshot_adapter_benchmark.md` 显示 target-species adapter protocol 已超过 40% all-cell 目标：每个 held-out 物种随机 8 个带标签 support 细胞时，query all-cell accuracy 为 59.21%（10 个随机种子均值）；16/32/64 个 support 细胞分别达到 67.34%/72.30%/75.89%。这个结果必须写作“带少量标注的目标物种适配”，不能写成 zero-shot leave-species。

`release_metadata/revision_v11_runtime_head_benchmark.md` 报告部署型 full-vocabulary runtime head 在同一 3,964 个对齐细胞上达到 66.25% all-cell accuracy，并拆分为 covered-label accuracy 62.86% 与 open-set-label accuracy 70.54%。`release_metadata/revision_v11_third_party_closure.md` 记录 scPlantLLM 官方权重下载/OID 审计和 scPlantAnnotate 认证边界；第三方闭环已有追踪文件，但正式数值仍等待可执行 metric JSON。

## 推荐投稿路径

### 当前可立即递交的稳妥路径

首选：Plant Communications 或同级植物方法/资源期刊。

写法：以植物单细胞注释资源和方法为主，标题不突出 Snow Lotus。主线强调 public plant corpus、adapter framework、strict benchmark、Seurat comparator、Arabidopsis root case 和 reproducible CUDA service。

必须使用的核心材料：

1. `SUBMISSION_INDEX_v9.md`
2. `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx`
3. `release_metadata/plant_cellfm_v9_model_card.md`
4. `release_metadata/publication_peer_review_preflight_v9.md`
5. `release_metadata/species_holdout_failure_audit_v9.md`
6. `release_metadata/open_set_calibration_v9.md`
7. `release_metadata/third_party_benchmark_contract_v10.md`
8. `release_metadata/multispecies_scplantdb_case_v10.md`
9. `release_metadata/submission_scorecard_v11.md`
10. `figures/plant_cellfm_v9_arabidopsis_root_case/`

### 冲 Genome Biology 的增强路径

当前可以作为 strong target，但建议补强：

1. 完成至少一个 official third-party model comparator 的冻结数值，优先 scPlantLLM；当前 contract 已齐，缺官方权重/probe JSON。
2. 将 multi-species scPlantDB case 加上更完整的文献 marker anchor 或独立数据复现；当前已经不是单一 Arabidopsis 案例。
3. 基于已完成的 STC benchmark、ontology-label species-holdout benchmark 和 open-set calibration，继续模型侧改进：species adapter calibration、open-set rejection、ortholog-aware tokenization 或独立物种复现实验。
4. 把全部 benchmark、open-set calibration 和 case source data 组织成 supplement tables。

### 冲 Nature Methods 的增强路径

当前属于 stretch，不建议把冻结 v9 直接包装成 Nature Methods 已足够。要接近该档，需要：

1. 明确算法新意，不只是工程整合：当前已新增 all-plant adapter materialization + STC classifier calibration + open-set reliability + ontology-aware evaluation；下一版要进一步把 STC 前移到模型训练内部或加入 ortholog-aware tokenization。
2. 与 scPlantLLM、scPlantAnnotate、Seurat、Scanpy ingest、marker-rule 等形成完整横向 benchmark。
3. 至少两个独立生物学应用，并有 marker 文献验证或实验验证；当前已有 Arabidopsis root 和 multi-species scPlantDB 两个 public-data case，但湿实验验证尚未闭合。
4. 提供软件可用性材料：安装、demo、API、模型下载、license、protocol-like user guide。

## 本轮不再扩大训练的收口原则

当前用户要求已经从“继续扩大训练”转为“先收尾到发表级”。因此 v9 冻结稿不再把新增大规模训练作为必要前置条件，而是优先做：

1. 统一叙事：所有正式入口使用 Plant-CellFM v9、4090、plant-general、all-plant adapter。
2. 证据闭环：zip manifest、GitHub commit、server checksum、model card、benchmark JSON 一致。
3. 审稿防线：低留物种指标用 failure audit、ontology benchmark 和 open-set calibration 解释，第三方工具缺失用 official-source benchmark contract 陈述。
4. 生物学展示：Arabidopsis root 与 multi-species scPlantDB case 作为可复现计算案例，而非湿实验结论。
5. 后续路线：只把未完成内容放在 next revision，不写成当前结果。

## 最短编辑回复口径

如果编辑催问当前版本完成度，可以这样说：

Plant-CellFM v9 has been frozen as a reproducible plant-general single-cell annotation framework. The current package includes the GitHub branch, release checkpoint with SHA256, model card, final Word manuscript, v9-v3 strict benchmark, Seurat comparator, species-holdout failure audit, species ontology coverage audit, ontology-label species benchmark, open-set calibration and selective annotation audit, third-party benchmark contracts, Arabidopsis root marker case, a multi-species scPlantDB public-data case, live CUDA service evidence and watchdog recovery evidence. The manuscript is intentionally scoped as a computational method/resource paper: it does not claim universal high-accuracy annotation for all plant species, does not claim a completed Snow Lotus atlas, and keeps scPlantLLM/scPlantAnnotate at their audited execution boundaries until official runs are available.
