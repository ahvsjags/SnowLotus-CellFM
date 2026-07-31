from __future__ import annotations

"""Promote the audited GSE270342 best checkpoint into the release model registry."""

import argparse
import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "outputs" / "gse270342_wheat_root_lora_adapter_4070" / "best.pt"
DEFAULT_DESTINATION = ROOT / "models" / "Plant_CellFM_GSE270342_wheat_root_lora_adapter_best.pt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Missing audited training checkpoint: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file() or sha256(destination) != sha256(source):
        shutil.copy2(source, destination)
    source_sha = sha256(source)
    destination_sha = sha256(destination)
    if source_sha != destination_sha:
        raise RuntimeError("Promoted checkpoint checksum does not match source checkpoint.")
    print(f"{destination_sha}  {destination.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
