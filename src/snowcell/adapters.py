from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def normalize_species(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", (value or "").lower())
    return " ".join(value.split())


@dataclass(frozen=True)
class PlantAdapter:
    adapter_id: str
    species: str
    aliases: tuple[str, ...]
    status: str
    transfer_mode: str
    gene_id_namespace: str
    ortholog_map: str | None
    supervised_head: str | None
    tasks: tuple[str, ...]
    evidence: Any

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PlantAdapter":
        return cls(
            adapter_id=str(value["adapter_id"]),
            species=str(value["species"]),
            aliases=tuple(str(item) for item in value.get("aliases", [])),
            status=str(value.get("status", "unknown")),
            transfer_mode=str(value.get("transfer_mode", "exact_gene_ids_then_ortholog_map")),
            gene_id_namespace=str(value.get("gene_id_namespace", "dataset_defined")),
            ortholog_map=value.get("ortholog_map"),
            supervised_head=value.get("supervised_head"),
            tasks=tuple(str(item) for item in value.get("tasks", [])),
            evidence=value.get("evidence"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "species": self.species,
            "aliases": list(self.aliases),
            "status": self.status,
            "transfer_mode": self.transfer_mode,
            "gene_id_namespace": self.gene_id_namespace,
            "ortholog_map": self.ortholog_map,
            "supervised_head": self.supervised_head,
            "tasks": list(self.tasks),
            "evidence": self.evidence,
        }


class PlantAdapterRegistry:
    def __init__(self, adapters: list[PlantAdapter], fallback_adapter: str = "plant_universal") -> None:
        if not adapters:
            raise ValueError("plant adapter registry cannot be empty")
        self.adapters = tuple(adapters)
        self.fallback_adapter = fallback_adapter
        self._by_id = {item.adapter_id: item for item in self.adapters}
        self._by_name: dict[str, PlantAdapter] = {}
        for item in self.adapters:
            for name in (item.species, *item.aliases):
                key = normalize_species(name)
                if key:
                    self._by_name[key] = item

    @classmethod
    def from_json(cls, path: str | Path) -> "PlantAdapterRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        adapters = [PlantAdapter.from_dict(item) for item in payload.get("adapters", [])]
        return cls(adapters, fallback_adapter=str(payload.get("fallback_adapter", "plant_universal")))

    def resolve(self, species: str | None) -> tuple[PlantAdapter, bool]:
        key = normalize_species(species or "")
        if key and key in self._by_name:
            return self._by_name[key], False
        if self.fallback_adapter not in self._by_id:
            raise KeyError(f"fallback adapter not found: {self.fallback_adapter}")
        return self._by_id[self.fallback_adapter], True

    def get(self, adapter_id: str) -> PlantAdapter:
        return self._by_id[adapter_id]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fallback_adapter": self.fallback_adapter,
            "adapter_count": len(self.adapters),
            "adapters": [item.to_dict() for item in self.adapters],
        }


def load_registry(path: str | Path) -> PlantAdapterRegistry:
    return PlantAdapterRegistry.from_json(path)
