from __future__ import annotations

"""Inventory and extract only evaluation assets from the public GSE270140 TAR."""

import argparse
import hashlib
import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "data" / "external_validation" / "gse270140" / "GSE270140_RAW.tar"
DEFAULT_OUTPUT = ROOT / "outputs" / "external_validation" / "gse270140" / "raw_assets"
RELEASE_RECORD = ROOT / "release_metadata" / "gse270140_external_archive_inventory_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def selected_members(archive: Path) -> list[tarfile.TarInfo]:
    with tarfile.open(archive, "r") as handle:
        return sorted(
            [
                member
                for member in handle.getmembers()
                if member.isfile() and member.name.casefold().endswith((".rds", ".rds.gz", ".h5", ".h5ad"))
            ],
            key=lambda member: member.name,
        )


def extract_selected(archive: Path, output: Path, members: list[tarfile.TarInfo]) -> list[dict[str, object]]:
    output.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, object]] = []
    with tarfile.open(archive, "r") as handle:
        for member in members:
            source = handle.extractfile(member)
            if source is None:
                raise RuntimeError(f"Cannot read archive member: {member.name}")
            target = output / Path(member.name).name
            with source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination, length=1 << 20)
            if target.stat().st_size != member.size:
                raise RuntimeError(f"Extracted size mismatch for {member.name}")
            extracted.append(
                {
                    "archive_member": member.name,
                    "bytes": member.size,
                    "output": str(target.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256(target),
                }
            )
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output = args.output_dir.resolve()
    if not archive.exists():
        raise SystemExit(f"Missing archive: {archive}")
    members = selected_members(archive)
    rds_members = [member for member in members if member.name.casefold().endswith((".rds", ".rds.gz"))]
    h5_members = [member for member in members if member.name.casefold().endswith((".h5", ".h5ad"))]
    if not rds_members:
        raise SystemExit("GSE270140 archive has no RDS expert-annotation candidate.")
    extracted = extract_selected(archive, output, members)
    record = {
        "schema_version": "plant_cellfm_gse270140_archive_inventory_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "GSE270140",
        "archive": {
            "path": str(archive.relative_to(ROOT)).replace("\\", "/"),
            "bytes": archive.stat().st_size,
            "sha256": sha256(archive),
        },
        "rds_member_count": len(rds_members),
        "h5_member_count": len(h5_members),
        "members": extracted,
        "claim_boundary": "These files are reserved for a frozen external evaluation. Their expression matrix, expert labels and label mapping must be inspected and versioned before any accuracy is computed.",
    }
    RELEASE_RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rds": len(rds_members), "h5": len(h5_members), "assets": len(extracted)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
