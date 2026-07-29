from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SnowLotus-CellFM artifact checksums")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--checksums", required=True)
    args = parser.parse_args()

    root = Path(args.project_dir).resolve()
    checksum_path = Path(args.checksums)
    if not checksum_path.is_absolute():
        checksum_path = root / checksum_path

    checked = 0
    failures: list[str] = []
    with checksum_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            relative = Path(row["path"])
            path = root / relative
            checked += 1
            if not path.is_file():
                failures.append(f"missing: {relative}")
                continue
            actual_bytes = path.stat().st_size
            actual_sha256 = sha256_file(path)
            if actual_bytes != int(row["bytes"]):
                failures.append(f"bytes: {relative} expected={row['bytes']} actual={actual_bytes}")
            if actual_sha256 != row["sha256"]:
                failures.append(f"sha256: {relative}")

    print(f"checked={checked} failures={len(failures)}")
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
