from __future__ import annotations

import argparse
import html
import re
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = "SnowLotus-CellFM/0.1 public-data-collector"


def geo_sample_url(filename: str) -> str:
    sample_accession = filename.split("_", 1)[0]
    sample_bucket = f"{sample_accession[:-3]}nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/samples/{sample_bucket}/{sample_accession}/suppl/{filename}"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def normalize_href(href: str) -> tuple[str, str] | None:
    href = html.unescape(urllib.parse.unquote(href))
    parsed = urllib.parse.urlparse(href)
    query = urllib.parse.parse_qs(parsed.query)
    file_param = query.get("file", [""])[0]
    filename = Path(file_param or parsed.path).name
    if not filename:
        return None
    if href.startswith("//"):
        url = "https:" + href
    elif href.startswith("/"):
        url = "https://www.ncbi.nlm.nih.gov" + href
    elif href.startswith("ftp://ftp.ncbi.nlm.nih.gov/"):
        url = "https://" + href.removeprefix("ftp://")
    elif href.startswith(("http://", "https://")):
        url = href
    elif filename.startswith("GSM"):
        url = geo_sample_url(filename)
    else:
        return None
    return url, filename


def discover_urls(accession: str, pattern: str) -> list[tuple[str, str]]:
    accession = accession.upper()
    page = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
    text = fetch_text(page)
    regex = re.compile(pattern)
    seen: set[str] = set()
    urls: list[tuple[str, str]] = []
    for href in re.findall(r"href=['\"]([^'\"]+)['\"]", text):
        normalized = normalize_href(href)
        if normalized is None:
            continue
        url, filename = normalized
        if regex.search(filename) and filename not in seen:
            seen.add(filename)
            urls.append((url, filename))
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover downloadable GEO supplementary URLs from a GEO page")
    parser.add_argument("--accession", required=True)
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    urls = discover_urls(args.accession, args.pattern)
    if args.max_files is not None:
        urls = urls[: args.max_files]
    if not urls:
        raise SystemExit(f"no GEO page files matched pattern: {args.pattern}")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(f"{url}\t{filename}" for url, filename in urls) + "\n",
        encoding="utf-8",
    )
    print(output)
    for url, filename in urls:
        print(f"{filename}\t{url}")


if __name__ == "__main__":
    main()
