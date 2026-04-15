"""Configuration loading pipeline.

Orchestrates loading configuration from multiple sources in priority order:
1. Default values (lowest priority)
2. Configuration file (YAML/JSON)
3. Environment variables (highest priority)

After merging, variable interpolation resolves ${key} references.
"""

from copy import deepcopy

from confmerge.merger import deep_merge
from confmerge.loader import load_file
from confmerge.sources import load_env
from confmerge.interpolate import interpolate


def load_config(defaults=None, config_path=None, env_prefix="APP"):
    """Load configuration from all sources and return the merged result.

    Args:
        defaults: Base configuration dict with default values.
        config_path: Path to a YAML or JSON config file (optional).
        env_prefix: Prefix for environment variables (default: "APP").

    Returns:
        Merged configuration dict with interpolated values.
    """
    result = deepcopy(defaults) if defaults else {}

    if config_path:
        file_config = load_file(config_path)
        result = deep_merge(result, file_config)

    env_config = load_env(env_prefix)
    result = deep_merge(result, env_config)

    # Resolve ${key} references after all sources are merged
    result = interpolate(result)

    return result
