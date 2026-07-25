from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class PendingCorpusAddition:
    manifest: str
    dataset_ids: str
    rows: int
    rows_missing_from_public_mlm_manifest: int
    manifest_newer_than_public_corpus: bool
    pending_refresh: bool


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def public_manifest_paths(path: Path) -> set[str]:
    return {row.get("path", "") for row in read_tsv(path) if row.get("path")}


def manifest_pending_status(
    manifest: Path,
    public_manifest: Path,
    public_corpus: Path,
) -> PendingCorpusAddition:
    rows = read_tsv(manifest)
    public_paths = public_manifest_paths(public_manifest)
    missing_rows = sum(1 for row in rows if row.get("path", "") not in public_paths)
    manifest_newer = public_corpus.exists() and manifest.stat().st_mtime > public_corpus.stat().st_mtime
    pending = missing_rows > 0 or manifest_newer or not public_corpus.exists()
    dataset_ids = sorted({row.get("dataset_id", "") for row in rows if row.get("dataset_id")})
    return PendingCorpusAddition(
        manifest=manifest.as_posix(),
        dataset_ids=";".join(dataset_ids),
        rows=len(rows),
        rows_missing_from_public_mlm_manifest=missing_rows,
        manifest_newer_than_public_corpus=manifest_newer,
        pending_refresh=pending,
    )


def collect_pending(
    project_dir: Path,
    public_manifest: Path,
    public_corpus: Path,
) -> list[PendingCorpusAddition]:
    manifests = sorted(
        path
        for pattern in ("corpus_manifest.gse*.tsv", "corpus_manifest.scplantdb*.tsv")
        for path in (project_dir / "data").glob(pattern)
        if not path.name.endswith(".available.tsv")
    )
    return [
        manifest_pending_status(path, public_manifest, public_corpus)
        for path in manifests
        if read_tsv(path)
    ]


def write_markdown(items: list[PendingCorpusAddition], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pending Public Corpus Additions",
        "",
        "This audit compares completed `data/corpus_manifest.gse*.tsv` and `data/corpus_manifest.scplantdb*.tsv` files against the current `data/corpus_manifest_public_mlm.tsv` and `data/plant_foundation_corpus_public_mlm.h5ad`.",
        "",
        "| Manifest | Dataset IDs | Rows | Missing rows in public MLM manifest | Manifest newer than public corpus | Pending refresh |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for item in items:
        lines.append(
            "| {manifest} | {dataset_ids} | {rows} | {missing} | {newer} | {pending} |".format(
                manifest=item.manifest,
                dataset_ids=item.dataset_ids,
                rows=item.rows,
                missing=item.rows_missing_from_public_mlm_manifest,
                newer=item.manifest_newer_than_public_corpus,
                pending=item.pending_refresh,
            )
        )
    if not items:
        lines.append("| None |  | 0 | 0 | False | False |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def write_json(items: list[PendingCorpusAddition], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload: list[dict[str, Any]] = [asdict(item) for item in items]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit completed public manifests pending corpus refresh")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--public-manifest", default="data/corpus_manifest_public_mlm.tsv", type=Path)
    parser.add_argument("--public-corpus", default="data/plant_foundation_corpus_public_mlm.h5ad", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    project_dir = args.project_dir
    public_manifest = project_dir / args.public_manifest
    public_corpus = project_dir / args.public_corpus
    items = collect_pending(project_dir, public_manifest, public_corpus)
    write_markdown(items, args.output_md)
    write_json(items, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
