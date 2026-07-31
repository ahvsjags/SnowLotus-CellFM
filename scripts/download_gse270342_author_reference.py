from __future__ import annotations

"""Acquire the author-released GSE270342 wheat-root Seurat object reproducibly.

The raw count matrix from this accession appears in an earlier exploratory record.
This acquisition is therefore provenance-first: an author-label overlap audit is
required before it can be used for any scored analysis.
"""

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270342/suppl/"
    "GSE270342_seuratObj_for_publication.rds.gz"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "external_validation"
    / "gse270342"
    / "GSE270342_seuratObj_for_publication.rds.gz"
)
RECORD = ROOT / "release_metadata" / "gse270342_author_reference_acquisition_v1.json"


@dataclass(frozen=True)
class RemoteObject:
    url: str
    bytes: int
    accept_ranges: bool
    last_modified: str | None


def request(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    merged = {"User-Agent": "Plant-CellFM/0.1 public-data-collector"}
    if headers:
        merged.update(headers)
    return urlopen(Request(url, method=method, headers=merged), timeout=120)


def remote_object(url: str) -> RemoteObject:
    with request(url, method="HEAD") as response:
        headers = response.headers
    return RemoteObject(
        url=url,
        bytes=int(headers["Content-Length"]),
        accept_ranges=headers.get("Accept-Ranges", "").casefold() == "bytes",
        last_modified=headers.get("Last-Modified"),
    )


def ranges(size: int, chunk_bytes: int) -> list[tuple[int, int]]:
    return [(start, min(size - 1, start + chunk_bytes - 1)) for start in range(0, size, chunk_bytes)]


def part_path(directory: Path, start: int, end: int) -> Path:
    return directory / f"{start:012d}-{end:012d}.part"


def fetch_range(url: str, directory: Path, start: int, end: int) -> Path:
    target = part_path(directory, start, end)
    expected = end - start + 1
    if target.is_file() and target.stat().st_size == expected:
        return target
    target.unlink(missing_ok=True)
    with request(url, headers={"Range": f"bytes={start}-{end}"}) as response, target.open("wb") as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)
    if target.stat().st_size != expected:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Incomplete byte range {start}-{end}.")
    return target


def assemble(parts: list[tuple[int, int]], directory: Path, output: Path) -> str:
    temporary = output.with_suffix(output.suffix + ".assembling")
    digest = hashlib.sha256()
    with temporary.open("wb") as destination:
        for start, end in parts:
            with part_path(directory, start, end).open("rb") as source:
                while chunk := source.read(1 << 20):
                    destination.write(chunk)
                    digest.update(chunk)
    temporary.replace(output)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--chunk-mib", type=int, default=16)
    parser.add_argument("--keep-parts", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.chunk_mib < 1:
        raise SystemExit("--workers and --chunk-mib must be positive.")

    remote = remote_object(args.url)
    if not remote.accept_ranges:
        raise SystemExit("The GEO server does not advertise byte-range support.")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    parts_dir = output.with_suffix(output.suffix + ".parts")
    parts_dir.mkdir(parents=True, exist_ok=True)
    requested_ranges = ranges(remote.bytes, args.chunk_mib * 1024 * 1024)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_range, remote.url, parts_dir, start, end) for start, end in requested_ranges]
        for future in futures:
            future.result()
    digest = assemble(requested_ranges, parts_dir, output)
    if output.stat().st_size != remote.bytes:
        raise RuntimeError("Assembled output does not match the GEO Content-Length.")
    record = {
        "schema_version": "plant_cellfm_gse270342_author_reference_acquisition_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "GSE270342",
        "title": "A soil-grown wheat root atlas with validated cross-species cluster annotations",
        "role": "author-annotated wheat-root reference candidate with reported spatial validation",
        "remote": asdict(remote),
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
        "sha256": digest,
        "workers": args.workers,
        "chunk_mib": args.chunk_mib,
        "claim_boundary": (
            "The accession's raw count matrix appears in an earlier exploratory record. "
            "Before scoring, audit cell overlap, author annotations, gene identifiers and a frozen "
            "label mapping; do not present acquisition as an independent benchmark."
        ),
    }
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.keep_parts:
        for start, end in requested_ranges:
            part_path(parts_dir, start, end).unlink(missing_ok=True)
        parts_dir.rmdir()
    print(json.dumps({"output": record["output"], "bytes": remote.bytes, "sha256": digest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
