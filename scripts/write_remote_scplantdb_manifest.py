#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path("/mnt/snowlotus_cellfm")
H5AD_DIR = ROOT / "data/public/scPlantDB_h5ad"
OUT = ROOT / "data/corpus_manifest.current_scplantdb.tsv"

METADATA = {
    "CRA002977_1": ("Arabidopsis thaliana", "True leaf"),
    "CRA002977_2": ("Arabidopsis thaliana", "Vegetative shoot apex"),
    "DRP009643": ("Arabidopsis thaliana", "Rosette leaf"),
    "ERP132245": ("Arabidopsis thaliana", "True leaf"),
    "SRP065494": ("Arabidopsis thaliana", "Root stele cell"),
    "SRP148288": ("Arabidopsis thaliana", "Whole root"),
    "SRP169576": ("Arabidopsis thaliana", "Whole root"),
    "CRA006988": ("Brassica rapa", "Rosette leaf"),
    "CRA004848": ("Fragaria vesca", "True leaf"),
    "SRP335448": ("Catharanthus roseus", "Leaf"),
    "SRP424189": ("Gossypium bickii", "Cotyledon"),
}


rows = []
for path in sorted(H5AD_DIR.glob("*.h5ad")):
    dataset = path.stem
    species, tissue = METADATA.get(dataset, ("unknown_species", "unknown_tissue"))
    rows.append(
        {
            "path": path.as_posix(),
            "dataset_id": f"scplantdb_{dataset}",
            "species": species,
            "tissue": tissue,
            "layer": "",
            "label_key": "Celltype",
            "coarse_label_key": "Celltype",
            "sample_key": "Orig.ident",
        }
    )

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t") if rows else None
    if writer:
        writer.writeheader()
        writer.writerows(rows)
print(f"{OUT} rows={len(rows)}")
