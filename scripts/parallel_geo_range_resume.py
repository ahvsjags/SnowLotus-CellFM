#!/usr/bin/env python3
"""Resume a GEO object with parallel HTTP Range requests and atomic assembly."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-bytes", required=True, type=int)
    parser.add_argument("--chunk-bytes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--referer", default="https://www.ncbi.nlm.nih.gov/geo/")
    return parser.parse_args()


def download_chunk(
    url: str,
    part: Path,
    start: int,
    end: int,
    referer: str,
) -> Path:
    expected = end - start + 1
    if part.is_file() and part.stat().st_size == expected:
        return part
    partial = part.with_suffix(part.suffix + ".partial")
    partial.unlink(missing_ok=True)
    command = [
        "curl",
        "-L",
        "--fail",
        "--retry",
        "8",
        "--retry-all-errors",
        "--connect-timeout",
        "20",
        "--max-time",
        "7200",
        "-r",
        f"{start}-{end}",
        "-e",
        referer,
        "-A",
        "SnowLotus-CellFM/0.1 public-data-collector",
        "-o",
        str(partial),
        url,
    ]
    subprocess.run(command, check=True)
    received = partial.stat().st_size if partial.exists() else 0
    if received != expected:
        raise RuntimeError(f"short range {start}-{end}: expected {expected}, received {received}")
    partial.replace(part)
    return part


def main() -> int:
    args = parse_args()
    if args.expected_bytes < 1 or args.chunk_bytes < 1 or args.workers < 1:
        raise ValueError("expected-bytes, chunk-bytes, and workers must be positive")
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    current = output.stat().st_size if output.is_file() else 0
    if current > args.expected_bytes:
        raise ValueError(f"existing output is larger than expected: {current} > {args.expected_bytes}")
    if current == args.expected_bytes:
        print(f"already complete: {output} bytes={current}", flush=True)
        return 0

    part_dir = output.parent / f".{output.name}.parts"
    part_dir.mkdir(parents=True, exist_ok=True)
    ranges = []
    start = current
    while start < args.expected_bytes:
        end = min(args.expected_bytes - 1, start + args.chunk_bytes - 1)
        ranges.append((start, end, part_dir / f"{start:012d}-{end:012d}.part"))
        start = end + 1
    print(
        f"resume={current} expected={args.expected_bytes} ranges={len(ranges)} workers={args.workers}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_chunk, args.url, part, start, end, args.referer): (start, end)
            for start, end, part in ranges
        }
        for future in as_completed(futures):
            start, end = futures[future]
            future.result()
            print(f"ready {start}-{end}", flush=True)

    rebuilt = output.with_name(f".{output.name}.rebuild")
    rebuilt.unlink(missing_ok=True)
    with output.open("rb") as source, rebuilt.open("wb") as destination:
        shutil.copyfileobj(source, destination, length=1024 * 1024)
        for start, end, part in ranges:
            expected = end - start + 1
            if part.stat().st_size != expected:
                raise RuntimeError(f"range size changed: {part}")
            with part.open("rb") as handle:
                shutil.copyfileobj(handle, destination, length=1024 * 1024)
    if rebuilt.stat().st_size != args.expected_bytes:
        raise RuntimeError(
            f"assembled output size mismatch: {rebuilt.stat().st_size} != {args.expected_bytes}"
        )
    rebuilt.replace(output)
    shutil.rmtree(part_dir, ignore_errors=True)
    print(f"complete: {output} bytes={output.stat().st_size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
