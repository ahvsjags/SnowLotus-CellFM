from __future__ import annotations

import sys
import tarfile
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from extract_gse270140_external_assets import selected_members


def test_selected_members_retains_rds_and_h5_assets_only(tmp_path: Path) -> None:
    archive = tmp_path / "fixture.tar"
    payload = tmp_path / "payload"
    payload.mkdir()
    for name in ("object.rds.gz", "matrix.h5", "notes.txt"):
        (payload / name).write_bytes(b"fixture")
    with tarfile.open(archive, "w") as handle:
        for path in payload.iterdir():
            handle.add(path, arcname=path.name)
    assert [member.name for member in selected_members(archive)] == ["matrix.h5", "object.rds.gz"]
