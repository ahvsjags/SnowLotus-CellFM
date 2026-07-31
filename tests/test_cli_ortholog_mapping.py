from __future__ import annotations

from pathlib import Path

import snowcell.cli as cli


def test_predict_cli_forwards_declared_ortholog_map(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_predict(**kwargs: object) -> Path:
        captured.update(kwargs)
        return tmp_path / "predictions.csv"

    monkeypatch.setattr(cli, "predict_to_csv", fake_predict)
    cli.main(
        [
            "predict",
            "--checkpoint",
            "frozen.pt",
            "--data",
            "wheat.h5ad",
            "--output",
            "predictions.csv",
            "--ortholog-map",
            "wheat_to_ath.tsv",
            "--ortholog-aggregation",
            "mean",
            "--device",
            "cpu",
        ]
    )

    assert captured["ortholog_map"] == "wheat_to_ath.tsv"
    assert captured["ortholog_aggregation"] == "mean"
    assert captured["checkpoint_path"] == "frozen.pt"
    assert captured["data_path"] == "wheat.h5ad"


def test_annotation_bundle_cli_forwards_declared_ortholog_map(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_annotate(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"output_dir": str(tmp_path / "bundle")}

    monkeypatch.setattr(cli, "annotate_to_bundle", fake_annotate)
    cli.main(
        [
            "annotate-bundle",
            "--checkpoint",
            "frozen.pt",
            "--data",
            "wheat.h5ad",
            "--output-dir",
            "bundle",
            "--ortholog-map",
            "wheat_to_ath.tsv",
            "--ortholog-aggregation",
            "mean",
            "--device",
            "cpu",
        ]
    )

    assert captured["ortholog_map"] == "wheat_to_ath.tsv"
    assert captured["ortholog_aggregation"] == "mean"
    assert captured["checkpoint_path"] == "frozen.pt"
    assert captured["data_path"] == "wheat.h5ad"
