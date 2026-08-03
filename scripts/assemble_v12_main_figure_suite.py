from __future__ import annotations

"""Assemble the seven-page v12 main-figure suite and its review manifest."""

import hashlib
import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
V12 = ROOT / "figures" / "plant_cellfm_submission_v12"
MAIN = V12 / "main"
SOURCE = V12 / "source_data"
REVIEW = V12 / "review"

FIGURES = [
    ("Fig. 1", "Universal Plant-CellFM system", "plant_cellfm_v12_fig1_system", "v12 mechanism-led redesign"),
    ("Fig. 2", "Strict cross-species transfer", "plant_cellfm_v12_fig2_strict_transfer", "v12 outcome-atlas redesign"),
    ("Fig. 3", "Source-context transfer routing", "plant_cellfm_v12_fig3_context_stc", "v12 vector mechanism and retained data panels"),
    ("Fig. 4", "Sparse target adaptation", "plant_cellfm_v12_fig4_target_adaptation", "v12 adaptation-landscape redesign"),
    ("Fig. 5", "Arabidopsis root biology", "plant_cellfm_v12_fig5_root_biology", "v12 biology-led redesign"),
    ("Fig. 6", "Wheat matched benchmark", "plant_cellfm_v12_fig6_wheat_benchmark", "v12 allopolyploid benchmark redesign"),
    ("Fig. 7", "Sorghum sealed-library recovery", "plant_cellfm_v12_fig7_sorghum_recovery", "v12 sealed-validation redesign"),
]

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_fig3_reexport() -> list[dict[str, object]]:
    stem = "plant_cellfm_v12_fig3_context_stc"
    MAIN.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for suffix in ("svg", "pdf", "png", "tiff"):
        path = MAIN / f"{stem}.{suffix}"
        if not path.exists():
            raise FileNotFoundError(path)
        records.append(
            {
                "artifact": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "policy": "accepted layout and source tables retained; re-exported at 600 dpi",
            }
        )
    for table in SOURCE.glob(f"{stem}_*.tsv"):
        records.append(
            {
                "artifact": table.relative_to(ROOT).as_posix(),
                "bytes": table.stat().st_size,
                "sha256": sha256(table),
                "policy": "accepted source table retained",
            }
        )
    return records


def build_contact_sheet() -> Path:
    REVIEW.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11.6, 16.4), facecolor="#101417")
    grid = fig.add_gridspec(4, 2, left=0.025, right=0.975, bottom=0.025, top=0.975, hspace=0.055, wspace=0.035)
    for index, (number, title, stem, _) in enumerate(FIGURES):
        ax = fig.add_subplot(grid[index // 2, index % 2])
        image = Image.open(MAIN / f"{stem}.png").convert("RGB")
        ax.imshow(image)
        ax.set_axis_off()
        ax.set_title(f"{number} | {title}", color="white", fontsize=9.4, fontweight="bold", loc="left", pad=5)
    ax = fig.add_subplot(grid[3, 1])
    ax.set_axis_off()
    ax.text(0.05, 0.77, "Plant-CellFM v12", color="white", fontsize=21, fontweight="bold")
    ax.text(0.05, 0.65, "seven-figure main narrative", color="#79C7C2", fontsize=12)
    ax.text(
        0.05,
        0.44,
        "foundation system -> strict exclusion\n-> context gate -> sparse adaptation\n-> biological coherence -> matched benchmarks",
        color="#D8E5EA",
        fontsize=11,
        linespacing=1.55,
    )
    ax.text(0.05, 0.20, "All quantitative panels are rebuilt from archived source tables.\nMechanism layers are scripted vector schematics.", color="#91A7B2", fontsize=8.8, linespacing=1.45)
    output = REVIEW / "plant_cellfm_v12_main_contact_sheet.png"
    fig.savefig(output, dpi=240, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output


def write_manifest(fig3_records: list[dict[str, object]], contact_sheet: Path) -> None:
    records: list[dict[str, object]] = []
    for number, title, stem, provenance in FIGURES:
        files: dict[str, object] = {}
        for suffix in ("svg", "pdf", "png", "tiff"):
            path = MAIN / f"{stem}.{suffix}"
            if not path.exists():
                raise FileNotFoundError(path)
            files[suffix] = {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        source_tables = sorted(path.relative_to(ROOT).as_posix() for path in SOURCE.glob(f"{stem}_*.tsv"))
        records.append(
            {
                "figure": number,
                "title": title,
                "stem": stem,
                "provenance": provenance,
                "files": files,
                "source_tables": source_tables,
            }
        )

    payload = {
        "schema_version": "plant_cellfm_v12_main_figure_manifest",
        "visual_policy": "All seven pages are exported at 600 dpi. Quantitative panels are table driven and non-quantitative mechanism panels are scripted vector schematics.",
        "n_main_figures": len(records),
        "figures": records,
        "assets": [],
        "asset_provenance": "No generative-image assets are used in the submission figures.",
        "fig3_reexport_records": fig3_records,
        "contact_sheet": contact_sheet.relative_to(ROOT).as_posix(),
    }
    (V12 / "MAIN_FIGURE_MANIFEST.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Plant-CellFM v12 main figure suite",
        "",
        "v12 presents a seven-page evidence narrative. Every page is delivered as editable SVG/PDF plus 600-dpi PNG/TIFF; Fig. 3 preserves its accepted layout while being re-exported at the same production standard.",
        "",
        "| Figure | Title | Provenance | Source tables |",
        "| --- | --- | --- | ---: |",
    ]
    for record in records:
        lines.append(f"| {record['figure']} | {record['title']} | {record['provenance']} | {len(record['source_tables'])} |")
    lines.extend(["", f"Contact sheet: `{contact_sheet.relative_to(ROOT).as_posix()}`", ""])
    (V12 / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    fig3_records = validate_fig3_reexport()
    contact_sheet = build_contact_sheet()
    write_manifest(fig3_records, contact_sheet)
    print({"main_figures": len(FIGURES), "contact_sheet": str(contact_sheet), "fig3_reexport_artifacts": len(fig3_records)})


if __name__ == "__main__":
    main()
