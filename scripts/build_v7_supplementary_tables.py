from __future__ import annotations

"""Package all current S1-S27 TSVs into a v7 reviewer workbook and manifest."""

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "supplementary_tables" / "submission_v4"
WORKBOOK = TABLE_DIR / "Plant_CellFM_Supplementary_Tables_v7.xlsx"
MANIFEST = TABLE_DIR / "MANIFEST_v7.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"Supplementary_Table_S(\d+)", path.name)
    return (int(match.group(1)) if match else 10_000, path.name)


def main() -> int:
    tables = sorted(TABLE_DIR.glob("Supplementary_Table_S*.tsv"), key=sort_key)
    observed_numbers = {sort_key(table)[0] for table in tables}
    required_numbers = set(range(1, 28))
    missing_numbers = sorted(required_numbers - observed_numbers)
    if missing_numbers:
        raise ValueError(f"Expected S1-S27; missing table numbers: {missing_numbers}")
    rows = []
    with pd.ExcelWriter(WORKBOOK, engine="openpyxl") as writer:
        for table in tables:
            frame = pd.read_csv(table, sep="\t")
            sheet = table.stem.replace("Supplementary_Table_", "")[:31]
            frame.to_excel(writer, sheet_name=sheet, index=False)
            rows.append(
                {
                    "table": table.name,
                    "sheet": sheet,
                    "rows": int(len(frame)),
                    "columns": int(len(frame.columns)),
                    "sha256": sha256(table),
                }
            )
    payload = {
        "schema_version": "plant_cellfm_submission_v7_supplementary_inventory_v1",
        "status": "S1_TO_S27_PACKAGED",
        "workbook": {"path": WORKBOOK.relative_to(ROOT).as_posix(), "sha256": sha256(WORKBOOK)},
        "tables": rows,
        "claim_boundary": "Tables S25-S27 record the GSE297576 frozen external audit and sealed-library Sorghum adaptation. Their results are target-species adaptation evidence, not a replacement for the primary strict leave-species protocol or a third-party ranking.",
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "table_count": len(rows), "workbook_sha256": payload["workbook"]["sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
