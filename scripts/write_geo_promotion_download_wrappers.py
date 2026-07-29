from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMOTE_STATUS = "PROMOTE_DOWNLOAD_CANDIDATE"
REVIEWED_QUEUE_SCRIPT = Path("scripts/queue_reviewed_geo_downloads.sh")
REVIEWED_QUEUE_JOB_RE = re.compile(
    r'"[^"\n|]+\|(?P<manifest>data/corpus_manifest\.[^"\n|]+\.tsv)\|'
)


@dataclass
class PromotionDownloadJob:
    accession: str
    dataset_id: str
    species: str
    tissue: str
    title: str
    file_type_counts: str
    downloader_script: str
    wrapper_script: str
    queue_session: str
    manifest: str
    log_path: str
    source_url: str


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clean_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def infer_tissue(title: str) -> str:
    lower = title.lower()
    if "root" in lower:
        return "root"
    if "stem" in lower or "xylem" in lower:
        return "stem"
    if "leaf" in lower or "leaves" in lower:
        return "leaf"
    if "flower" in lower:
        return "flower"
    if "embryo" in lower or "embryonic" in lower:
        return "embryo"
    if "seed" in lower:
        return "seed"
    return "public_discovery"


def downloader_for(row: dict[str, str]) -> str:
    recommended = row.get("recommended_downloader", "")
    file_types = row.get("file_type_counts", "")
    if "mtx_component:" in file_types and "mtx_archive:" not in file_types:
        return "download_geo_mtx_component_subset.sh"
    if "mtx_archive:" in file_types:
        return "download_geo_raw_tar_mtx_subset.sh"
    if "seurat_rds:" in file_types:
        return "download_geo_page_rds_subset.sh"
    if "tenx_h5:" in file_types:
        return "download_geo_raw_tar_h5_subset.sh"
    if recommended == "download_geo_rds_subset.sh":
        return "download_geo_page_rds_subset.sh"
    if recommended in {
        "download_geo_raw_tar_mtx_subset.sh",
        "download_geo_raw_tar_h5_subset.sh",
        "download_geo_page_rds_subset.sh",
        "download_geo_mtx_component_subset.sh",
    }:
        return recommended
    return "manual_review"


def promotion_rows(path: Path) -> list[dict[str, str]]:
    rows = []
    for row in read_tsv(path):
        if row.get("promotion_status") != PROMOTE_STATUS:
            continue
        downloader = downloader_for(row)
        if downloader == "manual_review":
            continue
        item = dict(row)
        item["downloader_script"] = downloader
        rows.append(item)
    return rows


def read_reviewed_queue_manifests(
    project_dir: Path,
    queue_script: Path = REVIEWED_QUEUE_SCRIPT,
) -> list[str]:
    path = project_dir / queue_script if not queue_script.is_absolute() else queue_script
    if not path.exists():
        return []
    seen: set[str] = set()
    manifests: list[str] = []
    for match in REVIEWED_QUEUE_JOB_RE.finditer(path.read_text(encoding="utf-8")):
        manifest = match.group("manifest")
        if manifest in seen:
            continue
        seen.add(manifest)
        manifests.append(manifest)
    return manifests


def shell_export(name: str, value: str) -> str:
    return f"export {name}={shlex.quote(value)}"


