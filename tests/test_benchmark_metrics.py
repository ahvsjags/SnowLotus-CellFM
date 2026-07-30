from __future__ import annotations

import numpy as np

import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from benchmark_public_plants_v1 import nearest_centroid_metrics


def test_benchmark_reports_open_set_errors_separately() -> None:
    train_embeddings = np.asarray([[1.0, 0.0], [0.9, 0.0], [0.0, 1.0], [0.0, 0.9]])
    train_labels = np.asarray(["a", "a", "b", "b"])
    test_embeddings = np.asarray([[1.0, 0.0], [0.95, 0.0]])
    test_labels = np.asarray(["a", "new_species_cell_type"])

    metrics = nearest_centroid_metrics(
        train_embeddings,
        train_labels,
        test_embeddings,
        test_labels,
    )

    assert metrics["coverage"] == 0.5
    assert metrics["accuracy"] == 1.0
    assert metrics["accuracy_all"] == 0.5
    assert metrics["n_evaluable"] == 1
