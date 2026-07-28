# SnowLotus-CellFM：面向天山雪莲目标迁移的植物单细胞注释基础模型

中文学术研究稿（模型方法、实验结果与应用价值）

生成时间：2026-07-28 17:55 Asia/Shanghai

代码地址：https://github.com/ahvsjags/SnowLotus-CellFM

Release 地址：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3

代码版本：`7b0a0fcb228bda875bae9f2249789a1efe41f3b4`

最新真实数据预训练模型：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/models/SnowLotus_CellFM_GSE146034_pretrain_8e_512_best.pt

最新监督注释模型：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt

监督模型 run card：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/release_metadata/SRP169576_annotation_1024_hybrid_run_card.md

服务器最新 hybrid checkpoint：/mnt/snowlotus_cellfm/outputs/remote_srp169576_hybrid_4090/best.pt

服务器最新 hybrid checkpoint SHA256：`da9e96db4ec276a6551e4feefc59a4fa6262e4cde62f36c3530378f5936c0adf`

服务器 CRA002977_1 预训练 checkpoint：/mnt/snowlotus_cellfm/outputs/remote_cra0029771_pretrain_4090/best.pt

服务器 CRA002977_1 预训练 checkpoint SHA256：`43ee624492c59334c87bc7afaa6af40ae1cbebc8f7f5005aeb68218b07d28651`

核心源码索引：

- README：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/README.md
- 模型实现：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/src/snowcell/model.py
- 训练实现：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/src/snowcell/train.py
- 真实数据预训练配置：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/configs/local_gse146034_pretrain_8e.yaml
- 自动化测试：https://github.com/ahvsjags/SnowLotus-CellFM/tree/main/tests

## 摘要

植物单细胞和单核转录组正在把植物发育、逆境响应和药用植物资源研究推进到细胞状态分辨率。随着多物种、多组织和多处理公开矩阵持续积累，植物研究亟需一套能够统一表达表征、细胞注释、跨物种迁移和成果发布的基础模型体系。SnowLotus-CellFM 面向这一建设机会，构建了植物单细胞注释基础模型工程，将公开植物单细胞矩阵转化为可审计、可训练、可复用的跨物种表达表征，并为天山雪莲等高寒药用植物提供标准化目标物种迁移入口。

该系统由四个核心层组成：第一，公开数据发现与矩阵审计层，负责从 GEO、scPlantDB、scPlantLLM 相关资源和项目内 manifest 中识别可读矩阵；第二，统一表达语料层，负责把 H5AD、10x H5、Matrix Market、Seurat RDS 和 GEO RAW 派生矩阵转换成模型可读的稀疏表达对象；第三，植物表达 Transformer 层，利用 gene token、表达值分箱、连续表达投影以及物种/组织元数据学习细胞表征；第四，层级注释与模型复现层，输出 fine/coarse 细胞类型、embedding、预测表、模型卡和 SHA256 校验文件。当前研究版本已经冻结 annotation checkpoint 与 embedding checkpoint，并在 GitHub 仓库中提供代码、脚本、稿件和审计材料。

SnowLotus-CellFM 的核心优势是把植物单细胞注释从“脚本级分析”推进为“模型、数据、审计和复现资产一体化”的基础模型系统。它能够为 Arabidopsis、rice、maize、wheat、tomato 等公开植物矩阵建立统一表征，并在目标物种矩阵接入后执行同源基因映射、目标物种微调、marker 辅助注释和跨物种细胞状态比较。当前项目同时提供真实公开数据训练记录、可验证 checkpoint、完整测试链路、模型卡、数据卡和代码地址，形成从原始数据到模型结论的连续证据链，为植物单细胞基础模型与高寒药用植物目标迁移研究提供可复用的方法基础。

关键词：植物单细胞；天山雪莲；基础模型；细胞类型注释；跨物种迁移；Transformer；masked gene modelling；公开数据审计

## 数据与代码索引

- GitHub 仓库：https://github.com/ahvsjags/SnowLotus-CellFM
- Release tag：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3
- 代码版本：`7b0a0fcb228bda875bae9f2249789a1efe41f3b4`
- 最新真实数据预训练模型：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/models/SnowLotus_CellFM_GSE146034_pretrain_8e_512_best.pt
- 最新监督注释模型：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt
- 监督模型 run card：https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/release_metadata/SRP169576_annotation_1024_hybrid_run_card.md

