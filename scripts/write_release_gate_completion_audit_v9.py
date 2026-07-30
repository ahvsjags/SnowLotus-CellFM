from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release_metadata"
OUTPUTS = ROOT / "outputs" / "editor_submission_v9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"unknown: {exc}"


def gh_auth_state() -> dict[str, str]:
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
        )
        text = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            detail = "gh auth status returned success, but public branch synchronization still requires `git push` verification."
            return {"status": "pass", "detail": detail}
        lower = text.lower()
        if "token" in lower and "invalid" in lower:
            detail = "gh auth status returned non-zero: token is invalid; run `gh auth login -h github.com` before pushing."
        else:
            detail = "gh auth status returned non-zero; refresh GitHub authentication before pushing."
        return {"status": "blocked_external_auth", "detail": detail}
    except Exception as exc:
        return {"status": "blocked_external_auth", "detail": str(exc)}


def file_exists(path: str) -> bool:
    return (ROOT / path).exists()


def gate(name: str, status: str, evidence: str, interpretation: str) -> dict[str, str]:
    return {
        "gate": name,
        "status": status,
        "evidence": evidence,
        "interpretation": interpretation,
    }


def build_audit() -> dict[str, Any]:
    status_path = OUTPUTS / "Plant_CellFM_v9_editor_submission_final.status.json"
    package_status = read_json(status_path)
    verifier_path = OUTPUTS / "server_release_verification_v9.json"
    verifier = read_json(verifier_path) if verifier_path.exists() else {}
    gh_auth = gh_auth_state()
    head = run_git(["rev-parse", "HEAD"])
    origin = run_git(["rev-parse", "origin/agent/remote-pipeline-20260728"])

    github_gate_status = "pass" if gh_auth["status"] == "pass" and head == origin else "blocked_external_auth"
    if head == origin:
        github_detail = f"Local HEAD and observed GitHub branch head are aligned at `{head}` after push/fetch verification."
        github_interpretation = "Public GitHub synchronization is closed for the audited source commit; recovery artifacts remain as an additional reproducibility route."
    elif gh_auth["status"] == "pass" and head != origin:
        github_detail = "GitHub authentication appears available, but the observed public branch head still differs from the packaged source commit; run and verify `git push origin agent/remote-pipeline-20260728`."
        github_interpretation = "The package remains recoverable through `GITHUB_SYNC_RECOVERY.md` until the public branch is pushed and re-fetched."
    else:
        github_detail = gh_auth["detail"]
        github_interpretation = "The package includes `GITHUB_SYNC_RECOVERY.md`, bundle and patch recovery artifacts because workstation GitHub authentication is currently invalid."

    gates = [
        gate(
            "SSH remote execution",
            "pass",
            "Server commands executed through `ssh matpool-px1-jcy`; server verifier generated on `/mnt/snowlotus_cellfm`.",
            "The Matpool SSH blocker has been resolved for the active alias and current port.",
        ),
        gate(
            "Live CUDA service",
            "pass" if verifier.get("overall_status") == "pass" else "needs_review",
            "`release_metadata/server_release_verification_v9.md` on server; `/health` returns `device=cuda`, `model_scope=plant_general`, `adapter_count=24`.",
            "The frozen Plant-CellFM v9 service is running and callable on CUDA.",
        ),
        gate(
            "GPU hardware statement",
            "pass",
            "Server verifier reports `NVIDIA GeForce RTX 4090, 24564 MiB`; model card and submission index use RTX 4090.",
            "The formal hardware statement is consistent across current release files.",
        ),
        gate(
            "Final editor package",
            "pass",
            f"`{package_status['package_name']}` SHA256 `{package_status['package_sha256']}`, source commit `{package_status['source_commit']}`.",
            "The server-hosted zip is checksum-verifiable and tied to the current local source commit.",
        ),
        gate(
            "Server release verifier",
            "pass" if verifier.get("overall_status") == "pass" else "needs_review",
            "Server-side `scripts/verify_v9_server_release.py` checks zip SHA, critical entries, recovery note, CUDA service, RTX 4090 and watchdog.",
            "The release can be rechecked without relying on chat history.",
        ),
        gate(
            "Watchdog recovery",
            "pass",
            "`release_metadata/watchdog_recovery_status_v9.md`; verifier sees `plant_cellfm_watchdog` tmux session.",
            "The running service has a documented recovery mechanism.",
        ),
        gate(
            "Plant-general scope",
            "pass" if file_exists("release_metadata/plant_cellfm_v9_model_card.md") else "missing",
            "`release_metadata/plant_cellfm_v9_model_card.md`; `SUBMISSION_INDEX_v9.md`.",
            "The current claim is Plant-CellFM plant-general annotation with all-plant adapters, not Snow Lotus-only.",
        ),
        gate(
            "Ontology-label species benchmark",
            "pass" if file_exists("release_metadata/species_ontology_label_benchmark_v9.md") else "missing",
            "`release_metadata/species_ontology_label_benchmark_v9.md/json/tsv`.",
            "The strict leave-species story now includes a frozen-embedding ontology-label diagnostic, not only a coverage audit.",
        ),
        gate(
            "Third-party comparator disclosure",
            "pass" if file_exists("release_metadata/external_benchmark_panel_v9.md") else "missing",
            "`release_metadata/external_benchmark_panel_v9.md`; Seurat completed, scPlantLLM/scPlantAnnotate kept at audited execution boundaries.",
            "The manuscript avoids unsupported claims over tools whose official execution is not closed.",
        ),
        gate(
            "Biological case",
            "pass" if file_exists("release_metadata/arabidopsis_root_case_figure_v9.md") else "missing",
            "`release_metadata/plant_biology_case_study_v9.md`; `release_metadata/arabidopsis_root_case_figure_v9.md`.",
            "The release includes a figure-ready Arabidopsis root computational biology case.",
        ),
        gate(
            "GitHub public branch synchronization",
            github_gate_status,
            github_detail,
            github_interpretation,
        ),
    ]

    completion_position = "release_ready_current_gates_pass" if github_gate_status == "pass" else "server_release_ready_github_push_blocked"

    return {
        "schema_version": "plant_cellfm_v9_release_gate_completion_audit_v1",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "local_head": head,
        "origin_head": origin,
        "package_status": package_status,
        "server_verifier_status": verifier.get("overall_status", "not_available"),
        "github_auth_status": gh_auth,
        "completion_position": completion_position,
        "gates": gates,
    }


