from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path("/mnt/snowlotus_cellfm")
ACCESSION = "GSE262840"
DATASET_ID = "geo_gse262840_arabidopsis_thaliana_single_cell_rna_seq_data"
RAW_DIR = PROJECT / "data/public/GSE262840_raw_tar"
MANIFEST = PROJECT / "data/corpus_manifest.gse262840.tsv"
REPORT = RAW_DIR / "unsupported_single_cell_matrix.json"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "path",
                "dataset_id",
                "species",
                "tissue",
                "layer",
                "label_key",
                "coarse_label_key",
                "sample_key",
            ]
        )

    payload = {
        "accession": ACCESSION,
        "dataset_id": DATASET_ID,
        "species": "Arabidopsis thaliana",
        "tissue": "root",
        "status": "deferred_large_raw_tar_file_level_retrieval_required",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": (
            "The GEO supplementary endpoint exposes a single 55 GiB RAW tar. "
            "Through the current server link it preallocates 55 GiB and downloads at only tens of KiB/s, "
            "so whole-tar retrieval is deferred to protect disk and keep the active v0.3/v0.4 training pipeline healthy. "
            "A later pass should retrieve only matrix-bearing members or use a mirror/source-specific file list."
        ),
        "raw_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE262nnn/GSE262840/suppl/GSE262840_RAW.tar",
        "corpus_manifest": MANIFEST.relative_to(PROJECT).as_posix(),
        "corpus_manifest_rows": 0,
        "queue_behavior": "The header-only manifest plus this report make the GEO promotion queue skip whole-tar retry.",
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(MANIFEST)
    print(REPORT)


if __name__ == "__main__":
    main()
