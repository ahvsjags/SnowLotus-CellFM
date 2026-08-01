from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v7_supplementary_packager_requires_gse297576_tables() -> None:
    script = (ROOT / "scripts" / "build_v7_supplementary_tables.py").read_text(encoding="utf-8")
    assert "range(1, 28)" in script
    assert "missing table numbers" in script
