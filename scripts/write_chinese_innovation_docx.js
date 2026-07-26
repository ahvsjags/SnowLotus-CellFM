const fs = require("fs");
const path = require("path");
const {
  AlignmentType,
  BorderStyle,
  Document,
  ExternalHyperlink,
  Footer,
  HeadingLevel,
  LevelFormat,
  Packer,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = require("docx");

const OUT_DIR = path.join(
  "editor_package",
  "current_submit_v0.3",
);
const DOCX_PATH = path.join(OUT_DIR, "SnowLotus_CellFM_中文功能创新说明_v0_1.docx");
const MD_PATH = path.join(OUT_DIR, "SnowLotus_CellFM_中文功能创新说明_v0_1.md");
const GENERATED_AT = "2026-07-26 15:25 Asia/Shanghai";
const REPO_URL = "https://github.com/ahvsjags/SnowLotus-CellFM";
const RELEASE_URL = "https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3";
const COMMIT_SHA = "088cd8a6b6fce2eadcfff01dbd3e6ecd402c5cf6";

const CONTENT_WIDTH = 9906;
const FONT = "Microsoft YaHei";
const DARK = "1F2937";
const BLUE = "1F4E79";
const LIGHT_BLUE = "D9EAF7";
const LIGHT_GREEN = "E2F0D9";
const LIGHT_YELLOW = "FFF2CC";
const LIGHT_GRAY = "F2F2F2";
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "C8D1DA" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

function textRun(text, options = {}) {
  return new TextRun({
    text,
    font: FONT,
    color: options.color || DARK,
    bold: options.bold || false,
    italics: options.italics || false,
    size: options.size || 22,
  });
}

function p(text, options = {}) {
  return new Paragraph({
    alignment: options.alignment || AlignmentType.LEFT,
    spacing: { before: options.before || 80, after: options.after || 80, line: 330 },
    children: [textRun(text, options)],
  });
}

function heading(text, level = 1) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 320 : 220, after: 140 },
    children: [
      textRun(text, {
        bold: true,
        size: level === 1 ? 30 : 25,
        color: level === 1 ? BLUE : DARK,
      }),
    ],
  });
}

function numbered(text, reference = "main-numbering") {
  return new Paragraph({
    numbering: { reference, level: 0 },
    spacing: { before: 60, after: 60, line: 320 },
    children: [textRun(text)],
  });
}

function callout(title, body, fill = LIGHT_YELLOW) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            borders: BORDERS,
            shading: { fill, type: ShadingType.CLEAR },
            margins: { top: 160, bottom: 160, left: 180, right: 180 },
            children: [
              new Paragraph({
                spacing: { after: 80 },
                children: [textRun(title, { bold: true, color: BLUE, size: 24 })],
              }),
              p(body, { before: 0, after: 0 }),
            ],
          }),
        ],
      }),
    ],
  });
}

function cell(text, width, fill = "FFFFFF", bold = false) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders: BORDERS,
    shading: { fill, type: ShadingType.CLEAR },
    margins: { top: 90, bottom: 90, left: 120, right: 120 },
    children: [
      new Paragraph({
        spacing: { before: 0, after: 0, line: 300 },
        children: [textRun(text, { bold, size: 20, color: bold ? BLUE : DARK })],
      }),
    ],
  });
}

function table(headers, rows, widths) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((item, idx) => cell(item, widths[idx], LIGHT_BLUE, true)),
      }),
      ...rows.map((row) =>
        new TableRow({
          children: row.map((item, idx) => cell(item, widths[idx])),
        }),
      ),
    ],
  });
}

function linkParagraph(label, url) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [
      textRun(label + "：", { bold: true }),
      new ExternalHyperlink({
        link: url,
        children: [new TextRun({ text: url, style: "Hyperlink", font: FONT, size: 22 })],
      }),
    ],
  });
}

