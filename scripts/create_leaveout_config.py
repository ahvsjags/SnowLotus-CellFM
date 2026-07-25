from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(payload: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)
    return output


def create_leaveout_config(
    base_config: str | Path,
    output: str | Path,
    leaveout_key: str,
    test_values: list[str],
    validation_values: list[str],
    data_path: str | None = None,
    output_dir: str | None = None,
) -> Path:
    if not test_values:
        raise ValueError("at least one --test-value is required")
    payload = load_yaml(base_config)
    data = payload.setdefault("data", {})
    data["split_strategy"] = "explicit_leaveout"
    data["leaveout_key"] = leaveout_key
    data["leaveout_test_values"] = test_values
    data["leaveout_validation_values"] = validation_values
    if data_path:
        data["path"] = data_path
    if output_dir:
        payload.setdefault("output", {})["directory"] = output_dir
    return write_yaml(payload, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an explicit leave-out benchmark config")
    parser.add_argument("--base-config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--leaveout-key", required=True)
    parser.add_argument("--test-value", action="append", required=True)
    parser.add_argument("--validation-value", action="append", default=[])
    parser.add_argument("--data-path")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    print(
        create_leaveout_config(
            base_config=args.base_config,
            output=args.output,
            leaveout_key=args.leaveout_key,
            test_values=args.test_value,
            validation_values=args.validation_value,
            data_path=args.data_path,
            output_dir=args.output_dir,
        )
    )


if __name__ == "__main__":
    main()
