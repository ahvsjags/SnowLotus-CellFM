from __future__ import annotations

import argparse
import copy
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

from latex2mathml.converter import convert as latex_to_mathml
from lxml import etree
from mathml2omml import convert as mathml_to_omml


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W_NS, "m": M_NS}
EQUATION_PATTERN = re.compile(
    r"<!--\s*equation:([A-Za-z0-9_-]+)\s*-->\s*\$\$(.*?)\$\$",
    flags=re.DOTALL,
)
MARKER_PATTERN = re.compile(r"^\[\[EQUATION:([A-Za-z0-9_-]+)\]\]$")
TAG_PATTERN = re.compile(r"\\tag\{([^{}]+)\}\s*$")
INLINE_PATTERN = re.compile(r"\\\((.+?)\\\)")


def qname(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def parse_equations(markdown_path: Path) -> dict[str, tuple[str, str]]:
    text = markdown_path.read_text(encoding="utf-8")
    equations: dict[str, tuple[str, str]] = {}
    for match in EQUATION_PATTERN.finditer(text):
        equation_id = match.group(1)
        latex = match.group(2).strip()
        tag_match = TAG_PATTERN.search(latex)
        if not tag_match:
            raise ValueError(f"Equation {equation_id} is missing a terminal \\tag{{...}}")
        number = tag_match.group(1)
        latex = TAG_PATTERN.sub("", latex).strip()
        if equation_id in equations:
            raise ValueError(f"Duplicate equation identifier: {equation_id}")
        equations[equation_id] = (latex, number)
    return equations


def omml_element(latex: str) -> etree._Element:
    mathml = latex_to_mathml(latex)
    omml = mathml_to_omml(mathml)
    # mathml2omml 0.0.2 closes group-character properties with the parent tag.
    # It also omits the required radical properties and empty degree element.
    # Repair both known serialization defects before parsing the native OMML.
    omml = omml.replace("</m:groupChr><m:e>", "</m:groupChrPr><m:e>")
    omml = omml.replace(
        "<m:rad><m:e>",
        '<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>',
    )
    wrapper = etree.fromstring(
        f'<root xmlns:m="{M_NS}">{omml}</root>'.encode("utf-8")
    )
    element = wrapper[0]
    for nary in element.xpath(".//m:nary", namespaces=NS):
        properties = nary.find("m:naryPr", namespaces=NS)
        if properties is None:
            continue
        missing: dict[str, bool] = {}
        for name in ("sup", "sub"):
            limit = nary.find(f"m:{name}", namespaces=NS)
            text = "" if limit is None else "".join(
                limit.xpath(".//m:t/text()", namespaces=NS)
            ).strip()
            missing[name] = limit is None or not text
            if limit is not None and not text:
                for child in list(limit):
                    limit.remove(child)
        if missing["sup"]:
            hidden = etree.SubElement(properties, qname(M_NS, "supHide"))
            hidden.set(qname(M_NS, "val"), "1")
        if missing["sub"]:
            hidden = etree.SubElement(properties, qname(M_NS, "subHide"))
            hidden.set(qname(M_NS, "val"), "1")
    for parent in element.iter():
        children = list(parent)
        index = 0
        while index < len(children):
            run = children[index]
            if run.tag != qname(M_NS, "r"):
                index += 1
                continue
            style = run.find("m:rPr/m:sty", namespaces=NS)
            text_node = run.find("m:t", namespaces=NS)
            text = "" if text_node is None else (text_node.text or "")
            if style is None or style.get(qname(M_NS, "val")) != "p" or not text.isalpha():
                index += 1
                continue
            merged = text
            next_index = index + 1
            while next_index < len(children):
                candidate = children[next_index]
                if candidate.tag != qname(M_NS, "r"):
                    break
                candidate_style = candidate.find("m:rPr/m:sty", namespaces=NS)
                candidate_text_node = candidate.find("m:t", namespaces=NS)
                candidate_text = "" if candidate_text_node is None else (candidate_text_node.text or "")
                if (
                    candidate_style is None
                    or candidate_style.get(qname(M_NS, "val")) != "p"
                    or not candidate_text.isalpha()
                ):
                    break
                merged += candidate_text
                parent.remove(candidate)
                next_index += 1
            if text_node is not None:
                text_node.text = merged
            children = list(parent)
            index += 1
    return element


def append_tab(paragraph: etree._Element) -> None:
    run = etree.SubElement(paragraph, qname(W_NS, "r"))
    etree.SubElement(run, qname(W_NS, "tab"))


def append_number(paragraph: etree._Element, number: str) -> None:
    run = etree.SubElement(paragraph, qname(W_NS, "r"))
    properties = etree.SubElement(run, qname(W_NS, "rPr"))
    size = etree.SubElement(properties, qname(W_NS, "sz"))
    size.set(qname(W_NS, "val"), "20")
    size_cs = etree.SubElement(properties, qname(W_NS, "szCs"))
    size_cs.set(qname(W_NS, "val"), "20")
    text = etree.SubElement(run, qname(W_NS, "t"))
    text.text = f"({number})"


def append_text_run(parent: etree._Element, position: int, template: etree._Element, text: str) -> int:
    if not text:
        return position
    run = etree.Element(qname(W_NS, "r"))
    properties = template.find("w:rPr", namespaces=NS)
    if properties is not None:
        run.append(copy.deepcopy(properties))
    text_element = etree.SubElement(run, qname(W_NS, "t"))
    if text[:1].isspace() or text[-1:].isspace():
        text_element.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_element.text = text
    parent.insert(position, run)
    return position + 1


def inject_inline_math(root: etree._Element) -> int:
    converted = 0
    runs = list(root.xpath(".//w:r[not(ancestor::m:oMath)]", namespaces=NS))
    for run in runs:
        text_nodes = run.xpath("./w:t", namespaces=NS)
        if len(text_nodes) != 1:
            continue
        text = text_nodes[0].text or ""
        matches = list(INLINE_PATTERN.finditer(text))
        if not matches:
            continue
        parent = run.getparent()
        position = parent.index(run)
        cursor = 0
        for match in matches:
            position = append_text_run(parent, position, run, text[cursor:match.start()])
            parent.insert(position, omml_element(match.group(1).strip()))
            position += 1
            converted += 1
            cursor = match.end()
        append_text_run(parent, position, run, text[cursor:])
        parent.remove(run)
    return converted


def set_equation_paragraph_properties(paragraph: etree._Element) -> etree._Element:
    properties = paragraph.find("w:pPr", namespaces=NS)
    if properties is None:
        properties = etree.Element(qname(W_NS, "pPr"))
        paragraph.insert(0, properties)

    for child in list(properties):
        if child.tag in {qname(W_NS, "tabs"), qname(W_NS, "jc"), qname(W_NS, "spacing")}:
            properties.remove(child)

    tabs = etree.SubElement(properties, qname(W_NS, "tabs"))
    center = etree.SubElement(tabs, qname(W_NS, "tab"))
    center.set(qname(W_NS, "val"), "center")
    center.set(qname(W_NS, "pos"), "4513")
    right = etree.SubElement(tabs, qname(W_NS, "tab"))
    right.set(qname(W_NS, "val"), "right")
    right.set(qname(W_NS, "pos"), "9026")

    spacing = etree.SubElement(properties, qname(W_NS, "spacing"))
    spacing.set(qname(W_NS, "before"), "80")
    spacing.set(qname(W_NS, "after"), "80")
    spacing.set(qname(W_NS, "line"), "276")
    spacing.set(qname(W_NS, "lineRule"), "auto")
    return properties


def inject_document_xml(
    xml_bytes: bytes,
    equations: dict[str, tuple[str, str]],
) -> tuple[bytes, int, int]:
    root = etree.fromstring(xml_bytes)
    replaced = 0
    seen: set[str] = set()
    for paragraph in root.xpath(".//w:p", namespaces=NS):
        paragraph_text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()
        marker = MARKER_PATTERN.match(paragraph_text)
        if not marker:
            continue
        equation_id = marker.group(1)
        if equation_id not in equations:
            raise ValueError(f"DOCX marker has no Markdown equation: {equation_id}")
        latex, number = equations[equation_id]
        properties = set_equation_paragraph_properties(paragraph)
        for child in list(paragraph):
            if child is not properties:
                paragraph.remove(child)
        append_tab(paragraph)
        paragraph.append(omml_element(latex))
        append_tab(paragraph)
        append_number(paragraph, number)
        replaced += 1
        seen.add(equation_id)

    missing = sorted(set(equations) - seen)
    if missing:
        raise ValueError(f"Equations were not injected: {missing}")
    inline_count = inject_inline_math(root)
    output = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")
    return output, replaced, inline_count


def rewrite_docx(docx_path: Path, equations: dict[str, tuple[str, str]]) -> tuple[int, int]:
    with tempfile.NamedTemporaryFile(
        prefix=docx_path.stem + "_",
        suffix=".docx",
        dir=docx_path.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
    try:
        with zipfile.ZipFile(docx_path, "r") as source:
            document_xml = source.read("word/document.xml")
            updated_xml, replaced, inline_count = inject_document_xml(document_xml, equations)
            with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
                for item in source.infolist():
                    payload = updated_xml if item.filename == "word/document.xml" else source.read(item.filename)
                    target.writestr(item, payload)
        os.replace(temporary_path, docx_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return replaced, inline_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace Plant-CellFM equation markers with native OMML.")
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--docx", required=True, type=Path)
    args = parser.parse_args()

    equations = parse_equations(args.markdown)
    replaced, inline_count = rewrite_docx(args.docx, equations)
    print(
        json.dumps(
            {"docx": str(args.docx), "equations": replaced, "inline_math": inline_count},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
