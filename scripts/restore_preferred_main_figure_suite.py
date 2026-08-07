from __future__ import annotations

"""Restore the earlier Imagen-integrated v12 main-figure composition.

The quantitative source tables remain the current v12 records.  This script
restores the complete seven-figure suite in which the mechanism schematics
and the data panels were composed as one visual narrative.  All seven pages
come from the preserved v12 artwork so that figures are not mixed across
different data generations.
"""

import hashlib
import json
import shutil
import zipfile
from datetime import date
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
V12 = ROOT / "figures" / "plant_cellfm_submission_v12"
MAIN = V12 / "main"
SOURCE = V12 / "source_data"
REVIEW = V12 / "review"
HIST = V12 / "reference_designs"
SUBMISSION = ROOT / "manuscript" / "plant_methods_submission_v1" / "submission_files"
ZIP_PATH = ROOT / "manuscript" / "plant_methods_submission_v1" / "Plant_CellFM_Plant_Methods_submission_v1.zip"
ZIP_SHA = ZIP_PATH.with_suffix(ZIP_PATH.suffix + ".sha256")

SUFFIXES = ("svg", "pdf", "png", "tiff")
FIGURES = [
    ("Fig. 1", "Universal Plant-CellFM system", "plant_cellfm_v12_fig1_system", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig1_system"),
    ("Fig. 2", "Strict cross-species transfer", "plant_cellfm_v12_fig2_strict_transfer", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig2_strict_transfer"),
    ("Fig. 3", "Source-context transfer routing", "plant_cellfm_v12_fig3_context_stc", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig3_context_stc"),
    ("Fig. 4", "Sparse target adaptation", "plant_cellfm_v12_fig4_target_adaptation", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig4_target_adaptation"),
    ("Fig. 5", "Arabidopsis root biology", "plant_cellfm_v12_fig5_root_biology", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig5_root_biology"),
    ("Fig. 6", "Wheat matched benchmark", "plant_cellfm_v12_fig6_wheat_benchmark", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig6_wheat_benchmark"),
    ("Fig. 7", "Sorghum sealed-library recovery", "plant_cellfm_v12_fig7_sorghum_recovery", "Imagen-integrated v12 composition", "imagen_integrated_v12/plant_cellfm_v12_fig7_sorghum_recovery"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def restore_artwork() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for number, title, target_stem, provenance, source_stem in FIGURES:
        for suffix in SUFFIXES:
            target = MAIN / f"{target_stem}.{suffix}"
            if source_stem is None:
                if not target.exists():
                    raise FileNotFoundError(target)
                source = target
            else:
                source = HIST / f"{source_stem}.{suffix}"
                if suffix in {"png", "tiff"}:
                    source_pdf = HIST / f"{source_stem}.pdf"
                    if not source_pdf.exists():
                        raise FileNotFoundError(source_pdf)
                    document = fitz.open(source_pdf)
                    try:
                        pixmap = document[0].get_pixmap(dpi=600, alpha=False)
                        if suffix == "png":
                            pixmap.save(target)
                        else:
                            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                            image.save(target, compression="tiff_lzw", dpi=(600, 600))
                    finally:
                        document.close()
                    source = source_pdf
                else:
                    if not source.exists():
                        raise FileNotFoundError(source)
                    shutil.copy2(source, target)
            records.append(
                {
                    "figure": number,
                    "title": title,
                    "format": suffix,
                    "artifact": target.relative_to(ROOT).as_posix(),
                    "source": source.relative_to(ROOT).as_posix(),
                    "provenance": provenance,
                    "bytes": target.stat().st_size,
                    "sha256": sha256(target),
                }
            )
    return records


def build_contact_sheet() -> Path:
    REVIEW.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11.6, 16.4), facecolor="#101417")
    grid = fig.add_gridspec(4, 2, left=0.025, right=0.975, bottom=0.025, top=0.975, hspace=0.055, wspace=0.035)
    for index, (number, title, stem, _, _) in enumerate(FIGURES):
        ax = fig.add_subplot(grid[index // 2, index % 2])
        image = Image.open(MAIN / f"{stem}.png").convert("RGB")
        ax.imshow(image)
        ax.set_axis_off()
        ax.set_title(f"{number} | {title}", color="white", fontsize=9.4, fontweight="bold", loc="left", pad=5)
    ax = fig.add_subplot(grid[3, 1])
    ax.set_axis_off()
    ax.text(0.05, 0.78, "Plant-CellFM", color="white", fontsize=21, fontweight="bold")
    ax.text(0.05, 0.67, "Imagen-integrated v12 main suite", color="#79C7C2", fontsize=12)
    ax.text(
        0.05,
        0.46,
        "contract -> strict transfer -> context routing\n-> sparse adaptation -> root biology\n-> matched benchmarks",
        color="#D8E5EA",
        fontsize=11,
        linespacing=1.55,
    )
    ax.text(0.05, 0.21, "Mechanism schematics and current v12 results restored as one suite.", color="#91A7B2", fontsize=8.8, linespacing=1.45)
    output = REVIEW / "plant_cellfm_imagen_integrated_main_contact_sheet.png"
    fig.savefig(output, dpi=240, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output


def write_figure_manifest(records: list[dict[str, object]], contact_sheet: Path) -> None:
    figure_records: list[dict[str, object]] = []
    for number, title, stem, provenance, _ in FIGURES:
        files = {}
        for suffix in SUFFIXES:
            path = MAIN / f"{stem}.{suffix}"
            files[suffix] = {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        figure_records.append(
            {
                "figure": number,
                "title": title,
                "stem": stem,
                "provenance": provenance,
                "files": files,
                "source_tables": sorted(path.relative_to(ROOT).as_posix() for path in SOURCE.glob(f"{stem}_*.tsv")),
            }
        )
    payload = {
        "schema_version": "plant_cellfm_preferred_main_figure_manifest",
        "generated": date.today().isoformat(),
        "visual_policy": "All seven pages use the preserved Imagen-integrated v12 composition; quantitative panels remain table-driven and current v12 source tables are retained; SVG/PDF remain vector and PNG/TIFF are 600 dpi exports.",
        "n_main_figures": len(figure_records),
        "figures": figure_records,
        "assets": [],
        "contact_sheet": contact_sheet.relative_to(ROOT).as_posix(),
        "artwork_records": records,
        "asset_provenance": "The preserved v12 suite combines mechanism schematics with data-driven panels; no newly generated image was substituted during restoration.",
    }
    (V12 / "MAIN_FIGURE_MANIFEST.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Plant-CellFM Imagen-integrated v12 main figure suite",
        "",
        "The earlier Imagen-integrated v12 composition has been restored for all seven main submission figures. Current v12 quantitative source tables and endpoint definitions remain unchanged.",
        "",
        "| Figure | Title | Visual composition | Source tables |",
        "| --- | --- | --- | ---: |",
    ]
    for record in figure_records:
        lines.append(f"| {record['figure']} | {record['title']} | {record['provenance']} | {len(record['source_tables'])} |")
    lines.extend(["", f"Contact sheet: `{contact_sheet.relative_to(ROOT).as_posix()}`", ""])
    (V12 / "README.md").write_text("\n".join(lines), encoding="utf-8")


def sync_submission_pdfs() -> None:
    SUBMISSION_MAIN = SUBMISSION / "main_figures"
    SUBMISSION_MAIN.mkdir(parents=True, exist_ok=True)
    for index, (_, _, stem, _, _) in enumerate(FIGURES, start=1):
        shutil.copy2(MAIN / f"{stem}.pdf", SUBMISSION_MAIN / f"Figure_{index}.pdf")


def update_submission_manifest_and_zip() -> None:
    manifest_path = SUBMISSION / "SUBMISSION_FILE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generated"] = date.today().isoformat()
    manifest["figure_policy"] = "Main figures use the preserved Imagen-integrated v12 composition; current v12 table-driven quantitative panels and vector schematics are retained; no new image asset was substituted."
    for item in manifest.get("files", []):
        relative = item.get("path")
        if relative:
            path = SUBMISSION / relative
            if path.exists():
                item["bytes"] = path.stat().st_size
                item["sha256"] = sha256(path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(SUBMISSION.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(SUBMISSION).as_posix())
    ZIP_SHA.write_text(f"{sha256(ZIP_PATH)}  {ZIP_PATH.name}\n", encoding="utf-8")


def write_review_metadata(records: list[dict[str, object]], contact_sheet: Path) -> None:
    payload = {
        "schema_version": "plant_cellfm_preferred_main_visual_review",
        "generated": date.today().isoformat(),
        "visual_target": "earlier Imagen-integrated v12 composition",
        "server": "px1-jcy.matpool.com:26506",
        "server_role": "model/data verification only; image assets were restored from the preserved local historical v12 review set",
        "contact_sheet": contact_sheet.relative_to(ROOT).as_posix(),
        "current_source_policy": "All current v12 source tables remain in figures/plant_cellfm_submission_v12/source_data.",
        "records": records,
    }
    metadata_dir = ROOT / "release_metadata"
    (metadata_dir / "plant_cellfm_preferred_main_visual_review_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Preferred main-figure visual review",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "The main submission pages now use the earlier Imagen-integrated v12 composition requested by the author. Current v12 source tables, primary nested strict estimate (39.96%), and context-aware sensitivity endpoint (42.36%) remain the controlling records.",
        "",
        "The new server endpoint `px1-jcy.matpool.com:26506` was verified for connectivity and model/data presence. It did not contain a complete v11/v12 image suite, so no remote artwork was substituted.",
        "",
        f"Review sheet: `{contact_sheet.relative_to(ROOT).as_posix()}`",
        "",
        "The restored suite combines mechanism schematics with data-derived panels; no newly generated asset was substituted.",
    ]
    (metadata_dir / "plant_cellfm_preferred_main_visual_review_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    records = restore_artwork()
    contact_sheet = build_contact_sheet()
    write_figure_manifest(records, contact_sheet)
    sync_submission_pdfs()
    update_submission_manifest_and_zip()
    write_review_metadata(records, contact_sheet)
    print(json.dumps({"main_figures": len(FIGURES), "contact_sheet": str(contact_sheet), "zip": str(ZIP_PATH)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
