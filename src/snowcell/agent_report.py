"""Human-readable reports for auditable Plant-CellFM agent runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_agent_report(result: dict[str, Any]) -> str:
    audit = result.get("input_audit", {})
    route = result.get("route_decision", {})
    quality = result.get("quality", {})
    specialist = route.get("specialist_plan", {})
    primary = specialist.get("primary_agent", {})
    verification = quality.get("specialist_verification", {})
    lines = [
        "# Plant-CellFM Agent run report",
        "",
        f"- Run ID: `{result.get('run_id', '')}`",
        f"- Status: **{result.get('status', '')}**",
        f"- Route: **{result.get('route', '')}**",
        "",
        "## Input audit",
        "",
        f"- Matrix: `{audit.get('format', '')}`; cells={audit.get('n_cells', 0)}, genes={audit.get('n_genes', 0)}",
        f"- Density: {_number(audit.get('matrix_density', 0.0))}; unique gene IDs: {_number(audit.get('gene_id_unique_fraction', 0.0))}",
        f"- Species: {', '.join(audit.get('species', {}).get('values', [])) or 'unknown'}",
        f"- Missing optional metadata: {', '.join(audit.get('missing_required_obs', [])) or 'none'}",
        "",
        "## Route decision",
        "",
        f"- Adapter: `{route.get('adapter_id', '')}` ({route.get('adapter_status', '')})",
        f"- Contract: `{route.get('execution_contract', '')}`",
        f"- Species metadata consistency: {'review required' if route.get('species_metadata_mismatch') else 'consistent'}",
        f"- Rationale: {route.get('rationale', '')}",
        f"- Central model: `{specialist.get('central_model_id', 'plant_cellfm.central_model')}`",
        f"- Primary specialist: `{primary.get('agent_id', '')}` ({primary.get('role', '')})",
        f"- Fallback chain: {', '.join(item.get('agent_id', '') for item in specialist.get('fallback_chain', [])) or 'none'}",
        "",
        "## Evidence verification",
        "",
        f"- Specialist output contract: **{verification.get('status', 'not_recorded')}**",
        f"- Contract errors: {', '.join(verification.get('errors', [])) or 'none'}",
        f"- Fallback forced review: {'yes' if quality.get('fallback_forced_review') else 'no'}",
        "",
        "## Selective annotation quality",
        "",
        f"- Cells accepted: {quality.get('accepted_cells', 0)}/{quality.get('n_cells', 0)} ({_number(quality.get('accepted_coverage', 0.0))})",
        f"- Mean confidence: {_number(quality.get('mean_confidence', 0.0))}",
        f"- Open-set cells: {quality.get('open_set_cells', 0)}; manual-review cells: {quality.get('review_cells', 0)}",
        f"- Runtime: {_number(quality.get('runtime_seconds', 0.0))} s; CUDA peak: {_number(quality.get('cuda_peak_memory_mb', 0.0))} MB",
        f"- Fallback retry: {quality.get('retry', {}).get('status', 'not_run') if quality.get('retry') else 'not_run'}",
        f"- Decision: **{quality.get('decision', {}).get('status', 'manual_review_required')}**",
        "",
        "## Interpretation boundary",
        "",
        "This run reports selective reliability and audit evidence. It does not convert selective coverage into an all-cell accuracy claim, and it does not replace the locked benchmark metrics.",
        "",
        "## Artifacts",
        "",
    ]
    for name, path in result.get("artifacts", {}).items():
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def write_agent_report(result: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_agent_report(result), encoding="utf-8")
    return path
