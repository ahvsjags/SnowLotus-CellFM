"""Build the vector architecture schematic for the specialist-agent upgrade."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "figures" / "plantcell_agent" / "plantcell_agent_extended_data_fig1_v3.svg"


SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">
<rect width="1600" height="1000" fill="#fbfcfd"/>
<style>
  @page{size:1600px 1000px;margin:0}
  html,body{margin:0;width:1600px;height:1000px}
  .title{font:700 34px Arial,Helvetica,sans-serif;fill:#172b3a}
  .subtitle{font:400 17px Arial,Helvetica,sans-serif;fill:#607482}
  .section{font:700 18px Arial,Helvetica,sans-serif;fill:#173242;letter-spacing:.3px}
  .cardtitle{font:700 17px Arial,Helvetica,sans-serif;fill:#173242}
  .body{font:400 14px Arial,Helvetica,sans-serif;fill:#536875}
  .tiny{font:400 12px Arial,Helvetica,sans-serif;fill:#607482}
  .panel{fill:#fff;stroke:#d8e2e8;stroke-width:2}
  .card{stroke-width:2}
  .blue{fill:#e0effa;stroke:#2d77b3}.teal{fill:#d8f0eb;stroke:#168d83}
  .purple{fill:#eee7fa;stroke:#7956ab}.amber{fill:#fff0d5;stroke:#d58a25}
  .red{fill:#fbe2e1;stroke:#c45656}.slate{fill:#edf2f5;stroke:#718694}
  .arrow{fill:none;stroke:#587585;stroke-width:3;marker-end:url(#arrow)}
  .branch{fill:none;stroke:#91a7b3;stroke-width:2.2;marker-end:url(#arrow)}
  .loop{fill:none;stroke:#168d83;stroke-width:3;stroke-dasharray:10 8;marker-end:url(#loopArrow)}
</style>
<defs>
  <marker id="arrow" markerWidth="11" markerHeight="11" refX="9" refY="3.5" orient="auto"><path d="M0,0 L10,3.5 L0,7 Z" fill="#587585"/></marker>
  <marker id="loopArrow" markerWidth="11" markerHeight="11" refX="9" refY="3.5" orient="auto"><path d="M0,0 L10,3.5 L0,7 Z" fill="#168d83"/></marker>
</defs>

<text x="70" y="64" class="title">Plant-CellFM + Specialist Adapter Agents</text>
<text x="70" y="96" class="subtitle">A central plant cell foundation model with capability-scoped agents, evidence verification and explicit abstention</text>

<!-- top-level central model pipeline -->
<rect x="60" y="130" width="1480" height="205" rx="18" class="panel"/>
<text x="90" y="166" class="section">a  Central model and orchestration</text>
<rect x="95" y="205" width="260" height="95" rx="13" class="card blue"/>
<text x="125" y="239" class="cardtitle">Input audit</text>
<text x="125" y="264" class="body">cells · genes · QC · metadata</text>
<text x="125" y="284" class="tiny">identifier and tissue contracts</text>
<path d="M355 252 H425" class="arrow"/>
<rect x="445" y="185" width="430" height="135" rx="15" class="card teal"/>
<text x="480" y="225" class="cardtitle">Plant-CellFM central model</text>
<text x="480" y="251" class="body">shared plant expression encoder</text>
<text x="480" y="274" class="body">256-dimensional cell embedding</text>
<text x="480" y="297" class="tiny">fine/coarse labels · confidence · marker candidates</text>
<path d="M875 252 H945" class="arrow"/>
<rect x="965" y="205" width="285" height="95" rx="13" class="card purple"/>
<text x="995" y="239" class="cardtitle">PlantCell-Agent</text>
<text x="995" y="264" class="body">route · audit · contract check</text>
<text x="995" y="284" class="tiny">species · organ · coverage · open set</text>
<path d="M1250 252 H1320" class="arrow"/>
<rect x="1340" y="205" width="165" height="95" rx="13" class="card amber"/>
<text x="1370" y="239" class="cardtitle">Agent ledger</text>
<text x="1370" y="264" class="body">plan + trace</text>
<text x="1370" y="284" class="tiny">before inference</text>

<!-- specialist layer -->
<rect x="60" y="370" width="1180" height="360" rx="18" class="panel"/>
<text x="90" y="406" class="section">b  Specialist adapter-agent ecosystem</text>
<text x="90" y="432" class="tiny">Each specialist declares scope, required inputs, outputs, evidence and an explicit fallback chain.</text>

<rect x="95" y="470" width="320" height="92" rx="13" class="card blue"/>
<text x="125" y="505" class="cardtitle">Species Adapter Agent</text>
<text x="125" y="530" class="body">registered adapter · local vocabulary</text>
<text x="125" y="550" class="tiny">adapter manifest + gene audit</text>
<rect x="455" y="470" width="320" height="92" rx="13" class="card purple"/>
<text x="485" y="505" class="cardtitle">Organ Context Agent</text>
<text x="485" y="530" class="body">root · leaf · apex · tissue prior</text>
<text x="485" y="550" class="tiny">context evidence + routing prior</text>
<rect x="815" y="470" width="320" height="92" rx="13" class="card amber"/>
<text x="845" y="505" class="cardtitle">Orthology Transfer Agent</text>
<text x="845" y="530" class="body">projection · count retention · retry</text>
<text x="845" y="550" class="tiny">map coverage + aggregation rule</text>
<rect x="95" y="590" width="320" height="92" rx="13" class="card teal"/>
<text x="125" y="625" class="cardtitle">Support Prototype Agent</text>
<text x="125" y="650" class="body">few-shot label-space recovery</text>
<text x="125" y="670" class="tiny">support count + disjoint query contract</text>
<rect x="455" y="590" width="320" height="92" rx="13" class="card red"/>
<text x="485" y="625" class="cardtitle">Open-set Agent</text>
<text x="485" y="650" class="body">unsupported states · abstention</text>
<text x="485" y="670" class="tiny">coverage + open-set flags</text>
<rect x="815" y="590" width="320" height="92" rx="13" class="card slate"/>
<text x="845" y="625" class="cardtitle">Marker Evidence Agent</text>
<text x="845" y="650" class="body">predicted-label marker candidates</text>
<text x="845" y="670" class="tiny">evidence table, not wet-lab validation</text>

<!-- branch links -->
<path d="M1107 300 C1107 350 255 350 255 470" class="branch"/>
<path d="M1107 300 C1107 350 615 350 615 470" class="branch"/>
<path d="M1107 300 C1107 350 975 350 975 470" class="branch"/>
<path d="M1107 300 C1107 380 255 380 255 590" class="branch"/>
<path d="M1107 300 C1107 380 615 380 615 590" class="branch"/>
<path d="M1107 300 C1107 380 975 380 975 590" class="branch"/>

<!-- verification and decision layer -->
<rect x="1270" y="370" width="270" height="360" rx="18" class="panel"/>
<text x="1298" y="406" class="section">c  Verify</text>
<rect x="1300" y="470" width="210" height="102" rx="13" class="card teal"/>
<text x="1325" y="505" class="cardtitle">Evidence Agent</text>
<text x="1325" y="530" class="body">artifact contract</text>
<text x="1325" y="550" class="body">calibration · risk</text>
<path d="M1135 516 H1300" class="branch"/>
<path d="M1135 636 H1300" class="branch"/>
<rect x="1300" y="600" width="210" height="102" rx="13" class="card red"/>
<text x="1325" y="635" class="cardtitle">Review Agent</text>
<text x="1325" y="660" class="body">low confidence</text>
<text x="1325" y="680" class="tiny">open set · failed contract</text>

<!-- release outcomes -->
<rect x="60" y="765" width="1480" height="165" rx="18" class="panel"/>
<text x="90" y="801" class="section">d  Evidence-aware release</text>
<rect x="95" y="830" width="350" height="70" rx="12" class="card teal"/>
<text x="125" y="860" class="cardtitle">Automatic release</text>
<text x="125" y="882" class="tiny">accepted cells · confidence contract passed</text>
<path d="M1405 572 C1405 735 270 735 270 830" class="loop"/>
<rect x="520" y="830" width="350" height="70" rx="12" class="card red"/>
<text x="550" y="860" class="cardtitle">Expert review queue</text>
<text x="550" y="882" class="tiny">review cells · blinded audit worksheet</text>
<path d="M1405 702 C1405 760 695 760 695 830" class="loop"/>
<rect x="945" y="830" width="520" height="70" rx="12" class="card amber"/>
<text x="975" y="860" class="cardtitle">Reproducible evidence bundle</text>
<text x="975" y="882" class="tiny">specialist_plan.json · evidence_verification.json · uncertainty_review.tsv</text>

<text x="90" y="962" class="tiny">The central checkpoint remains unchanged; specialists add declared routing, evidence and abstention contracts around the same cell-level predictions.</text>
</svg>
'''


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(SVG, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
