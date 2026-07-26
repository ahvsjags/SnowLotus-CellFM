#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "editor_package" / "current_submit_v0.3"
ZIP_PATH = PACKAGE_DIR / "SnowLotus-CellFM_editor-v0.3_submit-now.zip"
FILES = [
    PACKAGE_DIR / "ARCHIVE_SHA256SUMS.txt",
    PACKAGE_DIR / "snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz",
    PACKAGE_DIR / "SnowLotus_CellFM_已完成工作校稿版_v0_4.docx",
    PACKAGE_DIR / "SnowLotus_CellFM_已完成工作校稿版_v0_4.md",
    PACKAGE_DIR / "SnowLotus_CellFM_中文论文稿_模型功能优势详版_v0_5.docx",
    PACKAGE_DIR / "SnowLotus_CellFM_中文论文稿_模型功能优势详版_v0_5.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    missing = [path for path in FILES if not path.is_file()]
    if missing:
        raise SystemExit(f"missing files: {missing}")
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = PACKAGE_DIR / f"SnowLotus-CellFM_editor-v0.3_submit-now.before-completed-proof-doc-{stamp}.zip"
    tmp = ZIP_PATH.with_suffix(".zip.tmp")
    shutil.copy2(ZIP_PATH, backup)
    names = {path.name for path in FILES}
    with zipfile.ZipFile(ZIP_PATH, "r") as source, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            if item.filename not in names:
                target.writestr(item, source.read(item.filename))
        for path in FILES:
            target.write(path, path.name)
    tmp.replace(ZIP_PATH)
    digest = sha256(ZIP_PATH)
    (ZIP_PATH.with_suffix(ZIP_PATH.suffix + ".sha256")).write_text(
        f"{digest}  {ZIP_PATH.name}\n",
        encoding="utf-8",
    )
    print(ZIP_PATH)
    print(digest)


if __name__ == "__main__":
    main()
