"use strict";

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
const manuscriptPath = path.join(root, "manuscript", "Plant_CellFM_v3_evidence_first_manuscript.md");
const outputPath = path.join(root, "manuscript", "Plant_CellFM_v3_evidence_first_manuscript.docx");
const figureDir = path.join(root, "figures", "plant_cellfm_submission_v3", "drafts");

const ink = "19222B";
const teal = "087E8B";
const muted = "60717D";
const pale = "F4F7F8";
const border = { style: BorderStyle.SINGLE, size: 1, color: "D8E0E4" };
const tableBorders = { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border };

function run(text, options = {}) {
  return new TextRun({ text, font: "Arial", size: 19, color: ink, ...options });
}

function cleanMarkdown(value) {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`(.*?)`/g, "$1")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1 ($2)");
}

function heading(text, level) {
  return new Paragraph({
    heading: level,
    children: [new TextRun({ text: cleanMarkdown(text), font: "Arial", color: ink, bold: true })],
  });
}

function normal(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children: [run(cleanMarkdown(text))],
  });
}

function cell(text, width, header = false) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders: tableBorders,
    shading: header ? { fill: "DDECEB", type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text, font: "Arial", size: 17, color: ink, bold: header })] })],
  });
}

function snapshotTable() {
  const widths = [2800, 1800, 4426];
  const rows = [
    ["Protocol", "Result", "Reporting role"],
    ["Nested strict leave-species (v17)", "39.96% all-cell", "Primary strict result; no held-out species labels used in fitting or selection."],
    ["Known-label subset (v17)", "71.48% accuracy; 0.2817 macro-F1", "Reported with 55.90% source-label coverage, not substituted for the all-cell denominator."],
    ["Few-shot target adaptation", "59.21% to 75.89%", "Mean query all-cell accuracy from 8 to 64 support cells per species across ten support draws."],
    ["Runtime full-vocabulary head", "66.25% all-cell", "Deployment analysis; explicitly separate from strict zero-shot transfer."],
  ];
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((row, rowIndex) => new TableRow({ children: row.map((value, index) => cell(value, widths[index], rowIndex === 0)) })),
  });
}

function figure(file, caption) {
  const imagePath = path.join(figureDir, `${file}.png`);
  if (!fs.existsSync(imagePath)) {
    throw new Error(`Missing manuscript figure: ${imagePath}`);
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 75 },
      children: [new ImageRun({ data: fs.readFileSync(imagePath), type: "png", transformation: { width: 650, height: 530 } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 210 },
      children: [new TextRun({ text: caption, font: "Arial", size: 17, italics: true, color: muted })],
    }),
  ];
}

function main() {
  const lines = fs.readFileSync(manuscriptPath, "utf8").replace(/\r/g, "").split("\n");
  const children = [];
  let inCode = false;
  let codeLines = [];

  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 90 },
    children: [new TextRun({ text: "Plant-CellFM", font: "Arial", size: 22, bold: true, color: teal, allCaps: true })],
  }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 220 },
    children: [new TextRun({ text: "Evidence-first manuscript draft | v3", font: "Arial", size: 18, color: muted, italics: true })],
  }));

  for (const line of lines) {
    if (line.startsWith("```")) {
      if (inCode) {
        children.push(new Paragraph({
          spacing: { before: 40, after: 150 },
          shading: { fill: pale, type: ShadingType.CLEAR },
          children: [new TextRun({ text: codeLines.join("\n"), font: "Consolas", size: 16, color: ink })],
        }));
        codeLines = [];
      }
      inCode = !inCode;
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }
    if (!line.trim()) {
      continue;
    }
    if (line.startsWith("# ")) {
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 260 },
        children: [new TextRun({ text: cleanMarkdown(line.slice(2)), font: "Arial", size: 34, bold: true, color: ink })],
      }));
      continue;
    }
    if (line.startsWith("## ")) {
      children.push(heading(line.slice(3), HeadingLevel.HEADING_1));
      if (line.slice(3).trim() === "Abstract") {
        continue;
      }
      if (line.slice(3).trim() === "Results") {
        children.push(new Paragraph({ spacing: { before: 30, after: 140 }, children: [new TextRun({ text: "Evidence snapshot", font: "Arial", size: 20, bold: true, color: teal })] }));
        children.push(snapshotTable());
        children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      }
      continue;
    }
    if (line.startsWith("### ")) {
      children.push(heading(line.slice(4), HeadingLevel.HEADING_2));
      continue;
    }
    if (/^\d+\. /.test(line)) {
      children.push(new Paragraph({ numbering: { reference: "numbered", level: 0 }, spacing: { after: 90 }, children: [run(cleanMarkdown(line.replace(/^\d+\. /, "")))] }));
      continue;
    }
    children.push(normal(line));
  }

  children.push(heading("Main Figures", HeadingLevel.HEADING_1));
  const figures = [
    ["plant_cellfm_v3_fig1_corpus_and_representation", "Figure 1 | Traceable corpus composition, evaluation embedding atlas and the shared Plant-CellFM data contract."],
    ["plant_cellfm_v3_fig2_nested_strict_transfer", "Figure 2 | Nested strict leave-species transfer, per-species heterogeneity, fixed-cell bootstrap and open-set coverage."],
    ["plant_cellfm_v3_fig3_matched_comparisons", "Figure 3 | Matched frozen v3-v9 comparisons and a non-ranking audit of external-comparator evidence closure."],
    ["plant_cellfm_v3_fig4_fewshot_target_adaptation", "Figure 4 | Target-species adaptation with disjoint support/query cells and ten independent support draws."],
    ["plant_cellfm_v3_fig5_arabidopsis_root_candidate_resource", "Figure 5 | Arabidopsis root identity taxonomy and computational marker-candidate resource."],
    ["plant_cellfm_v3_fig6_runtime_confidence", "Figure 6 | Runtime full-vocabulary confidence operating curve and per-species deployment outcomes."],
  ];
  for (const [file, caption] of figures) {
    children.push(...figure(file, caption));
  }

  const doc = new Document({
    creator: "Plant-CellFM project",
    title: "Plant-CellFM evidence-first manuscript v3",
    description: "Protocol-aware cross-species annotation and target-species adaptation for plant single-cell transcriptomics.",
    styles: {
      default: { document: { run: { font: "Arial", size: 19, color: ink } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Arial", size: 27, bold: true, color: ink }, paragraph: { spacing: { before: 260, after: 140 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Arial", size: 22, bold: true, color: teal }, paragraph: { spacing: { before: 210, after: 100 }, outlineLevel: 1 } },
      ],
    },
    numbering: { config: [{ reference: "numbered", levels: [{ level: 0, format: "decimal", text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 220 } } } }] }] },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Plant-CellFM v3 | Evidence-first manuscript draft", font: "Arial", size: 15, color: muted })] })] }) },
      children,
    }],
  });
  Packer.toBuffer(doc).then((buffer) => {
    fs.writeFileSync(outputPath, buffer);
    console.log(JSON.stringify({ out: outputPath, bytes: buffer.length }));
  });
}

main();