const featureRows = [
  [
    "植物单细胞专用基础模型",
    "不是把通用单细胞模型硬套到植物，而是围绕植物跨物种、跨组织、跨数据格式的表达矩阵重新设计训练与审计流程。",
    "已实现 `snowcell train/build-corpus/predict`、公开语料构建、模型 checkpoint 与 SHA256 冻结。",
  ],
  [
    "gene set Transformer 输入范式",
    "每个细胞以高表达基因集合、表达值分桶、连续表达投影共同表示，天然适合不同测序平台和不同物种的 gene set 表达结构。",
    "模型含 gene token、value bins、value projection、species/tissue embedding 和层级注释头。",
  ],
  [
    "层级注释输出",
    "同时预测细胞细类与粗类，降低跨数据集标签粒度不一致造成的评估噪声。",
    "训练中包含 fine/coarse 分类、hierarchy loss、macro-F1/accuracy 评估。",
  ],
  [
    "自监督与监督混合训练",
    "用 masked gene modelling 学习植物表达结构，用标签任务保持可解释注释能力。",
    "当前公开 MLM 长训 48,558,596 trainable parameters，epoch 1 已出 eval loss 9.1896。",
  ],
  [
    "天山雪莲转移框架",
    "诚实区分“已有公开植物训练语料”和“尚待获得的雪莲单细胞矩阵”，把雪莲定位为高寒药用植物目标迁移场景。",
    "已写入 Saussurea 数据需求、h5ad contract、同源基因和 marker 验证路线。",
  ],
];

const pipelineRows = [
  ["数据发现", "NCBI/GEO/scPlantDB/scPlantLLM", "发现、筛选、下载候选公开植物单细胞/单核表达数据。"],
  ["数据审计", "manifest + integrity audit", "逐行检查矩阵是否存在、可读、是否具备训练所需 obs 字段。"],
  ["语料构建", "H5AD/NPZ/10x/Seurat RDS 转换", "合并成公开 plant foundation corpus，记录可用与不可用边界。"],
  ["模型训练", "hybrid/pretrain/fine-tune", "支持 CUDA、bf16、gradient checkpointing、LoRA/last-n/head-only 等模式。"],
  ["模型应用", "predict/annotation bundle/embedding export", "输出细胞类型、置信度、embedding、预测 CSV 和审计报告。"],
  ["对照评估", "centroid baseline、Seurat、scPlantLLM、scPlantAnnotate", "已搭好外部 benchmark 输入与审计，scPlantAnnotate 需要授权后执行。"],
  ["发布交付", "GitHub + editor zip + SHA256", "源码、模型说明、状态页、远程审计、校验和统一归档。"],
];

const evidenceRows = [
  ["远程执行", "SSH 新端口已恢复，别名 `matpool-px1-jcy` 指向 `px2-jcy.matpool.com:29153`。"],
  ["硬件状态", "替换服务器实测为 NVIDIA GeForce RTX 4090 24GB；CUDA 可用，GPU 长训正在运行。"],
  ["代码链路", "远程 pytest 已通过核心测试、on-disk corpus builder 测试、端口探测测试。"],
  ["公开语料", "恢复后公开 MLM corpus 为 71,330 cells x 49,106 genes，含 scPlantLLM SRP169576 与 scPlantDB SRP169576。"],
  ["真实训练", "scPlantDB smoke train 已完成：fine accuracy 0.5991，fine macro-F1 0.5908，coarse accuracy 0.5993。"],
  ["长训状态", "当前 public MLM run 已输出 epoch 1：train loss 9.4579，eval loss 9.1896，184 个 validation batches。"],
  ["模型资产", "冻结 annotation checkpoint 与 embedding checkpoint 均有 SHA256；完整模型包本地与远程一致。"],
  ["GitHub 同步", `仓库 main 与 editor-v0.3 tag 已同步到 commit ${COMMIT_SHA}。`],
];

const innovationRows = [
  ["创新 1", "把“植物单细胞注释”从脚本级流程升级为基础模型工程", "不仅能训练，还能构建 corpus、导出预测、生成数据卡、审计矩阵、维护模型 release。"],
  ["创新 2", "数据可用性审计前置", "在训练前明确哪些 GEO/scPlantDB 数据可读、哪些只是元数据或不兼容，避免论文中虚增数据规模。"],
  ["创新 3", "跨物种表达表示", "通过 species/tissue embedding、同源基因路线和 gene set Transformer，为 Arabidopsis/rice/maize/wheat/tomato 等跨物种迁移预留机制。"],
  ["创新 4", "层级标签鲁棒性", "细类和粗类双头减少不同数据集注释体系不一致带来的泛化问题。"],
  ["创新 5", "面向雪莲的可落地转化", "当前不伪造雪莲单细胞结果，而是准备好 h5ad contract、同源映射、marker 发现、LoRA 微调和实验验证清单。"],
  ["创新 6", "持续训练与可审计交付并行", "编辑可先拿到固定版本，同时服务器后台继续训练；每个版本通过 SHA256、状态页和远程审计追踪。"],
];

