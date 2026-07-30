from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "editor_submission_v9"
DEFAULT_PACKAGE_NAME = "Plant_CellFM_v9_editor_submission_final"
RELEASE_URL = "https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora"
REPO_URL = "https://github.com/ahvsjags/SnowLotus-CellFM"
BRANCH_URL = "https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728"
CHECKPOINT_ASSET = (
    "https://github.com/ahvsjags/SnowLotus-CellFM/releases/download/"
    "v0.9.0-plant-general-lora/SnowLotus-CellFM-v9-lora-4090-best.pt"
)
CHECKPOINT_SHA256 = "9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93"


ASSET_PATHS = [
    "README.md",
    "SUBMISSION_INDEX_v9.md",
    "docs/publication_readiness_v9.md",
    "docs/development_plan.md",
    "docs/top_journal_strategy.md",
    "manuscript/Plant_CellFM_v9_final_submission_zh_v1.md",
    "manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx",
    "release_metadata/plant_cellfm_v9_model_card.md",
    "release_metadata/v9_data_card.md",
    "release_metadata/v9_release_notes.md",
    "release_metadata/v9_editor_issue_closure.md",
    "release_metadata/v9_editor_issue_closure.json",
    "release_metadata/publication_peer_review_preflight_v9.md",
    "release_metadata/publication_peer_review_preflight_v9.json",
    "release_metadata/top_journal_readiness_matrix.md",
    "release_metadata/top_journal_readiness_matrix.json",
    "release_metadata/final_editor_submission_package_recipe_v9.md",
    "release_metadata/final_editor_submission_package_recipe_v9.json",
    "release_metadata/v9_submission_stability_audit.md",
    "release_metadata/v9_submission_stability_audit.json",
    "release_metadata/server_sustainability_status_v9.md",
    "release_metadata/server_sustainability_status_v9.json",
    "release_metadata/api_runtime_smoke_v9.md",
    "release_metadata/api_runtime_smoke_v9.json",
    "release_metadata/watchdog_recovery_status_v9.md",
    "release_metadata/watchdog_recovery_status_v9.json",
    "release_metadata/external_benchmark_panel_v9.md",
    "release_metadata/external_benchmark_panel_v9.json",
    "release_metadata/external_benchmarks/seurat_v9_subset.json",
    "release_metadata/external_benchmarks/seurat_v9_subset_split_summary.json",
    "release_metadata/strict_benchmarks/public_sprint_group_random.centroid_baseline.json",
    "release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json",
    "release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json",
    "release_metadata/v9_benchmarks/v9_lora_cross_species_benchmark.json",
    "release_metadata/v9_benchmarks/v3_on_v9_shared_subset_cross_species_benchmark.json",
    "release_metadata/species_holdout_failure_audit_v9.md",
    "release_metadata/species_holdout_failure_audit_v9.json",
    "release_metadata/species_holdout_failure_audit_v9.tsv",
    "release_metadata/species_ontology_coverage_audit_v9.md",
    "release_metadata/species_ontology_coverage_audit_v9.json",
    "release_metadata/species_ontology_coverage_audit_v9.tsv",
    "release_metadata/species_ontology_label_benchmark_v9.md",
    "release_metadata/species_ontology_label_benchmark_v9.json",
    "release_metadata/species_ontology_label_benchmark_v9.tsv",
    "release_metadata/plant_cell_state_ontology_mapping_v9.tsv",
    "release_metadata/plant_cell_state_ontology_mapping_v9.json",
    "release_metadata/species_ontology_obs_labels_v9.tsv",
    "release_metadata/species_ontology_obs_labels_with_ids_v9.tsv",
    "release_metadata/plant_biology_case_study_v9.md",
    "release_metadata/plant_biology_case_study_v9.json",
    "release_metadata/plant_biology_case_study_top_markers_v9.tsv",
    "release_metadata/arabidopsis_root_literature_anchor_v9.md",
    "release_metadata/arabidopsis_root_literature_anchor_v9.json",
    "release_metadata/arabidopsis_root_case_figure_v9.md",
    "release_metadata/arabidopsis_root_case_figure_v9.json",
    "figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.svg",
    "figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.pdf",
    "figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.png",
    "figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.tiff",
    "figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case_figure_metadata.json",
    "figures/plant_cellfm_v9_arabidopsis_root_case/source_data/arabidopsis_root_marker_candidates_figure_source_v9.tsv",
    "figures/plant_cellfm_v9_arabidopsis_root_case/source_data/arabidopsis_root_top_marker_matrix_source_v9.tsv",
    "figures/plant_cellfm_v9_arabidopsis_root_case/source_data/arabidopsis_root_identity_summary_source_v9.tsv",
    "release_metadata/plant_species_adapters.json",
    "release_metadata/scplantllm_input_readiness.md",
    "release_metadata/scplantllm_input_readiness.json",
    "release_metadata/scplantllm_preprocess_probe_readiness.md",
    "release_metadata/scplantllm_preprocess_probe_readiness.json",
    "release_metadata/scplantannotate_access_audit.md",
    "release_metadata/scplantannotate_access_audit.json",
    "release_metadata/third_party_comparator_sources_v9.md",
    "release_metadata/saussurea_h5ad_contract.md",
    "release_metadata/saussurea_public_data_discovery.md",
    "scripts/write_v9_integrated_stable_manuscript.py",
    "scripts/render_arabidopsis_root_case_figure_v9.py",
    "scripts/write_species_holdout_failure_audit_v9.py",
    "scripts/write_species_ontology_coverage_audit_v9.py",
    "scripts/run_species_ontology_label_benchmark_v9.py",
    "scripts/verify_v9_server_release.py",
    "scripts/write_release_gate_completion_audit_v9.py",
    "scripts/package_v9_editor_submission.py",
]


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
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def collect_assets() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in ASSET_PATHS:
        source = ROOT / relative
        if not source.exists():
            missing.append(relative)
            continue
        entries.append(
            {
                "source": source,
                "relative_path": relative,
                "size_bytes": source.stat().st_size,
                "sha256": sha256_file(source),
            }
        )
    if missing:
        raise FileNotFoundError("Missing package assets: " + ", ".join(missing))
    return entries


