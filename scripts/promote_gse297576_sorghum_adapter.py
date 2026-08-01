from __future__ import annotations

"""Promote the audited locked-library Sorghum adapter into the model registry."""

import argparse
import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "outputs" / "gse297576_sorghum_root_lora_adapter_4070_oughw_holdout" / "best.pt"
DEFAULT_DESTINATION = ROOT / "models" / "Plant_CellFM_GSE297576_sorghum_root_lora_adapter_oughw_holdout_best.pt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Missing audited Sorghum adapter: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file() or sha256(destination) != sha256(source):
        shutil.copy2(source, destination)
    if sha256(destination) != sha256(source):
        raise RuntimeError("Promoted Sorghum adapter checksum does not match its audited source checkpoint.")
    print(f"{sha256(destination)}  {destination.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
