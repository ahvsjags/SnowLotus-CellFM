const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  AlignmentType,
  BorderStyle,
  Document,
  ExternalHyperlink,
  Footer,
  HeadingLevel,
  LineNumberRestartFormat,
  LineRuleType,
  Packer,
  PageNumber,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "manuscript", "plant_methods_submission_v1");

const jobs = [
  {
    input: "Plant_CellFM_Plant_Methods_manuscript_v1.md",
    output: "Plant_CellFM_Plant_Methods_manuscript_v1.docx",
    lineNumbers: true,
    doubleSpace: true,
  },
  {
    input: "Plant_CellFM_Plant_Methods_supporting_information_v1.md",
    output: "Plant_CellFM_Plant_Methods_supporting_information_v1.docx",
    lineNumbers: true,
    doubleSpace: true,
  },
  {
    input: "Plant_CellFM_Plant_Methods_cover_letter_v1.md",
    output: "Plant_CellFM_Plant_Methods_cover_letter_v1.docx",
    lineNumbers: false,
    doubleSpace: false,
  },
];

function inlineRuns(text) {
  const runs = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)]+\)|\*[^*]+\*)/g;
  let cursor = 0;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) runs.push(new TextRun(text.slice(cursor, match.index)));
    const token = match[0];
    if (token.startsWith("**")) {
      runs.push(new TextRun({ text: token.slice(2, -2), bold: true }));
    } else if (token.startsWith("`")) {
      runs.push(new TextRun({ text: token.slice(1, -1), font: "Courier New", size: 19 }));
    } else if (token.startsWith("[")) {
      const linkMatch = token.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/);
      runs.push(new ExternalHyperlink({
        link: linkMatch[2],
        children: [new TextRun({ text: linkMatch[1], color: "0563C1", underline: {} })],
      }));
    } else {
      runs.push(new TextRun({ text: token.slice(1, -1), italics: true }));
    }
    cursor = match.index + token.length;
  }
  if (cursor < text.length) runs.push(new TextRun(text.slice(cursor)));
  return runs.length ? runs : [new TextRun(text)];
}

function isTableLine(line) {
  return /^\s*\|.*\|\s*$/.test(line);
}

function parseTable(lines, start) {
  const rows = [];
  let i = start;
  while (i < lines.length && isTableLine(lines[i])) {
    const cells = lines[i].trim().slice(1, -1).split("|").map((v) => v.trim());
    rows.push(cells);
    i += 1;
  }
  if (rows.length > 1 && rows[1].every((c) => /^:?-{3,}:?$/.test(c))) rows.splice(1, 1);
  const columnCount = Math.max(...rows.map((r) => r.length));
  const borders = {
    top: { style: BorderStyle.SINGLE, size: 4, color: "808080" },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: "808080" },
    left: { style: BorderStyle.SINGLE, size: 4, color: "808080" },
    right: { style: BorderStyle.SINGLE, size: 4, color: "808080" },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "B7B7B7" },
    insideVertical: { style: BorderStyle.SINGLE, size: 2, color: "B7B7B7" },
  };
  const tableRows = rows.map((row, rowIndex) => new TableRow({
    tableHeader: rowIndex === 0,
    cantSplit: true,
    children: Array.from({ length: columnCount }, (_, colIndex) => new TableCell({
      width: { size: 100 / columnCount, type: WidthType.PERCENTAGE },
      margins: { top: 70, bottom: 70, left: 90, right: 90 },
      children: [new Paragraph({
        spacing: { before: 0, after: 0, line: 240, lineRule: LineRuleType.AUTO },
        children: rowIndex === 0
          ? [new TextRun({ text: row[colIndex] || "", bold: true, size: 18 })]
          : inlineRuns(row[colIndex] || ""),
      })],
    })),
  }));
  return {
    next: i,
    element: new Table({
      rows: tableRows,
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders,
    }),
  };
}

