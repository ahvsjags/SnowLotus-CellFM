from __future__ import annotations

"""Compose the recovered Imagen mechanism layers with the v12 data figures."""

import base64
import hashlib
import json
import shutil
import zipfile
from datetime import date
from pathlib import Path

import fitz
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
V12 = ROOT / "figures" / "plant_cellfm_submission_v12"
MAIN = V12 / "main"
REFERENCE = V12 / "reference_designs" / "imagen_integrated_v12"
ASSETS = V12 / "assets" / "imagen_recovered"
REVIEW = V12 / "review"
SUBMISSION = ROOT / "manuscript" / "plant_methods_submission_v1" / "submission_files"
ZIP_PATH = ROOT / "manuscript" / "plant_methods_submission_v1" / "Plant_CellFM_Plant_Methods_submission_v1.zip"


FIGURES = [
    ("Fig. 1", "Universal Plant-CellFM system", "plant_cellfm_v12_fig1_system"),
    ("Fig. 2", "Strict cross-species transfer", "plant_cellfm_v12_fig2_strict_transfer"),
    ("Fig. 3", "Source-context transfer routing", "plant_cellfm_v12_fig3_context_stc"),
    ("Fig. 4", "Sparse target adaptation", "plant_cellfm_v12_fig4_target_adaptation"),
    ("Fig. 5", "Arabidopsis root biology", "plant_cellfm_v12_fig5_root_biology"),
    ("Fig. 6", "Wheat matched benchmark", "plant_cellfm_v12_fig6_wheat_benchmark"),
    ("Fig. 7", "Sorghum sealed-library recovery", "plant_cellfm_v12_fig7_sorghum_recovery"),
]

