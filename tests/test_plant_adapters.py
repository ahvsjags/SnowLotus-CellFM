from __future__ import annotations

import json
from pathlib import Path

from snowcell.adapters import PlantAdapterRegistry, normalize_species


def test_species_normalization_collapses_common_names() -> None:
    assert normalize_species("Arabidopsis_thaliana") == "arabidopsis thaliana"
    assert normalize_species("  Oryza   sativa ") == "oryza sativa"


def test_registry_resolves_registered_and_fallback_species(tmp_path: Path) -> None:
    registry_path = tmp_path / "adapters.json"
    registry_path.write_text(
        json.dumps(
            {
                "fallback_adapter": "plant_universal",
                "adapters": [
                    {
                        "adapter_id": "plant_universal",
                        "species": "__unregistered_plant__",
                        "aliases": ["unknown plant"],
                        "tasks": ["embedding"],
                    },
                    {
                        "adapter_id": "plant_arabidopsis_thaliana",
                        "species": "Arabidopsis thaliana",
                        "aliases": [],
                        "tasks": ["embedding", "annotation_transfer"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    registry = PlantAdapterRegistry.from_json(registry_path)

    registered, used_fallback = registry.resolve("Arabidopsis_thaliana")
    assert registered.adapter_id == "plant_arabidopsis_thaliana"
    assert used_fallback is False

    fallback, used_fallback = registry.resolve("A newly sequenced crop")
    assert fallback.adapter_id == "plant_universal"
    assert used_fallback is True
