from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ManifestReadiness:
    manifest: str
    rows: int
    dataset_ids: str
    missing_from_active_manifest: int
    missing_from_plus_manifest: int | None
    newer_than_active_corpus: bool
    newer_than_plus_corpus: bool | None


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def manifest_paths(path: Path) -> set[str]:
    return {row.get("path", "") for row in read_tsv(path) if row.get("path")}


def iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def tmux_sessions() -> list[str]:
    try:
        result = subprocess.run(
            ["tmux", "ls"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    return [line.split(":", 1)[0] for line in result.stdout.splitlines() if line.strip()]


def active_training_processes() -> list[str]:
    try:
        result = subprocess.run(
            ["pgrep", "-af", "[s]nowcell train --config"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def progress_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"unparsed_text_tail": path.read_text(encoding="utf-8", errors="replace")[-2000:]}


def collect_manifest_readiness(
    root: Path,
    active_manifest: Path,
    active_corpus: Path,
    plus_manifest: Path,
    plus_corpus: Path,
) -> list[ManifestReadiness]:
    active_paths = manifest_paths(active_manifest)
    plus_paths = manifest_paths(plus_manifest) if plus_manifest.exists() else set()
    manifests = sorted(
        path
        for pattern in ("corpus_manifest.gse*.tsv", "corpus_manifest.scplantdb*.tsv")
        for path in (root / "data").glob(pattern)
        if not path.name.endswith(".available.tsv")
    )
    items: list[ManifestReadiness] = []
    for manifest in manifests:
        rows = read_tsv(manifest)
        if not rows:
            continue
        dataset_ids = sorted({row.get("dataset_id", "") for row in rows if row.get("dataset_id")})
        row_paths = [row.get("path", "") for row in rows if row.get("path")]
        items.append(
            ManifestReadiness(
                manifest=manifest.relative_to(root).as_posix(),
                rows=len(rows),
                dataset_ids=";".join(dataset_ids),
                missing_from_active_manifest=sum(path not in active_paths for path in row_paths),
                missing_from_plus_manifest=(
                    sum(path not in plus_paths for path in row_paths) if plus_manifest.exists() else None
                ),
                newer_than_active_corpus=active_corpus.exists()
                and manifest.stat().st_mtime > active_corpus.stat().st_mtime,
                newer_than_plus_corpus=(
                    plus_corpus.exists() and manifest.stat().st_mtime > plus_corpus.stat().st_mtime
                    if plus_corpus.exists()
                    else None
                ),
            )
        )
    return items


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = args.project_dir
    active_manifest = root / args.active_manifest
    active_corpus = root / args.active_corpus
    plus_manifest = root / args.plus_manifest
    plus_corpus = root / args.plus_corpus
    items = collect_manifest_readiness(root, active_manifest, active_corpus, plus_manifest, plus_corpus)
    sessions = tmux_sessions()
    active_train = active_training_processes()
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_manifest": args.active_manifest.as_posix(),
        "active_manifest_exists": active_manifest.exists(),
        "active_manifest_rows": len(read_tsv(active_manifest)),
        "active_corpus": args.active_corpus.as_posix(),
        "active_corpus_exists": active_corpus.exists(),
        "active_corpus_modified_utc": iso_mtime(active_corpus),
        "plus_manifest": args.plus_manifest.as_posix(),
        "plus_manifest_exists": plus_manifest.exists(),
        "plus_manifest_rows": len(read_tsv(plus_manifest)),
        "plus_corpus": args.plus_corpus.as_posix(),
        "plus_corpus_exists": plus_corpus.exists(),
        "plus_corpus_modified_utc": iso_mtime(plus_corpus),
        "v03_progress": progress_json(root / args.v03_progress),
        "v03_best_exists": (root / args.v03_best).exists(),
        "v04_config_exists": (root / args.v04_config).exists(),
        "v04_output_best_exists": (root / args.v04_output_dir / "best.pt").exists(),
        "v04_watcher_session_active": args.v04_watcher_session in sessions,
        "active_training_processes": active_train,
        "manifest_readiness": [asdict(item) for item in items],
    }
    payload["summary"] = {
        "completed_manifest_count": len(items),
        "completed_manifest_rows": sum(item.rows for item in items),
        "manifests_with_rows_missing_from_active": sum(
            item.missing_from_active_manifest > 0 for item in items
        ),
        "rows_missing_from_active": sum(item.missing_from_active_manifest for item in items),
        "manifests_with_rows_missing_from_plus": (
            sum((item.missing_from_plus_manifest or 0) > 0 for item in items)
            if plus_manifest.exists()
            else None
        ),
        "rows_missing_from_plus": (
            sum(item.missing_from_plus_manifest or 0 for item in items)
            if plus_manifest.exists()
            else None
        ),
        "v03_status": (payload["v03_progress"] or {}).get("status")
        if isinstance(payload["v03_progress"], dict)
        else None,
        "v03_epoch": (payload["v03_progress"] or {}).get("epoch")
        if isinstance(payload["v03_progress"], dict)
        else None,
        "v03_step": (payload["v03_progress"] or {}).get("step")
        if isinstance(payload["v03_progress"], dict)
        else None,
        "v03_train_batches_per_epoch": (payload["v03_progress"] or {}).get("train_batches_per_epoch")
        if isinstance(payload["v03_progress"], dict)
        else None,
        "active_training_process_count": len(active_train),
    }
    return payload


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Public MLM Plus-Corpus Readiness",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Completed public manifests | {summary['completed_manifest_count']} |",
        f"| Completed public manifest rows | {summary['completed_manifest_rows']} |",
        f"| Rows missing from active public MLM manifest | {summary['rows_missing_from_active']} |",
        f"| Rows missing from plus manifest | {summary['rows_missing_from_plus']} |",
        f"| v0.3 status | {summary['v03_status']} |",
        f"| v0.3 epoch/step | {summary['v03_epoch']} / {summary['v03_step']} |",
        f"| v0.3 batches per epoch | {summary['v03_train_batches_per_epoch']} |",
        f"| v0.4 watcher active | {payload['v04_watcher_session_active']} |",
        f"| Active training processes | {summary['active_training_process_count']} |",
        "",
        "## Corpus Files",
        "",
        "| Corpus | Exists | Rows | Modified UTC |",
        "| --- | --- | ---: | --- |",
        (
            f"| Active manifest `{payload['active_manifest']}` | {payload['active_manifest_exists']} | "
            f"{payload['active_manifest_rows']} | - |"
        ),
        (
            f"| Active corpus `{payload['active_corpus']}` | {payload['active_corpus_exists']} | "
            f"- | {payload['active_corpus_modified_utc']} |"
        ),
        (
            f"| Plus manifest `{payload['plus_manifest']}` | {payload['plus_manifest_exists']} | "
            f"{payload['plus_manifest_rows']} | - |"
        ),
        (
            f"| Plus corpus `{payload['plus_corpus']}` | {payload['plus_corpus_exists']} | "
            f"- | {payload['plus_corpus_modified_utc']} |"
        ),
        "",
        "## Completed Manifests",
        "",
        "| Manifest | Rows | Dataset IDs | Missing active | Missing plus | Newer active corpus | Newer plus corpus |",
        "| --- | ---: | --- | ---: | ---: | --- | --- |",
    ]
    for item in payload["manifest_readiness"]:
        lines.append(
            "| {manifest} | {rows} | {dataset_ids} | {active} | {plus} | {newer_active} | {newer_plus} |".format(
                manifest=item["manifest"],
                rows=item["rows"],
                dataset_ids=item["dataset_ids"],
                active=item["missing_from_active_manifest"],
                plus=item["missing_from_plus_manifest"],
                newer_active=item["newer_than_active_corpus"],
                newer_plus=item["newer_than_plus_corpus"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write public MLM plus-corpus readiness audit")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--active-manifest", default=Path("data/corpus_manifest_public_mlm.tsv"), type=Path)
    parser.add_argument("--active-corpus", default=Path("data/plant_foundation_corpus_public_mlm.h5ad"), type=Path)
    parser.add_argument("--plus-manifest", default=Path("data/corpus_manifest_public_mlm_plus_latest.tsv"), type=Path)
    parser.add_argument("--plus-corpus", default=Path("data/plant_foundation_corpus_public_mlm_plus_latest.h5ad"), type=Path)
    parser.add_argument(
        "--v03-progress",
        default=Path("outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/progress_latest.json"),
        type=Path,
    )
    parser.add_argument(
        "--v03-best",
        default=Path("outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt"),
        type=Path,
    )
    parser.add_argument(
        "--v04-config",
        default=Path("configs/generated/foundation_5090_mlm_public_expansion_v0_4_plus_latest.yaml"),
        type=Path,
    )
    parser.add_argument(
        "--v04-output-dir",
        default=Path("outputs/foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm"),
        type=Path,
    )
    parser.add_argument(
        "--v04-watcher-session",
        default="snowcell_mlm_public_expansion_v0_4_after_v0_3_watchdog",
    )
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()

    payload = build_payload(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
