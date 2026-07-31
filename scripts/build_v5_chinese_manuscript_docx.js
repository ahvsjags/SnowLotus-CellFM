"use strict";

/* Build a clean Chinese submission manuscript from the evidence-first v5 Markdown. */

const fs = require("fs");
const path = require("path");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  HeadingLevel,
  ImageRun,
  Packer,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = require("docx");

const root = path.resolve(__dirname, "..");
const inputPath = path.resolve(root, process.argv[2] || "manuscript/Plant_CellFM_v5_顶刊证据主文.md");
const outputPath = path.resolve(root, process.argv[3] || "manuscript/Plant_CellFM_v5_顶刊证据主文.docx");
const figureDir = path.join(root, "figures", "plant_cellfm_submission_v5", "main");
const extendedFigureDir = path.join(root, "figures", "plant_cellfm_submission_v5", "extended_data");
const font = "Microsoft YaHei";
const ink = "18242E";
const teal = "007C83";
const muted = "60717D";
const pale = "F4F7F8";
const line = { style: BorderStyle.SINGLE, size: 1, color: "D8E0E4" };
const borders = { top: line, bottom: line, left: line, right: line, insideHorizontal: line, insideVertical: line };

function text(value, options = {}) {
  return new TextRun({ text: value, font, size: 20, color: ink, ...options });
}

function clean(value) {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`(.*?)`/g, "$1")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1 ($2)");
}

function paragraph(value, options = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 125, line: 296, ...options.spacing },
    children: [text(clean(value), options.run || {})],
  });
}

function heading(value, level) {
  const sizes = { 1: 29, 2: 24, 3: 21 };
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 280 : 210, after: 120 },
    children: [new TextRun({ text: clean(value), font, size: sizes[level], color: level === 1 ? ink : teal, bold: true })],
  });
}

function tableCell(value, width, isHeader = false) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: isHeader ? { fill: "DDECEB", type: ShadingType.CLEAR } : undefined,
    margins: { top: 90, bottom: 90, left: 100, right: 100 },
    children: [new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: value, font, size: 17, color: ink, bold: isHeader })] })],
  });
}

function evidenceSnapshot() {
  const widths = [2500, 1700, 4826];
  const rows = [
    ["证据协议", "核心结果", "在本文中的角色"],
    ["嵌套严格留物种（v17）", "39.96% 全细胞准确率", "唯一严格主结果；目标物种标签不参与拟合、选择或校准。"],
    ["开放集标签空间（v17）", "55.90% 覆盖率；71.48% 条件准确率", "全细胞分母与可覆盖身份子集并列报告，不以条件指标替代开放集难度。"],
    ["身份完整性伴随队列（v18）", "2,324 显式身份细胞", "1,640 个无信息标签仅用于审计；伴随队列不替代 v17。"],
    ["少样本目标物种适配", "59.21% 至 75.89%", "每物种 8 至 64 个支持细胞，10 次独立抽样；支持与查询严格不重叠。"],
    ["外部无标签根系盲推理", "6,566 细胞；5/6 marker 顶位一致", "GSE152766 / GSM4626007 不在冻结 v4 profile；为 marker 一致性审计，不是外部准确率。"],
    ["运行时全词表注释头", "66.25% 全细胞准确率", "部署分析，与严格零样本迁移分开报告。"],
  ];
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((row, rowIndex) => new TableRow({ children: row.map((value, index) => tableCell(value, widths[index], rowIndex === 0)) })),
  });
}

function figure(stem, caption, height, directory = figureDir) {
  const imagePath = path.join(directory, `${stem}.png`);
  if (!fs.existsSync(imagePath)) throw new Error(`Missing manuscript figure: ${imagePath}`);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 70 },
      children: [new ImageRun({ data: fs.readFileSync(imagePath), type: "png", transformation: { width: 630, height } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 220 },
      children: [new TextRun({ text: caption, font, size: 17, color: muted, italics: true })],
    }),
  ];
}

