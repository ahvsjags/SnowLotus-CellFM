from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = "SnowCell/scplantdb-size-probe"
SPECIES_PRIORITY = [
    "Arabidopsis thaliana",
    "Oryza sativa",
    "Zea mays",
    "Triticum aestivum",
    "Gossypium hirsutum",
    "Solanum lycopersicum",
    "Catharanthus roseus",
    "Stevia rebaudiana",
    "Marchantia polymorpha",
]


def read_catalog(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _header_int(headers: Any, key: str) -> int | None:
    value = headers.get(key)
    if not value:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def probe_url(url: str, timeout: float = 20.0) -> dict[str, Any]:
    request = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            headers = response.headers
            return {
                "ok": 200 <= int(response.status) < 400,
                "status_code": int(response.status),
                "error": "",
                "content_length": _header_int(headers, "Content-Length"),
                "content_type": headers.get("Content-Type", ""),
                "accept_ranges": headers.get("Accept-Ranges", ""),
                "etag": headers.get("ETag", ""),
                "last_modified": headers.get("Last-Modified", ""),
            }
    except HTTPError as error:
        return {
            "ok": False,
            "status_code": int(error.code),
            "error": str(error),
            "content_length": _header_int(error.headers, "Content-Length"),
            "content_type": error.headers.get("Content-Type", ""),
            "accept_ranges": error.headers.get("Accept-Ranges", ""),
            "etag": error.headers.get("ETag", ""),
            "last_modified": error.headers.get("Last-Modified", ""),
        }
    except URLError as error:
        return {
            "ok": False,
            "status_code": 0,
            "error": str(error.reason),
            "content_length": None,
            "content_type": "",
            "accept_ranges": "",
            "etag": "",
            "last_modified": "",
        }


def species_rank(species: str) -> int:
    try:
        return SPECIES_PRIORITY.index(species)
    except ValueError:
        return len(SPECIES_PRIORITY) + 1


def ranked_rows(
    catalog_rows: list[dict[str, str]],
    max_bytes: int,
    max_total_bytes: int,
    min_cells: int,
    max_datasets: int,
    timeout: float,
    diverse_species: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in catalog_rows:
        url = row.get("h5ad_gz_url") or (
            f"https://biobigdata.nju.edu.cn/scplantdb/datasets/{row.get('dataset', '')}.h5ad.gz"
        )
        probe = probe_url(url, timeout=timeout)
        content_length = probe.get("content_length")
        cells = int(row.get("cells") or 0)
        available = bool(probe.get("ok")) and isinstance(content_length, int)
        eligible = available and content_length <= max_bytes and cells >= min_cells
        rows.append(
            {
                "dataset": row.get("dataset", ""),
                "species": row.get("species", ""),
                "tissue": row.get("tissue", ""),
                "cells": cells,
                "bioproject": row.get("bioproject", ""),
                "pmid": row.get("pmid", ""),
                "h5ad_gz_url": url,
                "status_code": probe.get("status_code", 0),
                "ok": bool(probe.get("ok")),
                "error": probe.get("error", ""),
                "content_length": content_length or 0,
                "size_mb": round((content_length or 0) / (1024 * 1024), 3),
                "content_type": probe.get("content_type", ""),
                "accept_ranges": probe.get("accept_ranges", ""),
                "etag": probe.get("etag", ""),
                "last_modified": probe.get("last_modified", ""),
                "species_priority": species_rank(row.get("species", "")),
                "eligible_for_download": eligible,
                "selected_for_download": False,
                "selection_skip_reason": "",
            }
        )
    rows.sort(
        key=lambda item: (
            not item["eligible_for_download"],
            item["species_priority"],
            item["content_length"] or 10**18,
            -int(item["cells"] or 0),
            item["dataset"],
        )
    )
    selected = 0
    selected_total_bytes = 0
    selected_species: set[str] = set()
    eligible_rows = [row for row in rows if row["eligible_for_download"]]

    def maybe_select(row: dict[str, Any]) -> bool:
        nonlocal selected, selected_total_bytes
        if selected >= max_datasets:
            row["selection_skip_reason"] = "max_datasets_reached"
            return False
        row_bytes = int(row.get("content_length") or 0)
        if max_total_bytes > 0 and selected_total_bytes + row_bytes > max_total_bytes:
            row["selection_skip_reason"] = "max_total_bytes_reached"
            return False
        row["selected_for_download"] = True
        row["selection_skip_reason"] = ""
        selected += 1
        selected_total_bytes += row_bytes
        return True

    if diverse_species:
        for row in eligible_rows:
            species = str(row.get("species", ""))
            if species in selected_species:
                row["selection_skip_reason"] = "species_already_selected"
                continue
            if maybe_select(row):
                selected_species.add(species)
    for row in eligible_rows:
        if row["selected_for_download"]:
            continue
        maybe_select(row)
    return rows


FIELDNAMES = [
    "dataset",
    "species",
    "tissue",
    "cells",
    "bioproject",
    "pmid",
    "h5ad_gz_url",
    "status_code",
    "ok",
    "error",
    "content_length",
    "size_mb",
    "content_type",
    "accept_ranges",
    "etag",
    "last_modified",
    "species_priority",
    "eligible_for_download",
    "selected_for_download",
    "selection_skip_reason",
]


def write_tsv(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})
    print(output_path)
    return output_path


def write_json(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_selected_ids(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ids = [str(row["dataset"]) for row in rows if row.get("selected_for_download")]
    output_path.write_text("\n".join(ids).rstrip() + ("\n" if ids else ""), encoding="utf-8")
    print(output_path)
    return output_path


def write_markdown(rows: list[dict[str, Any]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok_count = sum(1 for row in rows if row.get("ok"))
    selected = [row for row in rows if row.get("selected_for_download")]
    selected_total_mb = round(
        sum(int(row.get("content_length") or 0) for row in selected) / (1024 * 1024),
        3,
    )
    lines = [
        "# scPlantDB H5AD Size Probe",
        "",
        f"Rows probed: `{len(rows)}`.",
        f"Reachable H5AD gzip URLs: `{ok_count}`.",
        f"Selected for bounded acquisition: `{len(selected)}`.",
        f"Selected gzip size total MB: `{selected_total_mb}`.",
        "",
        "## Selected Datasets",
        "",
        "| Dataset | Species | Tissue | Cells | Size MB | PMID |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in selected:
        lines.append(
            "| {dataset} | {species} | {tissue} | {cells} | {size_mb} | {pmid} |".format(
                dataset=row.get("dataset", ""),
                species=row.get("species", ""),
                tissue=str(row.get("tissue", "")).replace("|", "/"),
                cells=row.get("cells", 0),
                size_mb=row.get("size_mb", 0),
                pmid=row.get("pmid", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Smallest Reachable Candidates",
            "",
            "| Dataset | Species | Tissue | Cells | Size MB | Selected |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    reachable = [row for row in rows if row.get("ok") and row.get("content_length")]
    for row in sorted(reachable, key=lambda item: int(item.get("content_length") or 0))[:20]:
        lines.append(
            "| {dataset} | {species} | {tissue} | {cells} | {size_mb} | {selected} |".format(
                dataset=row.get("dataset", ""),
                species=row.get("species", ""),
                tissue=str(row.get("tissue", "")).replace("|", "/"),
                cells=row.get("cells", 0),
                size_mb=row.get("size_mb", 0),
                selected="yes" if row.get("selected_for_download") else "no",
            )
        )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe scPlantDB public .h5ad.gz file sizes")
    parser.add_argument("--catalog-tsv", default="data/public_discovery/scplantdb_dataset_catalog.tsv")
    parser.add_argument("--output-tsv", default="data/public_discovery/scplantdb_h5ad_size_probe.tsv")
    parser.add_argument("--output-json", default="data/public_discovery/scplantdb_h5ad_size_probe.json")
    parser.add_argument("--output-md", default="data/public_discovery/scplantdb_h5ad_size_probe.md")
    parser.add_argument("--selected-output", default="data/public_discovery/scplantdb_selected_h5ad_datasets.txt")
    parser.add_argument("--max-bytes", type=int, default=750_000_000)
    parser.add_argument(
        "--max-total-bytes",
        type=int,
        default=3_000_000_000,
        help="Maximum total selected gzip bytes; use 0 for no total budget",
    )
    parser.add_argument("--min-cells", type=int, default=0)
    parser.add_argument("--max-datasets", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--no-diverse-species", action="store_true")
    args = parser.parse_args()

    rows = ranked_rows(
        read_catalog(args.catalog_tsv),
        max_bytes=args.max_bytes,
        max_total_bytes=args.max_total_bytes,
        min_cells=args.min_cells,
        max_datasets=args.max_datasets,
        timeout=args.timeout,
        diverse_species=not args.no_diverse_species,
    )
    write_tsv(rows, args.output_tsv)
    write_json(rows, args.output_json)
    write_markdown(rows, args.output_md)
    write_selected_ids(rows, args.selected_output)


if __name__ == "__main__":
    main()
