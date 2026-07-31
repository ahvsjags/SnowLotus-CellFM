# Plant-CellFM 顶刊组图调研与主图蓝图 v1

**用途。** 本文档把 Plant-CellFM 的现有证据链转化为可投稿的主图方案。它借鉴的是顶刊论文的叙事结构、证据分层与版面逻辑，不复制任何已发表图的内容、插图或视觉资产。当前建议以 6 幅主图 + 6--8 幅 Extended Data / Supplementary Figures 组织；每幅主图采用 1 个占 40--55% 画布的 hero panel 与 4--7 个互补证据面板，形成高证据密度的非对称页。若目标期刊对主图数较严格，可将图 4 与图 6 合并为 5 幅主图。

**核心叙事一句话。** Plant-CellFM 以植物同源基因映射、物种/器官上下文和可解析的全植物适配层，将跨物种单细胞注释从“直接 label transfer”推进为可审计的严格 zero-shot、低标注物种适配和运行时开放集注释三种互不混淆的使用模式。

## 1. 已检索的高水平论文及其可复用的组图逻辑

| 论文 | 相关图组结构 | 对 Plant-CellFM 的可复用原则 | 不应照搬的部分 |
|---|---|---|---|
| [scGPT, Nature Methods, 2024](https://www.nature.com/articles/s41592-024-02201-0) | Fig. 1 先交代模型；Fig. 2 先给核心注释任务；后续主图分别展示扰动、多组学、嵌入和可解释性。 | 一个主图只回答一个问题；模型能力不要堆在同一面板。 | 不以人类多组学任务数量替代植物跨物种证据。 |
| [Nicheformer, Nature Methods, 2025](https://www.nature.com/articles/s41592-025-02814-z) | Fig. 1 把语料、token 化、架构和下游任务放在一条视觉链；Fig. 2 独立量化训练语料；Fig. 4 将空间实例、基准和 UMAP 并列。 | Fig. 1 必须同时解释“数据为何足以支撑模型”和“模型如何使用上下文”；比较基准必须带真实应用实例。 | 不把空间组学能力写入目前未训练的 Plant-CellFM 主张。 |
| [Universal Cell Embedding, Nature, 2026](https://www.nature.com/articles/s41586-026-10689-z) | Fig. 2 将 zero-shot 定义图、未见数据 UMAP、跨物种预测串成同一证据链；Fig. 3 用本体层级验证表示空间的生物学合理性。 | 严格 zero-shot 首先需要把训练/测试隔离画清楚，再给数字；再以本体或生物学层级解释嵌入空间。 | 不只给 UMAP 作为泛化证据，也不将“可视化分群”替代量化准确率。 |
| [scPlantLLM, GPB, 2025](https://academic.oup.com/gpb/article/23/3/qzaf024/8081791) | Fig. 1 工作流与预训练嵌入；Fig. 2--3 各自用独立测试数据展示 zero-shot；Fig. 4 专门展示 fine-tuning；后续再给 GRN 与效率。 | 将 strict zero-shot 与 few-shot / fine-tune 拆成不同图；用 Sankey、混淆矩阵和 marker 验证构成同一任务的三层证据。 | 不把 zero-shot 与 few-shot 放在同一柱状图中比较后宣称同一泛化水平。 |
| [Orthologous marker groups, Nature Communications, 2025](https://www.nature.com/articles/s41467-024-55755-0) | Fig. 1 为三步同源 marker 流程 + 15 个物种的数据覆盖；Fig. 2 用跨物种热图、UMAP 与显著性框回答实际转移是否成立。 | 植物跨物种图必须把“基因家族扩张 / 一对多同源”这一核心难题可视化；物种尺度与组织覆盖需要量化。 | 不能将简单的一对一 ortholog 矩阵包装成覆盖复杂植物基因家族的解决方案。 |
| [Arabidopsis life-cycle atlas, Nature Plants, 2025](https://www.nature.com/articles/s41477-025-02072-z) | Fig. 1 用时间/组织采样、UMAP、空间数据交代资源；Fig. 2 以空间定位和 marker 表达验证注释；后续图聚焦新生物学。 | 生物学案例必须包含“模型输出 -- marker / 外部证据 -- 可解释的细胞状态”三段，而非只放 marker 热图。 | 没有空间数据时，不使用伪空间定位或暗示湿实验验证。 |
| [Unified vascular-plant cell atlas, Cell, 2025](https://www.sciencedirect.com/science/article/abs/pii/S009286742500858X) | 图谱资源、细胞类型基础基因、基因发现和自动注释工具构成“资源到发现再到工具”的闭环。 | 把通用模型定位为能产生可检验候选 marker / 基础基因的研究基础设施，而非单纯分类器。 | 不在没有独立实验或文献锚定时，把候选 marker 写成已验证调控因子。 |

### 从上述论文得到的共同模板

1. **Fig. 1 是证据链入口，而不是 PPT 架构页。** 顶刊模型论文一般将数据范围、标准化、模型输入、模型输出和一个真实用途放进同一张图；其中数据覆盖和模型创新都必须有可量化面板。
2. **最严格的评价独占一幅图。** 对本项目即为 v14 strict leave-species zero-shot STC。图中必须呈现训练/测试物种隔离、exact-label 分母、55.90% label coverage 和 Gossypium hirsutum 的 exact open-set 状态。
3. **同一结果的最小证据单元为“定义 + 总体数值 + 异质性”。** 例如协议示意、总体 point estimate / 置信区间、按物种/组织拆分的热图或 forest plot。只给总体准确率最容易被追问。
4. **案例图需有独立生物学闭环。** 合格顺序是输入数据与模型预测、细胞状态/marker 证据、可解释的生物学结果。现有 Arabidopsis root 图可作为后两段，但前段必须新增 query-cell UMAP 或 annotation overlay。
5. **系统工程和训练效率不抢主结论。** CUDA 服务、watchdog、显存/吞吐、完整 manifest 和 API 截图应成为 Extended Data 或 Supplementary Note；它们证明可复现性，却不是核心生物学创新。

## 2. Plant-CellFM 主图蓝图

### Figure 1 | 从植物表达矩阵到可审计的全植物注释

**图要回答的问题：** 为什么 Plant-CellFM 是植物通用模型，且为什么它的跨物种设计不是普通 label transfer？

| 面板 | 内容与作图类型 | 已有输入 / 待生成数据 | 结论责任 |
|---|---|---|---|
| a | 植物谱系 + 物种/组织/细胞数量覆盖的分层气泡图或矩形树图。 | corpus manifest、species ontology、scPlantDB case。 | 训练与测试数据的植物多样性可见。 |
| b | 数据规范化与同源映射流程：原始 gene IDs -> ortholog / shared-gene vocabulary -> cell-state ontology。用窄长流程图。 | 数据卡、ontology mapping、ortholog map。 | 说明植物基因家族和标签异质性如何被显式处理。 |
| c | 模型架构：frozen encoder、LoRA、24 个动态 adapter、STC context gate、open-set confidence、输出三种模式。 | 模型卡、adapter registry、v14/v15 methods。 | 突出全植物 adapter + context-aware STC 的方法核心。 |
| d | 一个 query cell 从表达向量到“strict zero-shot / few-shot adapter / runtime annotation”三条路径的结果示例。 | 运行服务输出与实例细胞。 | 让读者在 Fig. 1 就理解后续所有指标属于不同使用模式。 |

**版式。** 采用 Nicheformer 型的 `a,b` 横向数据-处理链为主视觉，`c` 为右下大架构，`d` 为下方窄条实例。全图不放完整 benchmark 数字，只放数据量、物种数、adapter 数和任务名称。

### Figure 2 | 严格跨物种 zero-shot：上下文门控提高可迁移注释，同时保持开放集边界

**图要回答的问题：** 在不使用被留出物种标签的严格协议下，模型到底提高了多少，代价和失败模式是什么？

| 面板 | 内容与作图类型 | 现有证据 | 关键写法 |
|---|---|---|---|
| a | leave-species-out protocol 图：held-out species 的 labels 以锁定图标显示；仅训练物种提供标签和 phylogeny/organ context。 | `revision_v14_context_stc_benchmark.*`。 | 明确 `no held-out species labels`。 |
| b | 从 v3、v9、v10、v13 到 v14 的严格 all-cell accuracy 阶梯 / point-range 图；v14 为主色。 | v9--v14 benchmark JSON。 | 只比较完全一致的 strict 分母；不要放 v15。 |
| c | 按物种的 all-cell accuracy、known-label accuracy、coverage 三轨 forest plot 或 aligned dot plot。 | v14 per-species JSON。 | 让总体 42.36% 的物种异质性透明化。 |
| d | coverage--accuracy 二维散点：每个物种一个点，`G. hirsutum` 标注为 exact open-set label。 | v14 audit。 | 将 55.90% coverage 和开放集困难转成清楚的科学边界。 |
| e | label ontology / organ-context 消融：no context、organ-only、phylogeny-only、phylo-organ gate。 | v14 method rows。 | 证明增益来自设计而不是换了评测口径。 |

**必须固定的数字。** v14 strict all-cell accuracy `42.36%`；known-label accuracy `75.77%`；coverage `55.90%`；macro-F1 `0.3045`。所有图例和 caption 必须说明：这不是 full-vocabulary runtime 指标。

### Figure 3 | 统一 benchmark 面板：内部升级、传统基线与审计式外部比较

**图要回答的问题：** 模型对不同留出方式是否稳定，且是否相对现有可执行方法有增益？

| 面板 | 内容与作图类型 | 现有输入 | 放置原则 |
|---|---|---|---|
| a | 3 x 2 benchmark grid：leave-dataset、leave-sample、normalized leave-species；accuracy 与 macro-F1 两列。 | `v9_lora_vs_v3_shared_comparison.json`。 | 主文只展示同一冻结数据、同一分割下的 completed rows。 |
| b | 传统方法对比：Plant-CellFM、centroid、Seurat；点估计 + bootstrap CI。 | Seurat / centroid benchmark exports。 | 勿将未闭合的 scPlantLLM / scPlantAnnotate 画成 0、NA 或弱于本模型。 |
| c | error taxonomy：标签别名、organ mismatch、exact open-set、低置信度，各类的细胞数与准确率。 | failure audit、ontology coverage audit。 | 把审稿人会问的错误来源主动回答。 |
| d | representation quality：可选择一个 held-out species UMAP，左右以真值与预测着色，并用 marker 叠加小图验证。 | frozen embeddings + compatible labels。 | UMAP 只能作案例，主结论来自 a--c 的量化图。 |

**第三方模型规则。** scPlantLLM / scPlantAnnotate 在得到可复现的官方预测前只放入 Extended Data 的“execution status and input contract”表。主文绝不把它们伪装成完成的横向数值。

### Figure 4 | 从严格 zero-shot 到少量标注物种适配：adapter 的可量化收益

**图要回答的问题：** 当新植物物种可提供极少量标注细胞时，适配层是否以可预测的方式提高准确率？

| 面板 | 内容与作图类型 | 现有输入 | 结论责任 |
|---|---|---|---|
| a | zero-shot、1/2/4/8-shot、full runtime 的模式图；训练/查询细胞绝不重叠。 | v11 few-shot protocol。 | 把“模式不同”可视化。 |
| b | support budget -- query all-cell accuracy 曲线，按物种细线、总体粗线，bootstrap CI。 | v11 few-shot JSON。 | 显示 8 support cells 的 `59.21%` 是 query 指标。 |
| c | 物种 x support budget heatmap，突出难物种与易物种。 | v11 per-species results。 | 不以整体平均掩盖种间差异。 |
| d | adapter resolution / ortholog coverage 与收益的关联散点。 | adapter registry、species mapping coverage。 | 给出可解释的“何时值得适配”。 |

### Figure 5 | Arabidopsis root：模型注释引出可解释的根系细胞身份与 marker 候选

**图要回答的问题：** 输出能否转化为可被植物研究者阅读与复查的细胞身份及 marker 候选？

| 面板 | 内容与作图类型 | 现有输入 | 需要调整 |
|---|---|---|---|
| a | query root cells 的 UMAP：人工/参考标签与 Plant-CellFM 输出并列，附 small Sankey 或 confusion inset。 | root matrices、predictions、existing case metadata。 | 新增；这是目前案例图缺少的“模型输出”第一段。 |
| b | 13 个 cell states 的 marker dot plot 或紧凑 heatmap。 | 现有 `arabidopsis_root_top_marker_matrix_source_v9.tsv`。 | 改造现有热图，删去图内大标题，保留 5--8 个最有判别力的 identity。 |
| c | 260 个 marker candidates 的 effect-size / detection-rate scatter。 | 现有 source TSV。 | 保留现有图逻辑，但仅直接标注 8--12 个高价值候选。 |
| d | root identity marker strength + 2--3 个文献锚定 marker 的表达 feature plots。 | 现有 summary TSV + marker literature anchors。 | 从“候选列表”提升到“生物学一致性证据”。 |

**现有图的定位。** `figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.png` 的 b--d 面板有可复用的数据价值，但它更像补充材料中的 marker-candidate 图。升级后应作为 Figure 5 的 b--d，去掉页面级标题，新增 a 的真实 query-cell annotation，并压缩 b 的行数以确保期刊缩小后可读。

### Figure 6 | 面向真实植物数据的开放集部署与可复现资源

**图要回答的问题：** 在实际输入中，模型如何拒绝低置信度预测、何时调用 runtime head，以及读者如何复现实验？

| 面板 | 内容与作图类型 | 现有输入 | 关键边界 |
|---|---|---|---|
| a | confidence-gated runtime-teacher rescue 流程：confidence >= 0.70 进入 teacher；其余回退 v14。 | v15 script and report。 | 标注为 deployment/readiness protocol。 |
| b | strict v14、v15 fallback rescue、v15 full runtime head 的三指标分面图。 | v14/v15 JSON。 | 不能用同一标题把 v15 写成 strict zero-shot。 |
| c | open-set exact accuracy 与 teacher-acceptance rate 的 threshold 曲线。 | v15 threshold sweep。 | 将部署折中透明化。 |
| d | 可复现资源卡：checkpoint、source code、benchmark JSON、source data、adapter registry、CUDA API。 | model/data card、manifest、service audit。 | 用极简图标/清单，不放终端截图。 |

## 2A. 视觉密度与冲击力升级版式

### 统一的“高密度而不拥挤”规则

- **每张图一眼只读到一个结论。** 用跨行/跨列 hero panel 承担结论，其他小面板只回答“为什么可信、对谁有效、何时失效”。小面板不再平铺为等大的六宫格。
- **每张图都必须有三层视觉节奏。** 远看是一个主形状或主趋势；中看能读到量化差异；近看有样本量、CI、物种标签、marker 或错误类别等可复查细节。
- **以数据纹理增加密度。** 将点估计升级为 jittered cells / bootstrap distribution、按物种分层、注释式热图、marker micro-panels 和 transparent source-count；不用阴影、渐变球、装饰边框或无信息图标凑密度。
- **稀有的强调色只服务结论。** Plant-CellFM 为深青蓝，strict v14 为同一蓝系中最深色，v15 deployment 为琥珀橙，baseline 为冷灰，open-set / abstention 为紫色；全文颜色保持一一对应。
- **用共享视觉元素把面板粘成一页。** Fig. 1 定义的物种图标、细胞状态颜色、adapter 六边形和 protocol 锁定符号贯穿全文；同类 method 在所有图中使用同一色系、线型和 marker 形状。
- **避免“满屏小字”。** 每幅图最多 2 个密集文字区域（通常为热图行标签或方法表头）；其他面板用直接标注和共享 legend strip。论文最终缩小后，关键数字和物种名必须仍高于 5 pt。

### Figure 1：数据规模 + 模型机制的主视觉页

**推荐版式：asymmetric schematic-led composite，约 183 x 150 mm。**

```text
┌───────────────────────────────a  Plant phylogeny + corpus coverage (55%)─────────────────────────────┐
│  plant lineages / species / organs / cells, with adapter availability and open-set query icons        │
├────────────b  ortholog + ontology mapping (22%)─────────────┬──────────c  Plant-CellFM architecture (23%)──┤
│  gene-family expansion -> shared vocabulary -> state terms  │  frozen encoder, LoRA, adapters, context gate   │
├──────────d  three annotation modes (35%)──────────┬──────────e  query-cell trace (30%)──┬──f  stats card (35%)──┤
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **hero a：** 不只画分布图。以淡灰植物谱系树作骨架，叠加物种节点大小（cell count）、扇形环（organ count）、短色条（available adapters），右端单独放 query species / open-set 的虚线节点。该面板让“全植物”在第一眼成立。
- **b--c：** 以一条连续的 gene-to-cell-to-label 信息流穿过两个面板。b 内呈现一对多同源这一植物难点，c 中将 context token、adapter 和 confidence gate 画为与 b 相同颜色的模块。
- **d--f：** d 用三段式模式带区分 strict、few-shot 和 runtime；e 以一条真实细胞的 token / adapter / label trace 作为微观实例；f 只放 4 个大数字（物种、组织、adapter、aligned cells）而不放性能指标。
- **冲击来源：** 植物谱系大面板 + 同源映射流线，而非一个普通 Transformer 方框图。

### Figure 2：严格泛化的“证据墙”

**推荐版式：quantitative asymmetric grid，约 183 x 145 mm。**

```text
┌────a  locked leave-species protocol (25%)────┬──────────────────b  strict-performance ladder (75%)──────────────────┐
│  train species / held-out species / labels    │  v3 -> v9 -> v10 -> v13 -> v14; bootstrap distributions + deltas    │
├────────────────────────────c  species-level accuracy/coverage forest hero (60%)─────────────────┬──d  error anatomy (40%)──┤
│   three aligned tracks: all-cell / known-label / coverage; organism silhouettes at left          │  open-set / aliases / tissue mismatch │
├───────────────────────────────e  accuracy-versus-coverage map (45%)─────────────┬──f  context ablation (55%)──────┤
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **hero c：** 每个物种显示三个 point-range / lollipop 轨道，同列可比较。用一根细透明线连同一物种的 all-cell 与 known-label 数值；这会使“覆盖不足而非模型全面失败”的结构一眼可见。
- **b：** 不用单柱图。放 repeated bootstrap dots 与粗体中位数，v14 以深蓝突出，且在顶部以箭头注明提升幅度。所有版本共享同一 strict denominator 的锁形标记。
- **d：** 以 100% 堆叠错误谱 + 1 个放大的 `G. hirsutum` exact open-set badge 构成“失败模式放大镜”，让低 coverage 成为透明贡献而非图外备注。
- **f：** context 组件采用同一蓝色 alpha 由浅到深，层次直观；每项都标注 n 和 delta，不使用彩虹色。
- **冲击来源：** 物种异质性 forest hero 和 open-set failure anatomy，共同构成可信而有张力的主视觉。

### Figure 3：基准比较的“竞技场”

**推荐版式：dense quantitative grid，约 183 x 145 mm。**

```text
┌────────────a  benchmark matrix / dataset x split x metric (55%)──────────────┬──b  method ranking + CI (45%)──┐
│  3 evaluation regimes x accuracy/macro-F1; proposed method column highlighted │  Plant-CellFM / centroid / Seurat │
├────────────c  effect-size / gain distribution across resamples (38%)──────────┼──d  calibrated confusion inset (27%)──┤
├─────────────────────e  held-out embedding / true-vs-predicted paired UMAP (35%)───────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **hero a：** 使用带 cell count / split label 的矩阵，不用只显示颜色的热图。每格给数值、CI 短线及相对 v3 的小箭头，既密集又可读。
- **b：** 采用 horizontal point-range 排名，不拉大无关的 0--100 坐标范围；Plant-CellFM 始终在最上、深色；基线冷灰色。
- **c：** 以每个 resample 的 gain distribution 取代另一张重复柱图，显示增益不是单一运行的偶然数值。
- **d--e：** d 只显示最易混淆的 8--12 个 state，e 以相同细胞的 ground truth / prediction 成对 UMAP 加 marker micro-inset，完成“数字--错误--细胞”的视觉链。
- **冲击来源：** a 的高密度 benchmark matrix，配合 e 的双 UMAP，从工程指标快速落到真实细胞结构。

### Figure 4：少量标注带来的适配跃迁

**推荐版式：trajectory-led composite，约 183 x 135 mm。**

```text
┌────────a  support/query isolation schema (22%)───┬──────────────b  support-budget trajectory hero (58%)─────┬──c adapter anatomy (20%)──┐
│                                                    │  0,1,2,4,8 support cells; species thin lines + mean CI    │                     │
├───────────────────────d  species x budget heatmap (55%)───────────────────────┬──e  gain vs mapping coverage scatter (45%)──┤
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **hero b：** 把每个物种的少量标注提升画成细线，并将总体中位线变粗；在 `8` support cells 处用 ring callout 标出 59.21% query all-cell，而不是一行文字。
- **d：** heatmap 同时编码增益和难物种；与 b 使用相同物种顺序和颜色。
- **e：** 以 ortholog / mapping coverage 为 x 轴，accuracy gain 为 y 轴，点大小为 query-cell count。这个关系面板将 adapter 提升变成可解释规律。
- **冲击来源：** “少量标注 -> 明显跃迁”的斜率与物种级差异，而不是普通 bar chart。

### Figure 5：从细胞图到 marker 的生物学案例页

**推荐版式：image-plate-plus-quant（白底单细胞图谱），约 183 x 150 mm。**

```text
┌─────────────────────────────a  paired root-cell atlas hero (52%)───────────────────────────┬──b label-flow Sankey (18%)──┤
│  same UMAP coordinates: reference labels / Plant-CellFM labels / confidence; selected cell states outlined │                         │
├─────────────────────────c  compact identity marker heatmap (30%)──────┬─────d feature-plot triptych (25%)───┬──e candidate landscape (45%)──┤
├──────────────────────────────────f  effect-size / detection-rate scatter + literature-anchor callouts (100%)───────────────────────────┤
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **hero a：** 不是单张 UMAP，而是共享坐标的三联 atlas：reference identity、model output、confidence / abstention。白底、半透明细胞点、加粗描边的根冠/维管 identity 让远看也能分辨结构。
- **b：** 用小而清晰的 Sankey 显示 reference state 到预测 state 的映射，只有 flow >= 3% 的边被保留；该面板对编辑特别有效。
- **c--d：** c 只保留 6--8 个最能区分 identity 的行，d 三个 feature plots 共享色条；全量 marker matrix 移到 Extended Data。
- **e--f：** e 将 260 marker candidates 的全景变成气泡云，f 放大效应最强、且有文献锚定的 8--12 个点，配以连线 / label。这样案例既有“多”又有“深”。
- **冲击来源：** triple UMAP atlas + marker 证据链，而不是单一热图。

### Figure 6：部署可信度与开放集决策页

**推荐版式：risk-coverage-led composite，约 183 x 140 mm。**

```text
┌────a  strict-to-runtime decision schematic (30%)────┬────────────b  risk-coverage curve hero (55%)─────────────┬──c threshold card (15%)──┐
│  v14 fallback -> confidence -> teacher / abstention  │ accuracy, coverage, open-set exact rate across thresholds │ t0.70 operating point     │
├──────────────────d  all-cell / known / open-set three-way comparison (60%)──────────────┬──e per-species deployment map (40%)──┤
├──────────────────────────────────────────f  reproducibility resource strip (100%)───────────────────────────────────────────┤
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **hero b：** 以 threshold 连续曲线替代散碎柱图；三条曲线统一 x 轴为 teacher confidence。`t=0.70` 用一条浅橙竖线和一个只含三行数字的小卡片标出。
- **d：** 只用同一测试分母下的 strict v14、fallback rescue、full runtime head，横向三段 point-range；标题和图例中直接标注 protocol class，避免读者误混淆。
- **e：** 对所有物种显示 deployment gain / teacher acceptance / open-set exact 的蜂群或 tile map，保留 `G. hirsutum` 失败点作为可信边界。
- **f：** 用 6 个等距 resource glyph（checkpoint、code、data card、benchmark JSON、adapters、API）和 checksum / reproducible 字样形成干净的收束，不放任何 terminal 或网页截图。
- **冲击来源：** risk--coverage 曲线把“更高准确率”变成可控的部署决策，而非额外数字堆叠。

### 渲染前必须补齐的 source-data 表

高密度不能用未计算的误差条或模拟重复来填充。开始渲染前应从冻结 benchmark 重新导出以下表；若某表当前无法得到，则相应面板改为点估计 + 完整 source-data，而不虚构 CI。

| 图 | 必需的新增 / 规范化表 | 允许的替代方案 |
|---|---|---|
| Fig. 2b--f | 每物种、每 seed / bootstrap replicate 的 v3/v9/v10/v13/v14 accuracy、macro-F1、coverage 与 component ablation。 | 尚未完成 bootstrap 时保留 point estimate，并把 CI 面板移至 Extended Data。 |
| Fig. 3a--c | 3 种 split、每个 comparator、每个 resample 的共同 metric table。 | 无 resample 的 comparator 只显示点估计，不与有 CI 的方法做显著性宣称。 |
| Fig. 4b--e | support budget x species x random support draw 的 query metrics、ortholog coverage、query-cell count。 | 只有 aggregated results 时，主图只画总体曲线，物种 heatmap 置补充材料。 |
| Fig. 5a--f | root query-cell embedding coordinates、reference labels、model predictions、confidence、marker expression 与 literature-anchor table。 | 没有独立 marker 文献锚定前，只称 candidate markers。 |
| Fig. 6b--e | v15 全部 threshold、per-species runtime / rescue results、teacher acceptance 与 open-set decomposition。 | 若无完整阈值扫表，主图保留 t=0.70 operating point 与三协议比较。 |

## 3. 完整 Supporting Package：Extended Data、补充图、补充表与 Source Data

### 3.1 支撑材料的分层规则

| 层级 | 放什么 | 读者问题 | 不放什么 |
|---|---|---|---|
| Extended Data | 与主图同一结论、但因密度或完整性不能放入主文的关键证据。 | “主图的结论在每个物种、fold、阈值下仍成立吗？” | 与主图无关的训练日志或部署截图。 |
| Supplementary Figures | 全量审计、错误剖面、完整参数扫描、输入准备和额外案例。 | “我能否复查每个技术边界和负面结果？” | 与 Extended Data 重复的简化总览图。 |
| Supplementary Tables | 可搜索、可下载、可复算的数值和元数据。 | “分母、标签、参数、数据来源分别是什么？” | 不能被复算的宣传性评分或长段落。 |
| Source Data | 每个数据图的绘图输入，保留 panel-level tidy table。 | “图中的每个点、线、柱来自哪里？” | 原始 H5AD/模型权重等超大文件。 |
| Supplementary Notes | 复杂方法、评测边界、第三方工具执行条件和资源获取步骤。 | “严格协议与部署协议是否被清楚区分？” | 主结论的替代文本。 |

### 3.2 Extended Data（9 幅，直接守住主结论）

| 编号 | 图组与面板 | 对应主图 | 现有输入 | 当前状态 / 缺口 |
|---|---|---|---|---|
| Extended Data Fig. 1 | **全植物训练语料质量与覆盖。** a 物种 x 组织 x cells composition；b detected genes / counts QC ridge plots；c shared-gene / ortholog coverage；d train-test phylogenetic distance。 | Fig. 1 | `plant_general_corpus_species.tsv`、`model_data_card.*`、corpus provenance / integrity audit。 | 可导出；需整理成单一 plotting table。 |
| Extended Data Fig. 2 | **标签本体与跨物种覆盖审计。** a raw labels -> canonical states Sankey；b alias frequency；c covered / open-set cells by species；d exact-label examples。 | Fig. 1, 2 | `plant_cell_state_ontology_mapping_v9.tsv`、species ontology coverage audit、failure audit。 | 可导出；必须保留 exact open-set 分母。 |
| Extended Data Fig. 3 | **v14 strict zero-shot 的完整 fold 证据。** a all-cell/known-label/coverage per species；b fine-label confusion matrix；c top error pairs；d species-wise macro-F1。 | Fig. 2 | `revision_v14_context_stc_benchmark.*`、species holdout failure audit。 | 可导出；需统一每物种可视化表。 |
| Extended Data Fig. 4 | **context-aware STC 的机制与消融。** a no-context / organ / phylogeny / combined gate；b sensitivity to metadata availability；c seed stability；d case-level gate routing。 | Fig. 2 | v10/v13/v14 result JSON 与 v14 methods。 | 需要确认完整 component / seed result；无数据不画 CI。 |
| Extended Data Fig. 5 | **多协议 benchmark 的完整矩阵。** a v3-v9 gain across split；b centroid / Seurat detailed rows；c split audit；d normalized vs exact-label metric reconciliation。 | Fig. 3 | `v9_benchmarks/*`、`external_benchmark_panel_v9.*`、Seurat export、strict benchmark audit。 | 可导出；第三方未闭合模型只展示状态，不绘数值。 |
| Extended Data Fig. 6 | **few-shot adapter 稳定性。** a 10 seeds distribution；b every species x support budget；c support/query overlap audit；d query-cell-number sensitivity。 | Fig. 4 | `revision_v11_fewshot_adapter_benchmark.json`。 | 可导出；将 10 seeds 明确呈现而非只报均值。 |
| Extended Data Fig. 7 | **root case 的全量 marker 证据。** a 13-state full marker heatmap；b all feature plots；c complete candidate scatter；d marker annotations / evidence tier。 | Fig. 5 | root case source TSV、`plant_biology_case_study_v9.*`。 | 可导出；独立文献锚定需补充后才能标为 validated。 |
| Extended Data Fig. 8 | **独立多物种 scPlantDB 生物学案例。** a 4 species x 4 tissues composition；b state-marker heatmap；c 96 marker candidates；d one non-Arabidopsis focus panel。 | Fig. 5 | `multispecies_scplantdb_case_v10.*`、marker-candidate TSV。 | 可导出；优先选择数据量和标签结构最完整的非 Arabidopsis 物种。 |
| Extended Data Fig. 9 | **runtime / 开放集部署审计。** a complete threshold sweep；b per-species rescue / runtime decomposition；c confidence distribution；d teacher acceptance and abstention map。 | Fig. 6 | `revision_v15_runtime_teacher_rescue.*`、`open_set_calibration_ontology_curve_v9.tsv`。 | 可导出；所有标题必须标 deployment protocol。 |

### 3.3 Supplementary Figures（13 组，确保审稿人可逐层复查）

| 编号 | 图组 | 审稿人问题 | 主要输入 | 状态 |
|---|---|---|---|---|
| Supplementary Fig. 1 | Public-data discovery、纳入/排除流图与每个 accession 的可用性。 | 数据是否经过选择性筛选？ | public discovery manifests、corpus provenance audit。 | 可导出。 |
| Supplementary Fig. 2 | 每个数据集的 QC、细胞数、基因数、稀疏度和 batch composition。 | Fig. 1 的语料质量是否均一？ | v9 data card、dataset manifests。 | 需导出统一 QC 表。 |
| Supplementary Fig. 3 | ortholog / shared-vocabulary mapping 的保留率、gene-family multiplicity 与未映射基因类别。 | 植物一对多同源问题被如何处理？ | ortholog map、model data card。 | 需补充 mapping summary。 |
| Supplementary Fig. 4 | 原始标签、别名、canonical ontology state、organ context 的完整映射与冲突审计。 | 标签规范化会不会制造性能增益？ | ontology mapping TSV、coverage / failure audit。 | 可导出。 |
| Supplementary Fig. 5 | v9、v10、v13、v14 的 held-out species 全量 confusion / error atlas。 | v14 的提升来自哪些标签，哪些仍失败？ | revision JSON、species failure audit。 | 需整合绘图表。 |
| Supplementary Fig. 6 | 完成型 comparator 的参数、输入、split、运行时间与结果审计。 | Plant-CellFM 与 centroid / Seurat 是否公平比较？ | external benchmark panel、Seurat exports、centroid outputs。 | 可导出。 |
| Supplementary Fig. 7 | scPlantLLM / scPlantAnnotate 的官方权重、API / 认证、input package、缺失 artifact 与 closure criteria。 | 为什么第三方数值尚未出现在主图？ | third-party contract、access audit、closure audit。 | 可导出；只写审计事实。 |
| Supplementary Fig. 8 | 全 adapter registry：物种、组织、本体覆盖、mapping coverage、available / resolved status。 | “all-plant adapter layer”具体包含什么？ | `plant_species_adapters.json`、adapter registry。 | 可导出。 |
| Supplementary Fig. 9 | few-shot 的每个 seed、每个 support draw、per-species error pairs 与 support-label diversity。 | 8-shot 增益是否稳健？ | v11 few-shot JSON。 | 可导出。 |
| Supplementary Fig. 10 | v15 每个阈值的 per-species accuracy、open-set exact、teacher acceptance 与 fallback 行为。 | t=0.70 是否为选择性报告？ | v15 JSON。 | 可导出。 |
| Supplementary Fig. 11 | Arabidopsis root 全量 state-specific feature plots、候选 marker 排名与 literature-anchor matrix。 | 根系案例的每个候选是否可追溯？ | root source data、marker literature table。 | feature plots 可导出；文献表待补。 |
| Supplementary Fig. 12 | multi-species scPlantDB 的完整数据切片与 96 marker candidate 全景。 | 生物学案例是否只在 Arabidopsis 成立？ | multi-species case JSON / TSV。 | 可导出。 |
| Supplementary Fig. 13 | 环境锁定、checkpoint / source-data checksum、CUDA smoke test 和 watchdog recovery。 | 代码和模型能否被他人复现？ | release manifest、environment snapshot、API / watchdog audit。 | 可导出；采用矢量状态图，不截终端图。 |

### 3.4 Supplementary Tables（13 张，可搜索且可复算）

| 表 | 内容 | 精确来源 | 作用 | 状态 |
|---|---|---|---|---|
| Supplementary Table 1 | 公开训练/评测数据集清单：accession、物种、组织、技术、细胞数、用途、许可 / 可访问状态。 | corpus manifest、public discovery manifests。 | 锁定数据分母与来源。 | 可导出。 |
| Supplementary Table 2 | 语料纳入、排除和 QC 阈值的逐数据集记录。 | data integrity / provenance audit。 | 排除选择偏倚。 | 可导出。 |
| Supplementary Table 3 | canonical plant cell-state ontology、原始标签别名、组织上下文及映射理由。 | `plant_cell_state_ontology_mapping_v9.tsv`。 | 允许复查标签标准化。 | 可导出。 |
| Supplementary Table 4 | 每物种的 shared genes、ortholog mapping coverage、gene-family multiplicity 和 adapter resolution。 | mapping summary、adapter registry。 | 支撑“植物通用”而非单物种说法。 | mapping summary 需导出。 |
| Supplementary Table 5 | Plant-CellFM architecture、LoRA、token / embedding、optimization、checkpoint 和推理配置。 | model card、configs、release manifest。 | 完整方法可复现。 | 可导出。 |
| Supplementary Table 6 | 全部 split definition、train/test cells、label coverage、open-set cells、evaluation denominator。 | strict benchmark audits、v14 / v15 JSON。 | 消除不同协议的分母歧义。 | 可导出。 |
| Supplementary Table 7 | strict zero-shot per-species 指标：all-cell、known-label、macro-F1、coverage、open-set。 | v14 JSON。 | 支持 Fig. 2 与 ED3。 | 可导出。 |
| Supplementary Table 8 | v3、centroid、Seurat 的输入、参数、结果与可复现性状态；scPlantLLM/scPlantAnnotate 单列为 pending audit。 | external benchmark panel、third-party contracts。 | 公平地组织横向比较。 | 可导出。 |
| Supplementary Table 9 | few-shot every seed x species x support budget 的 query metrics、support/query cell counts。 | v11 few-shot JSON。 | 支持 Fig. 4 / ED6。 | 可导出。 |
| Supplementary Table 10 | runtime / rescue 全阈值、每物种 deployment metrics、teacher acceptance、open-set decomposition。 | v15 JSON、calibration curve TSV。 | 支持 Fig. 6 / ED9。 | 可导出。 |
| Supplementary Table 11 | Arabidopsis root 全部 marker candidates、效应量、检测率、细胞状态、证据等级、文献锚定。 | root source TSV、marker literature anchor。 | 将生物学案例变成可再利用资源。 | 候选数据可导出；文献锚定待补。 |
| Supplementary Table 12 | multi-species scPlantDB 细胞状态、组织、marker candidates、物种比较统计。 | multi-species case TSV / JSON。 | 给出第二个生物学支点。 | 可导出。 |
| Supplementary Table 13 | 软件、环境、硬件、模型文件 SHA256、脚本命令、随机种子与输出路径清单。 | environment snapshot、release manifest、training configs。 | 复现与长期保存。 | 可导出。 |

### 3.5 Source Data 与 Supplementary Notes 的提交结构

| 文件组 | 应包含的 tidy 数据 | 对应图 / 表 |
|---|---|---|
| Source Data Fig. 1 | species / organ / cells counts、ortholog coverage、adapter counts、query trace values。 | Fig. 1, ED1--2。 |
| Source Data Fig. 2 | strict v3--v14 summary、per-species v14 metrics、coverage / error class、ablation records。 | Fig. 2, ED3--4。 |
| Source Data Fig. 3 | all completed comparator rows、split audit、resample records、embedding plotting coordinates。 | Fig. 3, ED5, Supplementary Fig. 5--7。 |
| Source Data Fig. 4 | every support draw / seed、query metrics、ortholog coverage、adapter resolution. | Fig. 4, ED6, Supplementary Fig. 8--9。 |
| Source Data Fig. 5 | root UMAP coordinates、predictions、confidence、marker expression / effect size、multi-species marker tables。 | Fig. 5, ED7--8, Supplementary Fig. 11--12。 |
| Source Data Fig. 6 | threshold sweep、rescue/runtime per-species metrics、teacher acceptance、resource manifest identifiers。 | Fig. 6, ED9, Supplementary Fig. 10 / 13。 |
| Supplementary Note 1 | 数据收集、基因 ID / ortholog 处理、标签本体与质量控制。 | Tables 1--4、ED1--2。 |
| Supplementary Note 2 | 严格 zero-shot、few-shot 与 deployment 三种协议的形式化定义和禁止混报规则。 | Fig. 2, Fig. 4, Fig. 6。 |
| Supplementary Note 3 | 全部 benchmark、外部 comparator 执行合同、缺失 artifact 与 closure criteria。 | Fig. 3、ED5、Supplementary Fig. 6--7。 |
| Supplementary Note 4 | 生物学案例、marker-candidate 生成规则、文献锚定与可检验性。 | Fig. 5、ED7--8。 |
| Supplementary Note 5 | 安装、复算、checkpoint、release checksum、API / watchdog 与长期可用性。 | ED9、Supplementary Fig. 13、Table 13。 |

### 3.6 支撑材料的生产顺序

1. 先导出 Supplementary Tables 1、3、5、6、7、9、10、13；它们定义所有图的分母、标签和协议。
2. 再用这些整洁表生成 Extended Data Fig. 1--6；主图的数据可由同一张 source-data 表派生，防止两个版本的数字不一致。
3. 完成根系和多物种案例的 Table 11--12、ED7--8 与 Supplementary Fig. 11--12；没有文献锚定时统一写为 candidate。
4. 最后编排 Supplementary Fig. 7 与 Table 8，完整展示第三方比较的执行状态，但不伪造缺失的模型输出。

### 3.7 自动化顶刊图版审稿代理

项目内的 `agents/top_journal_figure_auditor/` 保存代理规则、经过验证的顶刊锚点库和评分准则。它以 8 篇相关的 Nature / Nature Methods / Nature Plants / Cell / GPB 论文与 Nature 官方图件规范为初始语料，后续只允许加入可验证的原始论文或官方期刊规范。

```powershell
python scripts/audit_top_journal_figure_suite.py
```

运行后会更新：

- `release_metadata/top_journal_figure_audit_latest.md`
- `release_metadata/top_journal_figure_audit_latest.json`

代理会检查 6 幅主图、9 幅 Extended Data、13 组补充图、13 张补充表、6 组 Source Data、5 个 Supplementary Notes 是否全部被规划；随后按 `release_metadata/top_journal_figure_asset_manifest.json` 检查最终 SVG/PDF/TIFF/PNG 是否存在、SVG 文本是否可编辑、TIFF/PNG 分辨率是否足够。最终投稿放行还必须完成视觉审阅，静态检查不能代替人工/视觉代理对层级、可读性、遮挡、色彩和信息密度的判断。

## 4. 统一视觉模板与导出约束

### 全文统一规则

- 主图宽度按双栏 `180--183 mm` 设计，最大高度 `170 mm`；单栏图 `89--90 mm`。Nature 的官方说明要求 panel label 约 `8 pt` bold，其他文字缩小后 `5--7 pt`，并建议将线宽控制在 `0.25--1 pt`。参考：[Nature final submission](https://www.nature.com/nature/for-authors/final-submission)、[Nature figure guide](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/)。
- 同一图内只用一种 sans-serif 字体（Arial/Helvetica），纯数据图白底；只有真实显微/空间图像的图像板可使用黑底。
- 全文固定方法色：`Plant-CellFM` 深青绿；`v14 strict` 深蓝；`v15 deployment` 暖橙；经典 baseline 中性灰；开放集/拒识浅紫；对照真值深灰。颜色不得仅靠红绿区分。
- 每个面板左上角用小写粗体 `a, b, c...`，不使用带底色的大型字母标签；不在图像内部放总标题，标题由 legend 承担。
- 所有统计图都提供 source-data TSV/CSV、样本量、重复定义、误差条含义和精确评测分母；每一张多面板图导出为一个单独文件。GPB 也明确要求多面板作为一个图文件提交并在左上角标面板字母。[GPB author instructions](https://academic.oup.com/GPB/pages/general-instructions)。
- 导出 `PDF/SVG`（可编辑矢量）以及 `TIFF 600 dpi`（含线条时优先 600--1200 dpi）；文本不能 rasterize 或转 outlines。

### 当前根系图的版面修订原则

- 删除画布顶端的 `Plant-CellFM v9 Arabidopsis root...` 大标题；这会在期刊 caption 存在时造成重复。
- 将现有 b 面板热图行数从 10 个 identity 压缩为 6--8 个，并将完整版本放 Extended Data。
- c 面板减少重叠 gene label，仅保留最强、最具生物学解释的 8--12 个；其他点保留无标签。
- d 面板采用固定色标或单色柱，不再同时出现单独 colorbar 和柱颜色梯度，避免编码冗余。
- 对 a 面板新增同一嵌入空间的真值/预测并列 UMAP，保证它首先是“模型生物学案例”，其次才是 marker 资源图。

## 5. 现有证据到作图数据的映射

| 图 | 可直接使用的项目证据 | 目前缺口 | 生成优先级 |
|---|---|---|---|
| Fig. 1 | model card、data card、adapter registry、ontology map、corpus manifest。 | 需要统一统计表和架构 schematic 源文件。 | P0 |
| Fig. 2 | `revision_v14_context_stc_benchmark.json`、coverage/failure audit。 | 需要统一 bootstrap CI 和 species-level plotting table。 | P0 |
| Fig. 3 | v9-v3 comparison、centroid、Seurat、error taxonomy。 | 需要规范化的共同 evaluation table；第三方模型数值仍不可用。 | P0 |
| Fig. 4 | `revision_v11_fewshot_adapter_benchmark.json`、adapter registry。 | 需要检查每物种 support-budget 结果是否齐全。 | P1 |
| Fig. 5 | root figure source TSV、260 marker candidates、root case metadata。 | 需要 query-cell predictions / UMAP 和文献锚定 marker。 | P1 |
| Fig. 6 | `revision_v15_runtime_teacher_rescue.json`、service/model/data card。 | 需要用同一分母绘制 threshold sweep 和 resource manifest card。 | P1 |

## 6. 明确的风险控制

1. Fig. 2 严格 zero-shot 只能报告 `42.36%` all-cell accuracy，不得用 v15 的 `60.09%` 或 `66.25%` 覆盖其标题或图例。
2. `Gossypium hirsutum` 的 exact open-set label 是结果边界，应在 Fig. 2d 直接标出而非隐藏。
3. 在 scPlantLLM/scPlantAnnotate 尚未形成可复现官方预测前，主图只使用已经完成的 v3、centroid 和 Seurat 数值；其余作为审计状态。
4. Arabidopsis case 的 marker candidates 是计算候选；除非有独立文献或实验验证，不称为新调控因子。
5. 天山雪莲只作为后续 target-species adapter / application extension，不作为已经完成的单细胞图谱主结论。

## 7. 推荐落地顺序

1. 先生成 Fig. 2（最严格结果）和 Fig. 3（完整 benchmark），二者决定方法论文是否站得住。
2. 再把现有根系图升级为 Fig. 5，补齐模型输出、marker 证据与文献锚定。
3. 然后绘制 Fig. 1 的模型/数据概览，确保它引用的是已经冻结的统计结果。
4. 最后生成 Fig. 4、Fig. 6 与全部 Extended Data，统一字体、颜色、caption 和 source-data package。
