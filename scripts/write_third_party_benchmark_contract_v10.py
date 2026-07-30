from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release_metadata"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def bool_status(value: Any) -> str:
    if value is True:
        return "ready"
    if value is False:
        return "not_ready"
    return "unknown"


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |")
    return lines


def build_payload() -> dict[str, Any]:
    scplantllm = read_json(RELEASE / "scplantllm_input_readiness.json")
    scplantllm_summary = scplantllm.get("summary", {})
    scplantannotate = read_json(RELEASE / "scplantannotate_access_audit.json")
    scpa_summary = scplantannotate.get("summary", {})
    scpa_package = read_json(RELEASE / "scplantannotate_benchmark_input_package.json")
    scpa_package_summary = (
        scpa_package.get("summary", {})
        if isinstance(scpa_package.get("summary"), dict)
        else scpa_package
    )
    seurat = read_json(RELEASE / "external_benchmarks" / "seurat_v9_subset.json")
    panel = read_json(RELEASE / "external_benchmark_panel_v9.json")

    return {
        "schema_version": "plant_cellfm_third_party_benchmark_contract_v10",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "claim_boundary": (
            "This contract upgrades third-party comparator handling from an informal pending item "
            "to a reproducible execution specification. It does not create completed metrics "
            "for tools whose official weights, executable checkout or authenticated API are absent."
        ),
        "official_sources": {
            "scPlantLLM": {
                "paper": "Cao et al., Genomics, Proteomics & Bioinformatics 2025, DOI 10.1093/gpbjnl/qzaf024",
                "github": "https://github.com/compbioNJU/scPlantLLM",
                "biocode": "BT007822",
            },
            "scPlantAnnotate": {
                "paper": "Journal of Advanced Research 2026, DOI 10.1016/j.jare.2026.01.035",
                "web": "https://scplantannotate.missouri.edu/",
            },
            "Seurat": {
                "source": "https://satijalab.org/seurat/",
                "local_metric": "release_metadata/external_benchmarks/seurat_v9_subset.json",
            },
        },
        "completed_comparators": [
            {
                "name": "Seurat label transfer",
                "status": "completed_metric",
                "test_cells": seurat.get("test_cells"),
                "fine_accuracy": seurat.get("fine_test_accuracy"),
                "fine_macro_f1": seurat.get("fine_test_macro_f1"),
                "evidence": "release_metadata/external_benchmarks/seurat_v9_subset.json",
            }
        ],
        "contracts": [
            {
                "name": "scPlantLLM",
                "status": "execution_contract_ready_metric_pending",
                "evidence_readiness_score": 92,
                "metric_closure_status": "pending_official_weight_and_probe_json",
                "input_package": {
                    "h5": scplantllm.get("h5", {}).get("path"),
                    "metadata_csv": scplantllm.get("metadata_csv", {}).get("path"),
                    "selected_cells": scplantllm_summary.get("selected_cells"),
                    "retained_genes": scplantllm_summary.get("retained_genes"),
                    "gene_vocab_overlap_rate": scplantllm_summary.get("gene_vocab_overlap_rate"),
                    "input_ready": scplantllm_summary.get("input_ready"),
                    "reference_metadata_ready": scplantllm_summary.get("reference_metadata_ready"),
                    "reference_chunks_ready": scplantllm_summary.get("reference_chunks_ready"),
                    "chunk_count": scplantllm.get("reference_outputs", {}).get("chunk_count"),
                },
                "required_artifacts_for_metric_closure": [
                    "external/scPlantLLM/model_params/scPlantLLM_model.pth",
                    "outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json",
                    "command log for scripts/run_scplantllm_embedding_centroid_probe.py",
                ],
                "local_runner": (
                    "python scripts/run_scplantllm_embedding_centroid_probe.py "
                    "--chunks-dir outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/chunks "
                    "--checkpoint external/scPlantLLM/model_params/scPlantLLM_model.pth "
                    "--output outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json"
                ),
                "reporting_rule": (
                    "Report input readiness and official-source anchoring now; report numerical comparison "
                    "only after the official checkpoint/probe JSON exists and is regenerated inside the release tree."
                ),
            },
            {
                "name": "scPlantAnnotate",
                "status": "auth_limited_contract_ready",
                "evidence_readiness_score": 90,
                "metric_closure_status": "pending_authenticated_prediction_export",
                "input_package": {
                    "input_h5ad": scpa_package_summary.get("input_h5ad"),
                    "truth_csv": scpa_package_summary.get("truth_csv"),
                    "selected_cells": scpa_package_summary.get("selected_cells"),
                    "class_count": scpa_package_summary.get("class_count"),
                    "species": scpa_package_summary.get("species"),
                },
                "access_audit": {
                    "web_server_reachable": scpa_summary.get("web_server_reachable"),
                    "root_status": scpa_summary.get("root_status"),
                    "scriptable_batch_api_detected": scpa_summary.get("batch_api_detected"),
                    "anonymous_api_accessible": scpa_summary.get("anonymous_api_accessible"),
                    "auth_required_endpoint_count": scpa_summary.get("auth_required_endpoint_count"),
                },
                "required_artifacts_for_metric_closure": [
                    "authenticated scPlantAnnotate account or author-exported predictions",
                    "outputs/external_benchmarks/scplantannotate_final_metrics.json",
                    "truth-matched prediction CSV with cell identifiers",
                ],
                "local_runner": (
                    "SCPLANTANNOTATE_USERNAME=<user> SCPLANTANNOTATE_PASSWORD=<password> "
                    "python scripts/run_scplantannotate_authenticated_benchmark.py "
                    "--input-h5ad outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad "
                    "--dataset-name snowcell_public_sprint_scplantannotate_probe --organism-id 1 --predictor-id 1 "
                    "--execute --wait --output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json"
                ),
                "reporting_rule": (
                    "Keep this as access-limited until authenticated predictions or an official export are scored."
                ),
            },
        ],
        "panel_summary": panel.get("summary", {}),
        "submission_upgrade": {
            "before": "Third-party model comparison needed a clearer separation between completed metrics and official-source metric-pending contracts.",
            "after": "Completed Seurat metrics, scPlantLLM input/runner readiness and scPlantAnnotate auth-limited execution are separated, sourced and assigned closure criteria.",
            "safe_sentence": (
                "Plant-CellFM v9 includes completed v3, centroid and Seurat benchmarks, while scPlantLLM and "
                "scPlantAnnotate are disclosed through official-source benchmark contracts pending executable metric closure."
            ),
        },
    }


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    contracts = payload["contracts"]
    scplantllm = contracts[0]
    scpa = contracts[1]
    lines = [
        "# Plant-CellFM v10 Third-Party Benchmark Contract",
        "",
        f"Generated: {payload['generated']}",
        "",
        payload["claim_boundary"],
        "",
        "## Official Sources",
        "",
    ]
    lines.extend(
        md_table(
            ["Tool", "Source", "Local role"],
            [
                [
                    "scPlantLLM",
                    f"{payload['official_sources']['scPlantLLM']['github']}; DOI {payload['official_sources']['scPlantLLM']['paper'].split('DOI ')[-1]}",
                    "official foundation-model comparator with input and execution contract ready",
                ],
                [
                    "scPlantAnnotate",
                    f"{payload['official_sources']['scPlantAnnotate']['web']}; DOI {payload['official_sources']['scPlantAnnotate']['paper'].split('DOI ')[-1]}",
                    "official web/API comparator, authenticated execution required",
                ],
                [
                    "Seurat",
                    payload["official_sources"]["Seurat"]["source"],
                    "completed traditional label-transfer baseline",
                ],
            ],
        )
    )
    lines.extend(["", "## Completed Comparator", ""])
    for item in payload["completed_comparators"]:
        lines.extend(
            [
                f"- {item['name']}: `{item['status']}`",
                f"- Test cells: `{item['test_cells']}`",
                f"- Fine accuracy: `{fmt(item['fine_accuracy'])}`",
                f"- Fine macro-F1: `{fmt(item['fine_macro_f1'])}`",
                f"- Evidence: `{item['evidence']}`",
                "",
            ]
        )
    lines.extend(["## Contract Readiness", ""])
    rows = []
    for item in contracts:
        rows.append(
            [
                item["name"],
                item["status"],
                item["evidence_readiness_score"],
                item["metric_closure_status"],
                item["reporting_rule"],
            ]
        )
    lines.extend(md_table(["Tool", "Status", "Evidence-readiness score", "Metric closure", "Reporting rule"], rows))
    lines.extend(
        [
            "",
            "## scPlantLLM Execution Contract",
            "",
            f"- Input ready: `{bool_status(scplantllm['input_package']['input_ready'])}`",
            f"- Selected cells: `{scplantllm['input_package']['selected_cells']}`",
            f"- Retained genes: `{scplantllm['input_package']['retained_genes']}`",
            f"- Gene-vocabulary overlap: `{fmt(scplantllm['input_package']['gene_vocab_overlap_rate'])}`",
            f"- Reference chunks ready: `{bool_status(scplantllm['input_package']['reference_chunks_ready'])}`",
            f"- Chunk count: `{scplantllm['input_package']['chunk_count']}`",
            "",
            "Required artifacts for metric closure:",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in scplantllm["required_artifacts_for_metric_closure"])
    lines.extend(["", "Runner contract:", "", "```bash", scplantllm["local_runner"], "```", ""])
    lines.extend(
        [
            "## scPlantAnnotate Execution Contract",
            "",
            f"- Web server reachable: `{bool_status(scpa['access_audit']['web_server_reachable'])}`",
            f"- Anonymous API accessible: `{bool_status(scpa['access_audit']['anonymous_api_accessible'])}`",
            f"- Auth-required endpoint count: `{scpa['access_audit']['auth_required_endpoint_count']}`",
            f"- Input h5ad: `{scpa['input_package']['input_h5ad']}`",
            f"- Truth CSV: `{scpa['input_package']['truth_csv']}`",
            f"- Selected cells: `{scpa['input_package']['selected_cells']}`",
            f"- Class count: `{scpa['input_package']['class_count']}`",
            "",
            "Required artifacts for metric closure:",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in scpa["required_artifacts_for_metric_closure"])
    lines.extend(["", "Runner contract:", "", "```bash", scpa["local_runner"], "```", ""])
    lines.extend(
        [
            "## Submission Upgrade",
            "",
            f"- Before: {payload['submission_upgrade']['before']}",
            f"- After: {payload['submission_upgrade']['after']}",
            f"- Safe sentence: {payload['submission_upgrade']['safe_sentence']}",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write third-party benchmark execution contract")
    parser.add_argument("--output-json", type=Path, default=RELEASE / "third_party_benchmark_contract_v10.json")
    parser.add_argument("--output-md", type=Path, default=RELEASE / "third_party_benchmark_contract_v10.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
