from __future__ import annotations

"""Resumable, range-based acquisition for the GSE270140 external validation archive.

The archive is a public GEO TAR containing an H5 matrix and a Seurat RDS object.
It is kept outside the frozen training corpus and is only eligible for evaluation
after a label and ontology mapping are frozen in a separate preparation step.
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
DEFAULT_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE270nnn/GSE270140/suppl/GSE270140_RAW.tar"
DEFAULT_OUTPUT = ROOT / "data" / "external_validation" / "gse270140" / "GSE270140_RAW.tar"


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
    size = int(headers["Content-Length"])
    accept_ranges = headers.get("Accept-Ranges", "").casefold() == "bytes"
    if not accept_ranges:
        raise RuntimeError("GSE270140 server does not advertise byte-range support.")
    return RemoteObject(url=url, bytes=size, accept_ranges=accept_ranges, last_modified=headers.get("Last-Modified"))


def byte_ranges(size: int, chunk_bytes: int) -> list[tuple[int, int]]:
    return [(start, min(size - 1, start + chunk_bytes - 1)) for start in range(0, size, chunk_bytes)]


def part_path(directory: Path, start: int, end: int) -> Path:
    return directory / f"{start:012d}-{end:012d}.part"


def download_part(url: str, directory: Path, start: int, end: int) -> Path:
    target = part_path(directory, start, end)
    expected = end - start + 1
    if target.exists() and target.stat().st_size == expected:
        return target
    if target.exists():
        target.unlink()
    with request(url, headers={"Range": f"bytes={start}-{end}"}) as response, target.open("wb") as handle:
        remaining = expected
        while remaining:
            chunk = response.read(min(1 << 20, remaining))
            if not chunk:
                break
            handle.write(chunk)
            remaining -= len(chunk)
    if target.stat().st_size != expected:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Incomplete range {start}-{end}: expected {expected} bytes.")
    return target


def assemble(parts: list[tuple[int, int]], directory: Path, output: Path) -> str:
    temporary = output.with_suffix(output.suffix + ".assembling")
    digest = hashlib.sha256()
    with temporary.open("wb") as destination:
        for start, end in parts:
            path = part_path(directory, start, end)
            with path.open("rb") as source:
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
    output = args.output.resolve()
    parts_directory = output.with_suffix(output.suffix + ".parts")
    output.parent.mkdir(parents=True, exist_ok=True)
    parts_directory.mkdir(parents=True, exist_ok=True)
    ranges = byte_ranges(remote.bytes, args.chunk_mib * 1024 * 1024)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(download_part, remote.url, parts_directory, start, end) for start, end in ranges]
        for future in futures:
            future.result()
    sha256 = assemble(ranges, parts_directory, output)
    if output.stat().st_size != remote.bytes:
        raise RuntimeError("Assembled output length does not match remote Content-Length.")
    record = {
        "schema_version": "plant_cellfm_gse270140_acquisition_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "GSE270140",
        "role": "external expert-label candidate; never a frozen-corpus training input",
        "remote": asdict(remote),
        "output": str(output.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256,
        "workers": args.workers,
        "chunk_mib": args.chunk_mib,
        "claim_boundary": "Acquisition alone does not establish an external benchmark. Expert labels, an ontology mapping and the frozen checkpoint must be audited before any score is reported.",
    }
    record_path = ROOT / "release_metadata" / "gse270140_external_acquisition_v1.json"
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if not args.keep_parts:
        for start, end in ranges:
            part_path(parts_directory, start, end).unlink(missing_ok=True)
        parts_directory.rmdir()
    print(json.dumps({"output": record["output"], "bytes": remote.bytes, "sha256": sha256}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
