from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def load_probe_module():
    module_path = Path(__file__).parents[1] / "scripts" / "probe_matpool_candidate_ports.py"
    spec = importlib.util.spec_from_file_location("probe_matpool_candidate_ports", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_candidate_port_parser_reads_explicit_unique_ports(tmp_path: Path) -> None:
    module = load_probe_module()
    ports_file = tmp_path / "ports.txt"
    ports_file.write_text("27683, 28186\n# comment\n27683 29243\n", encoding="utf-8")

    ports = module.read_candidate_ports(ports_file, allow_ranges=False, max_ports=64)

    assert ports == [27683, 28186, 29243]


def test_candidate_port_parser_rejects_ranges_by_default(tmp_path: Path) -> None:
    module = load_probe_module()
    ports_file = tmp_path / "ports.txt"
    ports_file.write_text("27683-27685\n", encoding="utf-8")

    with pytest.raises(ValueError, match="--allow-ranges"):
        module.read_candidate_ports(ports_file, allow_ranges=False, max_ports=64)


def test_candidate_port_parser_allows_ranges_when_explicit(tmp_path: Path) -> None:
    module = load_probe_module()
    ports_file = tmp_path / "ports.txt"
    ports_file.write_text("27683-27685\n", encoding="utf-8")

    ports = module.read_candidate_ports(ports_file, allow_ranges=True, max_ports=64)

    assert ports == [27683, 27684, 27685]
