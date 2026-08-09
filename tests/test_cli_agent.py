from __future__ import annotations

from snowcell import cli


def test_cli_agent_forwards_policy(monkeypatch) -> None:
    captured = {}

    def fake_run_agent(**kwargs):
        captured.update(kwargs)
        return {"status": "manual_review_required"}

    monkeypatch.setattr(cli, "run_agent", fake_run_agent)
    cli.main(
        [
            "agent-annotate",
            "--checkpoint",
            "checkpoint.pt",
            "--data",
            "matrix.npz",
            "--output-dir",
            "out",
            "--species",
            "Sorghum bicolor",
            "--support-labels",
            "support.tsv",
            "--review-threshold",
            "0.8",
            "--coverage-target",
            "0.9",
            "--device",
            "cpu",
        ]
    )
    assert captured["species"] == "Sorghum bicolor"
    assert captured["support_labels"] == "support.tsv"
    assert captured["review_threshold"] == 0.8
    assert captured["accepted_coverage_target"] == 0.9