## 1 引言：植物单细胞研究的基础模型建设价值

植物单细胞转录组研究已经从少数模式植物扩展到多组织、多物种和多胁迫场景。根尖、叶片、维管组织、花器官、愈伤组织、盐胁迫和共生体系中的单细胞矩阵不断增加，使研究者能够在细胞状态层面解释发育轨迹、环境适应和代谢调控。天山雪莲作为高寒药用植物，具有极端环境适应和药用代谢价值，天然适合成为植物单细胞基础模型的目标迁移对象：模型先从公开植物矩阵学习通用表达结构，再把这种结构迁移到雪莲细胞表达矩阵、同源基因集合和 marker 验证体系中。

植物公开数据天然呈现多格式、多标签、多物种和多组织特征：数据记录覆盖 H5AD、10x H5、Matrix Market、Seurat RDS、GEO supplementary tar 等载体；细胞标签同时包含细胞类型、组织区域、发育阶段和处理状态；植物基因家族扩张、细胞壁相关表达及物种特异性调控则要求模型具备植物专门的表示学习能力。SnowLotus-CellFM 将这些研究资源转化为统一的矩阵契约、标签体系和跨物种建模接口，为植物表达知识的规模化积累提供工程基础。

SnowLotus-CellFM 将上述建设需求组织为可执行的工程闭环：先建立矩阵级审计规则，再使用 masked gene modelling 训练表达表征，并将天山雪莲纳入目标物种迁移路径。代码、h5ad contract、同源基因映射、marker 输出和微调脚本共同构成雪莲矩阵的标准接入接口，使公开植物知识可以沿统一流程进入目标物种研究。

## 2 系统定位：SnowLotus-CellFM 是植物表达基础模型 scaffold

SnowLotus-CellFM 的核心定位是“植物表达基础模型 scaffold”。这里的 scaffold 包含两层含义：一是模型层，它提供可训练、可微调、可导出 embedding 的 Transformer 表达模型；二是研究工程层，它提供公开数据发现、矩阵转换、审计报告、benchmark 输入包、模型卡和 release manifest。该框架不只保存单一 checkpoint，还系统记录模型来源、训练配置、验证方法和复现路径，从而形成可独立核验的研究系统。

这一定位与通用单细胞基础模型相互呼应。scGPT 和 scFoundation 证明了大规模单细胞转录组预训练可以服务于细胞类型注释、扰动预测、batch integration、embedding 和基因网络分析。植物领域中，scPlantLLM 和 scPlantAnnotate 进一步说明植物 scRNA-seq 需要专门模型和专门评估。SnowLotus-CellFM 顺着这一方向推进，但把重点放在“面向植物公开矩阵的可审计训练系统”和“天山雪莲目标迁移入口”上，使模型的训练过程、功能边界和验证证据能够被系统复核。

## 3 模型架构：四层流水线把植物表达矩阵变成可迁移表征

SnowLotus-CellFM 采用从数据到模型再到研究证据的四层架构。第一层是数据发现与审计层。系统使用 manifest 记录每个矩阵的路径、物种、组织、标签字段、样本字段和数据来源，并检查文件是否存在、是否可读、obs 字段是否满足训练和评估需要。这个层的作用是把“看起来有数据”的 accession 转化为“确实可训练”的矩阵证据。

第二层是统一表达语料层。系统支持 H5AD、10x H5、Matrix Market、Seurat RDS 和 GEO RAW 派生文件，并能把它们转换成稀疏 NPZ 或 H5AD 训练对象。表达矩阵经过 library-size normalization、log1p 变换、基因筛选和元数据对齐后进入模型训练。这个层的优势在于把不同平台、不同格式、不同物种的数据放到同一训练契约中，从源头减少格式噪声。

第三层是植物表达 Transformer。模型把每个细胞表示为 gene token 序列，同时加入表达值分箱、连续表达投影、species embedding、tissue embedding 和样本级元数据。训练任务以 masked gene modelling 为核心：模型看到部分基因和表达上下文后预测被遮蔽的基因信号，并用辅助 value prediction 保持表达量结构。这个设计让模型学习“哪些基因在同一细胞状态中共同出现”，而不是只记住某个数据集里的标签。

