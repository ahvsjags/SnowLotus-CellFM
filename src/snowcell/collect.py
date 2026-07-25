from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import urllib.request
from pathlib import Path

USER_AGENT = "SnowLotus-CellFM/0.1 public-data-collector"
FIGSHARE_ARTICLE_PAGES = {
    "20255094": "https://figshare.com/articles/dataset/Single-cell_multi-omics_of_Catharanthus_roseus/20255094"
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def shell_quote(value: str | Path) -> str:
    return shlex.quote(str(value))


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("._") or "source"


def list_figshare_files(article_id: str) -> list[dict]:
    url = f"https://api.figshare.com/v2/articles/{article_id}"
    payload = fetch_json(url)
    return list(payload.get("files", []))


def extract_figshare_article_ids(accession: str, source_url: str) -> list[str]:
    text = f"{accession} {source_url}".strip()
    if "figshare" not in text.lower():
        return []
    return sorted(set(re.findall(r"(?<!\d)(\d{6,})(?!\d)", text)))


def write_figshare_download_script(article_id: str, output: str | Path) -> Path:
    files = list_figshare_files(article_id)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write("mkdir -p data/public/figshare_%s\n" % article_id)
        for item in files:
            name = str(item.get("name", f"file_{item.get('id', 'unknown')}"))
            url = item.get("download_url")
            if not url:
                continue
            target = f"data/public/figshare_{article_id}/{name}"
            handle.write(
                "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
                f"{shell_quote('User-Agent: ' + USER_AGENT)} "
                f"-o {shell_quote(target)} {shell_quote(str(url))}\n"
            )
    return output_path


def write_figshare_fallback_script(article_id: str, output: str | Path, reason: str) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    api_url = f"https://api.figshare.com/v2/articles/{article_id}"
    article_url = FIGSHARE_ARTICLE_PAGES.get(
        article_id, f"https://figshare.com/articles/dataset/{article_id}"
    )
    target_dir = f"data/public/figshare_{article_id}"
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write(f"mkdir -p {shell_quote(target_dir)}\n")
        handle.write(
            "echo "
            f"{shell_quote('Figshare API file listing failed during script generation: ' + reason)}\n"
        )
        handle.write(
            "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
            f"{shell_quote('User-Agent: ' + USER_AGENT)} "
            f"-o {shell_quote(target_dir + '/article_api.json')} {shell_quote(api_url)} || true\n"
        )
        handle.write(
            "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
            f"{shell_quote('User-Agent: ' + USER_AGENT)} "
            f"-o {shell_quote(target_dir + '/article_page.html')} {shell_quote(article_url)} || true\n"
        )
    return output_path


def geo_series_ftp(accession: str) -> str:
    accession = accession.strip().upper()
    if not accession.startswith("GSE"):
        raise ValueError("GEO series accession must start with GSE")
    digits = accession[3:]
    if not digits.isdigit():
        raise ValueError(f"invalid GEO accession: {accession}")
    bucket = f"GSE{digits[:-3]}nnn" if len(digits) > 3 else "GSEnnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{bucket}/{accession}/suppl/"


def write_geo_download_script(accessions: list[str], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write("mkdir -p data/public/geo\n")
        for accession in accessions:
            url = geo_series_ftp(accession)
            target = f"data/public/geo/{accession.upper()}"
            handle.write(f"mkdir -p '{target}'\n")
            handle.write(
                "wget -r -np -nH --cut-dirs=5 --accept '*.h5ad,*.h5,*.h5.gz,*.mtx.gz,"
                "*.tsv.gz,*.txt.gz,*.csv.gz,*.rds,*.RDS,*.loom,*.tar,*.tar.gz' "
                f"-P '{target}' '{url}' || true\n"
            )
    return output_path


def write_geo_filelist_script(accessions: list[str], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write("mkdir -p data/public/geo_filelists\n")
        for accession in accessions:
            accession = accession.upper()
            url = geo_series_ftp(accession)
            target = f"data/public/geo_filelists/{accession}"
            handle.write(f"mkdir -p {shell_quote(target)}\n")
            handle.write(
                "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
                f"{shell_quote('User-Agent: ' + USER_AGENT)} "
                f"-o {shell_quote(target + '/index.html')} {shell_quote(url)} || true\n"
            )
            handle.write(
                "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
                f"{shell_quote('User-Agent: ' + USER_AGENT)} "
                f"-o {shell_quote(target + '/filelist.txt')} "
                f"{shell_quote(url + 'filelist.txt')} || true\n"
            )
    return output_path


def write_sra_runinfo_script(accessions: list[str], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write("mkdir -p data/public/sra_runinfo\n")
        for accession in accessions:
            accession = accession.strip()
            if not accession:
                continue
            url = f"https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc={accession}"
            handle.write(
                "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
                f"{shell_quote('User-Agent: ' + USER_AGENT)} "
                f"-o {shell_quote('data/public/sra_runinfo/' + accession + '.runinfo.csv')} "
                f"{shell_quote(url)} || true\n"
            )
    return output_path


def write_source_provenance_script(
    rows: list[dict[str, str]], output: str | Path
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write("mkdir -p data/public/source_pages\n")
        for row in rows:
            dataset_id = safe_slug(row.get("dataset_id", "dataset"))
            url = (row.get("source_url") or "").strip()
            if not url.lower().startswith(("http://", "https://")):
                continue
            target = f"data/public/source_pages/{dataset_id}.html"
            handle.write(
                "curl -L --retry 5 --connect-timeout 20 --max-time 120 -H "
                f"{shell_quote('User-Agent: ' + USER_AGENT)} "
                f"-o {shell_quote(target)} {shell_quote(url)} || true\n"
            )
    return output_path


def write_direct_download_script(rows: list[dict[str, str]], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        handle.write("mkdir -p data/public/direct_downloads\n")
        for row in rows:
            url = (row.get("source_url") or "").strip()
            if "box.nju.edu.cn" not in url:
                continue
            dataset_id = safe_slug(row.get("dataset_id", "direct_download"))
            download_url = url.replace("op=view", "op=download")
            target = f"data/public/direct_downloads/{dataset_id}.download"
            handle.write(
                "curl -L --retry 5 --connect-timeout 20 --max-time 7200 -H "
                f"{shell_quote('User-Agent: ' + USER_AGENT)} "
                f"-o {shell_quote(target)} {shell_quote(download_url)} || true\n"
            )
    return output_path


def read_manifest_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_manifest_accessions(
    path: str | Path,
) -> tuple[list[str], list[str], list[str], list[dict[str, str]]]:
    geo: list[str] = []
    sra: list[str] = []
    figshare: list[str] = []
    rows = read_manifest_rows(path)
    for row in rows:
        accession = (row.get("accession_or_doi") or "").strip()
        source_url = (row.get("source_url") or "").strip()
        for token in accession.replace("/", " ").split():
            token = token.strip(",;")
            if token.upper().startswith("GSE"):
                geo.append(token.upper())
            elif token.upper().startswith(("PRJNA", "SRP", "SRR", "SRX")):
                sra.append(token.upper())
        figshare.extend(extract_figshare_article_ids(accession, source_url))
    return sorted(set(geo)), sorted(set(sra)), sorted(set(figshare)), rows


def write_manifest_download_scripts(manifest: str | Path, output_dir: str | Path) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    geo, sra, figshare, rows = read_manifest_accessions(manifest)
    paths: list[Path] = []
    paths.append(write_source_provenance_script(rows, output / "download_source_pages.sh"))
    if any("box.nju.edu.cn" in (row.get("source_url") or "") for row in rows):
        paths.append(write_direct_download_script(rows, output / "download_direct_reference_data.sh"))
    if geo:
        paths.append(write_geo_filelist_script(geo, output / "download_geo_filelists.sh"))
        paths.append(write_geo_download_script(geo, output / "download_geo_processed.sh"))
    if sra:
        paths.append(write_sra_runinfo_script(sra, output / "download_sra_runinfo.sh"))
    for article_id in figshare:
        figshare_output = output / f"download_figshare_{article_id}.sh"
        try:
            paths.append(write_figshare_download_script(article_id, figshare_output))
        except Exception as exc:
            paths.append(write_figshare_fallback_script(article_id, figshare_output, repr(exc)))
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SnowCell public data collection helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)
    figshare = subparsers.add_parser("figshare-script")
    figshare.add_argument("--article-id", required=True)
    figshare.add_argument("--output", required=True)
    geo = subparsers.add_parser("geo-script")
    geo.add_argument("--accession", action="append", required=True)
    geo.add_argument("--output", required=True)
    geo_filelist = subparsers.add_parser("geo-filelist-script")
    geo_filelist.add_argument("--accession", action="append", required=True)
    geo_filelist.add_argument("--output", required=True)
    sra = subparsers.add_parser("sra-runinfo-script")
    sra.add_argument("--accession", action="append", required=True)
    sra.add_argument("--output", required=True)
    manifest = subparsers.add_parser("manifest-scripts")
    manifest.add_argument("--manifest", required=True)
    manifest.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    if args.command == "figshare-script":
        print(write_figshare_download_script(args.article_id, args.output))
    elif args.command == "geo-script":
        print(write_geo_download_script(args.accession, args.output))
    elif args.command == "geo-filelist-script":
        print(write_geo_filelist_script(args.accession, args.output))
    elif args.command == "sra-runinfo-script":
        print(write_sra_runinfo_script(args.accession, args.output))
    elif args.command == "manifest-scripts":
        for path in write_manifest_download_scripts(args.manifest, args.output_dir):
            print(path)


if __name__ == "__main__":
    main()
