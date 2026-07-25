from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_URL = "https://scplantannotate.missouri.edu/"
USER_AGENT = "SnowLotus-CellFM scPlantAnnotate audit/0.1"
DEFAULT_ENDPOINT_PROBES = [
    "/api/organisms/api/organism_query/",
    "/api/predictors/api/predictor_query_public/",
    "/api/jobs/api/job_annotate_and_plot_query/",
]
ASSET_RE = re.compile(r"""(?:src|href)=["']([^"']+)["']""", re.IGNORECASE)
IMPORT_RE = re.compile(r"""(?:from\s+|import\s*\()["']([^"']+)["']""")
URL_RE = re.compile(r"""["']((?:https?://|/)[^"']{2,220})["']""")
KEYWORD_RE = re.compile(
    r"\b(api|axios|fetch|formdata|upload|predict|annotat|result|download|csv|h5ad|mtx)\b",
    re.IGNORECASE,
)


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int | None
    content_type: str
    bytes_read: int
    error: str
    text_excerpt: str


def fetch_text(url: str, timeout: int, max_bytes: int) -> tuple[FetchResult, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read(max_bytes)
            content_type = response.headers.get("content-type", "")
            text = data.decode("utf-8", errors="replace")
            return (
                FetchResult(
                    url=url,
                    final_url=response.geturl(),
                    status=response.status,
                    content_type=content_type,
                    bytes_read=len(data),
                    error="",
                    text_excerpt=text[:1000],
                ),
                text,
            )
    except urllib.error.HTTPError as exc:  # pragma: no cover - network errors are environment-specific
        data = exc.read(max_bytes)
        text = data.decode("utf-8", errors="replace")
        return (
            FetchResult(
                url=url,
                final_url=exc.geturl(),
                status=exc.code,
                content_type=exc.headers.get("content-type", ""),
                bytes_read=len(data),
                error=f"HTTPError: {exc.reason}",
                text_excerpt=text[:1000],
            ),
            text,
        )
    except Exception as exc:  # pragma: no cover - network errors are environment-specific
        return (
            FetchResult(
                url=url,
                final_url="",
                status=None,
                content_type="",
                bytes_read=0,
                error=f"{type(exc).__name__}: {exc}",
                text_excerpt="",
            ),
            "",
        )


def normalize_asset(base_url: str, value: str) -> str:
    value = html.unescape(value)
    if value.startswith("data:") or value.startswith("#"):
        return ""
    return urllib.parse.urljoin(base_url, value)


def same_origin(url: str, base_url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    base = urllib.parse.urlparse(base_url)
    return (parsed.scheme, parsed.netloc) == (base.scheme, base.netloc)


def discover_assets(base_url: str, root_text: str) -> list[str]:
    assets: set[str] = set()
    for match in ASSET_RE.findall(root_text):
        asset = normalize_asset(base_url, match)
        if asset and same_origin(asset, base_url):
            assets.add(asset)
    return sorted(assets)


def discover_imports(base_url: str, asset_url: str, text: str) -> list[str]:
    imports: set[str] = set()
    for match in IMPORT_RE.findall(text):
        if match.startswith(".") or match.startswith("/"):
            imported = normalize_asset(asset_url, match)
            if imported and same_origin(imported, base_url):
                imports.add(imported)
    return sorted(imports)


def scan_text(text: str) -> dict[str, Any]:
    url_literals = sorted(set(URL_RE.findall(text)))[:100]
    keyword_lines = []
    for line in text.splitlines():
        if KEYWORD_RE.search(line):
            cleaned = re.sub(r"\s+", " ", line.strip())
            if cleaned:
                keyword_lines.append(cleaned[:300])
        if len(keyword_lines) >= 80:
            break
    return {
        "url_literals": url_literals,
        "keyword_line_count": len(keyword_lines),
        "keyword_lines": keyword_lines,
    }


def likely_batch_api(url_literals: list[str], keyword_lines: list[str]) -> bool:
    combined = "\n".join(url_literals + keyword_lines).lower()
    apiish = any(token in combined for token in ["/api", "fetch(", "axios", "formdata"])
    actionish = any(token in combined for token in ["upload", "predict", "annotat", "submit"])
    return apiish and actionish


def probe_endpoint(base_url: str, endpoint: str, timeout: int, max_bytes: int) -> dict[str, Any]:
    url = urllib.parse.urljoin(base_url, endpoint)
    result, _ = fetch_text(url, timeout, max_bytes)
    return {
        **asdict(result),
        "endpoint": endpoint,
        "anonymous_accessible": result.status is not None and 200 <= result.status < 300,
        "authentication_required": result.status in {401, 403}
        or "Authentication credentials were not provided" in result.text_excerpt,
    }


def build_audit(
    base_url: str,
    *,
    timeout: int = 20,
    max_bytes: int = 2_000_000,
    max_assets: int = 40,
    max_endpoints: int = 20,
) -> dict[str, Any]:
    root_fetch, root_text = fetch_text(base_url, timeout, max_bytes)
    assets = discover_assets(root_fetch.final_url or base_url, root_text)
    queue = assets[:max_assets]
    fetched_assets: list[dict[str, Any]] = []
    seen = set(queue)
    index = 0
    while index < len(queue) and len(fetched_assets) < max_assets:
        asset = queue[index]
        index += 1
        result, text = fetch_text(asset, timeout, max_bytes)
        scan = scan_text(text)
        fetched_assets.append({**asdict(result), "scan": scan})
        if len(seen) < max_assets:
            for imported in discover_imports(base_url, asset, text):
                if imported not in seen:
                    seen.add(imported)
                    queue.append(imported)
    all_url_literals: list[str] = []
    all_keyword_lines: list[str] = []
    for item in fetched_assets:
        all_url_literals.extend(item["scan"]["url_literals"])
        all_keyword_lines.extend(item["scan"]["keyword_lines"])
    root_scan = scan_text(root_text)
    all_url_literals.extend(root_scan["url_literals"])
    all_keyword_lines.extend(root_scan["keyword_lines"])
    url_literals = sorted(set(all_url_literals))
    keyword_lines = sorted(set(all_keyword_lines))
    batch_api = likely_batch_api(url_literals, keyword_lines)
    endpoint_candidates = sorted(
        {
            value
            for value in url_literals
            if value.startswith("/api/")
            and any(token in value for token in ["organism", "predictor", "job_annotate", "job_inference"])
        }
    )
    endpoint_probe_targets = sorted(set(DEFAULT_ENDPOINT_PROBES + endpoint_candidates))[:max_endpoints]
    endpoint_probes = [
        probe_endpoint(base_url, endpoint, timeout=timeout, max_bytes=20_000)
        for endpoint in endpoint_probe_targets
    ]
    anonymous_api_accessible = any(item["anonymous_accessible"] for item in endpoint_probes)
    auth_required_count = sum(1 for item in endpoint_probes if item["authentication_required"])
    return {
        "base_url": base_url,
        "summary": {
            "web_server_reachable": root_fetch.status is not None and 200 <= root_fetch.status < 400,
            "root_status": root_fetch.status,
            "asset_count": len(assets),
            "fetched_asset_count": len(fetched_assets),
            "api_or_upload_terms_detected": bool(keyword_lines),
            "batch_api_detected": batch_api,
            "endpoint_probe_count": len(endpoint_probes),
            "anonymous_api_accessible": anonymous_api_accessible,
            "auth_required_endpoint_count": auth_required_count,
            "comparison_ready": batch_api and anonymous_api_accessible,
        },
        "root": {**asdict(root_fetch), "scan": root_scan},
        "assets": fetched_assets,
        "endpoint_probes": endpoint_probes,
        "discovered_assets": assets,
        "url_literals": url_literals[:200],
        "keyword_lines": keyword_lines[:120],
        "interpretation": (
            "A reachable web front end and discoverable API route are not enough for "
            "a reproducible benchmark if the routes require an authenticated session. "
            "SnowLotus-CellFM should keep scPlantAnnotate comparison missing unless "
            "valid credentials, a scriptable guest API, a CLI, official model weights, "
            "or an author-provided result export path is available."
        ),
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# scPlantAnnotate Access Audit",
        "",
        f"- Base URL: `{payload['base_url']}`",
        f"- Web server reachable: `{summary['web_server_reachable']}`",
        f"- Root HTTP status: `{summary['root_status']}`",
        f"- Assets discovered: `{summary['asset_count']}`",
        f"- Assets fetched: `{summary['fetched_asset_count']}`",
        f"- API/upload terms detected: `{summary['api_or_upload_terms_detected']}`",
        f"- Scriptable batch API detected: `{summary['batch_api_detected']}`",
        f"- Endpoint probes: `{summary['endpoint_probe_count']}`",
        f"- Anonymous API accessible: `{summary['anonymous_api_accessible']}`",
        f"- Auth-required endpoint count: `{summary['auth_required_endpoint_count']}`",
        f"- Reproducible comparison ready: `{summary['comparison_ready']}`",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
        "## Candidate URL Literals",
        "",
    ]
    if payload["url_literals"]:
        lines.extend(f"- `{value}`" for value in payload["url_literals"][:40])
    else:
        lines.append("- None detected.")
    lines.extend(["", "## Endpoint Probes", ""])
    if payload["endpoint_probes"]:
        lines.extend(
            "- `{endpoint}` status `{status}` anonymous `{anonymous}` auth_required `{auth}`".format(
                endpoint=item["endpoint"],
                status=item["status"],
                anonymous=item["anonymous_accessible"],
                auth=item["authentication_required"],
            )
            for item in payload["endpoint_probes"]
        )
    else:
        lines.append("- None.")
    lines.extend(["", "## Keyword Lines", ""])
    if payload["keyword_lines"]:
        lines.extend(f"- `{value}`" for value in payload["keyword_lines"][:40])
    else:
        lines.append("- None detected.")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit scPlantAnnotate web access for reproducible benchmarking.")
    parser.add_argument("--base-url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--max-bytes", type=int, default=500_000)
    parser.add_argument("--max-assets", type=int, default=12)
    parser.add_argument("--max-endpoints", type=int, default=8)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = build_audit(
        args.base_url,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
        max_assets=args.max_assets,
        max_endpoints=args.max_endpoints,
    )
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
