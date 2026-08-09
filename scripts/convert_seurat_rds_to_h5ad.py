"""Convert a Seurat RDS count assay to a sparse H5AD source.

The converter uses rdata only to read the public serialized object. It keeps
the raw count assay and observation identifiers; author labels are not needed
for strict input materialization and are omitted from the expression source.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import pandas as pd
import rdata
from scipy import sparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assay", default="RNA")
    args = parser.parse_args()
    parsed = rdata.parser.parse_file(str(args.input))
    obj = rdata.conversion.convert(parsed)
    assay = obj.assays[args.assay]
    counts = assay.counts
    shape = tuple(int(value) for value in counts.Dim)
    matrix = sparse.csc_matrix((counts.x, counts.i, counts.p), shape=shape).T.tocsr()
    genes = [str(value) for value in counts.Dimnames[0]]
    cells = [str(value) for value in counts.Dimnames[1]]
    obs = pd.DataFrame(index=pd.Index(cells, dtype=str))
    metadata = getattr(obj, "meta.data", None)
    if isinstance(metadata, pd.DataFrame):
        metadata = metadata.copy()
        metadata.index = metadata.index.astype(str)
        obs = obs.join(metadata, how="left")
    var = pd.DataFrame(index=pd.Index(genes, dtype=str))
    result = ad.AnnData(X=matrix, obs=obs, var=var)
    result.var_names_make_unique()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.write_h5ad(args.output, compression="gzip")
    print(f"wrote {args.output} cells={result.n_obs} genes={result.n_vars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
