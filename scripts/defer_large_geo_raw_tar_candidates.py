from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path("/mnt/snowlotus_cellfm")
WRAPPER_DIR = PROJECT / "scripts/generated_geo_promotion_downloads"
DEFAULT_THRESHOLD = 5 * 1024**3


def parse_export(text: str, name: str, default: str = "") -> str:
    pattern = re.compile(rf"export\s+{re.escape(name)}=(?:'([^']*)'|\"([^\"]*)\"|([^\s]+))")
    match = pattern.search(text)
    if not match:
        return default
    return next(group for group in match.groups() if group is not None)


def manifest_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def content_length(url: str) -> int | None:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "SnowLotus-CellFM/0.1 public-data-collector"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            value = response.headers.get("Content-Length")
    except Exception:
        return None
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def write_header_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "path",
                "dataset_id",
                "species",
                "tissue",
                "layer",
                "label_key",
                "coarse_label_key",
                "sample_key",
            ]
        )


def defer_large(accession: str, dataset_id: str, species: str, tissue: str, raw_url: str, size: int, threshold: int) -> None:
    accession_lower = accession.lower()
    session = f"snowcell_geo_promotion_{accession_lower}"
    raw_dir = PROJECT / f"data/public/{accession}_raw_tar"
    manifest = PROJECT / f"data/corpus_manifest.{accession_lower}.tsv"
    report = raw_dir / "unsupported_single_cell_matrix.json"
    raw_tar = raw_dir / f"{accession}_RAW.tar"
    raw_tmp = raw_dir / f"{accession}_RAW.tar.download"
    raw_aria2 = raw_dir / f"{accession}_RAW.tar.aria2"

    subprocess.run(["tmux", "kill-session", "-t", session], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for path in [raw_tar, raw_tmp, raw_aria2]:
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    raw_dir.mkdir(parents=True, exist_ok=True)
    write_header_manifest(manifest)
    payload = {
        "accession": accession,
        "dataset_id": dataset_id,
        "species": species,
        "tissue": tissue,
        "status": "deferred_large_raw_tar_file_level_retrieval_required",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": (
            f"GEO RAW tar is {size} bytes, exceeding the active queue threshold {threshold} bytes. "
            "Whole-tar retrieval is deferred to protect disk and keep the training/data queue moving; "
            "use file-level matrix member retrieval or rerun with an explicit larger budget."
        ),
        "raw_url": raw_url,
        "corpus_manifest": manifest.relative_to(PROJECT).as_posix(),
        "corpus_manifest_rows": 0,
    }
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"DEFERRED {accession} {size} {raw_url}")


def main() -> None:
    threshold = int(os.environ.get("SNOWCELL_GEO_RAW_TAR_QUEUE_MAX_BYTES", DEFAULT_THRESHOLD))
    for wrapper in sorted(WRAPPER_DIR.glob("download_gse*.sh")):
        text = wrapper.read_text(encoding="utf-8", errors="replace")
        accession = parse_export(text, "SNOWCELL_GEO_ACCESSION")
        if not accession:
            continue
        accession_lower = accession.lower()
        manifest = PROJECT / f"data/corpus_manifest.{accession_lower}.tsv"
        raw_dir = PROJECT / f"data/public/{accession}_raw_tar"
        report = raw_dir / "unsupported_single_cell_matrix.json"
        if manifest_rows(manifest) > 0:
            print(f"SKIP_DONE {accession}")
            continue
        if report.exists():
            print(f"SKIP_REPORTED {accession}")
            continue
        series_bucket = f"{accession[:-3]}nnn"
        raw_url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{series_bucket}/{accession}/suppl/{accession}_RAW.tar"
        size = content_length(raw_url)
        if size is None:
            print(f"UNKNOWN_SIZE {accession} {raw_url}")
            continue
        if size > threshold:
            defer_large(
                accession=accession,
                dataset_id=parse_export(text, "SNOWCELL_GEO_DATASET_ID", f"geo_{accession_lower}"),
                species=parse_export(text, "SNOWCELL_GEO_SPECIES", "unknown"),
                tissue=parse_export(text, "SNOWCELL_GEO_TISSUE", "unknown"),
                raw_url=raw_url,
                size=size,
                threshold=threshold,
            )
        else:
            print(f"ALLOW {accession} {size}")


if __name__ == "__main__":
    main()