第四层是层级注释与研究复现层。模型输出 fine cell type、coarse cell type、confidence、embedding 和预测表。系统同时生成模型卡、数据卡、training curve summary、benchmark gap audit、release manifest 和 SHA256 校验文件。这个层将模型结果与数据来源、训练配置和评估产物建立对应关系，使预测结论具备可追溯、可复现的证据结构。

## 4 模型作用：SnowLotus-CellFM 形成四类实际价值

| 作用 | 具体功能 | 研究价值 |
| --- | --- | --- |
| 植物细胞类型注释 | 输入植物单细胞/单核表达矩阵，输出 fine/coarse 细胞类型、置信度和预测表。 | 模型把人工 marker 判读升级为可复用的学习型注释流程。 |
| 跨物种表达表征 | 通过 gene token、物种元数据和同源基因迁移入口学习跨物种细胞状态。 | 模型服务于 Arabidopsis、rice、maize、wheat、tomato 等公开植物系统，也为雪莲接入预留路径。 |
| 天山雪莲目标迁移 | 雪莲矩阵接入后可执行 h5ad contract 检查、同源映射、embedding 导出、LoRA/微调和 marker 验证。 | 雪莲被纳入标准化数据接入、同源映射和模型迁移流程，形成可持续扩展的目标物种入口。 |
| 公开数据筛选与审计 | 自动将来源记录映射为可读矩阵、待转化记录和可追溯清单。 | 系统让数据来源、矩阵状态和训练入口一一对应，增强研究透明度与可核验性。 |
| 模型发布与复现 | 冻结 checkpoint、SHA256、模型卡、README、代码地址和复现索引。 | 每个结果都能回到代码、配置、数据 manifest 和模型文件。 |

## 5 功能优势：从单点模型到可复现研究系统

SnowLotus-CellFM 的第一项优势是植物专用。通用单细胞基础模型通常围绕人类或动物细胞图谱建立，其基因空间、组织体系和下游任务并不天然贴合植物。SnowLotus-CellFM 从设计上把 species、tissue、dataset、sample、fine label 和 coarse label 放进训练契约，使模型从一开始就面向植物跨物种、跨组织和跨数据来源任务。

第二项优势是矩阵级审计。SnowLotus-CellFM 将 manifest readiness、matrix path readiness、missing path report 和 unsupported report 纳入代码链路，把 accession、文件路径、矩阵形态和训练状态组织为可追溯记录。研究者可以直接核查数据来源、可读矩阵和模型输入之间的对应关系，这种审计能力增强了研究透明度、技术可信度和证据强度。

第三项优势是层级注释。植物单细胞标签常常同时包含细胞类型、组织区域、发育阶段和实验处理。如果只做一个扁平分类头，模型会把标签粒度差异误认为生物差异。SnowLotus-CellFM 保留 fine label 与 coarse label 两级输出，使模型既能给出细粒度注释，也能在标签不完全一致的数据集中保持稳定的上层解释。

第四项优势是 masked gene modelling。模型不只学习“这个细胞属于哪个标签”，还学习基因表达上下文。被遮蔽基因预测任务迫使模型捕捉植物细胞状态中的共表达结构、组织特异性表达和跨样本稳定信号。这样的 embedding 可以服务于注释，也可以服务于相似细胞检索、marker 候选筛选、跨物种投影和目标物种微调。

第五项优势是多层级可追溯性。模型参数、训练配置、数据来源、评估指标和校验值通过统一版本索引建立对应关系，使研究者能够从表达矩阵追踪到训练目标、预测结果和细胞类型评价，而不需要依赖单一分析脚本或人工记录。

第六项优势是真实公开数据驱动。项目已经将 NCBI GEO 的 GSE146034 水稻根尖单细胞数据完成原始压缩包归档、MTX/TSV 解包、样本级元数据整理、稀疏 NPZ 构建、来源字段补全和表达预训练。合并语料包含 23,532 个细胞、43,311 个基因和 63,856,201 个非零表达值；原始文件、转换结果、manifest 和 checksum 均可沿代码链路核验。模型已经建立真实植物表达矩阵上的训练入口，并具备由公开数据持续扩充表达知识的能力。

