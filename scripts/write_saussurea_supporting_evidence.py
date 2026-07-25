from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ACCESSION_RE = re.compile(r"\b(PRJNA\d+|PRJEB\d+|PRJDB\d+|SRP\d+|SRX\d+|SRR\d+)\b")
SAUSSUREA_CLOSE_GENUS_RE = re.compile(r"^(saussurea|dolomiaea)\b", re.IGNORECASE)
MAX_DISCOVERED_SPECIES_WITHOUT_PRIMARY_SNOW_LOTUS = 50
SAUSSUREA_DISCOVERY_RE = re.compile(r"(saussurea|snow lotus|天山雪莲|雪莲)", re.IGNORECASE)


@dataclass
class SaussureaEvidence:
    dataset_id: str
    species: str
    scope: str
    data_type: str
    priority: str
    accession_or_doi: str
    source_url: str
    role: str
    status: str
    runinfo_files: str
    run_count: int
    scientific_names: str
    library_strategies: str
    library_sources: str
    total_size_mb: float
    source_page_present: bool


def read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def accession_tokens(value: str) -> list[str]:
    return sorted(set(ACCESSION_RE.findall(value or "")))


def read_runinfo(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1", newline="") as handle:
            rows = list(csv.DictReader(handle))
    if rows and "Run" not in rows[0] and len(rows) == 1:
        return []
    return rows


def summarize_runinfos(project_dir: Path, accessions: list[str]) -> dict[str, Any]:
    runinfo_dir = project_dir / "data" / "public" / "sra_runinfo"
    files = [runinfo_dir / f"{accession}.runinfo.csv" for accession in accessions]
    files = [path for path in files if path.exists()]
    rows: list[dict[str, str]] = []
    for path in files:
        rows.extend(read_runinfo(path))
    total_size_mb = 0.0
    for row in rows:
        try:
            total_size_mb += float(row.get("size_MB") or 0)
        except ValueError:
            continue
    return {
        "files": files,
        "run_count": len(rows),
        "scientific_names": sorted({row.get("ScientificName", "") for row in rows if row.get("ScientificName")}),
        "library_strategies": sorted(
            {row.get("LibraryStrategy", "") for row in rows if row.get("LibraryStrategy")}
        ),
        "library_sources": sorted({row.get("LibrarySource", "") for row in rows if row.get("LibrarySource")}),
        "total_size_mb": round(total_size_mb, 3),
    }


def close_saussurea_names(scientific_names: list[str]) -> list[str]:
    return sorted({name for name in scientific_names if SAUSSUREA_CLOSE_GENUS_RE.search(name)})


def is_primary_snow_lotus_name(scientific_names: list[str]) -> bool:
    return any(name.lower() == "saussurea involucrata" for name in scientific_names)


def keep_discovered_runinfo_candidate(runinfo: dict[str, Any]) -> bool:
    scientific_names = runinfo["scientific_names"]
    close_names = close_saussurea_names(scientific_names)
    if not close_names:
        return False
    if (
        len(scientific_names) > MAX_DISCOVERED_SPECIES_WITHOUT_PRIMARY_SNOW_LOTUS
        and not is_primary_snow_lotus_name(close_names)
    ):
        return False
    return True


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [path for path in root.glob(pattern) if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def discovery_candidate_rows(project_dir: Path, known_accessions: set[str]) -> list[dict[str, str]]:
    discovery = latest_file(project_dir / "data" / "public_discovery", "ncbi_discovery_*.tsv")
    if discovery is None:
        return []
    rows = []
    for row in read_manifest(discovery):
        text = " ".join(
            row.get(key, "")
            for key in [
                "accession",
                "title",
                "organism",
                "summary",
                "matched_queries",
                "recommended_action",
                "url",
            ]
        )
        accessions = accession_tokens(f"{row.get('accession', '')} {row.get('url', '')}")
        if not accessions or any(accession in known_accessions for accession in accessions):
            continue
        priority = (row.get("priority") or "").upper()
        if priority not in {"S", "A", "B"}:
            continue
        if not SAUSSUREA_DISCOVERY_RE.search(text):
            continue
        rows.append(row)
    return rows


def discovered_evidence(project_dir: Path, known_accessions: set[str]) -> list[SaussureaEvidence]:
    evidence: list[SaussureaEvidence] = []
    seen: set[str] = set()
    for row in discovery_candidate_rows(project_dir, known_accessions):
        for accession in accession_tokens(f"{row.get('accession', '')} {row.get('url', '')}"):
            if accession in seen or accession in known_accessions:
                continue
            seen.add(accession)
            runinfo = summarize_runinfos(project_dir, [accession])
            if runinfo["run_count"] == 0:
                continue
            if not keep_discovered_runinfo_candidate(runinfo):
                continue
            dataset_id = f"saussurea_discovered_{accession.lower()}"
            source_page = project_dir / "data" / "public" / "source_pages" / f"{dataset_id}.html"
            scientific_names = close_saussurea_names(runinfo["scientific_names"]) or [
                row.get("organism", "")
            ]
            data_type = ";".join(runinfo["library_strategies"]) or "supporting omics"
            evidence.append(
                SaussureaEvidence(
                    dataset_id=dataset_id,
                    species=";".join(name for name in scientific_names if name),
                    scope="public discovery candidate",
                    data_type=data_type,
                    priority=row.get("priority", ""),
                    accession_or_doi=accession,
                    source_url=row.get("url", ""),
                    role=(
                        "Automatically discovered Saussurea/Snow Lotus supporting omics runinfo; "
                        "use as secondary evidence until manually curated into the public manifest."
                    ),
                    status="discovered_runinfo_candidate",
                    runinfo_files=";".join(
                        path.relative_to(project_dir).as_posix() for path in runinfo["files"]
                    ),
                    run_count=runinfo["run_count"],
                    scientific_names=";".join(runinfo["scientific_names"]),
                    library_strategies=";".join(runinfo["library_strategies"]),
                    library_sources=";".join(runinfo["library_sources"]),
                    total_size_mb=runinfo["total_size_mb"],
                    source_page_present=source_page.exists() and source_page.stat().st_size > 0,
                )
            )
    return evidence


def build_evidence(project_dir: Path) -> list[SaussureaEvidence]:
    manifest = project_dir / "data" / "public_dataset_manifest.tsv"
    rows = [
        row
        for row in read_manifest(manifest)
        if row.get("dataset_id", "").startswith("saussurea_")
        and row.get("dataset_id") != "saussurea_involucrata_private"
    ]
    evidence: list[SaussureaEvidence] = []
    known_accessions: set[str] = set()
    for row in rows:
        dataset_id = row.get("dataset_id", "")
        accessions = accession_tokens(
            f"{row.get('accession_or_doi', '')} {row.get('source_url', '')}"
        )
        known_accessions.update(accessions)
        runinfo = summarize_runinfos(project_dir, accessions)
        source_page = project_dir / "data" / "public" / "source_pages" / f"{dataset_id}.html"
        evidence.append(
            SaussureaEvidence(
                dataset_id=dataset_id,
                species=row.get("species", ""),
                scope=row.get("tissue_or_scope", ""),
                data_type=row.get("data_type", ""),
                priority=row.get("priority", ""),
                accession_or_doi=row.get("accession_or_doi", ""),
                source_url=row.get("source_url", ""),
                role=row.get("why_use", ""),
                status=row.get("status", ""),
                runinfo_files=";".join(
                    path.relative_to(project_dir).as_posix() for path in runinfo["files"]
                ),
                run_count=runinfo["run_count"],
                scientific_names=";".join(runinfo["scientific_names"]),
                library_strategies=";".join(runinfo["library_strategies"]),
                library_sources=";".join(runinfo["library_sources"]),
                total_size_mb=runinfo["total_size_mb"],
                source_page_present=source_page.exists() and source_page.stat().st_size > 0,
            )
        )
    evidence.extend(discovered_evidence(project_dir, known_accessions))
    return evidence


def write_json(evidence: list[SaussureaEvidence], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([asdict(item) for item in evidence], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def table_cell(value: str, max_chars: int = 240) -> str:
    text = str(value or "").replace("|", "/").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def write_markdown(evidence: list[SaussureaEvidence], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows_with_runinfo = sum(1 for item in evidence if item.run_count > 0)
    source_pages = sum(1 for item in evidence if item.source_page_present)
    total_runs = sum(item.run_count for item in evidence)
    total_size_mb = sum(item.total_size_mb for item in evidence)
    lines = [
        "# Saussurea Supporting Evidence",
        "",
        f"- Supporting Saussurea evidence layers: `{len(evidence)}`",
        f"- Layers with SRA runinfo: `{rows_with_runinfo}`",
        f"- Source pages archived: `{source_pages}`",
        f"- SRA runs indexed: `{total_runs}`",
        f"- Total indexed SRA size: `{total_size_mb:.3f} MB`",
        "",
        "This file documents public Snow Lotus and close-genus evidence used for gene-vocabulary, orthology, stress-response, and secondary-metabolism context. It does not replace the required primary `data/saussurea_involucrata.h5ad` single-cell dataset.",
        "",
        "| Dataset | Species | Scope | Type | Accession | Runinfo runs | Strategies | Sources | Source page | Role |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for item in evidence:
        lines.append(
            "| {dataset} | {species} | {scope} | {data_type} | {accession} | {runs} | {strategies} | {sources} | {source_page} | {role} |".format(
                dataset=table_cell(item.dataset_id, 120),
                species=table_cell(item.species),
                scope=table_cell(item.scope),
                data_type=table_cell(item.data_type),
                accession=table_cell(item.accession_or_doi, 120),
                runs=item.run_count,
                strategies=table_cell(item.library_strategies, 160),
                sources=table_cell(item.library_sources, 160),
                source_page=item.source_page_present,
                role=table_cell(item.role),
            )
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Saussurea supporting evidence report")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    evidence = build_evidence(args.project_dir)
    write_markdown(evidence, args.output_md)
    write_json(evidence, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
