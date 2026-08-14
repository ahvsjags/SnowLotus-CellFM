"""Source-only plant cell-state ontology and marker contract utilities.

The contract is deliberately independent of any benchmark matrix. It contains
canonical state names, generic aliases, and curated marker symbols only. It
must not be generated from held-out labels or from per-dataset cell counts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse


_FORBIDDEN_KEYS = {
    "target_labels",
    "held_out_labels",
    "test_labels",
    "test_cells",
    "cell_counts",
    "benchmark_counts",
    "prediction_counts",
    "target_species",
}


def normalize_label(value: Any) -> str:
    """Normalize a label for deterministic alias matching."""

    text = str(value).strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[/|:_().,;\\-]+", " ", text)
    return " ".join(text.split())


def _validate_source_only_payload(payload: dict[str, Any]) -> None:
    if payload.get("provenance") != "source_only_curated":
        raise ValueError("ontology contract must declare provenance=source_only_curated")
    if payload.get("schema_version", "").startswith("plant_cellfm_source_only") is False:
        raise ValueError("unsupported source-only ontology schema")
    for key in payload:
        if str(key).lower() in _FORBIDDEN_KEYS:
            raise ValueError(f"source-only ontology contains forbidden key: {key}")
    states = payload.get("states")
    if not isinstance(states, list) or not states:
        raise ValueError("source-only ontology must contain a non-empty states list")
    seen: set[str] = set()
    for state in states:
        if not isinstance(state, dict):
            raise ValueError("ontology states must be objects")
        required = {"id", "canonical_label", "coarse_label", "aliases", "marker_genes"}
        missing = required - set(state)
        if missing:
            raise ValueError(f"ontology state missing fields: {sorted(missing)}")
        state_id = str(state["id"])
        if state_id in seen:
            raise ValueError(f"duplicate ontology state id: {state_id}")
        seen.add(state_id)
        if not isinstance(state["aliases"], list) or not isinstance(state["marker_genes"], list):
            raise ValueError(f"ontology state fields must be lists: {state_id}")


def load_source_only_contract(path: str | Path) -> dict[str, Any]:
    contract_path = Path(path)
    with contract_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("ontology contract root must be an object")
    _validate_source_only_payload(payload)
    return payload


def _lookup(contract: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[tuple[str, dict[str, Any]]]]:
    exact: dict[str, dict[str, Any]] = {}
    contains: list[tuple[str, dict[str, Any]]] = []
    for state in contract["states"]:
        aliases = [state["canonical_label"], *state.get("aliases", [])]
        for alias in aliases:
            normalized = normalize_label(alias)
            if normalized:
                exact.setdefault(normalized, state)
        for term in state.get("contains", []):
            normalized = normalize_label(term)
            if normalized:
                contains.append((normalized, state))
    contains.sort(key=lambda item: len(item[0]), reverse=True)
    return exact, contains


def canonicalize_label(
    value: Any,
    contract: dict[str, Any],
    unknown_policy: str = "keep",
) -> tuple[str, str | None]:
    """Return canonical label and matched state id, if any."""

    if unknown_policy not in {"keep", "unknown"}:
        raise ValueError("unknown_policy must be keep or unknown")
    exact, contains = _lookup(contract)
    normalized = normalize_label(value)
    return _canonicalize_normalized(
        value,
        normalized,
        exact,
        contains,
        unknown_policy,
    )


def _canonicalize_normalized(
    original: Any,
    normalized: str,
    exact: dict[str, dict[str, Any]],
    contains: list[tuple[str, dict[str, Any]]],
    unknown_policy: str,
) -> tuple[str, str | None]:
    state = exact.get(normalized)
    if state is None:
        for term, candidate in contains:
            if term in normalized:
                state = candidate
                break
    if state is not None:
        return str(state["canonical_label"]), str(state["id"])
    if unknown_policy == "unknown":
        return "Unknown", None
    return str(original), None


def remap_observations(
    obs: dict[str, np.ndarray],
    *,
    label_key: str,
    coarse_label_key: str,
    contract: dict[str, Any],
    unknown_policy: str = "keep",
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Apply the fixed ontology to labels without inspecting expression values."""

    output = {key: np.asarray(values, dtype=str).copy() for key, values in obs.items()}
    if label_key not in output:
        return output, {"status": "label_key_absent", "mapped_cells": 0, "unmatched_cells": 0}

    states = {str(state["id"]): state for state in contract["states"]}
    exact, contains = _lookup(contract)
    labels = np.asarray(output[label_key], dtype=str)
    mapped = []
    state_ids: list[str | None] = []
    for value in labels:
        canonical, state_id = _canonicalize_normalized(
            value,
            normalize_label(value),
            exact,
            contains,
            unknown_policy,
        )
        mapped.append(canonical)
        state_ids.append(state_id)
    output[label_key] = np.asarray(mapped, dtype=str)

    if coarse_label_key != label_key:
        if coarse_label_key in output:
            coarse = [str(value) for value in output[coarse_label_key]]
        else:
            coarse = ["unknown"] * len(labels)
        for index, state_id in enumerate(state_ids):
            if state_id is not None:
                coarse[index] = str(states[state_id]["coarse_label"])
        output[coarse_label_key] = np.asarray(coarse, dtype=str)

    matched = np.asarray([state_id is not None for state_id in state_ids], dtype=bool)
    return output, {
        "status": "applied",
        "contract_schema": contract["schema_version"],
        "provenance": contract["provenance"],
        "mapped_cells": int(matched.sum()),
        "unmatched_cells": int((~matched).sum()),
        "mapped_fraction": float(matched.mean()) if len(matched) else 0.0,
        "canonical_labels": sorted(set(output[label_key].tolist())),
    }


def marker_prior_scores(
    matrix: np.ndarray | sparse.spmatrix,
    genes: np.ndarray,
    contract: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Compute a source-only marker score matrix for evidence or reranking."""

    gene_to_index = {normalize_label(gene): index for index, gene in enumerate(np.asarray(genes, dtype=str))}
    if sparse.issparse(matrix):
        values = matrix.tocsr().astype(np.float32)
    else:
        values = np.asarray(matrix, dtype=np.float32)
    scores = np.zeros((values.shape[0], len(contract["states"])), dtype=np.float32)
    coverage: dict[str, int] = {}
    for state_index, state in enumerate(contract["states"]):
        marker_indices = [
            gene_to_index[normalize_label(gene)]
            for gene in state.get("marker_genes", [])
            if normalize_label(gene) in gene_to_index
        ]
        coverage[str(state["id"])] = len(marker_indices)
        if not marker_indices:
            continue
        if sparse.issparse(values):
            scores[:, state_index] = np.asarray(values[:, marker_indices].mean(axis=1)).ravel()
        else:
            scores[:, state_index] = values[:, marker_indices].mean(axis=1)
    return scores, {
        "state_count": len(contract["states"]),
        "states_with_observed_markers": int(sum(count > 0 for count in coverage.values())),
        "marker_overlap_by_state": coverage,
    }