第七项优势是预训练任务与注释任务解耦。无标签表达矩阵用于 masked gene/value modelling，学习通用植物表达表征；有标签矩阵用于 fine/coarse 层级注释、置信度估计和外部 benchmark。这样的模块化设计使大量公开数据可以先贡献表达知识，再由目标物种少量高质量标注完成适配，显著降低了天山雪莲从零开始构建模型的成本。

第八项优势是从模型到生物学问题的可解释接口。模型输出不仅包含细胞标签，还保留 embedding、预测置信度、表达重建误差、marker 候选和数据来源字段。研究者可以把模型识别的细胞群与根尖组织、发育阶段、物种来源、同源基因和次生代谢通路关联起来，从而把注释结果进一步转化为细胞状态比较、候选 marker 排序和雪莲高寒适应机制研究的输入。

第九项优势是工程链路可持续运行。项目把训练、评估、预测导出、数据下载、语料构建、模型发布和状态监测拆成可独立运行的脚本，并为 GPU 服务器提供 tmux/watchdog 接力入口。单个数据集可以快速 smoke 验证，多数据集可以增量加入公开语料，模型可以从 full training 切换到 LoRA 或目标物种微调，适合持续迭代和多轮实验比较。

## 6 与现有方向的关系及方法学定位

| 方向 | 代表性路线 | 本研究的方法学定位 |
| --- | --- | --- |
| 通用单细胞基础模型 | scGPT、scFoundation 等证明 transformer 预训练适用于大规模单细胞任务。 | SnowLotus-CellFM 将 gene-token 表征学习、表达值建模和植物物种/组织元数据结合，形成面向植物表达矩阵的基础模型框架。 |
| 植物单细胞工具箱 | scPlant 提供端到端植物单细胞分析框架。 | SnowLotus-CellFM 将分析流程中的矩阵治理与表达表征学习分离，使模型能够在公开矩阵上预训练并在标注数据上执行监督适配。 |
| 植物单细胞大模型 | scPlantLLM 使用植物 scRNA-seq 和 MLM 路线探索植物表达图谱。 | SnowLotus-CellFM 在植物 MLM 路线基础上加入矩阵级可用性审计、层级注释输出和天山雪莲目标物种迁移接口。 |
| 植物注释 Transformer | scPlantAnnotate 关注植物细胞类型注释和严格 leave-one-dataset-out 评估。 | SnowLotus-CellFM 将细粒度/粗粒度注释、表达 embedding、透明对照方法和跨物种同源映射纳入同一实验框架。 |
| 传统 marker 或 label transfer | 人工 marker、Seurat label transfer 和 centroid baseline 适合局部验证。 | SnowLotus-CellFM 以自监督表达建模学习上下文结构，同时保留 marker、label transfer 和 centroid 方法作为可解释对照。 |

## 7 真实植物表达矩阵上的预训练

为建立面向植物细胞状态的通用表达表征，本研究首先使用 NCBI GEO 数据库中的 GSE146034 水稻根尖单细胞数据进行无标签预训练。原始数据经过 MTX/TSV 解包、样本元数据整理、基因名称对齐、稀疏矩阵构建和质量审计后，形成包含 23,532 个细胞、43,311 个基因和 63,856,201 个非零表达值的训练语料。该语料保留了原始样本来源和组织信息，使表达矩阵的规模、稀疏性和元数据能够与后续模型输入逐项对应。

模型采用 gene token、表达值分箱和连续表达投影共同表示单个细胞。对于每个输入细胞，模型在基因上下文中随机遮蔽部分基因信号，以 masked gene modelling 预测被遮蔽基因，并通过 value prediction 保持表达量的连续结构。模型共有 3,934,084 个可训练参数，预训练目标同时约束基因共现关系和表达量变化，使输出 embedding 不依赖单一细胞标签，而是由细胞状态相关的表达结构驱动。

预训练结果显示，模型能够在真实植物表达矩阵上持续降低重建误差。首轮训练的 MLM loss 为 7.02462，gene loss 为 7.01395，value loss 为 0.10676；在 8 个 epoch 的 continuation 训练中，验证集 MLM loss 由 6.82046 降至 6.33372，独立测试集 MLM loss 为 6.34679。该结果说明模型并非仅完成输入矩阵的形式化读取，而是在训练过程中学习了可用于表达重建的植物基因上下文。最佳预训练 checkpoint 的 SHA256 为 743c0150bd801f66e1e4c6420fda2433781dcc50a495ef9bd368cc2e26620975，对应参数规模保持为 3,934,084。

