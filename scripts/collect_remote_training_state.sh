#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
cd "${PROJECT_DIR}"

mkdir -p outputs/recovery_audit logs
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
json_out="outputs/recovery_audit/remote_training_state_${stamp}.json"
md_out="outputs/recovery_audit/remote_training_state_${stamp}.md"
latest_json="outputs/recovery_audit/remote_training_state_latest.json"
latest_md="outputs/recovery_audit/remote_training_state_latest.md"

python_bin="python3"
if [ -x ".venv/bin/python" ]; then
  python_bin=".venv/bin/python"
fi

"${python_bin}" - "${json_out}" "${md_out}" <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.cwd()
JSON_OUT = Path(sys.argv[1])
MD_OUT = Path(sys.argv[2])


def run(command: str, timeout: int = 30) -> dict[str, object]:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": repr(exc)}


def read_json(path: str) -> object | None:
    target = ROOT / path
    if not target.exists():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": repr(exc), "path": path}


def tail_text(path: str, lines: int = 80) -> dict[str, object]:
    target = ROOT / path
    if not target.exists():
        return {"exists": False, "path": path, "tail": ""}
    text = target.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"exists": True, "path": path, "line_count": len(text), "tail": "\n".join(text[-lines:])}


def file_info(path: str) -> dict[str, object]:
    target = ROOT / path
    if not target.exists():
        return {"exists": False, "path": path}
    stat = target.stat()
    return {
        "exists": True,
        "path": path,
        "bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def h5ad_shape(path: str) -> dict[str, object]:
    target = ROOT / path
    if not target.exists():
        return {"exists": False, "path": path}
    try:
        import anndata as ad

        adata = ad.read_h5ad(target, backed="r")
        try:
            return {
                "exists": True,
                "path": path,
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
                "bytes": target.stat().st_size,
            }
        finally:
            adata.file.close()
    except Exception as exc:
        info = file_info(path)
        info["error"] = repr(exc)
        return info


progress_paths = {
    "v0_3_progress_latest": "outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/progress_latest.json",
    "v0_3_history": "outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/history.json",
    "v0_3_current_best": "outputs/post_training_release/editor_v0_3_current_best.json",
    "v0_4_progress_latest": "outputs/foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm/progress_latest.json",
    "plus_summary": "outputs/publication_package/public_mlm_plus_latest_manifest_summary.json",
    "full_on_disk_summary": "outputs/publication_package/public_mlm_full_on_disk_manifest_summary.json",
}

payload = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "project_dir": str(ROOT),
    "hostname": run("hostname"),
    "date": run("date -Is"),
    "git_head": run("git rev-parse HEAD 2>/dev/null || true"),
    "disk": run("df -h . /tmp 2>/dev/null || df -h"),
    "memory": run("free -h 2>/dev/null || true"),
    "gpu": run("nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits 2>/dev/null || true"),
    "tmux_sessions": run("tmux ls 2>/dev/null || true"),
    "progress": {name: read_json(path) for name, path in progress_paths.items()},
    "files": {
        "v0_3_best": file_info("outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt"),
        "v0_3_latest": file_info("outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/latest.pt"),
        "v0_4_latest": file_info("outputs/foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm/latest.pt"),
        "plus_corpus": h5ad_shape("data/plant_foundation_corpus_public_mlm_plus_latest.h5ad"),
        "full_on_disk_corpus": h5ad_shape("data/plant_foundation_corpus_public_mlm_full_on_disk.h5ad"),
        "full_on_disk_manifest": file_info("data/corpus_manifest_public_mlm_full_on_disk.tsv"),
    },
    "logs": {
        "full_on_disk": tail_text("logs/public_mlm_full_on_disk_corpus.log"),
        "v0_4_watchdog": tail_text("logs/mlm_public_expansion_v0_4_after_v0_3_watchdog.log"),
        "editor_release": tail_text("logs/editor_v03_best_release_watchdog.log"),
    },
    "environment": {
        "python": run("(.venv/bin/python --version 2>&1 || python3 --version 2>&1 || true)"),
        "anndata": run(".venv/bin/python - <<'PY2'\nimport anndata as ad\nprint(ad.__version__)\nPY2", timeout=20),
    },
}

JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
JSON_OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

def first_line(value: object) -> str:
    if isinstance(value, dict):
        text = str(value.get("stdout", "") or value.get("stderr", ""))
        return text.splitlines()[0] if text else ""
    return str(value)


v03 = payload["progress"].get("v0_3_progress_latest") or {}
v04 = payload["progress"].get("v0_4_progress_latest") or {}
best = payload["progress"].get("v0_3_current_best") or {}
full_summary = payload["progress"].get("full_on_disk_summary") or {}
plus_summary = payload["progress"].get("plus_summary") or {}

md = [
    "# Remote training state",
    "",
    f"- Timestamp UTC: `{payload['timestamp_utc']}`",
    f"- Hostname: `{first_line(payload['hostname'])}`",
    f"- Git head: `{first_line(payload['git_head'])}`",
    f"- GPU: `{first_line(payload['gpu'])}`",
    f"- v0.3 status: `{v03.get('status')}` epoch=`{v03.get('epoch')}` step=`{v03.get('step')}` / `{v03.get('train_batches_per_epoch')}`",
    f"- v0.3 frozen best epoch: `{best.get('best_epoch')}` eval_loss=`{best.get('best_eval_loss')}`",
    f"- v0.4 status: `{v04.get('status')}` epoch=`{v04.get('epoch')}` step=`{v04.get('step')}`",
    f"- plus manifest rows: `{plus_summary.get('manifest_rows')}` corpus_bytes=`{plus_summary.get('corpus_bytes')}`",
    f"- full on-disk manifest rows: `{full_summary.get('manifest_rows')}` corpus_bytes=`{full_summary.get('corpus_bytes')}`",
    f"- full on-disk corpus exists: `{payload['files']['full_on_disk_corpus'].get('exists')}`",
    "",
    "## Tmux Sessions",
    "",
    "```text",
    str(payload["tmux_sessions"].get("stdout", "")),
    "```",
    "",
    "## Disk",
    "",
    "```text",
    str(payload["disk"].get("stdout", "")),
    "```",
]
MD_OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
print(JSON_OUT)
print(MD_OUT)
PY

cp -f "${json_out}" "${latest_json}"
cp -f "${md_out}" "${latest_md}"
echo "${latest_json}"
echo "${latest_md}"
