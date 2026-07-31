from __future__ import annotations

"""Prepare a compact external GSE152766 root input for blind model inference."""

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import BinaryIO

import anndata as ad
import pandas as pd
from scipy.io import mmread


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse152766_gsm4626007"
    / "GSM4626007_sc_52_mtx.tar.gz"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse152766_gsm4626007"
    / "GSM4626007_sc_52_spliced_external_root.h5ad"
)
METADATA_OUTPUT = ROOT / "release_metadata" / "gse152766_external_input_acquisition_v4.json"
MARKDOWN_OUTPUT = ROOT / "release_metadata" / "gse152766_external_input_acquisition_v4.md"
SOURCE_URL = "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4626nnn/GSM4626007/suppl/GSM4626007_sc_52_mtx.tar.gz"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_member(archive: tarfile.TarFile, suffix: str) -> BinaryIO:
    matches = [member for member in archive.getmembers() if member.name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one member ending {suffix!r}, found {len(matches)}")
    handle = archive.extractfile(matches[0])
    if handle is None:
        raise ValueError(f"Could not read archive member {matches[0].name}")
    return handle


def build_anndata(archive_path: Path) -> ad.AnnData:
    with tarfile.open(archive_path, "r:gz") as archive:
        matrix = mmread(read_member(archive, "/spliced_counts_filtered/matrix.mtx")).tocsr().transpose().tocsr()
        genes = pd.read_csv(
            io.TextIOWrapper(read_member(archive, "/spliced_counts_filtered/genes.tsv"), encoding="utf-8"),
            sep="\t",
            header=None,
            dtype=str,
        )
        barcodes = pd.read_csv(
            io.TextIOWrapper(read_member(archive, "/spliced_counts_filtered/barcodes.tsv"), encoding="utf-8"),
            sep="\t",
            header=None,
            dtype=str,
        )
    if matrix.shape != (len(barcodes), len(genes)):
        raise ValueError(
            f"Matrix shape {matrix.shape} does not match {len(barcodes)} barcodes and {len(genes)} genes."
        )
    if genes.iloc[:, 0].duplicated().any():
        raise ValueError("GSE152766 input has duplicate gene identifiers in the selected matrix.")
    obs = pd.DataFrame(
        {
            "cell_id": barcodes.iloc[:, 0].astype(str).to_numpy(),
            "species": "Arabidopsis thaliana",
            "tissue": "root",
            "dataset_id": "GSE152766_GSM4626007_external",
            "sample_id": "GSM4626007_sc_52",
        },
        index=barcodes.iloc[:, 0].astype(str).to_numpy(),
    )
    var = pd.DataFrame(index=genes.iloc[:, 0].astype(str).to_numpy())
    var["gene_symbol"] = genes.iloc[:, 1].astype(str).to_numpy() if genes.shape[1] > 1 else var.index
    return ad.AnnData(X=matrix, obs=obs, var=var)


def write_markdown(payload: dict[str, object]) -> str:
    shape = payload["matrix"]
    return "\n".join(
        [
            "# GSE152766 External Root Input Acquisition",
            "",
            f"- Source: `{payload['source_url']}`",
            f"- GEO sample: `{payload['sample_accession']}`",
            f"- Archive SHA256: `{payload['archive_sha256']}`",
            f"- Spliced matrix: `{shape['cells']}` cells x `{shape['genes']}` TAIR10 gene identifiers",
            f"- Prepared input: `{payload['prepared_h5ad']}`",
            "",
            "## Evidence Boundary",
            "",
            "- This is a blinded external input used for inference; its downloaded matrix does not contain expert cell-type labels.",
            "- GSE152766 is absent from the frozen v4 corpus profile dataset IDs. This establishes only non-membership in that documented corpus, not a blanket claim about every historical resource used by all upstream models.",
            "- Any resulting prediction is an external execution and marker-coherence case, not an accuracy benchmark unless expert labels are acquired under a frozen protocol.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a GSE152766 external root input from a GEO MatrixMarket archive.")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output = args.output.resolve()
    if not archive.exists():
        raise FileNotFoundError(f"Missing GEO archive: {archive}")
    adata = build_anndata(archive)
    output.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output)
    corpus = json.loads((ROOT / "figure_data" / "corpus_profile_v1" / "corpus_profile.json").read_text(encoding="utf-8"))
    dataset_profile = pd.read_csv(
        ROOT / "figure_data" / "corpus_profile_v1" / "species_by_dataset.tsv",
        sep="\t",
    )
    frozen_dataset_ids = sorted(dataset_profile["dataset_id"].astype(str).unique().tolist())
    listed_in_profile = any("gse152766" in value.casefold() for value in frozen_dataset_ids)
    payload: dict[str, object] = {
        "schema_version": "plant_cellfm_v4_external_gse152766_input_v1",
        "source_url": SOURCE_URL,
        "series_accession": "GSE152766",
        "sample_accession": "GSM4626007",
        "sample_name": "sc_52",
        "matrix_type": "spliced_counts_filtered",
        "archive_path": archive.relative_to(ROOT).as_posix(),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256(archive),
        "prepared_h5ad": output.relative_to(ROOT).as_posix(),
        "matrix": {"cells": int(adata.n_obs), "genes": int(adata.n_vars), "nonzero_counts": int(adata.X.nnz)},
        "frozen_v4_corpus_profile": corpus,
        "frozen_v4_dataset_ids": frozen_dataset_ids,
        "gse152766_listed_in_frozen_v4_corpus_profile": listed_in_profile,
        "claim_boundary": "Blinded external input preparation only. The archive has no expert cell-type labels and cannot by itself provide an accuracy benchmark.",
    }
    METADATA_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MARKDOWN_OUTPUT.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["matrix"], ensure_ascii=False))


if __name__ == "__main__":
    main()