LAYOUTS = {
    "plant_cellfm_v12_fig1_system": ((8, 26, 503, 218), [("foundation", 18, 32, 480, 192)]),
    "plant_cellfm_v12_fig2_strict_transfer": ((8, 26, 503, 218), [("cross_species", 18, 32, 480, 192)]),
    "plant_cellfm_v12_fig3_context_stc": ((8, 26, 503, 218), [("routing", 18, 32, 480, 192)]),
    "plant_cellfm_v12_fig4_target_adaptation": ((8, 26, 503, 218), [("adapter", 18, 32, 480, 192)]),
    "plant_cellfm_v12_fig5_root_biology": (
        (8, 26, 503, 230),
        [("root_states", 18, 31, 122, 196), ("tissue_transfer", 150, 42, 344, 174)],
    ),
    "plant_cellfm_v12_fig6_wheat_benchmark": ((8, 26, 503, 218), [("wheat", 18, 32, 480, 192)]),
    "plant_cellfm_v12_fig7_sorghum_recovery": (
        (8, 26, 503, 220),
        [("sorghum_root", 20, 30, 122, 192), ("root_cell", 155, 45, 340, 160)],
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_bytes(name: str) -> bytes:
    path = ASSETS / f"{name}.png"
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_bytes()


def compose_pdf(stem: str) -> None:
    source = REFERENCE / f"{stem}.pdf"
    target = MAIN / f"{stem}.pdf"
    cover, layers = LAYOUTS[stem]
    document = fitz.open(source)
    try:
        page = document[0]
        page.draw_rect(fitz.Rect(*cover), color=(0.83, 0.90, 0.94), fill=(0.97, 0.985, 0.99), width=0.65, overlay=True)
        for name, x, y, width, height in layers:
            page.insert_image(
                fitz.Rect(x, y, x + width, y + height),
                stream=asset_bytes(name),
                keep_proportion=True,
                overlay=True,
            )
        document.save(target, garbage=4, deflate=True)
    finally:
        document.close()


def compose_svg(stem: str) -> None:
    source = REFERENCE / f"{stem}.svg"
    target = MAIN / f"{stem}.svg"
    cover, layers = LAYOUTS[stem]
    body = source.read_text(encoding="utf-8")
    tags = [
        '<g id="imagen-integrated-mechanism-layer">',
        f'<rect x="{cover[0]}" y="{cover[1]}" width="{cover[2] - cover[0]}" height="{cover[3] - cover[1]}" rx="5" fill="#f7fbfd" stroke="#d5e4eb" stroke-width="0.65"/>',
    ]
    for name, x, y, width, height in layers:
        encoded = base64.b64encode(asset_bytes(name)).decode("ascii")
        tags.append(
            f'<image x="{x}" y="{y}" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}" xlink:href="data:image/png;base64,{encoded}"/>'
        )
    tags.append("</g>")
    target.write_text(body.replace("</svg>", "\n".join(tags) + "\n</svg>"), encoding="utf-8")


def render_rasters(stem: str) -> None:
    pdf = MAIN / f"{stem}.pdf"
    document = fitz.open(pdf)
    try:
        pixmap = document[0].get_pixmap(dpi=600, alpha=False)
        pixmap.set_dpi(600, 600)
        png = MAIN / f"{stem}.png"
        tiff = MAIN / f"{stem}.tiff"
        pixmap.save(png)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        image.save(tiff, compression="tiff_lzw", dpi=(600, 600))
    finally:
        document.close()


def build_contact_sheet() -> Path:
    REVIEW.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11.6, 16.4), facecolor="#101417")
    grid = fig.add_gridspec(4, 2, left=0.025, right=0.975, bottom=0.025, top=0.975, hspace=0.055, wspace=0.035)
    for index, (number, title, stem) in enumerate(FIGURES):
        ax = fig.add_subplot(grid[index // 2, index % 2])
        ax.imshow(Image.open(MAIN / f"{stem}.png").convert("RGB"))
        ax.set_axis_off()
        ax.set_title(f"{number} | {title}", color="white", fontsize=9.4, fontweight="bold", loc="left", pad=5)
    ax = fig.add_subplot(grid[3, 1])
    ax.set_axis_off()
    ax.text(0.05, 0.78, "Plant-CellFM", color="white", fontsize=21, fontweight="bold")
    ax.text(0.05, 0.67, "Imagen-integrated mechanism + v12 data", color="#79C7C2", fontsize=12)
    ax.text(0.05, 0.46, "mechanism layer -> strict transfer -> context routing\n-> sparse adaptation -> root biology\n-> matched benchmarks", color="#D8E5EA", fontsize=11, linespacing=1.55)
    ax.text(0.05, 0.21, "Recovered generated assets are composited above the current quantitative panels.", color="#91A7B2", fontsize=8.8, linespacing=1.45)
    output = REVIEW / "plant_cellfm_imagen_integrated_main_contact_sheet.png"
    fig.savefig(output, dpi=240, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output


def update_manifests(contact_sheet: Path) -> None:
    manifest_path = V12 / "MAIN_FIGURE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generated"] = date.today().isoformat()
    manifest["visual_policy"] = "Imagen-generated mechanism layers are composited into the top narrative panels; all quantitative panels and source tables remain the current v12 records; PDF/SVG retain editable source layers and PNG/TIFF are 600 dpi exports."
    manifest["asset_provenance"] = "Recovered from the Codex generated-image cache dated 2026-08-02, background-removed locally, and composited without changing benchmark data."
    manifest["contact_sheet"] = contact_sheet.relative_to(ROOT).as_posix()
    for record in manifest.get("figures", []):
        stem = record["stem"]
        record["provenance"] = "Recovered Imagen mechanism layer + current v12 quantitative panels"
        for suffix in ("svg", "pdf", "png", "tiff"):
            path = MAIN / f"{stem}.{suffix}"
            record["files"][suffix] = {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (V12 / "README.md").write_text(
        "# Plant-CellFM Imagen-integrated v12 main figure suite\n\n"
        "The top narrative panels use recovered Imagen mechanism assets composited with the current v12 quantitative figures. Source tables and benchmark denominators are unchanged.\n\n"
        + "| Figure | Title | Composition |\n| --- | --- | --- |\n"
        + "\n".join(f"| {n} | {t} | Recovered Imagen mechanism layer + current v12 data panels |" for n, t, _ in FIGURES)
        + f"\n\nContact sheet: `{contact_sheet.relative_to(ROOT).as_posix()}`\n",
        encoding="utf-8",
    )


def update_submission_bundle() -> None:
    submission_main = SUBMISSION / "main_figures"
    submission_main.mkdir(parents=True, exist_ok=True)
    for index, (_, _, stem) in enumerate(FIGURES, start=1):
        shutil.copy2(MAIN / f"{stem}.pdf", submission_main / f"Figure_{index}.pdf")
    manifest_path = SUBMISSION / "SUBMISSION_FILE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generated"] = date.today().isoformat()
    manifest["figure_policy"] = "Main figures combine recovered Imagen mechanism layers with current v12 quantitative panels; source tables, denominators and benchmark results are unchanged."
    for item in manifest.get("files", []):
        relative = item.get("path")
        if relative and (SUBMISSION / relative).exists():
            path = SUBMISSION / relative
            item["bytes"] = path.stat().st_size
            item["sha256"] = sha256(path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(SUBMISSION.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(SUBMISSION).as_posix())
    ZIP_PATH.with_suffix(ZIP_PATH.suffix + ".sha256").write_text(f"{sha256(ZIP_PATH)}  {ZIP_PATH.name}\n", encoding="utf-8")


def write_review(contact_sheet: Path) -> None:
    metadata_dir = ROOT / "release_metadata"
    payload = {
        "schema_version": "plant_cellfm_imagen_integrated_visual_review",
        "generated": date.today().isoformat(),
        "visual_target": "earlier Imagen-generated mechanism + current-data composite suite",
        "generated_assets": sorted(path.relative_to(ROOT).as_posix() for path in ASSETS.glob("*.png")),
        "contact_sheet": contact_sheet.relative_to(ROOT).as_posix(),
        "data_policy": "All benchmark data, source tables, denominators and endpoint values remain current v12.",
    }
    (metadata_dir / "plant_cellfm_imagen_integrated_visual_review_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (metadata_dir / "plant_cellfm_imagen_integrated_visual_review_latest.md").write_text(
        f"# Imagen-integrated visual review\n\nGenerated: {date.today().isoformat()}\n\n"
        "Recovered Imagen mechanism assets are composited into the top narrative panels of all seven main figures. Quantitative panels and source data remain current v12.\n\n"
        f"Contact sheet: `{contact_sheet.relative_to(ROOT).as_posix()}`\n",
        encoding="utf-8",
    )


def main() -> None:
    for _, _, stem in FIGURES:
        compose_pdf(stem)
        compose_svg(stem)
        render_rasters(stem)
    contact_sheet = build_contact_sheet()
    update_manifests(contact_sheet)
    update_submission_bundle()
    write_review(contact_sheet)
    print(json.dumps({"figures": len(FIGURES), "contact_sheet": str(contact_sheet), "zip": str(ZIP_PATH)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
