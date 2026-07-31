from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from .corpus import build_corpus
from .adapters import load_registry
from .baselines import run_centroid_baseline
from .markers import run_marker_candidates
from .report import generate_markdown_report
from .train import annotate_to_bundle, create_demo_dataset, predict_to_csv, train_from_config


def _device(value: str) -> torch.device:
    if value == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snowcell",
        description="Plant-CellFM general plant single-cell annotation foundation model",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("make-demo", help="Create a small synthetic plant scRNA dataset")
    demo.add_argument("--output", default="data/demo.npz")
    demo.add_argument("--cells", type=int, default=480)
    demo.add_argument("--genes", type=int, default=160)
    demo.add_argument("--samples", type=int, default=12)
    demo.add_argument("--seed", type=int, default=7)

    train = subparsers.add_parser("train", help="Train or fine-tune the general plant model")
    train.add_argument("--config", required=True, help="Path to a YAML experiment config")
    train.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N")

    predict = subparsers.add_parser("predict", help="Annotate cells with a trained checkpoint")
    predict.add_argument("--checkpoint", required=True)
    predict.add_argument("--data", required=True, help=".npz or .h5ad expression matrix")
    predict.add_argument("--output", required=True, help="CSV output path")
    predict.add_argument("--layer", default=None, help="Optional AnnData layer")
    predict.add_argument(
        "--ortholog-map",
        default=None,
        help="Optional TSV mapping source-gene identifiers to checkpoint-vocabulary identifiers",
    )
    predict.add_argument(
        "--ortholog-aggregation",
        choices=("first", "mean"),
        default=None,
        help="How multi-target orthogroups are projected: first target or count-conserving mean",
    )
    predict.add_argument("--batch-size", type=int, default=128)
    predict.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N")

    annotate = subparsers.add_parser(
        "annotate-bundle",
        help="Write predictions, embeddings, and metadata for a trained checkpoint",
    )
    annotate.add_argument("--checkpoint", required=True)
    annotate.add_argument("--data", required=True, help=".npz or .h5ad expression matrix")
    annotate.add_argument("--output-dir", required=True, help="Output directory for annotation bundle")
    annotate.add_argument("--layer", default=None, help="Optional AnnData layer")
    annotate.add_argument(
        "--ortholog-map",
        default=None,
        help="Optional TSV mapping source-gene identifiers to checkpoint-vocabulary identifiers",
    )
    annotate.add_argument(
        "--ortholog-aggregation",
        choices=("first", "mean"),
        default=None,
        help="How multi-target orthogroups are projected: first target or count-conserving mean",
    )
    annotate.add_argument("--batch-size", type=int, default=128)
    annotate.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N")

    corpus = subparsers.add_parser("build-corpus", help="Merge multiple h5ad/npz datasets")
    corpus.add_argument("--manifest", required=True, help="TSV with path, dataset_id, species columns")
    corpus.add_argument("--output", required=True, help="Merged h5ad path")

    report = subparsers.add_parser("report", help="Create a publication readiness report")
    report.add_argument("--project-dir", default=".")
    report.add_argument("--output", default="outputs/publication_readiness_report.md")
    report.add_argument("--run-dir", action="append", default=None)

    baseline = subparsers.add_parser("baseline-centroid", help="Run a cosine nearest-centroid baseline")
    baseline.add_argument("--config", required=True)
    baseline.add_argument("--output", required=True)

    markers = subparsers.add_parser("marker-candidates", help="Mine one-vs-rest marker candidates")
    markers.add_argument("--config", required=True)
    markers.add_argument("--output", required=True)
    markers.add_argument("--summary-output")
    markers.add_argument("--label-key")
    markers.add_argument("--top-n", type=int, default=25)
    markers.add_argument("--min-cells", type=int, default=20)

    adapter = subparsers.add_parser(
        "adapter-info",
        help="Resolve the species adapter used by the general plant model",
    )
    adapter.add_argument("--species", required=True)
    adapter.add_argument(
        "--registry",
        default="release_metadata/plant_species_adapters.json",
        help="JSON species-adapter registry",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "make-demo":
        path = create_demo_dataset(args.output, args.cells, args.genes, args.samples, args.seed)
        print(path)
        return
    if args.command == "train":
        result = train_from_config(args.config, device=_device(args.device))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.command == "predict":
        output = predict_to_csv(
            checkpoint_path=args.checkpoint,
            data_path=args.data,
            output_path=args.output,
            layer=args.layer,
            ortholog_map=args.ortholog_map,
            ortholog_aggregation=args.ortholog_aggregation,
            batch_size=args.batch_size,
            device=_device(args.device),
        )
        print(Path(output))
        return
    if args.command == "annotate-bundle":
        output = annotate_to_bundle(
            checkpoint_path=args.checkpoint,
            data_path=args.data,
            output_dir=args.output_dir,
            layer=args.layer,
            ortholog_map=args.ortholog_map,
            ortholog_aggregation=args.ortholog_aggregation,
            batch_size=args.batch_size,
            device=_device(args.device),
        )
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return
    if args.command == "build-corpus":
        print(build_corpus(args.manifest, args.output))
        return
    if args.command == "report":
        print(generate_markdown_report(args.project_dir, args.output, args.run_dir))
        return
    if args.command == "baseline-centroid":
        print(run_centroid_baseline(args.config, args.output))
        return
    if args.command == "marker-candidates":
        print(
            run_marker_candidates(
                config_path=args.config,
                output=args.output,
                label_key=args.label_key,
                top_n=args.top_n,
                min_cells=args.min_cells,
                summary_output=args.summary_output,
            )
        )
        return
    if args.command == "adapter-info":
        registry = load_registry(args.registry)
        adapter, used_fallback = registry.resolve(args.species)
        print(
            json.dumps(
                {
                    "requested_species": args.species,
                    "used_fallback": used_fallback,
                    "adapter": adapter.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