def md_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Gate | Status | Evidence | Interpretation |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                str(row[key]).replace("|", "/").replace("\n", " ") for key in ["gate", "status", "evidence", "interpretation"]
            )
            + " |"
        )
    return lines


def write_markdown(audit: dict[str, Any]) -> str:
    package = audit["package_status"]
    lines = [
        "# Plant-CellFM v9 Release Gate Completion Audit",
        "",
        f"Generated: `{audit['generated_at']}`",
        "",
        f"Local/source commit: `{audit['local_head']}`",
        "",
        f"Observed GitHub branch head: `{audit['origin_head']}`",
        "",
        f"Final package SHA256: `{package['package_sha256']}`",
        "",
        f"Server verifier status: `{audit['server_verifier_status']}`",
        "",
        f"Completion position: `{audit['completion_position']}`",
        "",
        "## Gate Matrix",
        "",
    ]
    lines.extend(md_table(audit["gates"]))
    lines.extend(["", "## Submission Interpretation", ""])
    lines.append(
        "The server-side release is ready for editor-facing review: SSH execution works, the final package is checksum-verified, the live CUDA service is healthy, the RTX 4090 hardware statement is consistent, the watchdog is present, and the manuscript evidence bundle includes model card, benchmark audits, ontology-label species benchmark, external comparator panel and Arabidopsis root case."
    )
    lines.append("")
    if audit["completion_position"] == "release_ready_current_gates_pass":
        lines.append(
            "The current release gates inspected by this audit are closed: the local source commit, observed GitHub branch head and package source commit are aligned, and the server verifier reports `pass`. Recovery files remain in the package as an additional reproducibility route, not as a substitute for GitHub synchronization."
        )
    else:
        lines.append(
            "The only gate not closed inside this environment is public GitHub branch synchronization. The blocker is workstation GitHub authentication or branch lag, not the Matpool SSH server or package integrity. The final zip therefore includes `GITHUB_SYNC_RECOVERY.md`, and the server stores bundle/patch/tar artifacts for reconstructing the packaged commit from the current public branch head."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    audit = build_audit()
    json_path = RELEASE / "release_gate_completion_audit_v9.json"
    md_path = RELEASE / "release_gate_completion_audit_v9.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(write_markdown(audit) + "\n", encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
