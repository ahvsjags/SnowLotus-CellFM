from __future__ import annotations

import argparse
from pathlib import Path

from snowcell.config import ExperimentConfig


def validate_configs(paths: list[Path]) -> list[Path]:
    validated: list[Path] = []
    for path in paths:
        config = ExperimentConfig.load(path)
        config.validate()
        validated.append(path)
    return validated


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate SnowLotus-CellFM experiment YAML files")
    parser.add_argument("configs", nargs="+", type=Path)
    args = parser.parse_args()
    for path in validate_configs(args.configs):
        print(f"config_ok\t{path.as_posix()}")


if __name__ == "__main__":
    main()