function paragraphFor(line, options) {
  const baseSpacing = options.doubleSpace
    ? { before: 0, after: 0, line: 480, lineRule: LineRuleType.AUTO }
    : { before: 0, after: 160, line: 276, lineRule: LineRuleType.AUTO };

  const heading = line.match(/^(#{1,4})\s+(.*)$/);
  if (heading) {
    const level = heading[1].length;
    const map = {
      1: HeadingLevel.TITLE,
      2: HeadingLevel.HEADING_1,
      3: HeadingLevel.HEADING_2,
      4: HeadingLevel.HEADING_3,
    };
    return new Paragraph({
      heading: map[level],
      spacing: { before: level === 1 ? 0 : 200, after: 80, line: 276, lineRule: LineRuleType.AUTO },
      alignment: level === 1 ? AlignmentType.CENTER : AlignmentType.LEFT,
      keepNext: true,
      children: inlineRuns(heading[2]),
    });
  }

  const bullet = line.match(/^\s*-\s+(.*)$/);
  if (bullet) {
    return new Paragraph({
      bullet: { level: 0 },
      spacing: baseSpacing,
      children: inlineRuns(bullet[1]),
    });
  }

  const numbered = line.match(/^\s*(\d+)\.\s+(.*)$/);
  if (numbered) {
    return new Paragraph({
      spacing: baseSpacing,
      indent: { left: 720, hanging: 360 },
      children: [new TextRun(`${numbered[1]}. `), ...inlineRuns(numbered[2])],
    });
  }

  return new Paragraph({
    spacing: baseSpacing,
    alignment: AlignmentType.JUSTIFIED,
    widowControl: true,
    children: inlineRuns(line),
  });
}

function markdownToElements(markdown, options) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const elements = [];
  let inCode = false;
  for (let i = 0; i < lines.length;) {
    const line = lines[i];
    if (line.startsWith("```")) {
      inCode = !inCode;
      i += 1;
      continue;
    }
    if (inCode) {
      elements.push(new Paragraph({
        spacing: { before: 0, after: 0, line: 240, lineRule: LineRuleType.AUTO },
        children: [new TextRun({ text: line || " ", font: "Courier New", size: 18 })],
      }));
      i += 1;
      continue;
    }
    const equation = line.trim().match(/^<!--\s*equation:([A-Za-z0-9_-]+)\s*-->$/);
    if (equation) {
      elements.push(new Paragraph({
        spacing: { before: 80, after: 80, line: 276, lineRule: LineRuleType.AUTO },
        alignment: AlignmentType.CENTER,
        children: [new TextRun(`[[EQUATION:${equation[1]}]]`)],
      }));
      i += 1;
      if (i < lines.length && lines[i].trim().startsWith("$$")) {
        const singleLine = lines[i].trim().length > 4 && lines[i].trim().endsWith("$$");
        i += 1;
        if (!singleLine) {
          while (i < lines.length && !lines[i].trim().endsWith("$$")) i += 1;
          if (i < lines.length) i += 1;
        }
      }
      continue;
    }
    if (isTableLine(line)) {
      const parsed = parseTable(lines, i);
      elements.push(parsed.element);
      i = parsed.next;
      continue;
    }
    if (!line.trim()) {
      i += 1;
      continue;
    }
    elements.push(paragraphFor(line, options));
    i += 1;
  }
  return elements;
}

async function build(job) {
  const markdown = fs.readFileSync(path.join(OUT, job.input), "utf8");
  const children = markdownToElements(markdown, job);
  const sectionProperties = {
    page: {
      size: { width: 11906, height: 16838 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720, footer: 720 },
    },
  };
  if (job.lineNumbers) {
    sectionProperties.lineNumbers = {
      countBy: 1,
      start: 1,
      restart: LineNumberRestartFormat.CONTINUOUS,
      distance: 360,
    };
  }

  const doc = new Document({
    creator: "Plant-CellFM authors",
    title: path.basename(job.output, ".docx"),
    description: "Plant Methods submission document",
    styles: {
      default: {
        document: { run: { font: "Arial", size: 22, color: "000000" } },
        title: { run: { font: "Arial", size: 30, bold: true }, paragraph: { spacing: { after: 240 } } },
        heading1: { run: { font: "Arial", size: 26, bold: true, color: "000000" } },
        heading2: { run: { font: "Arial", size: 23, bold: true, color: "000000" } },
        heading3: { run: { font: "Arial", size: 22, bold: true, italics: true, color: "000000" } },
      },
    },
    numbering: {
      config: [{
        reference: "numbered-list",
        levels: [{
          level: 0,
          format: "decimal",
          text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      }],
    },
    sections: [{
      properties: sectionProperties,
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })],
          })],
        }),
      },
      children,
    }],
  });
  const buffer = await Packer.toBuffer(doc);
  const outputPath = path.join(OUT, job.output);
  fs.writeFileSync(outputPath, buffer);

  let equationCount = 0;
  if (markdown.includes("<!-- equation:")) {
    const python = process.env.PLANT_CELLFM_PYTHON || process.env.PYTHON || "python";
    const injector = path.join(ROOT, "scripts", "inject_omml_equations.py");
    const result = spawnSync(
      python,
      [injector, "--markdown", path.join(OUT, job.input), "--docx", outputPath],
      { encoding: "utf8" },
    );
    if (result.status !== 0) {
      throw new Error(`Equation injection failed for ${job.output}:\n${result.stderr || result.stdout}`);
    }
    const parsed = JSON.parse(result.stdout);
    equationCount = parsed.equations;
  }
  return { file: job.output, bytes: fs.statSync(outputPath).size, equations: equationCount };
}

(async () => {
  const results = [];
  for (const job of jobs) results.push(await build(job));
  process.stdout.write(JSON.stringify(results, null, 2));
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exit(1);
});
