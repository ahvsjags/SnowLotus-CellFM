from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "manuscript" / "plant_methods_submission_v1"


def test_readme_exposes_the_current_plant_methods_entry_points() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Current Plant Methods v1 Submission Package" in readme
    assert "Plant_CellFM_Plant_Methods_manuscript_v1.md" in readme
    assert "Plant_CellFM_Plant_Methods_manuscript_v1.docx" in readme
    assert "Plant_CellFM_Plant_Methods_submission_v1.zip" in readme
    assert "figures/plant_cellfm_submission_v12" in readme
    assert "render_v12_system_figure.py" in readme
    assert "audit_v12_main_figure_suite.py" in readme
    assert "build_plant_methods_submission_docs.js" in readme


def test_current_submission_zip_matches_manifest_and_checksum() -> None:
    bundle = SUBMISSION / "Plant_CellFM_Plant_Methods_submission_v1.zip"
    digest_file = SUBMISSION / "Plant_CellFM_Plant_Methods_submission_v1.zip.sha256"
    expected = digest_file.read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == expected

    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())

    for index in range(1, 8):
        assert f"main_figures/Figure_{index}.pdf" in names
    assert "Plant_CellFM_Plant_Methods_manuscript_v1.docx" in names
    assert "Plant_CellFM_Plant_Methods_supporting_information_v1.docx" in names
    assert "Plant_CellFM_Plant_Methods_supplementary_figures_v1.pdf" in names
    assert "SUBMISSION_FILE_MANIFEST.json" in names


def test_v12_figure_manifest_tracks_all_final_main_figures() -> None:
    manifest = json.loads((ROOT / "figures" / "plant_cellfm_submission_v12" / "MAIN_FIGURE_MANIFEST.json").read_text())
    assert manifest["n_main_figures"] == 7
    assert manifest["visual_policy"].startswith("All seven pages")
    assert manifest.get("assets") == []
    for figure in manifest["figures"]:
        files = figure["files"]
        assert {"svg", "pdf", "png", "tiff"} <= set(files)
        for payload in files.values():
            path = ROOT / payload["path"]
            assert path.exists()
            assert path.stat().st_size == payload["bytes"]