def package_readme(git_head: str, generated_at: str) -> str:
    return "\n".join(
        [
            "# Plant-CellFM v9 Editor Submission Package",
            "",
            f"Generated UTC: `{generated_at}`",
            "",
            f"Repository: {REPO_URL}",
            "",
            f"Submission branch: {BRANCH_URL}",
            "",
            f"Current source commit when packaged: `{git_head}`",
            "",
            f"Frozen release: {RELEASE_URL}",
            "",
            f"Checkpoint asset: {CHECKPOINT_ASSET}",
            "",
            f"Checkpoint SHA256: `{CHECKPOINT_SHA256}`",
            "",
            "## Read First",
            "",
            "1. `SUBMISSION_INDEX_v9.md`",
            "2. `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx`",
            "3. `release_metadata/plant_cellfm_v9_model_card.md`",
            "4. `release_metadata/v9_editor_issue_closure.md`",
            "5. `release_metadata/publication_peer_review_preflight_v9.md`",
            "6. `release_metadata/top_journal_readiness_matrix.md`",
            "7. `release_metadata/arabidopsis_root_case_figure_v9.md`",
            "8. `release_metadata/species_holdout_failure_audit_v9.md`",
            "9. `release_metadata/species_ontology_coverage_audit_v9.md`",
            "10. `release_metadata/species_ontology_label_benchmark_v9.md`",
            "11. `release_metadata/server_sustainability_status_v9.md`",
            "12. `scripts/verify_v9_server_release.py`",
            "13. `scripts/write_release_gate_completion_audit_v9.py`",
            "14. `GITHUB_SYNC_RECOVERY.md`",
            "",
            "## Claim Boundary",
            "",
            "This package supports a Plant-CellFM v9 computational method/resource submission: general plant single-cell expression modelling, all-plant adapter resolution, completed v3/centroid/Seurat comparisons, Arabidopsis root computational biology case, live CUDA service evidence and watchdog recovery evidence.",
            "",
            "It does not claim universal high-accuracy zero-shot annotation for every plant species, a completed Snow Lotus single-cell atlas, or final scPlantLLM/scPlantAnnotate numeric superiority without executable third-party metric evidence.",
            "",
            "Cross-species generalization is reported with the normalized leave-species-out metrics, `release_metadata/species_holdout_failure_audit_v9.md`, `release_metadata/species_ontology_coverage_audit_v9.md` and `release_metadata/species_ontology_label_benchmark_v9.md`, which separate open-set label absence, known-label transfer errors, ontology-actionable labels, ontology-label benchmark accuracy and per-species revision targets.",
            "",
            "## GitHub Sync State",
            "",
            "If the public GitHub branch is behind this package, use `GITHUB_SYNC_RECOVERY.md` inside this zip. The recovery note records the local source commit, observed origin head and the server-side bundle/patch paths.",
            "",
            "## Server Verification",
            "",
            "The zip includes `scripts/verify_v9_server_release.py`. On the Matpool server, run it from `/mnt/snowlotus_cellfm` to regenerate the latest machine-readable and reviewer-readable release verification reports:",
            "",
            "```bash",
            "/root/miniconda3/envs/myconda/bin/python scripts/verify_v9_server_release.py --output-json release_metadata/server_release_verification_v9.json --output-md release_metadata/server_release_verification_v9.md",
            "```",
            "",
            "The verifier checks the final zip SHA256, critical zip entries, recovery note, root evidence files, addendum recovery note, live `/health`, CUDA device, RTX 4090 visibility and watchdog tmux session.",
            "",
        ]
    )


