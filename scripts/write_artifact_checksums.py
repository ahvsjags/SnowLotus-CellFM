from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


DEFAULT_PATTERNS = [
    "README.md",
    "docs/*.md",
    "configs/*.yaml",
    "configs/generated/*.yaml",
    "data/public_dataset_manifest.tsv",
    "data/public_discovery/*.tsv",
    "data/public_discovery/*.json",
    "data/public_discovery/*.md",
    "data/public_discovery/*.txt",
    "scripts/generated_geo_promotion_downloads/*.sh",
    "data/public/*_raw_tar/unsupported_single_cell_matrix.json",
    "data/corpus_manifest*.tsv",
    "data/plant_foundation_corpus*.h5ad",
    "outputs/*/best.pt",
    "outputs/*/history.json",
    "outputs/*/test_metrics.json",
    "outputs/*/config.resolved.json",
    "outputs/detailed_evaluations/**/*.json",
    "outputs/detailed_evaluations/**/*.md",
    "outputs/detailed_evaluations/**/*.tsv",
    "outputs/publication_package/status_summary.json",
    "outputs/publication_package/training_curve_summary.md",
    "outputs/publication_package/training_curve_summary.json",
    "outputs/publication_package/training_curve_summary.tsv",
    "outputs/publication_package/training_curve_summary.png",
    "outputs/publication_package/pending_corpus_additions.md",
    "outputs/publication_package/pending_corpus_additions.json",
    "outputs/publication_package/public_mlm_plus_readiness.md",
    "outputs/publication_package/public_mlm_plus_readiness.json",
    "outputs/publication_package/model_data_card.md",
    "outputs/publication_package/model_data_card.json",
    "outputs/publication_package/model_release_manifest.md",
    "outputs/publication_package/model_release_manifest.json",
    "outputs/publication_package/annotation_bundle_index.md",
    "outputs/publication_package/annotation_bundle_index.json",
    "outputs/publication_package/top_journal_readiness_matrix.md",
    "outputs/publication_package/top_journal_readiness_matrix.json",
    "outputs/publication_package/submission_action_plan.md",
    "outputs/publication_package/submission_action_plan.json",
    "outputs/publication_package/submission_action_plan.tsv",
    "outputs/publication_package/submission_dossier.md",
    "outputs/publication_package/submission_dossier.json",
    "outputs/publication_package/data_integrity_audit.md",
    "outputs/publication_package/data_integrity_audit.json",
    "outputs/publication_package/data_integrity_audit.tsv",
    "outputs/publication_package/corpus_provenance_audit.md",
    "outputs/publication_package/corpus_provenance_audit.json",
    "outputs/publication_package/corpus_provenance_audit.tsv",
    "outputs/publication_package/scplantdb_manifest_audit.md",
    "outputs/publication_package/scplantdb_manifest_audit.json",
    "outputs/publication_package/scplantdb_manifest_audit.tsv",
    "outputs/publication_package/download_progress_audit.md",
    "outputs/publication_package/download_progress_audit.json",
    "outputs/publication_package/transfer_queue_health_audit.md",
    "outputs/publication_package/transfer_queue_health_audit.json",
    "outputs/publication_package/geo_promotion_queue_health_audit.md",
    "outputs/publication_package/geo_promotion_queue_health_audit.json",
    "outputs/publication_package/training_health_audit.md",
    "outputs/publication_package/training_health_audit.json",
    "outputs/publication_package/modality_compatibility_audit.md",
    "outputs/publication_package/modality_compatibility_audit.json",
    "outputs/publication_package/saussurea_supporting_evidence.md",
    "outputs/publication_package/saussurea_supporting_evidence.json",
    "outputs/publication_package/saussurea_h5ad_contract.md",
    "outputs/publication_package/saussurea_h5ad_contract.json",
    "outputs/publication_package/saussurea_public_data_discovery.md",
    "outputs/publication_package/saussurea_public_data_discovery.json",
    "outputs/publication_package/saussurea_data_request_package.md",
    "outputs/publication_package/saussurea_data_request_package.json",
    "outputs/publication_package/saussurea_data_request_email.txt",
    "outputs/publication_package/benchmark_gap_audit.md",
    "outputs/publication_package/benchmark_gap_audit.json",
    "outputs/publication_package/benchmarks/stage2_*.json",
    "outputs/publication_package/benchmarks/stage2_*.marker",
    "outputs/publication_package/strict_benchmarks/foundation_public_plants_stage2_4090*",
    "outputs/publication_package/external_tool_environment.md",
    "outputs/publication_package/external_tool_environment.json",
    "outputs/publication_package/scplantllm_input_readiness.md",
    "outputs/publication_package/scplantllm_input_readiness.json",
    "outputs/publication_package/scplantannotate_access_audit.md",
    "outputs/publication_package/scplantannotate_access_audit.json",
    "outputs/publication_package/scplantannotate_benchmark_input_package.md",
    "outputs/publication_package/scplantannotate_benchmark_input_package.json",
    "outputs/publication_package/scplantllm_preprocess_probe_readiness.md",
    "outputs/publication_package/scplantllm_preprocess_probe_readiness.json",
    "outputs/external_benchmarks/scplantannotate_public_sprint_input/README.md",
    "outputs/external_benchmarks/scplantannotate_public_sprint_input/summary.json",
    "outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv",
    "outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad",
    "outputs/external_benchmarks/scplantllm_public_sprint_input/summary.json",
    "outputs/external_benchmarks/scplantllm_public_sprint_input/*.meta.csv",
    "outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/*.meta",
    "outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/*.meta.json",
    "outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/chunks/*.h5",
    "outputs/external_benchmarks/scplantllm_preprocess_probe_input/summary.json",
    "outputs/external_benchmarks/scplantllm_preprocess_probe_input/*.meta.csv",
    "outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/*.meta",
    "outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/*.meta.json",
    "outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/chunks/*.h5",
    "outputs/publication_package/public_discovery/*.tsv",
    "outputs/publication_package/public_discovery/*.json",
    "outputs/publication_package/public_discovery/*.md",
    "outputs/publication_package/public_discovery/*.txt",
    "outputs/publication_package/scripts/*.R",
    "outputs/publication_package/scripts/*.py",
    "outputs/publication_package/scripts/*.sh",
    "outputs/publication_package/scripts/generated_geo_promotion_downloads/*.sh",
    "outputs/external_benchmarks/*.json",
    "outputs/strict_benchmarks/*.json",
    "outputs/strict_benchmarks/*.tsv",
    "outputs/strict_benchmarks/*.yaml",
    "external/scPlantLLM/model_params/*.pth",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path, patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                paths.add(path)
    return sorted(paths, key=lambda item: item.as_posix())


def write_checksums(project_dir: str | Path, output: str | Path, patterns: list[str]) -> Path:
    root = Path(project_dir)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    files = [path for path in collect_files(root, patterns) if path.resolve() != output_path.resolve()]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["path", "bytes", "sha256"])
        for path in files:
            writer.writerow([path.relative_to(root).as_posix(), path.stat().st_size, sha256_file(path)])
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SHA256 checksums for SnowCell reproducibility artifacts")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--include", action="append", default=None, help="Glob pattern relative to project dir")
    args = parser.parse_args()
    write_checksums(args.project_dir, args.output, args.include or DEFAULT_PATTERNS)


if __name__ == "__main__":
    main()