const deliverableRows = [
  ["源码与配置", "训练、预测、数据转换、审计、benchmark、远程运行脚本均已纳入仓库。"],
  ["模型权重", "annotation/embedding checkpoint 已冻结；完整模型包约 1.3GB，远程与本地 SHA 一致。"],
  ["编辑包", "包含主稿、cover note、README、状态页、远程审计、checksum 和 source archive。"],
  ["中文说明", "本文档可直接给编辑、审稿人或内部负责人快速展示项目创新与当前证据。"],
  ["后续升级", "数据队列、GEO/scPlantDB 补数、外部 benchmark、雪莲原始 h5ad 接入可继续推进。"],
];

const riskRows = [
  ["雪莲公开单细胞矩阵", "当前未确认有可复用公开 Snow Lotus scRNA/snRNA matrix。", "不把雪莲写成已完成 atlas；定位为目标迁移与实验验证框架。"],
  ["外部强基线", "scPlantAnnotate 等工具需要授权或特定环境。", "保留 authenticated benchmark 脚本与输入包，获得授权后补齐指标。"],
  ["新服务器硬件", "用户原期望 5090，但替换端口当前实测为 4090 24GB。", "状态页已改为实测硬件，不再沿用旧服务器表述。"],
  ["公开数据迁移", "旧服务器部分 GEO 矩阵未完全迁入新机器。", "已恢复核心公共语料，并继续修复 manifest ready 判定和数据队列。"],
];

