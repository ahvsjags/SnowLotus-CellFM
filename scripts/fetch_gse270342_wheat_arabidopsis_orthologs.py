from __future__ import annotations

"""Build an author-resource-pinned wheat-to-Arabidopsis map for GSE270342.

GSE270342 quantifies wheat genes using IWGSC v2.1-style identifiers ending in
``03G``. Current Ensembl Plants BioMart uses a non-intersecting identifier
release, so direct identifier matching is invalid for this atlas. The
associated study publishes the orthogroup table used by its own cross-species
annotation workflow. This script derives every wheat-to-Arabidopsis relationship
within those published orthogroups, retaining the many-to-many structure for
audit and a deterministic first target for the Plant-CellFM loader.
"""

import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENES = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse270342"
    / "seurat_export"
    / "GSE270342_seuratObj_for_publication"
    / "genes.txt"
)
DEFAULT_OUTPUT = ROOT / "data" / "orthologs" / "gse270342_wheat_to_arabidopsis_author_orthogroups.tsv"
DEFAULT_RECORD = ROOT / "release_metadata" / "gse270342_wheat_ortholog_map_v1.json"
AUTHOR_REPOSITORY = "VIB-PSB/wheat_root_atlas"
AUTHOR_BRANCH = "main"
AUTHOR_PATH = "GRN_regulon_analysis/input/orthogroups.csv"
AUTHOR_RAW_URL = f"https://raw.githubusercontent.com/{AUTHOR_REPOSITORY}/{AUTHOR_BRANCH}/{AUTHOR_PATH}"
AUTHOR_CONTENT_API = f"https://api.github.com/repos/{AUTHOR_REPOSITORY}/contents/{AUTHOR_PATH}?ref={AUTHOR_BRANCH}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Plant-CellFM/0.1 ortholog-contract"})
    with urlopen(request, timeout=300) as response:
        return response.read()


def load_author_orthogroups(payload: bytes) -> pd.DataFrame:
    table = pd.read_csv(io.BytesIO(payload), sep="\t", dtype=str).fillna("")
    required = {"gene_id", "species", "gf_id"}
    if not required.issubset(table.columns):
        raise ValueError(f"Author orthogroup table is missing columns: {sorted(required - set(table.columns))}")
    return table.loc[:, ["gene_id", "species", "gf_id"]]


def build_map(source_genes: pd.Series, orthogroups: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    source_set = set(source_genes.astype(str))
    wheat = orthogroups.loc[orthogroups["species"].eq("tae"), ["gene_id", "gf_id"]].rename(
        columns={"gene_id": "source_gene", "gf_id": "orthogroup_id"}
    )
    arabidopsis = orthogroups.loc[orthogroups["species"].eq("ath"), ["gene_id", "gf_id"]].rename(
        columns={"gene_id": "target_gene", "gf_id": "orthogroup_id"}
    )
    observed_wheat = wheat.loc[wheat["source_gene"].isin(source_set)].copy()
    mapping = observed_wheat.merge(arabidopsis, on="orthogroup_id", how="inner", validate="many_to_many")
    mapping["source_species"] = "Triticum aestivum"
    mapping["target_species"] = "Arabidopsis thaliana"
    mapping["mapping_evidence"] = "author_custom_plaza_orthogroup"
    mapping = mapping.loc[
        :,
        ["source_gene", "target_gene", "orthogroup_id", "source_species", "target_species", "mapping_evidence"],
    ].drop_duplicates()
    mapping = mapping.sort_values(
        ["source_gene", "orthogroup_id", "target_gene"], kind="mergesort"
    ).reset_index(drop=True)
    if mapping.empty:
        raise ValueError("No GSE270342 source genes have Arabidopsis targets in the author-published orthogroups.")
    return mapping, {
        "source_gene_count": int(len(source_genes)),
        "source_genes_in_author_orthogroups": int(observed_wheat["source_gene"].nunique()),
        "source_genes_with_arabidopsis_target": int(mapping["source_gene"].nunique()),
    }


def fetch_content_metadata() -> dict[str, object]:
    return json.loads(fetch(AUTHOR_CONTENT_API).decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genes", type=Path, default=DEFAULT_GENES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--source-url", default=AUTHOR_RAW_URL)
    args = parser.parse_args()

    genes_path = args.genes.resolve()
    output = args.output.resolve()
    record_path = args.record.resolve()
    genes = pd.read_csv(genes_path, header=None, names=["source_gene"], dtype=str)["source_gene"].fillna("")
    if genes.duplicated().any() or not genes.astype(str).str.strip().all():
        raise ValueError("The source gene list must be non-empty and unique.")

    content_metadata = fetch_content_metadata()
    payload = fetch(args.source_url)
    orthogroups = load_author_orthogroups(payload)
    mapping, counts = build_map(genes, orthogroups)
    output.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(output, sep="\t", index=False)
    priority = mapping.drop_duplicates("source_gene", keep="first")
    record = {
        "schema_version": "plant_cellfm_gse270342_wheat_to_arabidopsis_author_orthogroup_map_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset": "GSE270342",
            "gene_list": str(genes_path.relative_to(ROOT)).replace("\\", "/"),
            "gene_list_sha256": sha256(genes_path),
            "provider": "VIB-PSB/wheat_root_atlas author repository",
            "repository": AUTHOR_REPOSITORY,
            "branch": AUTHOR_BRANCH,
            "path": AUTHOR_PATH,
            "raw_url": args.source_url,
            "github_blob_sha": content_metadata.get("sha"),
            "download_sha256": hashlib.sha256(payload).hexdigest(),
            "source_identifier_contract": "IWGSC v2.1 style wheat gene identifiers used by GSE270342",
        },
        "output": {
            "path": str(output.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(output),
            "all_relationships": int(len(mapping)),
            "source_gene_coverage_in_author_orthogroups": (
                counts["source_genes_in_author_orthogroups"] / counts["source_gene_count"]
            ),
            "source_gene_coverage_with_arabidopsis_target": (
                counts["source_genes_with_arabidopsis_target"] / counts["source_gene_count"]
            ),
            "source_genes": counts["source_gene_count"],
            "source_genes_in_author_orthogroups": counts["source_genes_in_author_orthogroups"],
            "source_genes_with_arabidopsis_target": counts["source_genes_with_arabidopsis_target"],
            "deterministic_first_target_count": int(len(priority)),
            "orthogroup_count_used": int(mapping["orthogroup_id"].nunique()),
            "target_gene_count": int(mapping["target_gene"].nunique()),
        },
        "claim_boundary": (
            "This mapping is derived from the author-published custom PLAZA orthogroups used in the associated "
            "cross-species annotation workflow. It preserves many-to-many relationships in the audit table; the "
            "Plant-CellFM loader deterministically collapses to the lexicographically first Arabidopsis target per "
            "wheat source gene. It is not a one-to-one identifier conversion, independent external validation, or "
            "a complete plant orthology resource."
        ),
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["output"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
