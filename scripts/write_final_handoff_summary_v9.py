from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release_metadata"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_summary() -> dict[str, Any]:
    comparison = read_json(RELEASE / "v9_benchmarks" / "v9_lora_vs_v3_shared_comparison.json")
    ontology = read_json(RELEASE / "species_ontology_label_benchmark_v9.json")
    case = read_json(RELEASE / "plant_biology_case_study_v9.json")

    candidate = comparison["candidate"]["summary"]
    baseline = comparison["baseline"]["summary"]
    ontology_action = ontology["protocols"]["leave_species_out_ontology_actionable"]

    return {
        "schema_version": "plant_cellfm_v9_final_handoff_summary_v1",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "project": "Plant-CellFM / SnowLotus-CellFM",
        "release_scope": "plant-general single-cell and single-nucleus expression foundation model with all-plant adapter framework",
        "formal_hardware_statement": "NVIDIA GeForce RTX 4090, 24 GB VRAM",
        "repository": "https://github.com/ahvsjags/SnowLotus-CellFM",
        "branch": "agent/remote-pipeline-20260728",
        "release_tag": "v0.9.0-plant-general-lora",
        "server_root": "/mnt/snowlotus_cellfm",
        "server_final_zip": "/mnt/snowlotus_cellfm/outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip",
        "server_verifier_command": "/root/miniconda3/envs/myconda/bin/python scripts/verify_v9_server_release.py --output-json release_metadata/server_release_verification_v9.json --output-md release_metadata/server_release_verification_v9.md",
        "release_gate_command": "/root/miniconda3/envs/myconda/bin/python scripts/write_release_gate_completion_audit_v9.py",
        "headline_metrics": {
            "leave_dataset_out_v9_all_cell_accuracy": candidate["leave_dataset_out"]["fine"]["accuracy_all"],
            "leave_dataset_out_v3_all_cell_accuracy": baseline["leave_dataset_out"]["fine"]["accuracy_all"],
            "leave_sample_out_v9_all_cell_accuracy": candidate["leave_sample_out"]["fine"]["accuracy_all"],
            "leave_sample_out_v3_all_cell_accuracy": baseline["leave_sample_out"]["fine"]["accuracy_all"],
            "leave_species_out_v9_all_cell_accuracy": candidate["leave_species_out"]["fine"]["accuracy_all"],
            "leave_species_out_v3_all_cell_accuracy": baseline["leave_species_out"]["fine"]["accuracy_all"],
            "leave_species_out_v9_coverage": candidate["leave_species_out"]["fine"]["coverage"],
            "leave_species_out_v9_known_label_accuracy": candidate["leave_species_out"]["fine"]["accuracy"],
            "ontology_label_actionable_coverage": ontology_action["coverage"],
            "ontology_label_actionable_all_cell_accuracy": ontology_action["accuracy_all"],
            "ontology_label_known_label_accuracy": ontology_action["accuracy"],
            "ontology_label_macro_f1": ontology_action["macro_f1"],
        },
        "biology_case": {
            "case": "Arabidopsis root adapter and marker-candidate case",
            "marker_candidate_rows": case["marker_overview"]["n_marker_rows"],
            "cell_states": case["marker_overview"]["n_labels"],
            "root_identity_states": case["marker_overview"]["root_identity_label_count"],
        },
        "read_first": [
            "SUBMISSION_INDEX_v9.md",
            "manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx",
            "release_metadata/final_handoff_summary_v9.md",
            "release_metadata/plant_cellfm_v9_model_card.md",
            "release_metadata/release_gate_completion_audit_v9.md (generated on server/outputs)",
            "release_metadata/server_release_verification_v9.md (generated on server/outputs)",
            "release_metadata/species_ontology_label_benchmark_v9.md",
            "GITHUB_SYNC_RECOVERY.md inside the final zip",
        ],
        "safe_claims": [
            "Plant-CellFM v9 is a reproducible plant-general foundation-model and adapter framework for plant single-cell expression annotation.",
            "The current release is not Snow Lotus-only; Snow Lotus is a target-species adapter entry point under the same contract.",
            "The strict leave-species result should be interpreted as open-set cross-species transfer evidence, not universal high-accuracy annotation for every plant species.",
            "The release includes completed v3, centroid and Seurat comparators; scPlantLLM/scPlantAnnotate remain disclosed at audited execution boundaries unless official runs are added later.",
            "The Arabidopsis root case is a public-data computational biology demonstration with marker candidates, not wet-lab validation.",
        ],
        "do_not_claim": [
            "Do not claim a completed Snow Lotus single-cell atlas.",
            "Do not claim universal high-accuracy zero-shot annotation for every plant species.",
            "Do not claim official scPlantLLM/scPlantAnnotate numerical superiority without executable third-party metrics.",
            "Do not cite early hardware planning notes as the formal hardware statement; use RTX 4090.",
        ],
    }