function main() {
  const lines = fs.readFileSync(inputPath, "utf8").replace(/\r/g, "").split("\n");
  const children = [];
  let code = false;
  let codeLines = [];

  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 80 },
    children: [new TextRun({ text: "PLANT-CELLFM", font: "Arial", size: 24, color: teal, bold: true })],
  }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 250 },
    children: [new TextRun({ text: "协议感知跨物种注释与目标物种适配 | 证据优先主文 v5", font, size: 19, color: muted, italics: true })],
  }));

  for (const lineValue of lines) {
    if (lineValue.startsWith("```")) {
      if (code) {
        children.push(new Paragraph({
          shading: { fill: pale, type: ShadingType.CLEAR },
          spacing: { before: 70, after: 150 },
          children: [new TextRun({ text: codeLines.join("\n"), font: "Consolas", size: 16, color: ink })],
        }));
        codeLines = [];
      }
      code = !code;
      continue;
    }
    if (code) {
      codeLines.push(lineValue);
      continue;
    }
    if (!lineValue.trim()) continue;
    if (lineValue.startsWith("# ")) {
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 280 },
        children: [new TextRun({ text: clean(lineValue.slice(2)), font, size: 34, color: ink, bold: true })],
      }));
    } else if (lineValue.startsWith("## ")) {
      const title = lineValue.slice(3).trim();
      children.push(heading(title, 1));
      if (title === "结果") {
        children.push(new Paragraph({ spacing: { before: 40, after: 130 }, children: [new TextRun({ text: "关键证据快照", font, size: 21, color: teal, bold: true })] }));
        children.push(evidenceSnapshot());
        children.push(new Paragraph({ spacing: { after: 70 }, children: [] }));
      }
    } else if (lineValue.startsWith("### ")) {
      children.push(heading(lineValue.slice(4), 2));
    } else if (/^\d+\. /.test(lineValue)) {
      children.push(paragraph(lineValue.replace(/^\d+\. /, ""), { spacing: { after: 90, line: 275 } }));
    } else {
      children.push(paragraph(lineValue));
    }
  }

  children.push(heading("主图", 1));
  const figures = [
    ["plant_cellfm_v5_fig1_foundation_contract", "图 1 | 跨物种植物单细胞图谱的数据契约与共享表征。", 480],
    ["plant_cellfm_v5_fig2_strict_transfer", "图 2 | 嵌套严格留物种迁移、开放集覆盖与标签完整性。", 480],
    ["plant_cellfm_v5_fig3_target_adaptation", "图 3 | 少样本目标物种适配的重复抽样剂量响应。", 480],
    ["plant_cellfm_v5_fig4_external_root_evidence", "图 4 | 无标签外部拟南芥根系矩阵的盲推理与 marker 一致性。", 500],
  ];
  for (const [stem, caption, height] of figures) children.push(...figure(stem, caption, height));
  children.push(heading("关键扩展数据图", 1));
  children.push(...figure(
    "plant_cellfm_v4_ed_fig1_label_integrity",
    "\u6269\u5c55\u6570\u636e\u56fe 1 | \u8eab\u4efd\u5b8c\u6574\u6027\u5ba1\u8ba1\uff1a\u663e\u5f0f\u8eab\u4efd\u961f\u5217\u4e0e audit-only \u65e0\u4fe1\u606f\u6807\u7b7e\u7684\u5206\u6bcd\u62c6\u5206\u3002",
    400,
    extendedFigureDir,
  ));
  children.push(...figure(
    "plant_cellfm_v4_ed_fig2_nested_selection_audit",
    "\u6269\u5c55\u6570\u636e\u56fe 2 | \u5d4c\u5957\u7559\u7269\u79cd\u89c4\u5219\u9009\u62e9\u5ba1\u8ba1\uff1a\u6e90\u7269\u79cd\u5185\u5c42\u8bc4\u4f30\u3001\u89c4\u5219\u9009\u62e9\u4e0e\u5916\u5c42\u8ba1\u5206\u5206\u79bb\u3002",
    400,
    extendedFigureDir,
  ));
  children.push(...figure(
    "plant_cellfm_v4_ed_fig3_matched_checkpoint_comparison",
    "\u6269\u5c55\u6570\u636e\u56fe 3 | \u51bb\u7ed3 v3 \u4e0e Plant-CellFM v9 \u5728\u76f8\u540c\u534f\u8bae\u4e0b\u7684\u5339\u914d\u68c0\u67e5\u70b9\u6bd4\u8f83\uff1b\u4e0d\u4f5c\u4e3a\u5916\u90e8\u6a21\u578b\u6392\u540d\u3002",
    400,
    extendedFigureDir,
  ));
  children.push(...figure(
    "plant_cellfm_v4_ed_fig4_literature_marker_concordance",
    "扩展数据图 4 | 拟南芥根系候选 marker 的预定义文献锚点一致性。",
    420,
    extendedFigureDir,
  ));
  children.push(...figure(
    "plant_cellfm_v4_ed_fig5_external_root_blind_inference",
    "扩展数据图 5 | 无标签外部拟南芥根系矩阵的盲推理与 marker 一致性。",
    560,
    extendedFigureDir,
  ));
  children.push(...figure(
    "plant_cellfm_v5_ed_fig6_secondary_root_adapter",
    "\u6269\u5c55\u6570\u636e\u56fe 6 | GSE270140 \u4f5c\u8005\u6807\u6ce8\u76d1\u7763\u7684\u6b21\u751f\u6839 LoRA-mode \u9002\u914d\u4e0e\u540c\u4e00\u9501\u5b9a\u6d4b\u8bd5\u7ec6\u80de\u4e0a\u7684\u4e09\u72b6\u6001\u8bed\u4e49\u6062\u590d\u3002\u8be5\u7ed3\u679c\u4e3a\u5355\u6837\u672c\u6709\u76d1\u7763\u9002\u914d\uff0c\u4e0d\u4f5c\u4e3a\u96f6\u6837\u672c\u6216\u72ec\u7acb\u5916\u90e8\u9a8c\u8bc1\u58f0\u660e\u3002",
    620,
    extendedFigureDir,
  ));

  const document = new Document({
    creator: "Plant-CellFM project",
    title: "Plant-CellFM 顶刊证据主文 v5",
    description: "面向植物单细胞转录组的协议感知跨物种注释与目标物种适配框架。",
    styles: {
      default: { document: { run: { font, size: 20, color: ink } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 29, color: ink, bold: true }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 24, color: teal, bold: true }, paragraph: { spacing: { before: 210, after: 110 }, outlineLevel: 1 } },
      ],
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1030, right: 1030, bottom: 1030, left: 1030 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Plant-CellFM v5 | 证据优先中文主文", font, size: 15, color: muted })] })] }) },
      children,
    }],
  });
  Packer.toBuffer(document).then((buffer) => {
    fs.writeFileSync(outputPath, buffer);
    console.log(JSON.stringify({ out: outputPath, bytes: buffer.length }));
  });
}

main();
