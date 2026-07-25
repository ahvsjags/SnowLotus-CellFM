from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from snowcell.config import ExperimentConfig
from snowcell.data import prepare_data


def _counter(values: np.ndarray) -> dict[str, int]:
    return dict(sorted(Counter([str(value) for value in values]).items()))


def _split_values(values: np.ndarray, indices: np.ndarray) -> dict[str, int]:
    return _counter(values[indices])


def audit_config(config_path: str | Path) -> dict[str, Any]:
    config = ExperimentConfig.load(config_path)
    prepared = prepare_data(config.data, config.train.seed, require_labels=True)
    split = prepared.split
    matrix = prepared.matrix
    group_values = matrix.obs[config.data.group_key]
    fine_values = matrix.obs[config.data.label_key]
    coarse_values = matrix.obs[config.data.coarse_label_key]
    leaveout_key = config.data.leaveout_key or config.data.group_key
    leaveout_values = matrix.obs.get(leaveout_key, group_values)

    split_sets = {
        "train": set(group_values[split.train].tolist()),
        "validation": set(group_values[split.validation].tolist()),
        "test": set(group_values[split.test].tolist()),
    }
    group_leakage = {
        "train_validation_overlap": sorted(split_sets["train"] & split_sets["validation"]),
        "train_test_overlap": sorted(split_sets["train"] & split_sets["test"]),
        "validation_test_overlap": sorted(split_sets["validation"] & split_sets["test"]),
    }

    fine_train = set(fine_values[split.train].tolist())
    fine_test = set(fine_values[split.test].tolist())
    coarse_train = set(coarse_values[split.train].tolist())
    coarse_test = set(coarse_values[split.test].tolist())
    unseen_fine_test = sorted(fine_test - fine_train)
    unseen_coarse_test = sorted(coarse_test - coarse_train)
    supervised_ready = (
        len(split.train) > 0
        and len(split.validation) > 0
        and len(split.test) > 0
        and not group_leakage["train_test_overlap"]
        and len(fine_train) >= 2
        and len(fine_test) >= 2
        and len(coarse_train) >= 2
        and len(coarse_test) >= 2
        and not unseen_fine_test
        and not unseen_coarse_test
    )

    return {
        "config": str(config_path),
        "data_path": config.data.path,
        "split_strategy": config.data.split_strategy,
        "group_key": config.data.group_key,
        "leaveout_key": leaveout_key,
        "leaveout_test_values": list(config.data.leaveout_test_values),
        "leaveout_validation_values": list(config.data.leaveout_validation_values),
        "cells": {
            "train": int(len(split.train)),
            "validation": int(len(split.validation)),
            "test": int(len(split.test)),
        },
        "group_leakage": group_leakage,
        "leaveout_values": {
            "train": _split_values(leaveout_values, split.train),
            "validation": _split_values(leaveout_values, split.validation),
            "test": _split_values(leaveout_values, split.test),
        },
        "fine_labels": {
            "train": _split_values(fine_values, split.train),
            "validation": _split_values(fine_values, split.validation),
            "test": _split_values(fine_values, split.test),
            "unseen_test_labels": unseen_fine_test,
        },
        "coarse_labels": {
            "train": _split_values(coarse_values, split.train),
            "validation": _split_values(coarse_values, split.validation),
            "test": _split_values(coarse_values, split.test),
            "unseen_test_labels": unseen_coarse_test,
        },
        "supervised_benchmark_ready": bool(supervised_ready),
        "preprocessing": prepared.preprocessing_stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit SnowCell split leakage and benchmark readiness")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit_config(args.config)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