def markdown(summary: dict[str, Any]) -> str:
    metrics = summary["headline_metrics"]
    case = summary["biology_case"]
    lines = [
        "# Plant-CellFM v9 Final Handoff Summary",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Position",
        "",
        f"Project: `{summary['project']}`",
        "",
        f"Scope: {summary['release_scope']}.",
        "",
        f"Formal hardware statement: `{summary['formal_hardware_statement']}`.",
        "",
        f"Repository: {summary['repository']}",
        "",
        f"Branch: `{summary['branch']}`",
        "",
        f"Release tag: `{summary['release_tag']}`",
        "",
        "## Server",
        "",
        f"Server root: `{summary['server_root']}`",
        "",
        f"Final editor zip: `{summary['server_final_zip']}`",
        "",
        "Verifier command:",
        "",
        "```bash",
        summary["server_verifier_command"],
        "```",
        "",
        "Release gate command:",
        "",
        "```bash",
        summary["release_gate_command"],
        "```",
        "",
        "## Read First",
        "",
    ]
    lines.extend(f"- `{item}`" if not item.startswith("GITHUB") else f"- {item}" for item in summary["read_first"])
    lines.extend(
        [
            "",
            "## Headline Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Leave-dataset-out v9 all-cell accuracy | {metrics['leave_dataset_out_v9_all_cell_accuracy']:.4f} |",
            f"| Leave-dataset-out v3 all-cell accuracy | {metrics['leave_dataset_out_v3_all_cell_accuracy']:.4f} |",
            f"| Leave-sample-out v9 all-cell accuracy | {metrics['leave_sample_out_v9_all_cell_accuracy']:.4f} |",
            f"| Leave-sample-out v3 all-cell accuracy | {metrics['leave_sample_out_v3_all_cell_accuracy']:.4f} |",
            f"| Normalized leave-species-out v9 all-cell accuracy | {metrics['leave_species_out_v9_all_cell_accuracy']:.4f} |",
            f"| Normalized leave-species-out v3 all-cell accuracy | {metrics['leave_species_out_v3_all_cell_accuracy']:.4f} |",
            f"| Normalized leave-species-out v9 coverage | {metrics['leave_species_out_v9_coverage']:.4f} |",
            f"| Normalized leave-species-out v9 known-label accuracy | {metrics['leave_species_out_v9_known_label_accuracy']:.4f} |",
            f"| Ontology-label actionable coverage | {pct(metrics['ontology_label_actionable_coverage'])} |",
            f"| Ontology-label actionable all-cell accuracy | {pct(metrics['ontology_label_actionable_all_cell_accuracy'])} |",
            f"| Ontology-label known-label accuracy | {pct(metrics['ontology_label_known_label_accuracy'])} |",
            f"| Ontology-label macro-F1 | {metrics['ontology_label_macro_f1']:.4f} |",
            "",
            "## Biology Case",
            "",
            f"{case['case']} contains `{case['marker_candidate_rows']}` marker-candidate rows, `{case['cell_states']}` cell states and `{case['root_identity_states']}` root-identity states.",
            "",
            "## Safe Claims",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["safe_claims"])
    lines.extend(["", "## Do Not Claim", ""])
    lines.extend(f"- {item}" for item in summary["do_not_claim"])
    lines.extend(
        [
            "",
            "## Handoff Interpretation",
            "",
            "Use this file as the short handoff layer. The authoritative proof remains the server verifier, release gate audit, model card, benchmark JSON files, final Word manuscript and final editor zip status JSON.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    summary = build_summary()
    json_path = RELEASE / "final_handoff_summary_v9.json"
    md_path = RELEASE / "final_handoff_summary_v9.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(summary) + "\n", encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
