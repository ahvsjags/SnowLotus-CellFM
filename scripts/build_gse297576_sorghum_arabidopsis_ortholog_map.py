from __future__ import annotations

"""Build a source-pinned Sorghum-to-Arabidopsis map for GSE297576.

The GSE297576 author Seurat object uses Sorghum bicolor RTx430 gene IDs.
This script retains every published Sorghum--Arabidopsis relation in the
authors' 10-species orthogroup table, then orders the table deterministically.
Plant-CellFM's inference loader records its first-target projection separately;
the full many-to-many table remains the auditable primary artifact.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import anndata as ad
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATLAS = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse297576_bicolor_root"
    / "GSE297576_bicolor_root_author_atlas.h5ad"
)
DEFAULT_ORTHOGROUPS = (
    ROOT
    / "tmp"
    / "plant-multidap-and-single-cell"
    / "dapseq"
    / "orthogroup_tables"
    / "10sp_orthology_table.tsv"
)
DEFAULT_OUTPUT = ROOT / "data" / "orthologs" / "gse297576_sorghum_to_arabidopsis_author_orthogroups.tsv"
DEFAULT_RECORD = ROOT / "release_metadata" / "gse297576_sorghum_ortholog_map_v1.json"
JGI_REPOSITORY = "https://code.jgi.doe.gov/LBaumgart/plant-multidap-and-single-cell"
JGI_COMMIT = "8a7e6cccb12ea45c32f8e42c75b439106ca22ffb"
JGI_TABLE_PATH = "dapseq/orthogroup_tables/10sp_orthology_table.tsv"
SOURCE_SPECIES = "Sorghum_bicolor_RTx430"
TARGET_SPECIES = "Arabidopsis_thaliana_Col-0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_orthogroups(path: Path) -> pd.DataFrame:
    table = pd.read_csv(path, sep="\t", dtype=str).fillna("")
    required = {"species", "orthogroup", "gene"}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"Orthogroup table is missing required columns: {sorted(missing)}")
    return table.loc[:, ["species", "orthogroup", "gene"]]


def build_map(source_genes: pd.Index, orthogroups: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    source = orthogroups.loc[
        orthogroups["species"].eq(SOURCE_SPECIES), ["gene", "orthogroup"]
    ].rename(columns={"gene": "source_gene", "orthogroup": "orthogroup_id"})
    target = orthogroups.loc[
        orthogroups["species"].eq(TARGET_SPECIES), ["gene", "orthogroup"]
    ].rename(columns={"gene": "target_gene", "orthogroup": "orthogroup_id"})
    observed_source = source.loc[source["source_gene"].isin(set(source_genes.astype(str)))].copy()
    mapping = observed_source.merge(target, on="orthogroup_id", how="inner", validate="many_to_many")
    mapping["source_species"] = "Sorghum bicolor"
    mapping["target_species"] = "Arabidopsis thaliana"
    mapping["mapping_evidence"] = "GSE297576_author_JGI_10sp_orthogroup"
    mapping = (
        mapping.loc[
            :,
            [
                "source_gene",
                "target_gene",
                "orthogroup_id",
                "source_species",
                "target_species",
                "mapping_evidence",
            ],
        ]
        .drop_duplicates()
        .sort_values(["source_gene", "orthogroup_id", "target_gene"], kind="mergesort")
        .reset_index(drop=True)
    )
    if mapping.empty:
        raise ValueError("No observed Sorghum features have Arabidopsis targets in the author orthogroups.")
    return mapping, {
        "source_gene_count": int(len(source_genes)),
        "source_genes_in_author_orthogroups": int(observed_source["source_gene"].nunique()),
        "source_genes_with_arabidopsis_target": int(mapping["source_gene"].nunique()),
        "mapping_relationship_count": int(len(mapping)),
        "arabidopsis_target_gene_count": int(mapping["target_gene"].nunique()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--orthogroups", type=Path, default=DEFAULT_ORTHOGROUPS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = parser.parse_args()

    atlas_path = args.atlas.resolve()
    orthogroups_path = args.orthogroups.resolve()
    output_path = args.output.resolve()
    record_path = args.record.resolve()
    if not atlas_path.is_file() or not orthogroups_path.is_file():
        raise FileNotFoundError("Both the converted atlas and author orthogroup table are required.")

    atlas = ad.read_h5ad(atlas_path, backed="r")
    source_genes = pd.Index(atlas.var_names.astype(str))
    if source_genes.empty or source_genes.has_duplicates:
        raise ValueError("The converted external atlas must provide non-empty unique source features.")
    mapping, counts = build_map(source_genes, load_orthogroups(orthogroups_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(output_path, sep="\t", index=False)

    record = {
        "schema_version": "plant_cellfm_gse297576_sorghum_to_arabidopsis_author_orthogroup_map_v1",
        "status": "AUTHOR_ORTHOGROUP_MAP_BUILT",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset": "GSE297576",
            "atlas": atlas_path.relative_to(ROOT).as_posix(),
            "atlas_sha256": sha256(atlas_path),
            "author_repository": JGI_REPOSITORY,
            "author_commit": JGI_COMMIT,
            "author_table_path": JGI_TABLE_PATH,
            "orthogroups": orthogroups_path.relative_to(ROOT).as_posix(),
            "orthogroups_sha256": sha256(orthogroups_path),
            "source_species_key": SOURCE_SPECIES,
            "target_species_key": TARGET_SPECIES,
        },
        "coverage": {
            **counts,
            "source_genes_in_author_orthogroups_fraction": counts["source_genes_in_author_orthogroups"] / len(source_genes),
            "source_genes_with_arabidopsis_target_fraction": counts["source_genes_with_arabidopsis_target"] / len(source_genes),
        },
        "output": {
            "mapping": output_path.relative_to(ROOT).as_posix(),
            "mapping_sha256": sha256(output_path),
            "ordering": "source_gene, orthogroup_id, target_gene ascending; first row is the declared deterministic loader target",
        },
        "claim_boundary": "The table preserves all author-published many-to-many orthogroup relations. It is an input-provenance and feature-coverage artifact, not evidence of annotation accuracy.",
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "coverage": record["coverage"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
