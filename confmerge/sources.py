"""Environment variable configuration source.

Loads configuration from environment variables with a common prefix.
Variable names are converted to nested dict keys using double-underscore
as a nesting separator.

Example:
    APP_DATABASE__HOST=localhost  ->  {"database": {"host": "localhost"}}
    APP_DATABASE__PORT=5432       ->  {"database": {"port": 5432}}
    APP_DEBUG=true                ->  {"debug": True}
"""

import os

from confmerge.coerce import coerce_value


def load_env(prefix="APP"):
    """Load configuration from environment variables.

    Scans os.environ for variables starting with '{prefix}_' and builds
    a nested dict. Double underscores in the variable name indicate
    nesting levels.

    Values are automatically coerced to appropriate Python types
    (bool, int, float) via coerce_value().
    """
    config = {}
    prefix_with_sep = prefix + "_"

    for env_name, env_value in sorted(os.environ.items()):
        if not env_name.startswith(prefix_with_sep):
            continue

        dotted_key = _env_to_key(env_name, prefix)
        coerced = coerce_value(env_value)
        _set_nested(config, dotted_key, coerced)

    return config


def _env_to_key(env_name, prefix):
    """Convert an environment variable name to a dotted config key.

    Strips the prefix and separator, lowercases the remainder,
    and converts double underscores to dots.

    Example:
        _env_to_key("APP_DATABASE__HOST", "APP") -> "database.host"
    """
    key = env_name[len(prefix) + 1:]
    key = key.lower()
    key = key.replace("__", ".")
    return key


def _set_nested(config, dotted_key, value):
    """Set a value in a nested dict using a dotted key path.

    Creates intermediate dicts as needed. Skips empty/unset values
    from environment to avoid polluting config with blank entries.
    """
    parts = dotted_key.split(".")
    current = config

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            # Don't overwrite a scalar value with a nested dict
            return
        current = current[part]

    if value:
        current[parts[-1]] = value