def model_asset_pointer() -> str:
    return "\n".join(
        [
            "Plant-CellFM v9 checkpoint is intentionally not duplicated in this editor zip.",
            "",
            f"Release asset: {CHECKPOINT_ASSET}",
            f"SHA256: {CHECKPOINT_SHA256}",
            "",
            "Server path used by the live CUDA service:",
            "/root/snowlotus_cellfm_v9_lora_shared_4090/best.pt",
            "",
        ]
    )


def github_sync_recovery(git_head: str, origin_head: str, generated_at: str) -> str:
    short_head = git_head[:7] if git_head != "unknown" else "unknown"
    short_origin = origin_head[:7] if origin_head != "unknown" else "unknown"
    bundle_name = f"Plant_CellFM_{short_head}_from_{short_origin}.bundle"
    patch_name = f"Plant_CellFM_{short_head}_from_{short_origin}.patch"
    changed_files_name = f"Plant_CellFM_changed_files_{short_head}.tar"
    return "\n".join(
        [
            "# Plant-CellFM v9 GitHub Sync Recovery",
            "",
            f"Generated UTC: `{generated_at}`",
            "",
            f"Packaged source commit: `{git_head}`",
            "",
            f"Observed origin branch head: `{origin_head}`",
            "",
            "The workstation GitHub CLI authentication was invalid during packaging, so the public branch may lag behind the package source commit. This recovery note is included so the exact packaged state can still be reconstructed from the server artifacts.",
            "",
            "## Server Artifacts",
            "",
            "- Final editor zip: `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip`",
            "- Final editor zip SHA256: recorded in `Plant_CellFM_v9_editor_submission_final.zip.sha256` and `.status.json`",
            f"- Changed-files tar, if generated for this commit: `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/{changed_files_name}`",
            f"- Git bundle, if generated for this commit range: `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/{bundle_name}`",
            f"- Binary patch, if generated for this commit range: `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/{patch_name}`",
            "",
            "## Recovery Commands",
            "",
            "From a clone that contains the observed origin branch head:",
            "",
            "```bash",
            f"git bundle verify {bundle_name}",
            f"git fetch {bundle_name} HEAD:{short_head}_recovery",
            f"git checkout {short_head}_recovery",
            "```",
            "",
            "If the bundle is unavailable but the binary patch is present, start from the observed origin head, apply the patch and verify the package status JSON before pushing.",
            "",
            "## Claim Boundary",
            "",
            "The GitHub sync lag does not change the model evidence in the zip: the package contains the final manuscript, model card, benchmark files, ontology-label species benchmark, server health evidence and recovery metadata for the packaged source commit.",
            "",
        ]
    )


