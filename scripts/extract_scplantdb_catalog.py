from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


SCPLANTDB_BASE = "https://biobigdata.nju.edu.cn/scplantdb"
CELLXGENE_BASE = "https://biobigdata.nju.edu.cn/cellxgene/view"


def _decode_js_string(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape")


def _json_parse_payloads(text: str) -> list[Any]:
    payloads: list[Any] = []
    for match in re.finditer(r"JSON\.parse\('((?:\\'|[^'])*)'\)", text):
        raw = _decode_js_string(match.group(1))
        try:
            payloads.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return payloads


def _flatten_labels(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    labels = []
    for item in values:
        if isinstance(item, dict) and item.get("name"):
            labels.append(str(item["name"]))
    return ";".join(labels)


def _dataset_rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    rows = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("dataset"):
            continue
        if not {"species", "bioproject", "cells"}.issubset(item):
            continue
        dataset_id = str(item["dataset"])
        article = item.get("article") if isinstance(item.get("article"), dict) else {}
        rows.append(
            {
                "dataset": dataset_id,
                "bioproject": str(item.get("bioproject", "")),
                "species": str(item.get("species", "")),
                "tissue": str(item.get("tissue", "")),
                "libraries": str(item.get("libraries", "")),
                "age": str(item.get("age", "")),
                "experiments": int(item.get("experiments") or 0),
                "cells": int(item.get("cells") or 0),
                "conditions": _flatten_labels(item.get("condition")),
                "genotypes": _flatten_labels(item.get("genotype")),
                "pmid": str(article.get("pmid", "")),
                "article": str(article.get("info", "")),
                "picname": str(item.get("picname", "")),
                "h5ad_gz_url": f"{SCPLANTDB_BASE}/datasets/{dataset_id}.h5ad.gz",
                "rds_gz_url": f"{SCPLANTDB_BASE}/datasets/{dataset_id}.rds.gz",
                "csv_gz_url": f"{SCPLANTDB_BASE}/datasets/{dataset_id}.csv.gz",
                "cellxgene_url": f"{CELLXGENE_BASE}/{dataset_id}.h5ad",
            }
        )
    return rows


def extract_catalog(chunks_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(chunks_dir)
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in sorted(root.glob("*.js")))
    by_dataset: dict[str, dict[str, Any]] = {}
    for payload in _json_parse_payloads(text):
        for row in _dataset_rows(payload):
            by_dataset[row["dataset"]] = row
    return sorted(by_dataset.values(), key=lambda row: (row["species"], row["dataset"]))


def write_tsv(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "dataset",
        "bioproject",
        "species",
        "tissue",
        "libraries",
        "age",
        "experiments",
        "cells",
        "conditions",
        "genotypes",
        "pmid",
        "article",
        "picname",
        "h5ad_gz_url",
        "rds_gz_url",
        "csv_gz_url",
        "cellxgene_url",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    print(output_path)
    return output_path


def write_json(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_markdown(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    species = sorted({str(row.get("species", "")) for row in rows if row.get("species")})
    total_cells = sum(int(row.get("cells") or 0) for row in rows)
    lines = [
        "# scPlantDB Acquisition Catalog",
        "",
        f"Datasets parsed from cached scPlantDB frontend chunks: `{len(rows)}`.",
        f"Species represented: `{len(species)}`.",
        f"Cells represented: `{total_cells}`.",
        "",
        "The public download pattern exposed by the frontend is:",
        "",
        "- H5AD gzip: `https://biobigdata.nju.edu.cn/scplantdb/datasets/<dataset>.h5ad.gz`",
        "- RDS gzip: `https://biobigdata.nju.edu.cn/scplantdb/datasets/<dataset>.rds.gz`",
        "- Browser route: `https://biobigdata.nju.edu.cn/cellxgene/view/<dataset>.h5ad`",
        "",
        "## Top Cell-Count Candidates",
        "",
        "| Dataset | Species | Tissue | Cells | Bioproject | PMID |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in sorted(rows, key=lambda item: int(item.get("cells") or 0), reverse=True)[:20]:
        lines.append(
            "| {dataset} | {species} | {tissue} | {cells} | {bioproject} | {pmid} |".format(
                dataset=row.get("dataset", ""),
                species=row.get("species", ""),
                tissue=str(row.get("tissue", "")).replace("|", "/"),
                cells=row.get("cells", 0),
                bioproject=row.get("bioproject", ""),
                pmid=row.get("pmid", ""),
            )
        )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract scPlantDB dataset metadata from cached frontend chunks")
    parser.add_argument("--chunks-dir", default="data/public/source_pages/scplantdb_chunks")
    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    rows = extract_catalog(args.chunks_dir)
    write_tsv(rows, args.output_tsv)
    write_json(rows, args.output_json)
    write_markdown(rows, args.output_md)


if __name__ == "__main__":
    main()
