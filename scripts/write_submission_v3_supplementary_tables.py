from __future__ import annotations

"""Write the traceable v3 supplementary-table package from frozen project records."""

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "supplementary_tables" / "submission_v3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fewshot_rows(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = pd.DataFrame(payload["summaries"])
    summary = summary[summary["mode"].eq("budgeted_random")].copy().sort_values("support_value")
    representative = []
    for row in summary.itertuples(index=False):
        for record in row.representative_per_species:
            representative.append({**record, "support_cells_per_species": int(row.support_value), "representative_seed": int(row.representative_seed)})
    return summary.drop(columns=["representative_per_species"]), pd.DataFrame(representative)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    corpus_dir = ROOT / "figure_data" / "corpus_profile_v1"
    profile = json.loads((corpus_dir / "corpus_profile.json").read_text(encoding="utf-8"))
    v17 = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    v14 = json.loads((ROOT / "release_metadata" / "revision_v14_context_stc_benchmark.json").read_text(encoding="utf-8"))
    v11 = json.loads((ROOT / "release_metadata" / "revision_v11_fewshot_adapter_benchmark.json").read_text(encoding="utf-8"))
    external = json.loads((ROOT / "release_metadata" / "external_benchmark_panel_v9.json").read_text(encoding="utf-8"))
    dataset = pd.read_csv(corpus_dir / "species_by_dataset.tsv", sep="\t")
    outer = pd.DataFrame(v17["outer_species_records"])
    selected = []
    ranking = []
    for record in v17["selected_configs"]:
        config = record["selected_candidate"]
        selected.append({"held_out_species": record["held_out_species"], **config})
        for rank, candidate in enumerate(record["inner_candidate_ranking"], start=1):
            ranking.append({"held_out_species": record["held_out_species"], "inner_rank": rank, "selected": candidate["candidate"]["name"] == config["name"], "candidate_name": candidate["candidate"]["name"], "candidate_kind": candidate["candidate"]["kind"], "scope": candidate["candidate"]["scope"], "minimum_family_support": candidate["candidate"]["minimum_family_support"], "k": candidate["candidate"]["k"], **candidate["summary"]})
    protocol = pd.DataFrame(
        [
            {"protocol": "primary strict leave-species", "primary": True, "target-label access": "none", "model/selection": "nested metadata gate; inner source-species selection", "reported_all_cell_accuracy": v17["summary"]["accuracy_all"], "reported_known_label_accuracy": v17["summary"]["accuracy"], "reported_macro_f1": v17["summary"]["macro_f1"], "coverage": v17["summary"]["coverage"], "reporting use": "main strict claim"},
            {"protocol": "global context gate sensitivity", "primary": False, "target-label access": "none", "model/selection": "global v14 context gate", "reported_all_cell_accuracy": v14["best_method"]["summary"]["accuracy_all"], "reported_known_label_accuracy": v14["best_method"]["summary"]["accuracy"], "reported_macro_f1": v14["best_method"]["summary"]["macro_f1"], "coverage": v14["best_method"]["summary"]["coverage"], "reporting use": "exploratory sensitivity only"},
            {"protocol": "few-shot target adaptation", "primary": False, "target-label access": "random support only; query held out", "model/selection": "target adapter, 10 support draws", "reported_all_cell_accuracy": v11["best_summary"]["mean_accuracy_all_query"], "reported_known_label_accuracy": None, "reported_macro_f1": v11["best_summary"]["mean_macro_f1_query"], "coverage": None, "reporting use": "adaptation analysis"},
            {"protocol": "runtime full-vocabulary head", "primary": False, "target-label access": "trained runtime vocabulary", "model/selection": "deployed annotation head", "reported_all_cell_accuracy": json.loads((ROOT / "release_metadata" / "revision_v11_runtime_head_benchmark.json").read_text(encoding="utf-8"))["full_vocabulary_runtime_head"]["accuracy_all"], "reported_known_label_accuracy": None, "reported_macro_f1": None, "coverage": None, "reporting use": "deployment analysis; not strict zero-shot"},
        ]
    )
    fewshot_summary, fewshot_representative = fewshot_rows(v11)
    root_markers = pd.read_csv(ROOT / "supplementary_tables" / "Supplementary_Table_11_root_marker_candidates.tsv", sep="\t")
    reproducibility_paths = [
        ROOT / "scripts" / "render_v3_data_first_main_figures.py",
        ROOT / "scripts" / "render_v3_extended_data_suite.py",
        ROOT / "scripts" / "run_revision_v17_nested_metadata_gate.py",
        ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json",
        corpus_dir / "corpus_profile.json",
    ]
    reproducibility = pd.DataFrame(
        [
            {"artifact": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "reproduction_command": "python scripts/render_v3_data_first_main_figures.py" if "render_v3_data_first" in path.name else ("python scripts/render_v3_extended_data_suite.py" if "extended_data" in path.name else "recorded frozen input")}
            for path in reproducibility_paths
        ]
    )
    tables = {
        "Supplementary_Table_S1_current_corpus_manifest.tsv": dataset,
        "Supplementary_Table_S2_protocol_boundaries.tsv": protocol,
        "Supplementary_Table_S3_primary_strict_v17_per_species.tsv": outer,
        "Supplementary_Table_S4_nested_inner_selection_audit.tsv": pd.DataFrame(ranking),
        "Supplementary_Table_S5_selected_nested_configurations.tsv": pd.DataFrame(selected),
        "Supplementary_Table_S6_fewshot_aggregate_metrics.tsv": fewshot_summary,
        "Supplementary_Table_S7_fewshot_representative_per_species.tsv": fewshot_representative,
        "Supplementary_Table_S8_external_benchmark_audit.tsv": pd.DataFrame(external["comparisons"]),
        "Supplementary_Table_S9_arabidopsis_root_marker_candidates.tsv": root_markers,
        "Supplementary_Table_S10_reproducibility_manifest.tsv": reproducibility,
    }
    for name, frame in tables.items():
        frame.to_csv(OUT / name, sep="\t", index=False)
    with pd.ExcelWriter(OUT / "Plant_CellFM_Supplementary_Tables_v3.xlsx", engine="openpyxl") as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name.replace("Supplementary_Table_", "")[:31], index=False)
    manifest = {
        "schema_version": "plant_cellfm_submission_v3_supplementary_tables",
        "corpus_profile": profile,
        "primary_strict_protocol": "revision_v17_nested_metadata_gate",
        "table_files": list(tables),
        "workbook": "Plant_CellFM_Supplementary_Tables_v3.xlsx",
        "claim_boundary": "The v17 nested metadata gate is the only primary strict leave-species result. v14 remains an exploratory sensitivity result; few-shot and runtime-head tables use distinct, explicitly labeled protocols.",
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "tables": len(tables)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
