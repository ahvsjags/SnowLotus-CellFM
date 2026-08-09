"""Write the independent blinded expert audit protocol and integrity record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=ROOT / "release_metadata/plantcell_agent_expert_audit_template_v2.tsv")
    parser.add_argument("--output-json", type=Path, default=ROOT / "release_metadata/plantcell_agent_blind_audit_protocol_v1.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "release_metadata/plantcell_agent_blind_audit_protocol_v1.md")
    args = parser.parse_args()
    for name in ("template", "output_json", "output_md"):
        path = getattr(args, name)
        if not path.is_absolute():
            setattr(args, name, ROOT / path)
    if not args.template.exists():
        raise FileNotFoundError(args.template)
    table = pd.read_csv(args.template, sep="\t")
    forbidden = sorted(set(table.columns) & {"reference_label", "hidden_group", "agent_correct"})
    if forbidden:
        raise ValueError(f"public worksheet leaks blinded fields: {forbidden}")
    if table["audit_id"].duplicated().any():
        raise ValueError("public worksheet audit_id values must be unique")
    payload = {
        "schema_version": "plantcell_agent_blind_audit_protocol_v1",
        "status": "pending_external_expert",
        "template": display_path(args.template),
        "template_sha256": sha256(args.template),
        "rows": int(len(table)),
        "fields": table.columns.tolist(),
        "blinding_checks": {
            "reference_label_hidden": "reference_label" not in table.columns,
            "acceptance_group_hidden": "hidden_group" not in table.columns,
            "agent_correct_hidden": "agent_correct" not in table.columns,
            "audit_ids_unique": not bool(table.audit_id.duplicated().any()),
        },
        "review_instructions": [
            "The reviewer receives only the TSV worksheet and the expression/visualization bundle identified by audit_id.",
            "The reviewer records expert_label, expert_confidence, expert_decision and expert_notes without access to reference_label or hidden_group.",
            "The reviewer returns the completed TSV with the original audit_id values unchanged.",
            "The scoring script verifies that no blinded columns were added and records the completed worksheet SHA256.",
        ],
        "completion_gate": "independent_blind_audit is completed_external_expert only after a non-empty expert_label worksheet is scored by run_agent_evidence_audit.py.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# PlantCell-Agent independent blind audit protocol v1",
        "",
        "Status: **pending_external_expert**",
        f"Worksheet rows: **{len(table)}**",
        f"Worksheet SHA256: `{payload['template_sha256']}`",
        "",
        "The public worksheet contains cell identifiers and Agent labels only. It does not contain the author/reference label, the acceptance group or the correctness flag.",
        "",
        "A manuscript claim of independent expert validation is permitted only after an external reviewer returns the completed worksheet and the scoring script records `completed_external_expert` with the completed file hash.",
    ]
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
