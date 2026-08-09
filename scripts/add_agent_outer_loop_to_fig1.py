"""Add a lightweight Agent plan-act-verify loop to the v12 Fig. 1 SVG."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figures" / "plant_cellfm_submission_v12" / "main" / "plant_cellfm_v12_fig1_system.svg"
TARGET = ROOT / "figures" / "plant_cellfm_submission_v12" / "main" / "plant_cellfm_v12_fig1_system_agent.svg"

OVERLAY = r'''
<g id="plantcell-agent-outer-loop" aria-label="PlantCell-Agent plan act verify loop">
  <path d="M 28 242 C 13 242 13 24 29 24 L 508 24 C 521 24 521 242 507 242"
        fill="none" stroke="#00877E" stroke-width="1.15" stroke-dasharray="3.4,2.5"
        stroke-linecap="round" opacity="0.82"/>
  <path d="M 28 242 L 37 238 L 35 245 Z" fill="#00877E" opacity="0.82"/>
  <path d="M 507 242 L 498 238 L 500 245 Z" fill="#00877E" opacity="0.82"/>
  <rect x="186" y="237.4" width="148" height="7.8" rx="3.9"
        fill="#FFFFFF" fill-opacity="0.94" stroke="#B8DCD7" stroke-width="0.55"/>
  <text x="260" y="242.6" text-anchor="middle"
        style="font-weight:700;font-size:3.25px;font-family:Arial,Helvetica,sans-serif;fill:#006E68;letter-spacing:0.12px">
    AGENT LOOP  ·  AUDIT  →  ROUTE  →  VERIFY
  </text>
</g>
'''


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    if 'id="plantcell-agent-outer-loop"' in text:
        TARGET.write_text(text, encoding="utf-8")
        return
    if not text.rstrip().endswith("</svg>"):
        raise ValueError(f"unexpected SVG terminator: {SOURCE}")
    TARGET.write_text(text.rstrip()[:-6] + OVERLAY + "</svg>\n", encoding="utf-8")


if __name__ == "__main__":
    main()
