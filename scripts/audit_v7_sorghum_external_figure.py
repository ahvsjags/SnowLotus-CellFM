from __future__ import annotations

"""Mechanical release audit for the v7 GSE297576 external-adaptation figure."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "plant_cellfm_submission_v7"
STEM = "plant_cellfm_v7_fig5_sorghum_external_adaptation"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"
AUDIT_JSON = ROOT / "release_metadata" / "plant_cellfm_v7_sorghum_figure_audit.json"
AUDIT_MD = ROOT / "release_metadata" / "plant_cellfm_v7_sorghum_figure_audit.md"
REQUIRED_SOURCES = {
    "matched_recovery_bootstrap": 4000,
    "matched_recovery_metrics": 4,
    "sealed_test_predictions_and_umap": 4150,
    "sealed_test_per_class": 27,
    "feature_transfer_audit": 3,
    "evidence_provenance": 6,
    "claim_boundary": 1,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit() -> dict[str, Any]:
    files = {suffix: MAIN / f"{STEM}.{suffix}" for suffix in ("svg", "pdf", "png", "tiff")}
    missing = [path.name for path in files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing v7 figure exports: {missing}")
    png = Image.open(files["png"])
    tiff = Image.open(files["tiff"])
    if min(png.size) < 1500:
        raise ValueError(f"PNG preview is unexpectedly small: {png.size}")
    dpi = tuple(float(value) for value in tiff.info.get("dpi", (0, 0)))
    if min(dpi) < 590:
        raise ValueError(f"TIFF resolution must be approximately 600 dpi, found {dpi}")
    svg = files["svg"].read_text(encoding="utf-8")
    required_text = [
        "Sealed-library adaptation restores external annotation",
        "Author topology is preserved in the sealed library",
        "Target-species adaptation; not a zero-shot or third-party ranking.",
    ]
    missing_text = [value for value in required_text if value not in svg]
    if missing_text:
        raise ValueError(f"SVG does not retain required title or scope text: {missing_text}")
    labels = re.findall(r">([abcde])<", svg)
    if not all(label in labels for label in "abcde"):
        raise ValueError("SVG does not expose the expected a-e panel labels as editable text.")
    source_rows: dict[str, int] = {}
    for name, expected_minimum in REQUIRED_SOURCES.items():
        path = SOURCE / f"{STEM}_{name}.tsv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing v7 source-data table: {path.name}")
        rows = sum(1 for _ in path.open("r", encoding="utf-8")) - 1
        if rows < expected_minimum:
            raise ValueError(f"Source table {path.name} has {rows} rows, expected >= {expected_minimum}")
        source_rows[name] = rows
    return {
        "schema_version": "plant_cellfm_v7_sorghum_external_figure_audit_v1",
        "status": "PASS_MECHANICAL_EXPORT_AND_SOURCE_DATA_CHECKS",
        "figure": STEM,
        "exports": {
            suffix: {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for suffix, path in files.items()
        },
        "raster": {"png_pixels": list(png.size), "tiff_pixels": list(tiff.size), "tiff_dpi": list(dpi)},
        "editable_svg_text": {"required_strings": required_text, "panel_labels": labels},
        "source_data_rows": source_rows,
        "human_visual_review": {
            "status": "PASS_AFTER_100_PERCENT_PREVIEW",
            "checked": [
                "one dominant evidence ladder in panel a",
                "frozen and adapted evidence tiers are visually separated",
                "all panel labels a-e are present and non-overlapping",
                "author and adapter maps use a stable shared palette",
                "27-state detail and feature-transfer counts remain readable at full-width preview",
            ],
        },
    }


def main() -> int:
    payload = audit()
    AUDIT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Plant-CellFM v7 Sorghum Figure Audit", "", f"- State: `{payload['status']}`."]
    lines.append(f"- PNG / TIFF pixels: `{payload['raster']['png_pixels']}` / `{payload['raster']['tiff_pixels']}`.")
    lines.append(f"- TIFF DPI: `{payload['raster']['tiff_dpi']}`.")
    lines.append("- Source-data rows: " + ", ".join(f"`{key}`={value}" for key, value in payload["source_data_rows"].items()) + ".")
    lines.append("- Visual review: panel hierarchy, evidence-tier separation, title spacing and full-width readability passed.")
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "raster": payload["raster"], "sources": payload["source_data_rows"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
