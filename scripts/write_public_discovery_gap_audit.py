from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACCESSION_RE = re.compile(
    r"\b(GSE\d+|GSM\d+|GDS\d+|SRP\d+|SRA\d+|SRX\d+|SRR\d+|PRJNA\d+|PRJEB\d+|PRJDB\d+)\b",
    re.IGNORECASE,
)
HIGH_PRIORITIES = {"S", "A"}
REVIEW_PRIORITIES = {"S", "A", "B"}


def read_tsv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [path for path in root.glob(pattern) if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def relpath(root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def iso_mtime(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def extract_accessions(*values: str) -> set[str]:
    text = " ".join(value or "" for value in values)
    return {match.upper() for match in ACCESSION_RE.findall(text)}


def manifest_accessions(root: Path) -> set[str]:
    rows = read_tsv(root / "data" / "public_dataset_manifest.tsv")
    accessions: set[str] = set()
    for row in rows:
        accessions.update(
            extract_accessions(
                row.get("accession_or_doi", ""),
                row.get("source_url", ""),
            )
        )
    return accessions


def corpus_manifest_accessions(root: Path) -> set[str]:
    accessions: set[str] = set()
    for path in sorted((root / "data").glob("corpus_manifest.gse*.tsv")):
        if path.name.endswith(".available.tsv"):
            continue
        match = re.search(r"corpus_manifest\.(gse\d+)\.tsv$", path.name, re.IGNORECASE)
        if match:
            accessions.add(match.group(1).upper())
    return accessions


def manifest_dataset_ids(root: Path) -> set[str]:
    rows = read_tsv(root / "data" / "public_dataset_manifest.tsv")
    return {row.get("dataset_id", "") for row in rows if row.get("dataset_id")}


def corpus_dataset_ids(root: Path) -> set[str]:
    dataset_ids: set[str] = set()
    for path in sorted((root / "data").glob("corpus_manifest*.tsv")):
        for row in read_tsv(path):
            dataset_id = row.get("dataset_id")
            if dataset_id:
                dataset_ids.add(dataset_id)
    return dataset_ids


def unsupported_corpus_targets(root: Path) -> set[str]:
    targets: set[str] = set()
    for path in sorted((root / "data" / "public").glob("*_raw_tar/unsupported_single_cell_matrix.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        dataset_id = payload.get("dataset_id")
        accession = payload.get("accession")
        if dataset_id:
            targets.add(str(dataset_id))
        if accession:
            targets.add(str(accession).upper())
    return targets


def promotion_hold_accessions(root: Path) -> set[str]:
    path = root / "data" / "public_discovery" / "geo_manifest_promotion_candidates.tsv"
    holds: set[str] = set()
    for row in read_tsv(path):
        status = (row.get("promotion_status") or "").upper()
        accession = (row.get("accession") or "").upper()
        if accession and status.startswith("HOLD_"):
            holds.add(accession)
    return holds


def queued_geo_jobs(root: Path) -> dict[str, dict[str, str]]:
    scripts = [
        root / "scripts" / "queue_reviewed_geo_downloads.sh",
        root / "scripts" / "generated_geo_promotion_downloads" / "queue_geo_promotion_downloads.sh",
    ]
    jobs: dict[str, dict[str, str]] = {}
    for script in scripts:
        jobs.update(queued_geo_jobs_from_script(root, script))
    return jobs


def queued_geo_jobs_from_script(root: Path, script: Path) -> dict[str, dict[str, str]]:
    if not script.exists():
        return {}
    jobs: dict[str, dict[str, str]] = {}
    for line in script.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not (stripped.startswith('"') and stripped.endswith('"')):
            continue
        parts = stripped.strip('"').split("|")
        if len(parts) != 4:
            continue
        session, manifest, command, log_path = parts
        accession_match = re.search(r"corpus_manifest\.([^.]+)\.tsv", manifest, re.IGNORECASE)
        if not accession_match:
            continue
        accession = accession_match.group(1).upper()
        jobs[accession] = {
            "session": session,
            "manifest": manifest,
            "command": command,
            "log_path": log_path,
            "queue_script": relpath(root, script) or script.as_posix(),
        }
    return jobs


def is_truthy(value: str | None) -> bool:
    return str(value or "").lower() in {"true", "1", "yes", "y"}


def row_priority(row: dict[str, str]) -> str:
    return (row.get("priority") or "").strip().upper()


def row_score(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("score") or 0))
    except ValueError:
        return 0


def discovery_rows_to_review(
    rows: list[dict[str, str]],
    known_accessions: set[str],
    priorities: set[str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in rows:
        accession = (row.get("accession") or row.get("uid") or "").upper()
        accessions = extract_accessions(accession, row.get("url", ""), row.get("summary", ""))
        if not accessions and accession:
            accessions = {accession}
        priority = row_priority(row)
        if priority not in priorities:
            continue
        if accessions & known_accessions:
            continue
        action = row.get("recommended_action", "")
        if "out-of-scope" in action.lower():
            continue
        candidates.append(
            {
                "accession": accession,
                "priority": priority,
                "score": row_score(row),
                "title": row.get("title", ""),
                "organism": row.get("organism", ""),
                "url": row.get("url", ""),
                "matched_queries": row.get("matched_queries", ""),
                "recommended_action": action,
            }
        )
    return sorted(candidates, key=lambda item: (item["priority"], -item["score"], item["accession"]))


def geo_rows_to_review(
    rows: list[dict[str, str]],
    known_accessions: set[str],
    corpus_ids: set[str],
    unsupported_targets: set[str],
    queued_jobs: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    unknown_ready: list[dict[str, Any]] = []
    manifest_ready_without_corpus: list[dict[str, Any]] = []
    for row in rows:
        matrix_count = int(row.get("matrix_file_count") or 0)
        ready = is_truthy(row.get("download_ready"))
        if not ready:
            continue
        accession = (row.get("accession") or "").upper()
        dataset_id = row.get("dataset_id", "")
        if accession in unsupported_targets or dataset_id in unsupported_targets:
            continue
        item = {
            "dataset_id": dataset_id,
            "accession": accession,
            "priority": row.get("priority", ""),
            "matrix_file_count": matrix_count,
            "file_type_counts": row.get("file_type_counts", ""),
            "recommended_action": row.get("recommended_action", ""),
            "page_url": row.get("page_url", ""),
            "queued_download": accession in queued_jobs,
            "queue_job": queued_jobs.get(accession),
        }
        if accession and accession not in known_accessions:
            unknown_ready.append(item)
        elif item["dataset_id"] and item["dataset_id"] not in corpus_ids:
            manifest_ready_without_corpus.append(item)
    return unknown_ready, manifest_ready_without_corpus


def build_audit(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    discovery_dir = root / "data" / "public_discovery"
    latest_ncbi = latest_file(discovery_dir, "ncbi_discovery_*.tsv")
    latest_geo = latest_file(discovery_dir, "geo_supplementary_review_*.tsv")
    latest_geo_files = latest_file(discovery_dir, "geo_supplementary_files_*.tsv")
    ncbi_rows = read_tsv(latest_ncbi)
    geo_rows = read_tsv(latest_geo)
    public_manifest_accessions = manifest_accessions(root)
    dynamic_corpus_accessions = corpus_manifest_accessions(root)
    known_accessions = public_manifest_accessions | dynamic_corpus_accessions
    manifest_ids = manifest_dataset_ids(root)
    corpus_ids = corpus_dataset_ids(root)
    unsupported_targets = unsupported_corpus_targets(root)
    queued_jobs = queued_geo_jobs(root)
    promotion_holds = promotion_hold_accessions(root)
    queued_accessions = set(queued_jobs)
    handled_accessions = known_accessions | queued_accessions | promotion_holds
    high_priority = discovery_rows_to_review(ncbi_rows, handled_accessions, HIGH_PRIORITIES)
    review_candidates = discovery_rows_to_review(ncbi_rows, handled_accessions, REVIEW_PRIORITIES)
    unknown_geo_ready, manifest_ready_without_corpus = geo_rows_to_review(
        geo_rows,
        known_accessions,
        corpus_ids,
        unsupported_targets | promotion_holds,
        queued_jobs,
    )
    unknown_geo_ready_queued = [
        item for item in unknown_geo_ready if item.get("queued_download")
    ]
    unknown_geo_ready_unqueued = [
        item for item in unknown_geo_ready if not item.get("queued_download")
    ]
    manifest_ready_queued = [
        item for item in manifest_ready_without_corpus if item.get("queued_download")
    ]
    manifest_ready_unqueued = [
        item for item in manifest_ready_without_corpus if not item.get("queued_download")
    ]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest_ncbi_discovery": relpath(root, latest_ncbi),
        "latest_ncbi_discovery_modified_utc": iso_mtime(latest_ncbi),
        "latest_geo_review": relpath(root, latest_geo),
        "latest_geo_review_modified_utc": iso_mtime(latest_geo),
        "latest_geo_file_index": relpath(root, latest_geo_files),
        "latest_geo_file_index_modified_utc": iso_mtime(latest_geo_files),
        "known_manifest_accession_count": len(known_accessions),
        "public_manifest_accession_count": len(public_manifest_accessions),
        "dynamic_corpus_manifest_accession_count": len(dynamic_corpus_accessions),
        "queued_geo_job_count": len(queued_jobs),
        "manifest_dataset_count": len(manifest_ids),
        "corpus_dataset_count": len(corpus_ids),
        "unsupported_expression_corpus_target_count": len(unsupported_targets),
        "promotion_hold_accession_count": len(promotion_holds),
        "discovery_record_count": len(ncbi_rows),
        "geo_review_count": len(geo_rows),
        "new_review_candidate_count": len(review_candidates),
        "new_high_priority_candidate_count": len(high_priority),
        "geo_download_ready_unknown_manifest_count": len(unknown_geo_ready),
        "geo_download_ready_unknown_manifest_queued_count": len(unknown_geo_ready_queued),
        "geo_download_ready_unknown_manifest_unqueued_count": len(unknown_geo_ready_unqueued),
        "manifest_download_ready_without_corpus_count": len(manifest_ready_without_corpus),
        "manifest_download_ready_queued_count": len(manifest_ready_queued),
        "manifest_download_ready_unqueued_count": len(manifest_ready_unqueued),
        "requires_manual_manifest_review": bool(high_priority or unknown_geo_ready_unqueued),
        "requires_downloader_or_manifest_followup": bool(manifest_ready_unqueued),
        "requires_queued_download_completion": bool(
            manifest_ready_queued or unknown_geo_ready_queued
        ),
    }
    return {
        "project_dir": str(root),
        "summary": summary,
        "new_high_priority_candidates": high_priority[:50],
        "new_review_candidates": review_candidates[:100],
        "geo_download_ready_unknown_manifest": unknown_geo_ready[:50],
        "geo_download_ready_unknown_manifest_queued": unknown_geo_ready_queued[:50],
        "geo_download_ready_unknown_manifest_unqueued": unknown_geo_ready_unqueued[:50],
        "manifest_download_ready_without_corpus": manifest_ready_without_corpus[:50],
        "manifest_download_ready_queued": manifest_ready_queued[:50],
        "manifest_download_ready_unqueued": manifest_ready_unqueued[:50],
    }


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join("---" for _ in rows[0]) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)


def compact(value: Any, limit: int = 120) -> str:
    text = str(value or "").replace("|", "/").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def candidate_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "None."
    table = [["Priority", "Score", "Accession", "Title", "Action"]]
    for row in rows:
        table.append(
            [
                str(row.get("priority") or "-"),
                str(row.get("score") or "-"),
                str(row.get("accession") or "-"),
                compact(row.get("title")),
                compact(row.get("recommended_action")),
            ]
        )
    return markdown_table(table)


def geo_table(rows: list[dict[str, Any]], include_queue: bool = False) -> str:
    if not rows:
        return "None."
    if include_queue:
        table = [["Dataset", "Accession", "Matrices", "File Types", "Queued", "Action"]]
    else:
        table = [["Dataset", "Accession", "Matrices", "File Types", "Action"]]
    for row in rows:
        base = [
            compact(row.get("dataset_id"), 60),
            compact(row.get("accession"), 20),
            str(row.get("matrix_file_count") or 0),
            compact(row.get("file_type_counts"), 80),
        ]
        if include_queue:
            queued = "yes" if row.get("queued_download") else "no"
            action = row.get("recommended_action")
            if row.get("queue_job"):
                action = f"{row['queue_job'].get('command', '')}"
            table.append(base + [queued, compact(action)])
        else:
            table.append(base + [compact(row.get("recommended_action"))])
    return markdown_table(table)


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Public Discovery Gap Audit",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "## Inputs",
        "",
        f"- Latest NCBI discovery: `{summary['latest_ncbi_discovery']}`",
        f"- Latest GEO review: `{summary['latest_geo_review']}`",
        f"- Latest GEO file index: `{summary['latest_geo_file_index']}`",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                ["Metric", "Value"],
                ["Known manifest accessions", str(summary["known_manifest_accession_count"])],
                ["Manifest datasets", str(summary["manifest_dataset_count"])],
                ["Corpus datasets", str(summary["corpus_dataset_count"])],
                ["Promotion hold accessions", str(summary["promotion_hold_accession_count"])],
                ["Discovery records", str(summary["discovery_record_count"])],
                ["GEO review rows", str(summary["geo_review_count"])],
                ["New review candidates", str(summary["new_review_candidate_count"])],
                ["New high-priority candidates", str(summary["new_high_priority_candidate_count"])],
                [
                    "GEO-ready unknown-manifest rows",
                    str(summary["geo_download_ready_unknown_manifest_count"]),
                ],
                [
                    "GEO-ready unknown-manifest already queued",
                    str(summary["geo_download_ready_unknown_manifest_queued_count"]),
                ],
                [
                    "GEO-ready unknown-manifest still unqueued",
                    str(summary["geo_download_ready_unknown_manifest_unqueued_count"]),
                ],
                [
                    "Manifest GEO-ready without corpus rows",
                    str(summary["manifest_download_ready_without_corpus_count"]),
                ],
                [
                    "Manifest GEO-ready already queued",
                    str(summary["manifest_download_ready_queued_count"]),
                ],
                [
                    "Manifest GEO-ready still unqueued",
                    str(summary["manifest_download_ready_unqueued_count"]),
                ],
                ["Requires manual manifest review", str(summary["requires_manual_manifest_review"])],
                [
                    "Requires downloader/manifest follow-up",
                    str(summary["requires_downloader_or_manifest_followup"]),
                ],
                [
                    "Requires queued download completion",
                    str(summary["requires_queued_download_completion"]),
                ],
            ]
        ),
        "",
        "## New High-Priority Candidates",
        "",
        candidate_table(payload["new_high_priority_candidates"]),
        "",
        "## GEO-Ready Unknown Manifest Rows",
        "",
        geo_table(payload["geo_download_ready_unknown_manifest"], include_queue=True),
        "",
        "## GEO-Ready Unknown Manifest Still Unqueued",
        "",
        geo_table(payload["geo_download_ready_unknown_manifest_unqueued"]),
        "",
        "## Manifest GEO-Ready Without Corpus Rows",
        "",
        geo_table(payload["manifest_download_ready_without_corpus"], include_queue=True),
        "",
        "## Manifest GEO-Ready Still Unqueued",
        "",
        geo_table(payload["manifest_download_ready_unqueued"]),
        "",
        "## New Review Candidates",
        "",
        candidate_table(payload["new_review_candidates"][:30]),
    ]
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write public discovery gap audit for SnowLotus-CellFM.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = build_audit(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