const sections = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 180 },
    children: [textRun("SnowLotus-CellFM", { bold: true, size: 42, color: BLUE })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 260 },
    children: [textRun("天山雪莲与植物单细胞注释大模型功能创新说明", { bold: true, size: 30 })],
  }),
  p("版本：中文展示稿 v0.1", { alignment: AlignmentType.CENTER }),
  p(`生成时间：${GENERATED_AT}`, { alignment: AlignmentType.CENTER }),
  p("用途：给编辑、审稿人、合作方或内部负责人快速展示项目功能创新、工程完成度与当前证据边界。", {
    alignment: AlignmentType.CENTER,
  }),
  linkParagraph("GitHub 仓库", REPO_URL),
  linkParagraph("GitHub Release tag", RELEASE_URL),
  p(`当前同步 commit：${COMMIT_SHA}`),
  callout(
    "一句话定位",
    "SnowLotus-CellFM 是一个面向植物跨物种单细胞/单核表达数据的注释与表征基础模型工程。它不是单个分类脚本，而是覆盖公开数据发现、矩阵审计、语料构建、Transformer 训练、层级注释、外部 benchmark、模型发布与远程持续训练的一套完整系统；天山雪莲被定位为高寒药用植物的目标迁移与实验验证场景。",
    LIGHT_GREEN,
  ),
  heading("1. 为什么这个项目不是普通注释器", 1),
  p("普通注释器通常只解决“给一个 h5ad 输出 cell type”的单点问题。SnowLotus-CellFM 的核心差异在于，它把植物单细胞注释拆成可审计的基础模型工程：先证明数据能读、标签能追溯、训练能复现、模型能冻结，再谈雪莲迁移和生物学发现。"),
  ...[
    "它面向植物而不是泛动物单细胞：植物存在更强的跨物种基因命名差异、细胞类型标签体系不统一、公开数据格式高度碎片化。",
    "它面向基础模型而不是一次性分类：同时训练 masked gene modelling、表达值预测、细类/粗类注释，后续可继续微调到雪莲或其他药用植物。",
    "它面向投稿审计而不是展示幻灯片：每个数据集、checkpoint、模型包和服务器状态都有 manifest、checksum、状态页或远程审计。",
  ].map((item) => numbered(item)),
  heading("2. 核心功能创新矩阵", 1),
  table(["功能创新", "解决的问题", "当前实现证据"], featureRows, [2300, 3850, 3756]),
  heading("3. 全链路功能模块", 1),
  p("项目已经形成从数据到模型再到交付的闭环。下面这张表可以直接给编辑说明：这不是只写了想法，而是已有可运行命令、可复现脚本和可交付包。"),
  table(["模块", "代表组件", "功能说明"], pipelineRows, [2100, 3100, 4706]),
  heading("4. 技术路线亮点", 1),
  ...[
    "输入层：每个细胞取 top expressed genes，将 gene token、表达值分桶、连续表达投影、species/tissue embedding 组合成模型输入。",
    "主干层：采用 gene set Transformer，不依赖基因输入顺序，适合不同平台和不同物种的表达集合。",
    "任务层：联合训练细胞细类、细胞粗类、masked gene prediction、masked value prediction，兼顾注释和表征学习。",
    "微调层：支持 full、head-only、last-n-layers、LoRA 等微调方式，适合小样本雪莲数据接入。",
    "审计层：通过 split audit、centroid baseline、data integrity audit、model release manifest 避免训练和评估口径失真。",
  ].map((item) => numbered(item, "tech-numbering")),
  heading("5. 当前可展示证据", 1),
  table(["证据类别", "当前状态"], evidenceRows, [2450, 7456]),
  heading("6. 对编辑/审稿人的三个强回答", 1),
  callout(
    "问题一：这是不是只有概念，没有模型？",
    "不是。项目已经有可运行 CLI、远程 CUDA 训练、冻结 checkpoint、模型包 SHA256、GitHub source tag、编辑提交 zip 和远程审计文件。恢复后的服务器上已完成 smoke train/predict 和 scPlantDB 真实公开数据训练。",
    LIGHT_BLUE,
  ),
  callout(
    "问题二：为什么叫天山雪莲，是否已经有雪莲单细胞结果？",
    "当前版本不夸大。公开审计尚未确认可复用的 Snow Lotus 单细胞矩阵，所以本文把雪莲定位为目标迁移场景：模型、数据 contract、同源基因映射、marker 验证和 LoRA 微调路线已经准备好，待雪莲 h5ad 接入即可执行。",
    LIGHT_YELLOW,
  ),
  callout(
    "问题三：创新性在哪里？",
    "创新点不是单个神经网络结构，而是植物单细胞基础模型的工程化闭环：跨物种表达表示、层级注释、多任务自监督、数据可用性审计、外部 benchmark 接口、可追溯模型发布，以及面向高寒药用植物的目标迁移框架。",
    LIGHT_GREEN,
  ),
  heading("7. 可写入稿件的创新点", 1),
  table(["编号", "创新点", "可写法"], innovationRows, [1200, 3000, 5706]),
  heading("8. 面向天山雪莲的应用场景", 1),
  ...[
    "雪莲 h5ad 接入后，可先执行模型预测，输出每个细胞的细类、粗类、置信度和 embedding。",
    "对低温、低压、强紫外或缺氧处理样本，可比较 stress-response 相关细胞状态和 marker 基因富集。",
    "结合 Saussurea 基因组或同源基因映射，可把 Arabidopsis/rice 等公开模型知识迁移到雪莲基因命名体系。",
    "后续可用 RNA in situ、smFISH、qPCR 或 reporter 验证模型提出的 3-5 个关键 marker 或调控候选。",
  ].map((item) => numbered(item, "saussurea-numbering")),
  heading("9. 交付物清单", 1),
  table(["交付物", "说明"], deliverableRows, [2400, 7506]),
  heading("10. 当前边界与处理方式", 1),
  table(["边界/风险", "事实", "处理方式"], riskRows, [2200, 3650, 4056]),
  heading("11. GitHub 与提交口径", 1),
  p("给编辑或合作方时，建议采用下面口径："),
  ...[
    `源码仓库：${REPO_URL}`,
    `发布标签：${RELEASE_URL}`,
    `当前提交：${COMMIT_SHA}`,
    "如果仓库保持 private，需要先给编辑/审稿账号授权；如果用于匿名审稿，可以临时开放 release 或导出提交 zip。",
    "1.3GB 完整模型权重已在本地和远程服务器保留；GitHub Release 大文件上传需单独确认后再执行。",
  ].map((item) => numbered(item, "github-numbering")),
  heading("12. 下一版增强计划", 1),
  ...[
    "继续让远程 public MLM 长训完成更多 epoch，择优冻结新的 embedding checkpoint。",
    "修复并重启公开数据队列，补入更多 GEO/scPlantDB 可读矩阵，避免旧 manifest 指向缺失文件。",
    "补齐 Seurat/scPlantLLM/scPlantAnnotate 的公平外部 benchmark 指标。",
    "一旦获得雪莲单细胞/单核 h5ad，立即执行 contract 校验、LoRA 微调、marker 候选和实验验证图表。",
    "把中文说明、主稿、模型卡、数据可用性说明和 GitHub release 对齐成正式投稿版本。",
  ].map((item) => numbered(item, "next-numbering")),
  callout(
    "可以直接对外说的结论",
    "SnowLotus-CellFM 已经从方案推进到可运行、可训练、可审计、可交付的植物单细胞基础模型工程。当前版本足以展示功能创新和工程完成度；后续顶刊级强化重点是更大公开语料、强外部 benchmark 和真实雪莲单细胞矩阵接入。",
    LIGHT_GREEN,
  ),
];

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: 22, color: DARK },
        paragraph: { spacing: { line: 330 } },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: BLUE },
        paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0 },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: DARK },
        paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  numbering: {
    config: [
      "main-numbering",
      "tech-numbering",
      "saussurea-numbering",
      "github-numbering",
      "next-numbering",
    ].map((reference) => ({
      reference,
      levels: [
        {
          level: 0,
          format: LevelFormat.DECIMAL,
          text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 520, hanging: 300 } } },
        },
      ],
    })),
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 },
        },
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                textRun("SnowLotus-CellFM 中文功能创新说明  |  Page ", { size: 18, color: "666666" }),
                new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "666666" }),
              ],
            }),
          ],
        }),
      },
      children: sections,
    },
  ],
});

