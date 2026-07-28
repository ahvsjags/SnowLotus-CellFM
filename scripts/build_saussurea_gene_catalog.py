#!/usr/bin/env python3
"""Extract a compact gene/CDS catalog from the NCBI GenBank flat file."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path
from typing import TextIO


QUALIFIER_START = re.compile(r"^/([A-Za-z0-9_]+)(?:=(.*))?$")
FEATURE_KEYS = {"gene", "CDS"}
KEEP_QUALIFIERS = {
    "db_xref",
    "gene",
    "gene_synonym",
    "locus_tag",
    "old_locus_tag",
    "product",
}


def _finish_qualifier(
    qualifiers: dict[str, list[str]],
    active_name: str | None,
    active_parts: list[str],
) -> tuple[str | None, list[str]]:
    if active_name is not None:
        value = "".join(active_parts).strip().strip('"')
        if value and active_name in KEEP_QUALIFIERS:
            qualifiers.setdefault(active_name, []).append(value)
    return None, []


def iter_features(handle: TextIO):
    current_key: str | None = None
    current_location = ""
    qualifiers: dict[str, list[str]] = {}
    active_name: str | None = None
    active_parts: list[str] = []
    in_features = False

    def flush():
        nonlocal current_key, current_location, qualifiers, active_name, active_parts
        active_name, active_parts = _finish_qualifier(qualifiers, active_name, active_parts)
        if current_key in FEATURE_KEYS:
            yield {
                "feature": current_key,
                "location": current_location,
                **{
                    name: ";".join(values)
                    for name, values in qualifiers.items()
                    if name in KEEP_QUALIFIERS and values
                },
            }
        current_key = None
        current_location = ""
        qualifiers = {}

    for raw_line in handle:
        line = raw_line.rstrip("\n")
        if line.startswith("FEATURES"):
            in_features = True
            continue
        if line.startswith("ORIGIN"):
            if current_key is not None:
                yield from flush()
            in_features = False
            continue
        if not in_features:
            continue

        feature_key = line[5:21].strip() if len(line) >= 21 else ""
        feature_location = line[21:].strip() if len(line) > 21 else ""
        if feature_key:
            if current_key is not None:
                yield from flush()
            current_key = feature_key
            current_location = feature_location
            continue

        if current_key is None or len(line) < 22:
            continue
        content = line[21:].strip()
        if content.startswith("/"):
            active_name, active_parts = _finish_qualifier(qualifiers, active_name, active_parts)
            match = QUALIFIER_START.match(content)
            if not match:
                continue
            active_name = match.group(1)
            value = match.group(2)
            if value is None:
                active_parts = ["true"]
                active_name, active_parts = _finish_qualifier(qualifiers, active_name, active_parts)
            elif value.startswith('"') and not value.endswith('"'):
                active_parts = [value]
            else:
                active_parts = [value]
                active_name, active_parts = _finish_qualifier(qualifiers, active_name, active_parts)
        elif active_name is not None:
            active_parts.append(content)
            if content.endswith('"'):
                active_name, active_parts = _finish_qualifier(qualifiers, active_name, active_parts)


def build_catalog(input_path: Path, output_path: Path, summary_path: Path) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    rows = 0
    genes_with_names = 0
    genes_with_locus = 0

    with gzip.open(input_path, "rt", encoding="utf-8", errors="replace") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        writer = csv.DictWriter(
            target,
            fieldnames=[
                "feature",
                "location",
                "gene",
                "gene_synonym",
                "locus_tag",
                "old_locus_tag",
                "product",
                "db_xref",
            ],
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in iter_features(source):
            writer.writerow(row)
            rows += 1
            counts[row["feature"]] += 1
            if row.get("gene") or row.get("gene_synonym"):
                genes_with_names += 1
            if row.get("locus_tag"):
                genes_with_locus += 1

    summary = {
        "source": str(input_path),
        "output": str(output_path),
        "status": "gene_features_parsed" if rows else "no_gene_or_cds_features_in_source",
        "records": rows,
        "feature_counts": dict(sorted(counts.items())),
        "records_with_gene_name_or_synonym": genes_with_names,
        "records_with_locus_tag": genes_with_locus,
    }
    if not rows:
        summary["warning"] = "The public assembly GenBank archive contains assembly/source records but no gene or CDS feature rows."
    summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Gzipped NCBI GenBank flat file")
    parser.add_argument("--output", type=Path, required=True, help="TSV gene catalog path")
    parser.add_argument("--summary", type=Path, required=True, help="JSON summary path")
    args = parser.parse_args()
    summary = build_catalog(args.input, args.output, args.summary)
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
