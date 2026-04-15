"""File-based configuration loading.

Supports YAML (.yaml, .yml) and JSON (.json) configuration files.
"""

import json
from pathlib import Path

import yaml


def load_file(path):
    """Load a configuration dict from a YAML or JSON file.

    File format is determined by extension:
    - .yaml, .yml -> YAML
    - .json -> JSON

    Returns an empty dict if the file is empty.
    Raises FileNotFoundError if the file doesn't exist.
    Raises ValueError for unsupported file extensions.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if not text.strip():
        return {}

    if suffix in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    elif suffix == ".json":
        return json.loads(text)
    else:
        raise ValueError(
            f"Unsupported config file format: {suffix}. "
            f"Use .yaml, .yml, or .json"
        )