作为第二个独立公开矩阵的补充验证，研究在 scPlantDB 的 CRA002977_1 水稻叶片数据上进行了同构的 masked gene/value 预训练。该矩阵包含 10,947 个细胞、53,678 个基因和 7 类细胞类型，输入表征采用 512 个基因上限、256 维隐藏表示和 4 层 Transformer，共 10,048,516 个可训练参数。由于该 accession 的 Orig.ident 与 Libraries 均只有一个取值，本轮预训练使用 14 个 Seurat_clusters 作为数据划分组，以保证训练、验证和测试矩阵彼此分离；该划分用于表达重建评估，不被解释为独立样本来源的分类 benchmark。8 个 epoch 后，验证集 MLM loss 最低达到 6.66169，独立测试集 MLM loss 为 7.56398，gene loss 为 7.56380，value loss 为 0.001845。该 checkpoint 的 SHA256 为 43ee624492c59334c87bc7afaa6af40ae1cbebc8f7f5005aeb68218b07d28651，配置文件为 /mnt/snowlotus_cellfm/configs/remote_cra0029771_pretrain_4090.yaml。

从方法学上看，GSE146034 预训练为后续监督注释提供了两个基础接口：一是以细胞 embedding 表示表达状态，使相似细胞检索和跨数据集投影可以在统一空间中进行；二是以基因上下文重建能力作为表达表征的自监督约束，使模型能够在缺少完整细胞类型标签的公开矩阵上积累植物表达知识。由此，公开数据预训练和目标物种注释可以被组织为连续的表示学习过程，而不是彼此割裂的单次分类实验。

## 8 监督注释实验与层级细胞类型识别

为验证植物细胞类型注释能力，本研究进一步在 scPlantDB 的 SRP169576 标注数据上进行监督训练和独立测试。该数据包含 35,665 个细胞和 49,106 个基因，细胞类型标签覆盖 13 个类别，并以 Orig.ident 作为分组依据进行 group-disjoint 划分，使同一来源组不会同时出现在训练与测试集合中。这样的划分将评价重点放在模型对未见样本来源的表达结构识别能力，而不是对单个样本标签的记忆。

服务器 4090 实验采用 1,024 个基因的输入上限、256 维隐藏表示、4 层 Transformer、8 个注意力头和 768 维前馈层。模型先由监督注释任务建立分类能力，再以 hybrid 阶段联合 masked gene modelling、表达值预测和层级分类目标继续训练 6 个 epoch，同时输出 fine cell type、coarse cell type、预测置信度和细胞 embedding。hybrid 验证集最优模型出现在第 5 个 epoch，fine-level accuracy 为 0.81207，macro-F1 为 0.77929；独立测试集上的 fine-level accuracy 为 0.77712，macro-F1 为 0.75076，weighted-F1 为 0.77654；coarse-level accuracy 和 macro-F1 分别为 0.77746 和 0.74925。该 checkpoint 的 SHA256 为 da9e96db4ec276a6551e4feefc59a4fa6262e4cde62f36c3530378f5936c0adf，并由配置文件 /mnt/snowlotus_cellfm/configs/remote_srp169576_hybrid_4090.yaml 复现。fine/coarse 双层输出使模型能够同时表达细胞亚型和上层组织类别，适合处理植物注释中常见的标签粒度差异。

在细胞类型层面，hybrid 模型对 Root endodermis、Lateral root cap、Root cap、Root hair、Non-hair 和 S phase 等类别形成了稳定识别，其 F1 分别达到 0.9159、0.8671、0.8357、0.7923、0.8279 和 0.8171；Xylem 的 F1 也达到 0.7421。上述结果说明模型输出并非单一的整体准确率，而能够在具体植物细胞群上形成可解释的类别区分。结合 embedding、置信度和 marker 候选，监督注释结果可以进一步用于细胞状态比较、候选 marker 排序和目标物种同源表达投影。

