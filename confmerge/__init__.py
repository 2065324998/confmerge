"""Hierarchical configuration merging for Python applications.

Supports deep merging from multiple sources (defaults, files, environment
variables) with configurable list merge strategies and type coercion.
"""

from confmerge.merger import deep_merge, merge_configs
from confmerge.coerce import coerce_value
from confmerge.loader import load_file
from confmerge.sources import load_env
from confmerge.interpolate import interpolate
from confmerge.pipeline import load_config
from confmerge.schema import validate, SchemaError

__version__ = "0.3.1"

__all__ = [
    "deep_merge",
    "merge_configs",
    "coerce_value",
    "load_file",
    "load_env",
    "interpolate",
    "load_config",
    "validate",
    "SchemaError",
]
