from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import subprocess
from datetime import datetime, timezone
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def _load_public_data_targets() -> list[dict[str, str]]:
    try:
        from write_status_summary import PUBLIC_DATA_TARGETS

        return [dict(item) for item in PUBLIC_DATA_TARGETS]
    except ModuleNotFoundError:
        sibling = Path(__file__).with_name("write_status_summary.py")
        spec = importlib.util.spec_from_file_location("write_status_summary", sibling)
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return [dict(item) for item in module.PUBLIC_DATA_TARGETS]


PUBLIC_DATA_TARGETS = _load_public_data_targets()
PROMOTION_SESSION_RE = re.compile(r"^snowcell_geo_promotion_(gse[0-9]+)$", re.IGNORECASE)


def read_json(path: Path | None) -> Any:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def file_entry(root: Path, path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": relpath(root, path),
        "bytes": stat.st_size,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def manifest_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def manifest_summary(root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": relpath(root, path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "rows": manifest_rows(path),
        "modified_utc": iso_mtime(path),
    }


def glob_files(root: Path, pattern: str | Iterable[str]) -> list[Path]:
    patterns = [pattern] if isinstance(pattern, str) else list(pattern)
    paths: dict[str, Path] = {}
    for item in patterns:
        for path in root.glob(item):
            if path.is_file():
                paths[path.as_posix()] = path
    return sorted(paths.values(), key=lambda item: item.as_posix())


def collect_target_files(root: Path, pattern: str | Iterable[str]) -> dict[str, Any]:
    files = glob_files(root, pattern)
    partials = [path for path in files if path.name.endswith(".aria2")]
    unsupported_reports = [
        path for path in files if path.name == "unsupported_single_cell_matrix.json"
    ]
    payloads = [path for path in files if not path.name.endswith(".aria2")]
    largest = max(payloads, key=lambda item: item.stat().st_size, default=None)
    latest_candidates = files
    latest = max((path.stat().st_mtime for path in latest_candidates), default=None)
    return {
        "pattern": pattern if isinstance(pattern, str) else list(pattern),
        "file_count": len(payloads),
        "bytes": sum(path.stat().st_size for path in payloads),
        "examples": [relpath(root, path) for path in payloads[:5]],
        "partial_file_count": len(partials),
        "partial_files": [file_entry(root, path) for path in partials],
        "partial_payloads": [
            file_entry(root, Path(str(path)[: -len(".aria2")]))
            for path in partials
            if Path(str(path)[: -len(".aria2")]).exists()
        ],
        "unsupported_report_count": len(unsupported_reports),
        "unsupported_reports": [file_entry(root, path) for path in unsupported_reports],
        "unsupported_payloads": [read_json(path) for path in unsupported_reports],
        "largest_file": file_entry(root, largest) if largest is not None else None,
        "latest_modified_utc": (
            datetime.fromtimestamp(latest, timezone.utc).isoformat() if latest is not None else None
        ),
    }


def public_manifest_rows(root: Path) -> dict[str, dict[str, str]]:
    path = root / "data" / "public_dataset_manifest.tsv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            row.get("dataset_id", ""): row
            for row in csv.DictReader(handle, delimiter="\t")
            if row.get("dataset_id")
        }


