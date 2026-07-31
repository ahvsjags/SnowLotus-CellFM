"use strict";

const fs = require("fs");
const path = require("path");
const { AlignmentType, BorderStyle, Document, Footer, HeadingLevel, ImageRun, Packer, Paragraph, ShadingType, TextRun } = require("docx");

const root = path.resolve(__dirname, "..");
const inputPath = path.join(root, "manuscript", "Plant_CellFM_v5_Manuscript_en.md");
const outputPath = path.join(root, "manuscript", "Plant_CellFM_v5_Manuscript_en.docx");
const figureDir = path.join(root, "figures", "plant_cellfm_submission_v5", "main");
const extendedFigureDir = path.join(root, "figures", "plant_cellfm_submission_v5", "extended_data");
const font = "Arial";
const ink = "18242E";
const teal = "007C83";
const muted = "60717D";
const pale = "F4F7F8";
const border = { style: BorderStyle.SINGLE, size: 1, color: "D8E0E4" };

function clean(value) {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`(.*?)`/g, "$1")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1 ($2)");
}

function bodyParagraph(value, options = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 125, line: 278, ...options.spacing },
    indent: options.indent,
    children: [new TextRun({ text: clean(value), font, size: 20, color: ink, ...options.run })],
  });
}

function heading(value, level) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 270 : 205, after: 110 },
    children: [new TextRun({ text: clean(value), font, size: level === 1 ? 28 : 23, color: level === 1 ? ink : teal, bold: true })],
  });
}

function figure(stem, caption, height, directory = figureDir) {
  const imagePath = path.join(directory, `${stem}.png`);
  if (!fs.existsSync(imagePath)) throw new Error(`Missing manuscript figure: ${imagePath}`);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 70 }, children: [new ImageRun({ data: fs.readFileSync(imagePath), type: "png", transformation: { width: 630, height } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 210 }, children: [new TextRun({ text: caption, font, size: 17, color: muted, italics: true })] }),
  ];
}

function buildDocument() {
  const lines = fs.readFileSync(inputPath, "utf8").replace(/\r/g, "").split("\n");
  const children = [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 70 }, children: [new TextRun({ text: "PLANT-CELLFM", font, size: 24, color: teal, bold: true })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 245 }, children: [new TextRun({ text: "Protocol-aware cross-species annotation and context adaptation | Evidence-first manuscript v5", font, size: 19, color: muted, italics: true })] }),
  ];
  let code = false;
  let codeLines = [];
  for (const value of lines) {
    if (value.startsWith("```")) {
      if (code) {
        children.push(new Paragraph({ shading: { fill: pale, type: ShadingType.CLEAR }, spacing: { before: 70, after: 145 }, border: { top: border, bottom: border, left: border, right: border }, children: [new TextRun({ text: codeLines.join("\n"), font: "Consolas", size: 16, color: ink })] }));
        codeLines = [];
      }
      code = !code;
      continue;
    }
    if (code) {
      codeLines.push(value);
      continue;
    }
    if (!value.trim()) continue;
    if (value.startsWith("# ")) {
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 275 }, children: [new TextRun({ text: clean(value.slice(2)), font, size: 32, color: ink, bold: true })] }));
    } else if (value.startsWith("## ")) {
      children.push(heading(value.slice(3), 1));
    } else if (value.startsWith("### ")) {
      children.push(heading(value.slice(4), 2));
    } else if (/^\d+\. /.test(value)) {
      children.push(bodyParagraph(value.replace(/^\d+\. /, ""), { indent: { left: 260, hanging: 260 } }));
    } else if (value.startsWith("- ")) {
      children.push(bodyParagraph(value.slice(2), { indent: { left: 260, hanging: 180 } }));
    } else {
      children.push(bodyParagraph(value));
    }
  }

  children.push(heading("Submission Figure Suite", 1));
  const figures = [
    ["plant_cellfm_v5_fig1_foundation_contract", "Figure 1 | Frozen corpus contract and shared strict-evaluation representation.", 480, figureDir],
    ["plant_cellfm_v5_fig2_strict_transfer", "Figure 2 | Nested strict leave-species transfer with visible open-set coverage and denominators.", 480, figureDir],
    ["plant_cellfm_v5_fig3_target_adaptation", "Figure 3 | Repeated target-species adaptation response across labelled support budgets.", 480, figureDir],
    ["plant_cellfm_v5_fig4_external_root_evidence", "Figure 4 | Label-free external root execution and pre-specified marker-coherence audit.", 500, figureDir],
    ["plant_cellfm_v4_ed_fig1_label_integrity", "Extended Data Figure 1 | Explicit-identity and audit-only label denominator analysis.", 400, extendedFigureDir],
    ["plant_cellfm_v4_ed_fig2_nested_selection_audit", "Extended Data Figure 2 | Inner-fold rule-selection audit for the strict protocol.", 400, extendedFigureDir],
    ["plant_cellfm_v4_ed_fig3_matched_checkpoint_comparison", "Extended Data Figure 3 | Matched frozen v3-to-v9 checkpoint comparison.", 400, extendedFigureDir],
    ["plant_cellfm_v4_ed_fig4_literature_marker_concordance", "Extended Data Figure 4 | Literature-fixed root-marker concordance for the candidate resource.", 420, extendedFigureDir],
    ["plant_cellfm_v4_ed_fig5_external_root_blind_inference", "Extended Data Figure 5 | Full label-free external-root inference audit.", 560, extendedFigureDir],
    ["plant_cellfm_v5_ed_fig6_secondary_root_adapter", "Extended Data Figure 6 | Author-labelled secondary-root LoRA-mode adaptation. This is one-sample supervised adaptation, not zero-shot or independent validation.", 620, extendedFigureDir],
  ];
  for (const [stem, caption, height, directory] of figures) children.push(...figure(stem, caption, height, directory));

  return new Document({
    creator: "Plant-CellFM project",
    title: "Plant-CellFM evidence-first manuscript v5",
    description: "Protocol-aware cross-species plant single-cell annotation and context adaptation.",
    styles: {
      default: { document: { run: { font, size: 20, color: ink } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 28, color: ink, bold: true }, paragraph: { spacing: { before: 270, after: 110 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 23, color: teal, bold: true }, paragraph: { spacing: { before: 205, after: 105 }, outlineLevel: 1 } },
      ],
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1030, right: 1030, bottom: 1030, left: 1030 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Plant-CellFM v5 | Evidence-first English manuscript", font, size: 15, color: muted })] })] }) },
      children,
    }],
  });
}

Packer.toBuffer(buildDocument()).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  console.log(JSON.stringify({ out: outputPath, bytes: buffer.length }));
});
