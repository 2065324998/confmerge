"""Variable interpolation for configuration values.

Resolves ${dotted.key} references within string values, allowing
config values to reference other config values.

Example:
    {"host": "localhost", "url": "http://${host}:8080"}
    -> {"host": "localhost", "url": "http://localhost:8080"}
"""

import re

_REF_PATTERN = re.compile(r"\$\{([^}]+)\}")


def interpolate(config):
    """Resolve ${key} references in all string values of a config dict.

    References use dotted notation for nested keys: ${database.host}
    resolves to config["database"]["host"].

    Missing keys are replaced with an empty string.
    Circular references raise ValueError.

    Returns a new config dict with all references resolved.
    """
    flat = _flatten(config)
    resolved = {}

    for key in flat:
        resolved[key] = _resolve(key, flat, frozenset())

    return _unflatten(resolved)


def _resolve(key, flat, visiting):
    """Resolve a single key's value, following references recursively."""
    if key in visiting:
        raise ValueError(
            f"Circular reference detected: {key} "
            f"(resolution chain: {' -> '.join(visiting)} -> {key})"
        )

    value = flat.get(key)
    if not isinstance(value, str):
        return value

    if not _REF_PATTERN.search(value):
        return value

    visiting = visiting | {key}

    def _replacer(match):
        ref_key = match.group(1)
        if ref_key not in flat:
            return ""
        ref_value = _resolve(ref_key, flat, visiting)
        return str(ref_value) if ref_value is not None else ""

    return _REF_PATTERN.sub(_replacer, value)


def _flatten(config, prefix=""):
    """Flatten a nested dict to dot-notation keys.

    {"a": {"b": 1}} -> {"a.b": 1}
    """
    result = {}
    for key, value in config.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten(value, full_key))
        else:
            result[full_key] = value
    return result


def _unflatten(flat):
    """Unflatten dot-notation keys back to a nested dict.

    {"a.b": 1} -> {"a": {"b": 1}}
    """
    result = {}
    for key in sorted(flat.keys()):
        value = flat[key]
        parts = key.split(".")
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result