def status_summary_targets(status_summary: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(status_summary, dict):
        return {}
    rows = status_summary.get("public_data_targets")
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("dataset_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("dataset_id")
    }


def manifest_dataset_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sorted(
            {
                row.get("dataset_id", "")
                for row in csv.DictReader(handle, delimiter="\t")
                if row.get("dataset_id")
            }
        )


def tmux_sessions() -> set[str]:
    try:
        result = subprocess.run(
            ["tmux", "ls"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return set()
    return {line.split(":", 1)[0].strip() for line in result.stdout.splitlines() if line.strip()}


def accession_from_gse_manifest(path: Path) -> str | None:
    name = path.name
    if not name.startswith("corpus_manifest.gse") or not name.endswith(".tsv"):
        return None
    if name.endswith(".available.tsv"):
        return None
    return name.removeprefix("corpus_manifest.").removesuffix(".tsv").upper()


def geo_raw_globs(accession: str) -> list[str]:
    return [
        f"data/public/{accession}_10x/*",
        f"data/public/{accession}_h5/*",
        f"data/public/{accession}_h5ad/*",
        f"data/public/{accession}_mtx_tar/*",
        f"data/public/{accession}_mtx_components/*",
        f"data/public/{accession}_raw_tar/*",
        f"data/public/{accession}_rds/*",
    ]


def dynamic_manifest_targets(root: Path, static_targets: list[dict[str, str]]) -> list[dict[str, str]]:
    covered_manifests = {
        target[key]
        for target in static_targets
        for key in ("manifest", "available_manifest")
        if target.get(key)
    }
    targets: list[dict[str, str]] = []
    for manifest_path in sorted((root / "data").glob("corpus_manifest.gse*.tsv")):
        manifest_rel = relpath(root, manifest_path)
        if manifest_rel in covered_manifests:
            continue
        accession = accession_from_gse_manifest(manifest_path)
        if accession is None:
            continue
        dataset_ids = manifest_dataset_ids(manifest_path)
        dataset_id = dataset_ids[0] if dataset_ids else f"geo_{accession.lower()}"
        targets.append(
            {
                "dataset_id": dataset_id,
                "manifest": manifest_rel,
                "raw_globs": geo_raw_globs(accession),
                "npz_glob": f"data/public/{accession}_npz/*.npz",
                "source": "dynamic_gse_manifest",
            }
        )
    return targets


def geo_promotion_queue_targets(
    root: Path,
    covered_targets: list[dict[str, str]],
) -> list[dict[str, str]]:
    queue_path = root / "data" / "public_discovery" / "geo_promotion_download_queue.tsv"
    if not queue_path.exists():
        return []
    covered_manifests = {
        target[key]
        for target in covered_targets
        for key in ("manifest", "available_manifest")
        if target.get(key)
    }
    targets: list[dict[str, str]] = []
    with queue_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            accession = (row.get("accession") or "").strip().upper()
            manifest = (row.get("manifest") or "").strip()
            if not accession or not manifest or manifest in covered_manifests:
                continue
            dataset_id = (
                row.get("dataset_id")
                or row.get("suggested_dataset_id")
                or f"geo_{accession.lower()}"
            )
            targets.append(
                {
                    "dataset_id": dataset_id,
                    "manifest": manifest,
                    "raw_globs": geo_raw_globs(accession),
                    "npz_glob": f"data/public/{accession}_npz/*.npz",
                    "source": "geo_promotion_queue",
                    "accession": accession,
                    "queue_session": row.get("queue_session", ""),
                    "log_path": row.get("log_path", ""),
                    "source_url": row.get("source_url", ""),
                }
            )
    return targets


def active_untracked_promotion_targets(
    root: Path,
    covered_targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    covered_manifests = {
        target[key]
        for target in covered_targets
        for key in ("manifest", "available_manifest")
        if target.get(key)
    }
    targets: list[dict[str, Any]] = []
    for session in sorted(tmux_sessions()):
        match = PROMOTION_SESSION_RE.match(session)
        if match is None:
            continue
        accession = match.group(1).upper()
        manifest = f"data/corpus_manifest.{accession.lower()}.tsv"
        if manifest in covered_manifests:
            continue
        covered_manifests.add(manifest)
        targets.append(
            {
                "dataset_id": f"geo_{accession.lower()}_active_promotion",
                "manifest": manifest,
                "raw_globs": geo_raw_globs(accession),
                "npz_glob": f"data/public/{accession}_npz/*.npz",
                "source": "active_untracked_geo_promotion",
                "accession": accession,
                "queue_session": session,
                "log_path": f"logs/geo_promotion_{accession.lower()}.log",
            }
        )
    return targets


def target_status(
    manifest: dict[str, Any],
    available_manifest: dict[str, Any] | None,
    raw: dict[str, Any],
    npz: dict[str, Any],
    public_row: dict[str, str] | None,
    source: str | None = None,
) -> str:
    if manifest["rows"] or (available_manifest or {}).get("rows", 0):
        return "complete_manifest"
    if raw["partial_file_count"] or npz["partial_file_count"]:
        return "downloading_partial"
    if raw.get("unsupported_report_count") or npz.get("unsupported_report_count"):
        return "unsupported_for_matrix_corpus"
    if npz["file_count"]:
        return "npz_ready_no_manifest"
    if raw["file_count"]:
        return "raw_ready_no_manifest"
    if source in {"geo_promotion_queue", "active_untracked_geo_promotion"}:
        return "queued_pending_download"
    if public_row:
        return "metadata_only"
    return "missing"


def latest_modified(*items: dict[str, Any] | None) -> str | None:
    values = [
        str(item.get("latest_modified_utc") or item.get("modified_utc"))
        for item in items
        if item and (item.get("latest_modified_utc") or item.get("modified_utc"))
    ]
    return max(values) if values else None


def summarize_target(
    root: Path,
    target: dict[str, str],
    public_rows: dict[str, dict[str, str]],
    status_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dataset_id = target["dataset_id"]
    manifest = manifest_summary(root, root / target["manifest"])
    available_manifest = (
        manifest_summary(root, root / target["available_manifest"])
        if target.get("available_manifest")
        else None
    )
    raw = collect_target_files(root, target.get("raw_globs") or target["raw_glob"])
    npz = collect_target_files(root, target.get("npz_globs") or target["npz_glob"])
    public_row = public_rows.get(dataset_id)
    status_row = status_rows.get(dataset_id, {})
    status = target_status(
        manifest,
        available_manifest,
        raw,
        npz,
        public_row,
        target.get("source"),
    )
    total_partials = raw["partial_file_count"] + npz["partial_file_count"]
    active_partials = total_partials if status == "downloading_partial" else 0
    residual_partials = total_partials - active_partials
    return {
        "dataset_id": dataset_id,
        "source": target.get("source", "public_data_target"),
        "accession": target.get("accession"),
        "queue_session": target.get("queue_session"),
        "log_path": target.get("log_path"),
        "source_url": target.get("source_url"),
        "priority": (public_row or {}).get("priority"),
        "public_manifest_status": (public_row or {}).get("status"),
        "status_summary_stage": status_row.get("stage"),
        "download_status": status,
        "manifest": manifest,
        "available_manifest": available_manifest,
        "raw_files": raw,
        "npz_files": npz,
        "manifest_rows": manifest["rows"] + (available_manifest or {}).get("rows", 0),
        "partial_file_count": total_partials,
        "active_partial_file_count": active_partials,
        "residual_partial_file_count": residual_partials,
        "latest_modified_utc": latest_modified(manifest, available_manifest, raw, npz),
    }


def build_audit(
    project_dir: str | Path,
    status_summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_dir)
    status_summary = read_json(Path(status_summary_path)) if status_summary_path else None
    public_rows = public_manifest_rows(root)
    status_rows = status_summary_targets(status_summary)
    static_targets = PUBLIC_DATA_TARGETS
    dynamic_targets = dynamic_manifest_targets(root, static_targets)
    queue_targets = geo_promotion_queue_targets(root, [*static_targets, *dynamic_targets])
    active_untracked_targets = active_untracked_promotion_targets(
        root,
        [*static_targets, *dynamic_targets, *queue_targets],
    )
    audit_targets = [*static_targets, *dynamic_targets, *queue_targets, *active_untracked_targets]
    targets = [
        summarize_target(root, target, public_rows, status_rows)
        for target in audit_targets
    ]
    by_status: dict[str, int] = {}
    for target in targets:
        by_status[target["download_status"]] = by_status.get(target["download_status"], 0) + 1
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_count": len(targets),
        "status_counts": by_status,
        "complete_manifest_count": by_status.get("complete_manifest", 0),
        "downloading_partial_count": by_status.get("downloading_partial", 0),
        "unsupported_for_matrix_corpus_count": by_status.get(
            "unsupported_for_matrix_corpus",
            0,
        ),
        "partial_file_count": sum(target["partial_file_count"] for target in targets),
        "active_partial_file_count": sum(
            target["active_partial_file_count"] for target in targets
        ),
        "residual_partial_file_count": sum(
            target["residual_partial_file_count"] for target in targets
        ),
        "raw_file_count": sum(target["raw_files"]["file_count"] for target in targets),
        "npz_file_count": sum(target["npz_files"]["file_count"] for target in targets),
        "manifest_row_count": sum(target["manifest_rows"] for target in targets),
    }
    return {
        "project_dir": str(root),
        "status_summary_path": str(status_summary_path) if status_summary_path else None,
        "summary": summary,
        "targets": targets,
    }


def human_bytes(value: int | None) -> str:
    if value is None:
        return "-"
    size = float(value)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TiB"


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    status_counts = summary["status_counts"]
    lines = [
        "# SnowLotus-CellFM Download Progress Audit",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                ["Status", "Targets"],
                *[[status, str(count)] for status, count in sorted(status_counts.items())],
            ]
        ),
        "",
        (
            f"Tracked targets: {summary['target_count']}; manifest rows: "
            f"{summary['manifest_row_count']}; raw payload files: {summary['raw_file_count']}; "
            f"npz files: {summary['npz_file_count']}; active partial control files: "
            f"{summary['active_partial_file_count']}; residual control files: "
            f"{summary['residual_partial_file_count']}."
        ),
        "",
        "## Target State",
        "",
    ]
    target_rows = [
        [
            "Dataset",
            "Source",
            "Session",
            "Status",
            "Stage",
            "Manifest rows",
            "Raw",
            "NPZ",
            "Partial",
            "Largest raw",
            "Latest UTC",
        ]
    ]
    for target in payload["targets"]:
        largest = target["raw_files"].get("largest_file")
        target_rows.append(
            [
                target["dataset_id"],
                target["source"],
                str(target.get("queue_session") or "-"),
                target["download_status"],
                str(target.get("status_summary_stage") or "-"),
                str(target["manifest_rows"]),
                str(target["raw_files"]["file_count"]),
                str(target["npz_files"]["file_count"]),
                str(target["partial_file_count"]),
                human_bytes(largest["bytes"] if largest else None),
                str(target.get("latest_modified_utc") or "-"),
            ]
        )
    lines.extend([markdown_table(target_rows), "", "## Partial/Residual Download Control Files", ""])
    partial_targets = [target for target in payload["targets"] if target["partial_file_count"]]
    if not partial_targets:
        lines.append("No `.aria2` partial download control files were found.")
    else:
        for target in partial_targets:
            lines.append(f"### {target['dataset_id']}")
            lines.append("")
            partial_rows = [
                [
                    "Download status",
                    "Partial control file",
                    "Control bytes",
                    "Payload file",
                    "Payload bytes",
                ]
            ]
            for area, files_key in [("raw_files", "raw"), ("npz_files", "npz")]:
                partials = target[area]["partial_files"]
                payloads_by_path = {
                    item["path"]: item
                    for item in target[area].get("partial_payloads", [])
                }
                for partial in partials:
                    payload_path = partial["path"][: -len(".aria2")]
                    payload = payloads_by_path.get(payload_path)
                    partial_rows.append(
                        [
                            target["download_status"],
                            partial["path"],
                            str(partial["bytes"]),
                            payload_path if payload else f"{files_key}:missing_payload",
                            str(payload["bytes"]) if payload else "0",
                        ]
                    )
            lines.extend([markdown_table(partial_rows), ""])
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write public data download progress audit")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--status-summary", default=None)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    payload = build_audit(args.project_dir, args.status_summary)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