def write_wrapper(job: PromotionDownloadJob, project_dir: Path) -> None:
    path = project_dir / job.wrapper_script
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'cd "$(dirname "$0")/../.."',
        "source .venv/bin/activate 2>/dev/null || true",
        shell_export("SNOWCELL_GEO_ACCESSION", job.accession),
        shell_export("SNOWCELL_GEO_DATASET_ID", job.dataset_id),
        shell_export("SNOWCELL_GEO_SPECIES", job.species),
        shell_export("SNOWCELL_GEO_TISSUE", job.tissue),
        'export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"',
        'export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"',
    ]
    if job.downloader_script == "download_geo_page_rds_subset.sh":
        lines.append('export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GEO_MAX_FILES:-1}"')
        lines.append('export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GEO_PAGE_PATTERN:-\\.rds(\\.gz)?$}"')
    elif job.downloader_script == "download_geo_raw_tar_h5_subset.sh":
        lines.append('export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GEO_MAX_FILES:-1}"')
    lines.extend(
        [
            f"bash scripts/{job.downloader_script}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def job_from_row(row: dict[str, str], output_dir: Path) -> PromotionDownloadJob:
    accession = row["accession"].upper()
    dataset_id = row.get("suggested_dataset_id") or f"geo_{accession.lower()}"
    species = row.get("organism") or "unknown plant"
    title = row.get("title", "")
    tissue = infer_tissue(title)
    suffix = clean_token(dataset_id)[:80]
    wrapper = output_dir / f"download_{accession.lower()}_{suffix}.sh"
    return PromotionDownloadJob(
        accession=accession,
        dataset_id=dataset_id,
        species=species,
        tissue=tissue,
        title=title,
        file_type_counts=row.get("file_type_counts", ""),
        downloader_script=row["downloader_script"],
        wrapper_script=wrapper.as_posix(),
        queue_session=f"snowcell_geo_promotion_{accession.lower()}",
        manifest=f"data/corpus_manifest.{accession.lower()}.tsv",
        log_path=f"logs/geo_promotion_{accession.lower()}.log",
        source_url=row.get("source_url", ""),
    )


def write_queue_script(jobs: list[PromotionDownloadJob], project_dir: Path, queue_script: Path) -> Path:
    path = project_dir / queue_script
    path.parent.mkdir(parents=True, exist_ok=True)
    job_lines = "\n".join(
        f'  "{job.queue_session}|{job.manifest}|bash {job.wrapper_script}|{job.log_path}"'
        for job in jobs
    )
    reviewed_manifest_lines = "\n".join(
        f'  "{manifest}"' for manifest in read_reviewed_queue_manifests(project_dir)
    )
    content = f"""#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs

poll_seconds="${{SNOWCELL_GEO_PROMOTION_QUEUE_POLL_SECONDS:-120}}"
large_raw_scan_interval="${{SNOWCELL_GEO_RAW_TAR_SCAN_INTERVAL_SECONDS:-1800}}"
last_large_raw_scan=0

jobs=(
{job_lines}
)

reviewed_manifests=(
{reviewed_manifest_lines}
)

manifest_row_count() {{
  local manifest="$1"
  python - "$manifest" <<'PY'
import csv
import sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.exists():
    print(0)
else:
    with path.open("r", encoding="utf-8", newline="") as handle:
        print(sum(1 for _ in csv.DictReader(handle, delimiter="\\t")))
PY
}}

unsupported_report_for_manifest() {{
  local manifest="$1"
  find_transfer_file_for_manifest "$manifest" "unsupported_single_cell_matrix.json"
}}

partial_download_for_manifest() {{
  local manifest="$1"
  find_transfer_file_for_manifest "$manifest" "*.aria2"
}}

find_transfer_file_for_manifest() {{
  local manifest="$1"
  local pattern="$2"
  local filename accession
  filename="$(basename "$manifest")"
  accession="${{filename#corpus_manifest.}}"
  accession="${{accession%.tsv}}"
  accession="${{accession^^}}"
  local suffix dir hit
  for suffix in 10x h5 h5ad mtx_tar mtx_components raw_tar rds; do
    dir="data/public/${{accession}}_${{suffix}}"
    hit="$(find "$dir" \\
      -maxdepth 1 \\
      -type f \\
      -name "$pattern" \\
      -print \\
      -quit 2>/dev/null || true)"
    if [ -n "$hit" ]; then
      echo "$hit"
      return 0
    fi
  done
}}

reviewed_manifest_done() {{
  local manifest="$1"
  local rows partial unsupported
  rows="$(manifest_row_count "$manifest")"
  if [ "$rows" -gt 0 ]; then
    return 0
  fi
  partial="$(partial_download_for_manifest "$manifest")"
  if [ -n "$partial" ]; then
    return 1
  fi
  unsupported="$(unsupported_report_for_manifest "$manifest")"
  if [ -n "$unsupported" ]; then
    return 0
  fi
  return 1
}}

promotion_manifest_done() {{
  local manifest="$1"
  local rows unsupported
  rows="$(manifest_row_count "$manifest")"
  if [ "$rows" -gt 0 ]; then
    echo "[$(date)] promotion GEO job complete: $manifest"
    return 0
  fi
  unsupported="$(unsupported_report_for_manifest "$manifest")"
  if [ -n "$unsupported" ]; then
    echo "[$(date)] promotion GEO job unsupported: $manifest ($unsupported)"
    return 0
  fi
  return 1
}}

reviewed_queue_pending() {{
  local manifest
  for manifest in "${{reviewed_manifests[@]}}"; do
    if ! reviewed_manifest_done "$manifest"; then
      return 0
    fi
  done
  return 1
}}

has_active_reviewed_transfer() {{
  tmux ls 2>/dev/null | cut -d: -f1 | grep -E '^snowcell_gse[0-9].*_subset$' >/dev/null 2>&1
}}

has_active_unfinished_promotion_transfer() {{
  local current_session="${{1:-}}"
  local active_session active_accession active_manifest
  while IFS= read -r active_session; do
    if [ "$active_session" = "$current_session" ]; then
      continue
    fi
    case "$active_session" in
      snowcell_geo_promotion_gse[0-9]*)
        active_accession="${{active_session#snowcell_geo_promotion_}}"
        active_manifest="data/corpus_manifest.${{active_accession}}.tsv"
        if promotion_manifest_done "$active_manifest" >/dev/null; then
          continue
        fi
        echo "[$(date)] another promotion GEO job is already active: $active_session"
        return 0
        ;;
    esac
  done < <(tmux ls 2>/dev/null | cut -d: -f1)

  local entry session manifest command log_file
  for entry in "${{jobs[@]}}"; do
    IFS='|' read -r session manifest command log_file <<< "$entry"
    if [ "$session" = "$current_session" ]; then
      continue
    fi
    if promotion_manifest_done "$manifest" >/dev/null; then
      continue
    fi
    if tmux has-session -t "$session" 2>/dev/null; then
      echo "[$(date)] another promotion GEO job is already active: $session"
      return 0
    fi
  done
  return 1
}}

run_large_raw_tar_defer_scan() {{
  local now
  if [ "${{SNOWCELL_GEO_PROMOTION_SKIP_LARGE_RAW_SCAN:-0}}" = "1" ]; then
    return 0
  fi
  if [ ! -f scripts/defer_large_geo_raw_tar_candidates.py ]; then
    return 0
  fi
  now="$(date +%s)"
  if [ "$last_large_raw_scan" -ne 0 ] && [ $((now - last_large_raw_scan)) -lt "$large_raw_scan_interval" ]; then
    return 0
  fi
  last_large_raw_scan="$now"
  echo "[$(date)] scanning GEO candidates for oversized RAW tar before launch"
  SNOWCELL_GEO_RAW_TAR_QUEUE_MAX_BYTES="${{SNOWCELL_GEO_RAW_TAR_QUEUE_MAX_BYTES:-5368709120}}" \\
    .venv/bin/python scripts/defer_large_geo_raw_tar_candidates.py || true
}}

echo "[$(date)] GEO promotion download queue started"

while true; do
  run_large_raw_tar_defer_scan
  launched=0
  all_done=1
  for entry in "${{jobs[@]}}"; do
    IFS='|' read -r session manifest command log_file <<< "$entry"
    if promotion_manifest_done "$manifest"; then
      continue
    fi
    all_done=0
    if tmux has-session -t "$session" 2>/dev/null; then
      echo "[$(date)] promotion GEO job running: $session"
      launched=1
      break
    fi
    if reviewed_queue_pending; then
      echo "[$(date)] reviewed GEO queue still has pending static jobs; waiting before starting $session"
      break
    fi
    if has_active_reviewed_transfer; then
      echo "[$(date)] reviewed GEO transfer active; waiting before starting $session"
      break
    fi
    if has_active_unfinished_promotion_transfer "$session"; then
      echo "[$(date)] promotion GEO transfer active; waiting before starting $session"
      break
    fi
    echo "[$(date)] starting promotion GEO job: $session"
    tmux new-session -d -s "$session" \\
      "cd /mnt/snowlotus_cellfm && source .venv/bin/activate 2>/dev/null || true; $command 2>&1 | tee -a $log_file; bash scripts/generate_publication_package.sh || true"
    launched=1
    break
  done
  if [ "$all_done" = "1" ]; then
    echo "[$(date)] all promotion GEO jobs complete"
  elif [ "$launched" = "0" ]; then
    echo "[$(date)] no promotion GEO job launched this cycle"
  fi
  sleep "$poll_seconds"
done
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_start_script(project_dir: Path, queue_script: Path, start_script: Path) -> Path:
    path = project_dir / start_script
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
session="${{SNOWCELL_GEO_PROMOTION_QUEUE_SESSION:-snowcell_geo_promotion_download_queue}}"
log_path="${{SNOWCELL_GEO_PROMOTION_QUEUE_LOG:-logs/geo_promotion_download_queue.log}}"
restart="${{SNOWCELL_GEO_PROMOTION_QUEUE_RESTART:-0}}"

mkdir -p logs

if tmux has-session -t "$session" 2>/dev/null; then
  if [ "$restart" = "1" ]; then
    echo "GEO promotion queue restarting supervisor: $session"
    tmux kill-session -t "$session"
  else
  echo "GEO promotion queue already running: $session"
  exit 0
  fi
fi

tmux new-session -d -s "$session" \\
  "cd /mnt/snowlotus_cellfm && bash {queue_script.as_posix()} >> '$log_path' 2>&1"
echo "GEO promotion queue started: $session"
echo "log: $log_path"
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_report(payload: dict[str, Any], output_md: Path, output_json: Path, output_tsv: Path) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    jobs = payload["jobs"]
    lines = [
        "# GEO Promotion Download Queue",
        "",
        f"Generated UTC: `{payload['summary']['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Jobs: `{payload['summary']['job_count']}`",
        f"- Queue script: `{payload['summary']['queue_script']}`",
        f"- Start script: `{payload['summary']['start_script']}`",
        "",
        "## Jobs",
        "",
        "| Accession | Dataset | Species | Tissue | Downloader | Manifest | Wrapper |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for job in jobs:
        lines.append(
            "| {accession} | {dataset_id} | {species} | {tissue} | {downloader_script} | {manifest} | {wrapper_script} |".format(
                **job
            )
        )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with output_tsv.open("w", encoding="utf-8", newline="") as handle:
        fields = list(asdict(PromotionDownloadJob("", "", "", "", "", "", "", "", "", "", "", "")).keys())
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)
    print(output_md)
    print(output_json)
    print(output_tsv)


def build_jobs(project_dir: Path, promotion_tsv: Path, output_dir: Path) -> list[PromotionDownloadJob]:
    rows = promotion_rows(project_dir / promotion_tsv if not promotion_tsv.is_absolute() else promotion_tsv)
    return [job_from_row(row, output_dir) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate download wrappers for GEO promotion candidates.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--promotion-tsv", default=Path("data/public_discovery/geo_manifest_promotion_candidates.tsv"), type=Path)
    parser.add_argument("--output-dir", default=Path("scripts/generated_geo_promotion_downloads"), type=Path)
    parser.add_argument("--queue-script", default=Path("scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh"), type=Path)
    parser.add_argument("--start-script", default=Path("scripts/generated_geo_promotion_downloads/start_geo_promotion_queue.sh"), type=Path)
    parser.add_argument("--output-md", default=Path("data/public_discovery/geo_promotion_download_queue.md"), type=Path)
    parser.add_argument("--output-json", default=Path("data/public_discovery/geo_promotion_download_queue.json"), type=Path)
    parser.add_argument("--output-tsv", default=Path("data/public_discovery/geo_promotion_download_queue.tsv"), type=Path)
    args = parser.parse_args()

    root = args.project_dir
    jobs = build_jobs(root, args.promotion_tsv, args.output_dir)
    for job in jobs:
        write_wrapper(job, root)
    write_queue_script(jobs, root, args.queue_script)
    write_start_script(root, args.queue_script, args.start_script)
    payload = {
        "summary": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "promotion_tsv": args.promotion_tsv.as_posix(),
            "job_count": len(jobs),
            "queue_script": args.queue_script.as_posix(),
            "start_script": args.start_script.as_posix(),
        },
        "jobs": [asdict(job) for job in jobs],
    }
    output_md = root / args.output_md if not args.output_md.is_absolute() else args.output_md
    output_json = root / args.output_json if not args.output_json.is_absolute() else args.output_json
    output_tsv = root / args.output_tsv if not args.output_tsv.is_absolute() else args.output_tsv
    write_report(payload, output_md, output_json, output_tsv)


if __name__ == "__main__":
    main()
