from __future__ import annotations

"""Build an external-literature concordance audit for the v4 root case.

Canonical markers are defined from primary Arabidopsis root studies before
looking up their ranks in the Plant-CellFM-derived candidate table. This is a
literature-concordance analysis, not wet-lab validation or an independent
single-cell matrix benchmark.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MARKERS = (
    ROOT
    / "figures"
    / "plant_cellfm_submission_v4"
    / "source_data"
    / "plant_cellfm_v4_fig4_arabidopsis_root_candidate_resource_root_marker_candidates.tsv"
)
JSON_OUTPUT = ROOT / "release_metadata" / "arabidopsis_root_literature_concordance_v4.json"
MARKDOWN_OUTPUT = ROOT / "release_metadata" / "arabidopsis_root_literature_concordance_v4.md"

# These are fixed before the candidate lookup. The first source explicitly
# documents COBL9, MYB46 and APL as root-cell-type markers; the second supplies
# the organ-scale root atlas and CASP1 endodermis context.
ANCHORS: tuple[dict[str, str], ...] = (
    {
        "label": "Root hair",
        "marker_symbol": "COBL9",
        "gene": "AT5G49270",
        "literature_identity": "root-hair epidermis",
        "source_key": "jean_baptiste_2019",
    },
    {
        "label": "Non-hair",
        "marker_symbol": "WER",
        "gene": "AT5G14750",
        "literature_identity": "non-hair / atrichoblast epidermis",
        "source_key": "jean_baptiste_2019",
    },
    {
        "label": "Non-hair",
        "marker_symbol": "GL2",
        "gene": "AT1G79840",
        "literature_identity": "non-hair / atrichoblast epidermis",
        "source_key": "jean_baptiste_2019",
    },
    {
        "label": "Root endodermis",
        "marker_symbol": "CASP1",
        "gene": "AT2G36100",
        "literature_identity": "endodermis",
        "source_key": "shahan_2022",
    },
    {
        "label": "Phloem",
        "marker_symbol": "APL",
        "gene": "AT1G79430",
        "literature_identity": "phloem within the stele",
        "source_key": "jean_baptiste_2019",
    },
    {
        "label": "Xylem",
        "marker_symbol": "MYB46",
        "gene": "AT5G12870",
        "literature_identity": "xylem within the stele",
        "source_key": "jean_baptiste_2019",
    },
)

SOURCES: dict[str, dict[str, str]] = {
    "jean_baptiste_2019": {
        "citation": "Jean-Baptiste et al. Dynamics of Gene Expression in Single Root Cells of Arabidopsis thaliana. Plant Cell (2019).",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8516002/",
        "evidence": "Reports high, cluster-specific expression for COBL9 in root hair, MYB46 in xylem, and APL in phloem; also discusses WER and GL2 heterogeneity.",
    },
    "shahan_2022": {
        "citation": "Shahan et al. A single cell Arabidopsis root atlas reveals developmental trajectories in wild-type and cell identity mutants. Developmental Cell (2022).",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9014886/",
        "evidence": "Provides an organ-scale Arabidopsis root atlas with major root branches and literature-supported endodermis marker context including CASP1.",
    },
}


def build_concordance() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not MARKERS.exists():
        raise FileNotFoundError(f"Missing v4 root marker source table: {MARKERS}")
    candidates = pd.read_csv(MARKERS, sep="\t")
    top_n = int(candidates["rank"].max())
    rows: list[dict[str, Any]] = []
    for anchor in ANCHORS:
        match = candidates.loc[
            candidates["label"].eq(anchor["label"]) & candidates["gene"].eq(anchor["gene"])
        ]
        record = {
            **anchor,
            "candidate_top_n": top_n,
            "recovered_in_matching_program": not match.empty,
        }
        if not match.empty:
            result = match.iloc[0]
            record.update(
                {
                    "candidate_rank": int(result["rank"]),
                    "candidate_score": float(result["score"]),
                    "candidate_log2fc": float(result["log2fc"]),
                    "candidate_detection_in": float(result["detection_in"]),
                    "candidate_detection_out": float(result["detection_out"]),
                    "candidate_detection_delta": float(result["detection_delta"]),
                }
            )
        else:
            record.update(
                {
                    "candidate_rank": None,
                    "candidate_score": None,
                    "candidate_log2fc": None,
                    "candidate_detection_in": None,
                    "candidate_detection_out": None,
                    "candidate_detection_delta": None,
                }
            )
        rows.append(record)
    table = pd.DataFrame(rows)
    hits = table.loc[table["recovered_in_matching_program"]].copy()
    summary = {
        "anchors_tested": int(len(table)),
        "candidate_top_n": top_n,
        "matching_program_hits": int(len(hits)),
        "matching_program_hit_rate": float(len(hits) / len(table)),
        "recovered_marker_symbols": hits["marker_symbol"].tolist(),
        "candidate_rows_in_root_case": int(len(candidates)),
        "root_identity_labels": int(candidates["label"].nunique()),
    }
    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_v4_root_literature_concordance_v1",
        "scope": "Predefined canonical Arabidopsis root markers looked up in the Plant-CellFM public-data candidate table.",
        "claim_boundary": "Literature concordance only: it is neither wet-lab validation nor an independent single-cell matrix replication.",
        "candidate_source": MARKERS.relative_to(ROOT).as_posix(),
        "sources": SOURCES,
        "summary": summary,
        "anchors": table.astype(object).where(pd.notna(table), None).to_dict(orient="records"),
    }
    return table, payload


def render_markdown(payload: dict[str, Any], table: pd.DataFrame) -> str:
    summary = payload["summary"]
    lines = [
        "# Arabidopsis Root Literature Concordance Audit",
        "",
        f"- Predefined canonical anchors: **{summary['anchors_tested']}**",
        f"- Candidate-list cutoff per identity: top **{summary['candidate_top_n']}**",
        f"- Matching-identity recovery: **{summary['matching_program_hits']}/{summary['anchors_tested']}** ({summary['matching_program_hit_rate']:.1%})",
        f"- Recovered canonical markers: {', '.join(summary['recovered_marker_symbols'])}",
        "",
        "## Evidence Boundary",
        "",
        "- Canonical loci and cell-identity assignments were fixed from primary literature before inspecting Plant-CellFM candidate ranks.",
        "- A recovered locus demonstrates concordance of a computational candidate program with an established identity marker; an unrecovered locus is not a negative biological result because this audit is limited to the stored top-20 ranking.",
        "- This analysis does not use a new expression matrix, does not test causal function, and does not replace reporter-line or perturbation validation.",
        "",
        "## Anchor Lookup",
        "",
        "| Plant-CellFM identity | Canonical marker | Locus | Candidate rank | log2 fold-change | Detection delta | Source |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in table.itertuples(index=False):
        rank = "not in top 20" if pd.isna(row.candidate_rank) else str(int(row.candidate_rank))
        lfc = "-" if pd.isna(row.candidate_log2fc) else f"{row.candidate_log2fc:.3f}"
        delta = "-" if pd.isna(row.candidate_detection_delta) else f"{row.candidate_detection_delta:.3f}"
        lines.append(
            f"| {row.label} | {row.marker_symbol} | {row.gene} | {rank} | {lfc} | {delta} | {row.source_key} |"
        )
    lines.extend(["", "## Primary Sources", ""])
    for key, source in payload["sources"].items():
        lines.append(f"- `{key}`: {source['citation']} {source['url']}")
    return "\n".join(lines) + "\n"


def write_artifacts() -> dict[str, Any]:
    table, payload = build_concordance()
    JSON_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MARKDOWN_OUTPUT.write_text(render_markdown(payload, table), encoding="utf-8")
    return payload


def main() -> None:
    payload = write_artifacts()
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
