from __future__ import annotations

"""Build the v4 submission tables directly from frozen Plant-CellFM records."""

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "supplementary_tables" / "submission_v4"
SOURCE = ROOT / "figures" / "plant_cellfm_submission_v4" / "source_data"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_rows(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranking: list[dict] = []
    selected: list[dict] = []
    for record in payload["selected_configs"]:
        picked = record["selected_candidate"]
        selected.append({"held_out_species": record["held_out_species"], **picked})
        for rank, candidate in enumerate(record["inner_candidate_ranking"], start=1):
            ranking.append(
                {
                    "held_out_species": record["held_out_species"],
                    "inner_rank": rank,
                    "selected": candidate["candidate"]["name"] == picked["name"],
                    **candidate["candidate"],
                    **candidate["summary"],
                }
            )
    return pd.DataFrame(ranking), pd.DataFrame(selected)


def fewshot_summary(payload: dict) -> pd.DataFrame:
    rows = []
    for item in payload["summaries"]:
        if item["mode"] != "budgeted_random":
            continue
        rows.append(
            {
                "support_cells_per_species": item["support_value"],
                "support_draws": len(item["seeds"]),
                "mean_support_cells_total": item["mean_support_cells"],
                "mean_query_cells_total": item["mean_query_cells"],
                "mean_query_all_cell_accuracy": item["mean_accuracy_all_query"],
                "sd_query_all_cell_accuracy": item["std_accuracy_all_query"],
                "minimum_query_all_cell_accuracy": item["min_accuracy_all_query"],
                "maximum_query_all_cell_accuracy": item["max_accuracy_all_query"],
                "mean_query_macro_f1": item["mean_macro_f1_query"],
            }
        )
    return pd.DataFrame(rows).sort_values("support_cells_per_species")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    profile_dir = ROOT / "figure_data" / "corpus_profile_v1"
    profile = json.loads((profile_dir / "corpus_profile.json").read_text(encoding="utf-8"))
    v17 = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    v18 = json.loads((ROOT / "release_metadata" / "revision_v18_identity_curated_strict.json").read_text(encoding="utf-8"))
    v14 = json.loads((ROOT / "release_metadata" / "revision_v14_context_stc_benchmark.json").read_text(encoding="utf-8"))
    v11 = json.loads((ROOT / "release_metadata" / "revision_v11_fewshot_adapter_benchmark.json").read_text(encoding="utf-8"))
    external = json.loads((ROOT / "release_metadata" / "external_benchmark_panel_v9.json").read_text(encoding="utf-8"))
    scplantllm_probe = json.loads((ROOT / "release_metadata" / "scplantllm_official_data_embedding_probe_256.json").read_text(encoding="utf-8"))
    scplantllm_audit = json.loads((ROOT / "release_metadata" / "scplantllm_official_execution_audit.json").read_text(encoding="utf-8"))
    root_literature = json.loads((ROOT / "release_metadata" / "arabidopsis_root_literature_concordance_v4.json").read_text(encoding="utf-8"))
    external_root = json.loads((ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "release_metadata" / "top_journal_figure_audit_v4.json").read_text(encoding="utf-8"))
    runtime = json.loads((ROOT / "release_metadata" / "revision_v11_runtime_head_benchmark.json").read_text(encoding="utf-8"))

    v17_ranking, v17_selected = nested_rows(v17)
    label_audit = v18["label_integrity_audit"]
    integrity = pd.DataFrame(
        {
            "species": list(label_audit["total_cells_by_species"]),
            "public_label_cells": list(label_audit["total_cells_by_species"].values()),
            "explicit_identity_cells": list(label_audit["kept_cells_by_species"].values()),
            "audit_only_unknown_or_unannotated_cells": list(label_audit["excluded_cells_by_species"].values()),
        }
    )
    protocol = pd.DataFrame(
        [
            {"protocol": "primary nested strict leave-species v17", "primary": True, "target_label_access": "none", "selection": "inner source-species folds", "all_cell_accuracy": v17["summary"]["accuracy_all"], "known_label_accuracy": v17["summary"]["accuracy"], "known_label_macro_f1": v17["summary"]["macro_f1"], "coverage": v17["summary"]["coverage"], "reporting_role": "strict headline"},
            {"protocol": "identity-curated strict companion v18", "primary": False, "target_label_access": "none", "selection": "inner source-species folds after fixed identity filter", "all_cell_accuracy": v18["summary"]["accuracy_all"], "known_label_accuracy": v18["summary"]["accuracy"], "known_label_macro_f1": v18["summary"]["macro_f1"], "coverage": v18["summary"]["coverage"], "reporting_role": "label-integrity companion; not a substituted headline"},
            {"protocol": "global context sensitivity v14", "primary": False, "target_label_access": "none", "selection": "global outer-fold context", "all_cell_accuracy": v14["best_method"]["summary"]["accuracy_all"], "known_label_accuracy": v14["best_method"]["summary"]["accuracy"], "known_label_macro_f1": v14["best_method"]["summary"]["macro_f1"], "coverage": v14["best_method"]["summary"]["coverage"], "reporting_role": "exploratory sensitivity only"},
            {"protocol": "few-shot target adaptation v11", "primary": False, "target_label_access": "random labelled support only; query held out", "selection": "10 independent draws at each support budget", "all_cell_accuracy": v11["best_summary"]["mean_accuracy_all_query"], "known_label_accuracy": None, "known_label_macro_f1": v11["best_summary"]["mean_macro_f1_query"], "coverage": None, "reporting_role": "target-species adaptation"},
            {"protocol": "runtime full-vocabulary head", "primary": False, "target_label_access": "deployed learned label vocabulary", "selection": "runtime inference", "all_cell_accuracy": runtime["full_vocabulary_runtime_head"]["accuracy_all"], "known_label_accuracy": None, "known_label_macro_f1": None, "coverage": None, "reporting_role": "deployment analysis; not strict zero-shot"},
        ]
    )
    figure_manifest = []
    for group, records in audit["figures"].items():
        for record in records:
            figure_manifest.append(
                {
                    "group": group,
                    "figure": record["stem"],
                    "exports_ready": record["ready"],
                    "editable_svg_text": record["editable_svg_text"],
                    "source_data_tables": "; ".join(record["source_tables"]),
                    "tiff_pixels": "x".join(map(str, record["raster"]["pixels"])),
                    "tiff_dpi": "x".join(f"{value:.0f}" for value in record["raster"]["dpi"]),
                }
            )
    reproducibility_paths = [
        ROOT / "scripts" / "run_revision_v18_identity_curated_strict.py",
        ROOT / "scripts" / "run_revision_v11_fewshot_adapter_benchmark.py",
        ROOT / "scripts" / "render_v4_top_journal_figures.py",
        ROOT / "scripts" / "build_v4_root_literature_concordance.py",
        ROOT / "scripts" / "download_gse152766_external_root_case.py",
        ROOT / "scripts" / "prepare_gse152766_external_root_case.py",
        ROOT / "scripts" / "audit_gse152766_external_root_case.py",
        ROOT / "scripts" / "write_submission_v4_supplementary_tables.py",
        ROOT / "scripts" / "audit_v4_submission_figure_suite.py",
        ROOT / "scripts" / "audit_scplantllm_official_execution.py",
        ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json",
        ROOT / "release_metadata" / "revision_v18_identity_curated_strict.json",
        ROOT / "release_metadata" / "plant_cellfm_model_card_v4.json",
        ROOT / "release_metadata" / "scplantllm_official_data_embedding_probe_256.json",
        ROOT / "release_metadata" / "scplantllm_official_execution_audit.json",
        ROOT / "release_metadata" / "arabidopsis_root_literature_concordance_v4.json",
        ROOT / "release_metadata" / "gse152766_external_input_acquisition_v4.json",
        ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json",
    ]
    reproducibility = pd.DataFrame(
        [
            {
                "artifact": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "reproduction_command": (
                    "python scripts/run_revision_v18_identity_curated_strict.py" if path.name.startswith("run_revision_v18") else
                    "python scripts/run_revision_v11_fewshot_adapter_benchmark.py" if path.name.startswith("run_revision_v11_fewshot") else
                    "python scripts/render_v4_top_journal_figures.py" if path.name.startswith("render_v4") else
                    "python scripts/write_submission_v4_supplementary_tables.py" if path.name.startswith("write_submission_v4") else
                    "python scripts/audit_v4_submission_figure_suite.py" if path.name.startswith("audit_v4") else
                    "python scripts/audit_scplantllm_official_execution.py" if path.name.startswith("audit_scplantllm") else
                    "python scripts/build_v4_root_literature_concordance.py" if path.name.startswith("build_v4_root") else
                    "python scripts/download_gse152766_external_root_case.py" if path.name.startswith("download_gse152766_external") else
                    "python scripts/prepare_gse152766_external_root_case.py" if path.name.startswith("prepare_gse152766") else
                    "python scripts/audit_gse152766_external_root_case.py" if path.name.startswith("audit_gse152766") else
                    "frozen release record"
                ),
            }
            for path in reproducibility_paths
        ]
    )
    external_evidence = pd.DataFrame(external["comparisons"])
    scplantllm_execution_row = pd.DataFrame(
        [
            {
                "comparison": "scPlantLLM official checkpoint execution on official processed chunks",
                "protocol": "official train/test chunks; stratified 256/256 frozen-encoder representation probe",
                "status": "completed_execution_not_matched_to_v17",
                "formal_comparison": False,
                "evidence": "release_metadata/scplantllm_official_execution_audit.json",
                "method": scplantllm_probe["method"],
                "test_cells": scplantllm_probe["data"]["selected_test_cells"],
                "train_cells": scplantllm_probe["data"]["selected_train_cells"],
                "fine_accuracy": scplantllm_probe["metrics"]["accuracy"],
                "fine_macro_f1": scplantllm_probe["metrics"]["macro_f1"],
                "interpretation": (
                    "Official scPlantLLM weight execution passed the release audit with zero missing or unexpected state keys. "
                    "Metric is a frozen-encoder centroid probe on scPlantLLM's own chunks, not the classifier head and not a matched Plant-CellFM v17 comparison."
                ),
                "audit_status": scplantllm_audit["audit_status"],
            }
        ]
    )
    external_evidence = pd.concat([external_evidence, scplantllm_execution_row], ignore_index=True, sort=False)
    tables = {
        "Supplementary_Table_S1_current_corpus_manifest.tsv": pd.read_csv(profile_dir / "species_by_dataset.tsv", sep="\t"),
        "Supplementary_Table_S2_protocol_boundaries.tsv": protocol,
        "Supplementary_Table_S3_primary_strict_v17_per_species.tsv": pd.DataFrame(v17["outer_species_records"]),
        "Supplementary_Table_S4_identity_curated_v18_per_species.tsv": pd.DataFrame(v18["outer_species_records"]),
        "Supplementary_Table_S5_label_integrity_audit.tsv": integrity,
        "Supplementary_Table_S6_nested_inner_selection_audit.tsv": v17_ranking,
        "Supplementary_Table_S7_selected_nested_configurations.tsv": v17_selected,
        "Supplementary_Table_S8_fewshot_aggregate_and_raw_draws.tsv": fewshot_summary(v11),
        "Supplementary_Table_S9_fewshot_raw_query_draws.tsv": pd.read_csv(SOURCE / "plant_cellfm_v4_fig3_fewshot_target_adaptation_fewshot_draws.tsv", sep="\t"),
        "Supplementary_Table_S10_fewshot_per_species_draws.tsv": pd.read_csv(SOURCE / "plant_cellfm_v4_fig3_fewshot_target_adaptation_fewshot_species_draws.tsv", sep="\t"),
        "Supplementary_Table_S11_matched_checkpoint_comparison.tsv": pd.read_csv(SOURCE / "plant_cellfm_v4_ed_fig3_matched_checkpoint_comparison_matched_checkpoint_metrics.tsv", sep="\t"),
        "Supplementary_Table_S12_external_comparator_evidence_audit.tsv": external_evidence,
        "Supplementary_Table_S13_arabidopsis_root_marker_candidates.tsv": pd.read_csv(SOURCE / "plant_cellfm_v4_fig4_arabidopsis_root_candidate_resource_root_marker_candidates.tsv", sep="\t"),
        "Supplementary_Table_S14_figure_and_source_data_manifest.tsv": pd.DataFrame(figure_manifest),
        "Supplementary_Table_S15_reproducibility_manifest.tsv": reproducibility,
        "Supplementary_Table_S16_arabidopsis_root_literature_concordance.tsv": pd.DataFrame(root_literature["anchors"]),
        "Supplementary_Table_S17_gse152766_external_root_blind_inference.tsv": pd.DataFrame(
            external_root["predefined_marker_coherence"]
        ),
    }
    for name, frame in tables.items():
        frame.to_csv(OUT / name, sep="\t", index=False)
    with pd.ExcelWriter(OUT / "Plant_CellFM_Supplementary_Tables_v4.xlsx", engine="openpyxl") as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name.replace("Supplementary_Table_", "")[:31], index=False)
    manifest = {
        "schema_version": "plant_cellfm_submission_v4_supplementary_tables",
        "corpus_profile": profile,
        "table_files": list(tables),
        "workbook": "Plant_CellFM_Supplementary_Tables_v4.xlsx",
        "primary_strict_protocol": "revision_v17_nested_metadata_gate",
        "label_integrity_companion": "revision_v18_identity_curated_strict",
        "claim_boundary": "v17 is the only primary strict leave-species result. v18 is a pre-specified identity-curated companion; v14, few-shot adaptation and runtime-head outputs use distinct protocols. External methods with unavailable official matched predictions are recorded as pending, not numerically ranked. Arabidopsis literature-marker concordance supports biological plausibility but is neither wet-lab validation nor independent-matrix replication. The GSE152766 case is blind external inference on a label-free matrix, so its marker-coherence statistics are not external accuracy or an external model ranking.",
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "tables": len(tables)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
