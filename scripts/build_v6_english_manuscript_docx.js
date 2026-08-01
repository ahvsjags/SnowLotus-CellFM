"use strict";

const fs = require("fs");
const path = require("path");
const JSZip = require("jszip");
const { AlignmentType, BorderStyle, Document, Footer, HeadingLevel, ImageRun, Packer, PageBreak, Paragraph, ShadingType, TextRun } = require("docx");

const root = path.resolve(__dirname, "..");
const edition = process.env.PLANT_CELLFM_EDITION || "v6";
const isV7 = edition === "v7";
const inputPath = path.join(root, "manuscript", `Plant_CellFM_${edition}_submission_evidence_manuscript.md`);
const outputPath = path.join(root, "manuscript", `Plant_CellFM_${edition}_submission_evidence_manuscript.docx`);
const figureDir = path.join(root, "figures", `plant_cellfm_submission_${edition}`, "main");
const extendedFigureDir = path.join(root, "figures", "plant_cellfm_submission_v6", "extended_data");
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
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 245 }, children: [new TextRun({ text: `Protocol-aware cross-species annotation and context adaptation | Evidence-first manuscript ${edition}`, font, size: 19, color: muted, italics: true })] }),
  ];
  let code = false;
  let codeLines = [];
  for (const value of lines) {
    if (value.startsWith("```")) {
      if (code) {
        children.push(new Paragraph({ shading: { fill: pale, type: ShadingType.CLEAR }, spacing: { before: 70, after: 145 }, border: { top: border, bottom: border }, children: [new TextRun({ text: codeLines.join("\n"), font: "Consolas", size: 16, color: ink })] }));
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
    ["plant_cellfm_v6_fig1_foundation_contract", "Figure 1 | Input contract, shared representation and auditable species-adaptation record.", 480, isV7 ? path.join(root, "figures", "plant_cellfm_submission_v6", "main") : figureDir],
    ["plant_cellfm_v6_fig2_strict_transfer", "Figure 2 | Nested leave-species transfer with the open-set denominator shown explicitly.", 480, isV7 ? path.join(root, "figures", "plant_cellfm_submission_v6", "main") : figureDir],
    ["plant_cellfm_v6_fig3_target_adaptation", "Figure 3 | Repeated target-labelled support response with strict support/query separation.", 480, isV7 ? path.join(root, "figures", "plant_cellfm_submission_v6", "main") : figureDir],
    ["plant_cellfm_v6_fig4_external_root_evidence", "Figure 4 | Label-free external root execution and prespecified marker-coherence evidence.", 500, isV7 ? path.join(root, "figures", "plant_cellfm_submission_v6", "main") : figureDir],
    isV7
      ? ["plant_cellfm_v7_fig5_sorghum_external_adaptation", "Figure 5 | Source-pinned external Sorghum screen and sealed-library recovery. The frozen result is species-absent and zero-shot; the high recovery is target-species supervised adaptation on the same sealed test library, not zero-shot or a third-party ranking.", 525, figureDir]
      : ["plant_cellfm_v6_fig5_wheat_adapter", "Figure 5 | Provenance-controlled wheat adaptation. The locked-test result is same-study supervised adaptation, not zero-shot or independent validation.", 620, figureDir],
    ["plant_cellfm_v6_ed_fig7_zero_target_transfer", "Extended Data Figure 7 | Source-only Arabidopsis-to-wheat transfer audit, retaining the negative source-adapter result.", 430, extendedFigureDir],
    ["plant_cellfm_v6_ed_fig8_scplantllm_matched_reference", "Extended Data Figure 8 | Official scPlantLLM reference on the same locked test, including frozen, partial-adaptation and full-backbone-plus-new-head paths. This is a same-study adaptation reference, not independent validation or a compute-matched rank.", 480, extendedFigureDir],
  ];
  figures.forEach(([stem, caption, height, directory], index) => {
    if (index > 0) children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(...figure(stem, caption, height, directory));
  });

  return new Document({
    creator: "Plant-CellFM project",
    title: `Plant-CellFM evidence-first manuscript ${edition}`,
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
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `Plant-CellFM ${edition} | Evidence-first English manuscript`, font, size: 15, color: muted })] })] }) },
      children,
    }],
  });
}

Packer.toBuffer(buildDocument())
  .then((buffer) => JSZip.loadAsync(buffer))
  .then(async (archive) => {
    const numbering = archive.file("word/numbering.xml");
    if (numbering) {
      // The document uses manual paragraphs rather than Word bullets.  ASCII
      // placeholders keep docx-js's unused default numbering XML portable.
      archive.file("word/numbering.xml", (await numbering.async("string")).replace(/[\u25CF\u25CB\u25A0]/g, "-"));
    }
    return archive.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  })
  .then((buffer) => {
    fs.writeFileSync(outputPath, buffer);
    console.log(JSON.stringify({ out: outputPath, bytes: buffer.length }));
  });
