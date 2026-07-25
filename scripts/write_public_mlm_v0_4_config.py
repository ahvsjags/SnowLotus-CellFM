#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SnowLotus public MLM v0.4 config")
    parser.add_argument(
        "--base-config",
        default="configs/generated/foundation_5090_mlm_public_expansion_continuation_v0_3.yaml",
        type=Path,
    )
    parser.add_argument(
        "--output",
        default="configs/generated/foundation_5090_mlm_public_expansion_v0_4_plus_latest.yaml",
        type=Path,
    )
    parser.add_argument(
        "--corpus",
        default="data/plant_foundation_corpus_public_mlm_plus_latest.h5ad",
    )
    parser.add_argument(
        "--init-checkpoint",
        default="outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm",
    )
    parser.add_argument("--seed", default=48, type=int)
    parser.add_argument("--epochs", default=8, type=int)
    args = parser.parse_args()

    cfg = yaml.safe_load(args.base_config.read_text(encoding="utf-8")) or {}
    data = dict(cfg.get("data") or {})
    data["path"] = args.corpus
    cfg["data"] = data

    train = dict(cfg.get("train") or {})
    train["seed"] = args.seed
    train["epochs"] = args.epochs
    train["init_checkpoint"] = args.init_checkpoint
    train["resume_checkpoint"] = None
    train.setdefault("heartbeat_steps", 250)
    train.setdefault("latest_checkpoint_every_updates", 50)
    cfg["train"] = train

    output = dict(cfg.get("output") or {})
    output["directory"] = args.output_dir
    cfg["output"] = output

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=False), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