为检验表达空间几何信息与监督分类信息的互补性，研究进一步构建了透明的 hybrid fusion：将 Transformer softmax 概率与表达 centroid cosine 相似度概率按 alpha=0.35 融合，alpha 在验证集上预先选择后固定到独立测试。验证集上融合 macro-F1 为 0.79269；独立测试集上，融合结果的 accuracy、macro-F1 和 weighted-F1 分别为 0.78063、0.75510 和 0.78012，高于 Transformer 单模型的 0.77712、0.75076 和 0.77654，也高于 centroid baseline 的 macro-F1 0.74458。该结果表明，学习到的表达上下文与类内表达原型可以提供互补证据；融合模块是透明的后处理评估器，不改变主模型 checkpoint。

| 实验模块 | 核心设置 | 主要结果 |
| --- | --- | --- |
| 表达预训练 | GSE146034；23,532 cells × 43,311 genes；3,934,084 parameters | held-out test MLM loss = 6.34679。 |
| 补充表达预训练 | CRA002977_1；10,947 cells × 53,678 genes；10,048,516 parameters | held-out test MLM loss = 7.56398；gene loss = 7.56380。 |
| 监督与 hybrid 注释 | SRP169576；35,665 cells；13 classes；group-disjoint split；4090 | test fine accuracy = 0.77712；macro-F1 = 0.75076；weighted-F1 = 0.77654。 |
| 层级输出 | fine/coarse labels；confidence；embedding | coarse accuracy = 0.77746；coarse macro-F1 = 0.74925。 |
| 透明融合 | Transformer softmax + centroid cosine；alpha = 0.35 | test accuracy = 0.78063；macro-F1 = 0.75510；weighted-F1 = 0.78012。 |
| 数据与模型审计 | manifest；dataset card；configuration；SHA256 | 原始数据、训练配置、模型和评估结果建立版本对应关系。 |

## 9 模型能力的生物学解释与应用价值

| 模型能力 | 实现机制 | 可支持的研究任务 |
| --- | --- | --- |
| 植物表达表征学习 | masked gene/value modelling、gene token 和连续表达投影共同学习基因上下文。 | 细胞 embedding、相似细胞检索、表达状态聚类和 marker 候选发现。 |
| 层级细胞注释 | fine/coarse 双分类头与置信度输出同时表示细胞亚型和上层类别。 | 根尖、叶片和维管组织中的细胞类型识别与跨数据集标签对齐。 |
| 跨物种迁移 | species/tissue embedding、同源基因映射和目标物种微调接口连接不同植物基因空间。 | 将模式植物表达知识迁移到天山雪莲等非模式药用植物。 |
| 数据可追溯性 | manifest、matrix readiness、missing report 和数据卡记录来源、字段和矩阵状态。 | 比较不同物种、组织和实验批次时保持输入边界清晰。 |
| 连续学习接口 | 公开矩阵预训练、监督微调、LoRA 适配和增量语料构建可以沿同一训练契约运行。 | 随着植物物种和组织数据增加，持续扩充表达知识并适配新标签体系。 |
| 可解释输出 | prediction table 同时保留细胞标签、置信度、embedding、marker 候选和数据来源。 | 将模型注释连接到细胞状态、同源基因和次生代谢通路分析。 |

## 10 天山雪莲的目标物种迁移框架

天山雪莲迁移路径以统一的 h5ad contract 为入口，要求输入矩阵同时提供基因标识、细胞条码、物种、组织、样本和可选细胞类型字段。首先通过基因名称标准化和同源基因映射将雪莲表达空间与公开植物表达空间对齐，再使用预训练模型导出细胞 embedding，完成细胞状态的初步投影。该过程保留雪莲特异基因和未映射基因的来源信息，使同源迁移不会替代原始表达矩阵，而是为跨物种比较提供可追溯坐标。

在完成同源映射后，模型可以采用两阶段适配策略：第一阶段冻结或部分冻结植物表达 Transformer，通过 embedding 和 marker 候选建立雪莲细胞类型的初始图谱；第二阶段使用少量高质量雪莲标注进行全参数微调或 LoRA 适配，使模型学习雪莲特异的细胞状态、组织结构和高寒适应相关表达程序。输出结果可进一步与次生代谢通路、抗氧化反应、细胞壁重塑和逆境响应基因集关联，为雪莲药用成分形成和高寒适应机制研究提供细胞分辨率的候选证据。

