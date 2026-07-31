from __future__ import annotations

"""Audit the reproducible execution record for the official scPlantLLM checkpoint.

This audit deliberately checks execution integrity rather than declaring a
Plant-CellFM comparison. The probe uses scPlantLLM's own processed chunks and a
frozen encoder plus nearest-centroid readout, so it must not be treated as an
official classifier score or as a matched v17 external benchmark.
"""

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = ROOT / "release_metadata" / "scplantllm_official_data_embedding_probe_256.json"
JSON_OUTPUT = ROOT / "release_metadata" / "scplantllm_official_execution_audit.json"
MARKDOWN_OUTPUT = ROOT / "release_metadata" / "scplantllm_official_execution_audit.md"


def load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing execution record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_equal(
    failures: list[str],
    payload: dict[str, Any],
    path: tuple[str, ...],
    expected: Any,
) -> None:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            failures.append(f"Missing field: {'.'.join(path)}")
            return
        current = current[key]
    if current != expected:
        failures.append(
            f"Unexpected {'.'.join(path)}: expected {expected!r}, found {current!r}"
        )


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    require_equal(
        failures,
        payload,
        ("method",),
        "scplantllm_frozen_embedding_nearest_centroid_probe",
    )
    require_equal(failures, payload, ("status",), "completed")
    require_equal(failures, payload, ("device",), "cuda")
    require_equal(failures, payload, ("model", "checkpoint_bytes"), 431801156)
    require_equal(failures, payload, ("model", "missing_keys_count"), 0)
    require_equal(failures, payload, ("model", "unexpected_keys_count"), 0)
    require_equal(failures, payload, ("data", "selected_train_cells"), 256)
    require_equal(failures, payload, ("data", "selected_test_cells"), 256)
    require_equal(failures, payload, ("data", "unseen_test_labels"), [])
    require_equal(failures, payload, ("probe", "classifier"), "cosine_nearest_centroid")

    metrics = payload.get("metrics", {})
    accuracy = metrics.get("accuracy")
    macro_f1 = metrics.get("macro_f1")
    for name, value in (("metrics.accuracy", accuracy), ("metrics.macro_f1", macro_f1)):
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            failures.append(f"{name} is not a probability in [0, 1]: {value!r}")

    return {
        "schema_version": "scplantllm_official_execution_audit_v1",
        "audit_status": "passed" if not failures else "failed",
        "execution_state": "official_encoder_executed_on_official_chunks_not_matched_to_plant_cellfm_v17",
        "probe_record": PROBE_PATH.relative_to(ROOT).as_posix(),
        "checks": {
            "official_checkpoint_bytes": payload["model"]["checkpoint_bytes"],
            "cuda_execution": payload["device"] == "cuda",
            "state_dict_missing_keys": payload["model"]["missing_keys_count"],
            "state_dict_unexpected_keys": payload["model"]["unexpected_keys_count"],
            "stratified_train_cells": payload["data"]["selected_train_cells"],
            "stratified_test_cells": payload["data"]["selected_test_cells"],
            "unseen_test_labels": payload["data"]["unseen_test_labels"],
        },
        "reported_probe_metrics": {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": metrics.get("weighted_f1"),
        },
        "interpretation": [
            "The official scPlantLLM checkpoint was loaded and executed on CUDA after documented FlashMHA-to-PyTorch attention-key conversion.",
            "The recorded metric is a frozen-encoder cosine-nearest-centroid representation probe on scPlantLLM's own 256-cell stratified train and test subsets.",
            "This is not the scPlantLLM classifier head, not a matched input to Plant-CellFM v17, and not evidence of numerical superiority by either method.",
        ],
        "remaining_requirement_for_fair_external_comparison": (
            "Acquire a frozen Plant-CellFM v17-compatible raw matrix and run both methods under a shared gene, label, split and open-set scoring contract."
        ),
        "failures": failures,
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["reported_probe_metrics"]
    checks = result["checks"]
    lines = [
        "# scPlantLLM Official Execution Audit",
        "",
        f"- Audit status: **{result['audit_status']}**",
        f"- Execution state: `{result['execution_state']}`",
        f"- Probe record: `{result['probe_record']}`",
        "",
        "## Verified execution facts",
        "",
        f"- CUDA execution: `{checks['cuda_execution']}`",
        f"- Checkpoint bytes: `{checks['official_checkpoint_bytes']}`",
        f"- Missing/unexpected state keys: `{checks['state_dict_missing_keys']}` / `{checks['state_dict_unexpected_keys']}`",
        f"- Stratified official train/test cells: `{checks['stratified_train_cells']}` / `{checks['stratified_test_cells']}`",
        f"- Probe accuracy / macro-F1: `{metrics['accuracy']:.6f}` / `{metrics['macro_f1']:.6f}`",
        "",
        "## Interpretation boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in result["interpretation"])
    lines.extend(
        [
            "",
            "## Requirement before a formal external ranking",
            "",
            f"- {result['remaining_requirement_for_fair_external_comparison']}",
        ]
    )
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines) + "\n"


def main() -> None:
    result = audit(load_payload(PROBE_PATH))
    JSON_OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MARKDOWN_OUTPUT.write_text(render_markdown(result), encoding="utf-8")
    if result["audit_status"] != "passed":
        raise SystemExit("scPlantLLM official execution audit failed")
    print(JSON_OUTPUT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