def write_manifest_files(staging: Path, entries: list[dict[str, Any]], git_head: str, generated_at: str) -> None:
    manifest = {
        "schema_version": "plant_cellfm_v9_editor_submission_package_manifest_v1",
        "generated_at_utc": generated_at,
        "repo_url": REPO_URL,
        "branch_url": BRANCH_URL,
        "source_commit": git_head,
        "release_url": RELEASE_URL,
        "checkpoint_asset": CHECKPOINT_ASSET,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "asset_count": len(entries),
        "assets": [
            {
                "path": entry["relative_path"],
                "size_bytes": entry["size_bytes"],
                "sha256": entry["sha256"],
            }
            for entry in entries
        ],
    }
    write_text(staging / "PACKAGE_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    with (staging / "PACKAGE_MANIFEST.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=["path", "size_bytes", "sha256"])
        writer.writeheader()
        for entry in manifest["assets"]:
            writer.writerow(entry)
    write_text(staging / "PACKAGE_README.md", package_readme(git_head, generated_at))
    write_text(staging / "MODEL_ASSET_POINTER.txt", model_asset_pointer())


def build_package(output_dir: Path, package_name: str) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    git_head = run_git(["rev-parse", "HEAD"])
    origin_head = run_git(["rev-parse", "origin/agent/remote-pipeline-20260728"])
    entries = collect_assets()
    staging = output_dir / "staging" / package_name
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        destination = staging / entry["relative_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry["source"], destination)
    write_manifest_files(staging, entries, git_head, generated_at)
    write_text(staging / "GITHUB_SYNC_RECOVERY.md", github_sync_recovery(git_head, origin_head, generated_at))

    zip_path = output_dir / f"{package_name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(staging).as_posix())
    zip_sha = sha256_file(zip_path)
    sha_path = output_dir / f"{package_name}.zip.sha256"
    write_text(sha_path, f"{zip_sha}  {zip_path.name}\n")

    status = {
        "schema_version": "plant_cellfm_v9_editor_submission_package_status_v1",
        "generated_at_utc": generated_at,
        "source_commit": git_head,
        "origin_branch_head": origin_head,
        "repo_url": REPO_URL,
        "branch_url": BRANCH_URL,
        "release_url": RELEASE_URL,
        "checkpoint_asset": CHECKPOINT_ASSET,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "package_name": zip_path.name,
        "package_path": str(zip_path),
        "package_sha256": zip_sha,
        "package_sha256_path": str(sha_path),
        "asset_count": len(entries),
        "read_first": [
            "SUBMISSION_INDEX_v9.md",
            "manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx",
            "release_metadata/plant_cellfm_v9_model_card.md",
            "release_metadata/v9_editor_issue_closure.md",
            "release_metadata/publication_peer_review_preflight_v9.md",
            "release_metadata/top_journal_readiness_matrix.md",
            "release_metadata/arabidopsis_root_case_figure_v9.md",
            "release_metadata/species_holdout_failure_audit_v9.md",
            "release_metadata/species_ontology_coverage_audit_v9.md",
            "release_metadata/species_ontology_label_benchmark_v9.md",
            "release_metadata/server_sustainability_status_v9.md",
            "scripts/verify_v9_server_release.py",
            "scripts/write_release_gate_completion_audit_v9.py",
            "GITHUB_SYNC_RECOVERY.md",
        ],
    }
    write_text(output_dir / f"{package_name}.status.json", json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Plant-CellFM v9 Final Editor Submission Package",
        "",
        f"Generated UTC: `{generated_at}`",
        "",
        f"- Package: `{zip_path}`",
        f"- SHA256: `{zip_sha}`",
        f"- SHA256 sidecar: `{sha_path}`",
        f"- Source commit at packaging time: `{git_head}`",
        f"- Origin branch head at packaging time: `{origin_head}`",
        f"- Asset count: `{len(entries)}`",
        "",
        "## Read First",
        "",
    ]
    lines.extend(f"- `{item}`" for item in status["read_first"])
    lines.extend(
        [
            "",
            "## Checkpoint",
            "",
            f"- Release asset: {CHECKPOINT_ASSET}",
            f"- SHA256: `{CHECKPOINT_SHA256}`",
            "",
        ]
    )
    write_text(output_dir / f"{package_name}.status.md", "\n".join(lines))
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Package the Plant-CellFM v9 editor submission assets")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--package-name", default=DEFAULT_PACKAGE_NAME)
    args = parser.parse_args()
    status = build_package(args.output_dir, args.package_name)
    print(status["package_path"])
    print(status["package_sha256"])


if __name__ == "__main__":
    main()