function markdownTable(headers, rows) {
  const head = `| ${headers.join(" | ")} |`;
  const sep = `| ${headers.map(() => "---").join(" | ")} |`;
  const body = rows.map((row) => `| ${row.map((item) => String(item).replace(/\n/g, "<br>")).join(" | ")} |`);
  return [head, sep, ...body].join("\n");
}

const markdown = `# SnowLotus-CellFM 天山雪莲与植物单细胞注释大模型功能创新说明

生成时间：${GENERATED_AT}

GitHub 仓库：${REPO_URL}

GitHub Release tag：${RELEASE_URL}

当前同步 commit：${COMMIT_SHA}

## 一句话定位

SnowLotus-CellFM 是一个面向植物跨物种单细胞/单核表达数据的注释与表征基础模型工程。它不是单个分类脚本，而是覆盖公开数据发现、矩阵审计、语料构建、Transformer 训练、层级注释、外部 benchmark、模型发布与远程持续训练的一套完整系统；天山雪莲被定位为高寒药用植物的目标迁移与实验验证场景。

## 核心功能创新矩阵

${markdownTable(["功能创新", "解决的问题", "当前实现证据"], featureRows)}

## 全链路功能模块

${markdownTable(["模块", "代表组件", "功能说明"], pipelineRows)}

## 当前可展示证据

${markdownTable(["证据类别", "当前状态"], evidenceRows)}

## 可写入稿件的创新点

${markdownTable(["编号", "创新点", "可写法"], innovationRows)}

## 当前边界与处理方式

${markdownTable(["边界/风险", "事实", "处理方式"], riskRows)}

## 可以直接对外说的结论

SnowLotus-CellFM 已经从方案推进到可运行、可训练、可审计、可交付的植物单细胞基础模型工程。当前版本足以展示功能创新和工程完成度；后续顶刊级强化重点是更大公开语料、强外部 benchmark 和真实雪莲单细胞矩阵接入。
`;

fs.mkdirSync(OUT_DIR, { recursive: true });
Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(DOCX_PATH, buffer);
  fs.writeFileSync(MD_PATH, markdown, "utf8");
  console.log(JSON.stringify({ docx: DOCX_PATH, markdown: MD_PATH, bytes: buffer.length }, null, 2));
});