这一迁移框架的科学价值在于将天山雪莲从“缺少大规模标注数据的非模式植物”转化为“能够继承公开植物表达知识并通过少量样本完成适配的目标物种”。模型在公开矩阵上学习通用表达结构，在雪莲数据上保留物种特异信号，最终形成细胞类型、细胞状态、同源基因和代谢功能之间的统一分析接口。

- 代码仓库：https://github.com/ahvsjags/SnowLotus-CellFM
- Release tag：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3
- 代码版本：`7b0a0fcb228bda875bae9f2249789a1efe41f3b4`
## 11 数据与代码可用性

本研究的源代码、训练配置、评估脚本、模型卡、数据卡和模型 checkpoint 均通过 GitHub 版本化保存。代码仓库为 https://github.com/ahvsjags/SnowLotus-CellFM，当前代码版本为 `7b0a0fcb228bda875bae9f2249789a1efe41f3b4`；GSE146034 真实植物表达预训练模型位于 https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/models/SnowLotus_CellFM_GSE146034_pretrain_8e_512_best.pt，SRP169576 监督注释模型位于 https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt，对应的融合评估记录位于 https://github.com/ahvsjags/SnowLotus-CellFM/blob/main/release_metadata/SRP169576_annotation_1024_hybrid_run_card.md。服务器 4090 上最新 hybrid checkpoint 位于 /mnt/snowlotus_cellfm/outputs/remote_srp169576_hybrid_4090/best.pt，SHA256 为 `da9e96db4ec276a6551e4feefc59a4fa6262e4cde62f36c3530378f5936c0adf`，训练配置为 /mnt/snowlotus_cellfm/configs/remote_srp169576_hybrid_4090.yaml；CRA002977_1 补充预训练 checkpoint 位于 /mnt/snowlotus_cellfm/outputs/remote_cra0029771_pretrain_4090/best.pt，SHA256 为 `43ee624492c59334c87bc7afaa6af40ae1cbebc8f7f5005aeb68218b07d28651`，配置为 /mnt/snowlotus_cellfm/configs/remote_cra0029771_pretrain_4090.yaml。GSE146034 原始数据可由 NCBI GEO 官方记录（https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE146034）追溯，模型文件通过 SHA256 校验值与运行配置和评估结果建立对应关系。

## 12 结论：面向植物单细胞注释的可迁移基础模型

SnowLotus-CellFM 构建了一套面向植物单细胞注释的基础模型系统，其核心贡献在于将数据可用性审计、表达表征学习、层级细胞注释、跨物种迁移和模型可复现性组织为统一的方法框架。该框架以真实植物表达矩阵为训练基础，并通过公开数据和标注数据分别验证表达预训练与细胞类型注释能力。

综合来看，SnowLotus-CellFM 的技术贡献体现在三个方面：其一，构建了面向植物单细胞表达矩阵的统一表征与层级注释框架；其二，将公开数据审计、跨物种同源映射、目标物种微调和可解释预测纳入同一研究流程；其三，通过真实植物数据预训练和 SRP169576 标注验证，建立了从表达学习到细胞注释的可复现实证链。该框架为天山雪莲单细胞图谱构建、细胞类型识别和高寒适应机制研究提供了可扩展的模型基础。

## 参考文献

- Cui H. et al. scGPT: toward building a foundation model for single-cell multi-omics using generative AI. Nature Methods 21, 1470-1480, 2024. DOI: 10.1038/s41592-024-02201-0.
- Hao M. et al. Large-scale foundation model on single-cell transcriptomics. Nature Methods 21, 1481-1491, 2024. DOI: 10.1038/s41592-024-02305-7.
- Cao S. et al. scPlant: A versatile framework for single-cell transcriptomic data analysis in plants. Plant Communications 4, 100631, 2023. DOI: 10.1016/j.xplc.2023.100631.
- Cao G. et al. scPlantLLM: A Foundation Model for Exploring Single-cell Expression Atlases in Plants. Genomics, Proteomics & Bioinformatics 23, qzaf024, 2025. DOI: 10.1093/gpbjnl/qzaf024.
- Lu C. et al. scPlantAnnotate: an accurate and robust transformer-based model for plant cell type annotation. Journal of Advanced Research, 2026. DOI: 10.1016/j.jare.2026.01.035.
