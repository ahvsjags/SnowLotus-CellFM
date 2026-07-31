from __future__ import annotations

"""Fetch and verify the fixed GEO input for the v4 external root case."""

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4626nnn/GSM4626007/suppl/GSM4626007_sc_52_mtx.tar.gz"
EXPECTED_SHA256 = "7e55c00b6cd651e01a90989a487328694e6f65f3841227675b171b115517edaa"
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse152766_gsm4626007"
    / "GSM4626007_sc_52_mtx.tar.gz"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path) -> dict[str, object]:
    actual = sha256(path)
    if actual != EXPECTED_SHA256:
        raise ValueError(
            f"SHA256 mismatch for {path}: expected {EXPECTED_SHA256}, observed {actual}."
        )
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": actual}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the fixed GSE152766/GSM4626007 external root archive.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="Re-download even when an existing archive passes verification.")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and not args.force:
        result = verify(output)
        print(json.dumps({"status": "existing_archive_verified", "source_url": SOURCE_URL, **result}, ensure_ascii=False))
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".part")
    request = Request(SOURCE_URL, headers={"User-Agent": "Plant-CellFM-v4-reproducibility/1.0"})
    try:
        with urlopen(request, timeout=60) as response, partial.open("wb") as handle:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                handle.write(chunk)
        result = verify(partial)
        os.replace(partial, output)
    finally:
        if partial.exists():
            partial.unlink()
    print(json.dumps({"status": "downloaded_and_verified", "source_url": SOURCE_URL, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
