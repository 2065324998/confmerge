"""Configuration export and serialization to various formats.

Provides functions to export configuration dictionaries to YAML, JSON, TOML,
and dotenv formats. Includes flattening logic for dotenv format and
pretty-printing options for human-readable output.
"""

import json


class SerializerError(Exception):
    """Raised when serialization operations fail."""
    pass


def to_json(config, pretty=True, indent=2):
    """Serialize configuration to JSON format.

    Args:
        config: Configuration dictionary
        pretty: If True, format with indentation (default: True)
        indent: Spaces per indentation level (default: 2)

    Returns:
        JSON string

    Raises:
        SerializerError: If serialization fails
    """
    try:
        if pretty:
            return json.dumps(config, indent=indent, sort_keys=True)
        else:
            return json.dumps(config, sort_keys=True)
    except (TypeError, ValueError) as e:
        raise SerializerError(f"JSON serialization failed: {e}")


def to_yaml(config, indent=2):
    """Serialize configuration to YAML format.

    Args:
        config: Configuration dictionary
        indent: Spaces per indentation level (default: 2)

    Returns:
        YAML string (simulated - basic format without external deps)

    Note:
        This is a simplified YAML serializer that doesn't require PyYAML.
        For production use with complex structures, consider using PyYAML.
    """
    return _dict_to_yaml(config, indent=indent, level=0)


def _dict_to_yaml(obj, indent=2, level=0):
    """Convert a dictionary to YAML format recursively.

    Args:
        obj: Object to convert
        indent: Spaces per indentation level
        level: Current nesting level

    Returns:
        YAML string representation
    """
    lines = []
    base_indent = " " * (indent * level)

    if isinstance(obj, dict):
        for key, value in sorted(obj.items()):
            if isinstance(value, dict):
                lines.append(f"{base_indent}{key}:")
                lines.append(_dict_to_yaml(value, indent, level + 1))
            elif isinstance(value, list):
                lines.append(f"{base_indent}{key}:")
                for item in value:
                    if isinstance(item, (dict, list)):
                        nested = _dict_to_yaml(item, indent, level + 1)
                        # Add list marker to first line
                        first_line, *rest = nested.split("\n")
                        lines.append(f"{' ' * (indent * (level + 1))}- {first_line.strip()}")
                        lines.extend(rest)
                    else:
                        item_str = _yaml_value(item)
                        lines.append(f"{' ' * (indent * (level + 1))}- {item_str}")
            else:
                value_str = _yaml_value(value)
                lines.append(f"{base_indent}{key}: {value_str}")
    elif isinstance(obj, list):
        for item in obj:
            item_str = _yaml_value(item)
            lines.append(f"{base_indent}- {item_str}")
    else:
        return f"{base_indent}{_yaml_value(obj)}"

    return "\n".join(lines)


def _yaml_value(value):
    """Format a value for YAML output.

    Args:
        value: Value to format

    Returns:
        String representation suitable for YAML
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        # Quote strings that contain special characters
        if any(c in value for c in [":", "#", "\n", "  "]) or value in ["true", "false", "null"]:
            return f'"{value}"'
        return value
    else:
        return str(value)


def to_toml(config):
    """Serialize configuration to TOML format.

    Args:
        config: Configuration dictionary

    Returns:
        TOML string (simulated - basic format without external deps)

    Note:
        This is a simplified TOML serializer. Only handles basic structures.
        For production use, consider using the tomli/tomli_w libraries.
    """
    lines = []

    # First, output top-level scalar values and simple lists
    for key, value in sorted(config.items()):
        if not isinstance(value, dict):
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Array of tables - handle later
                continue
            else:
                lines.append(f"{key} = {_toml_value(value)}")

    # Then output tables (nested dicts)
    for key, value in sorted(config.items()):
        if isinstance(value, dict):
            lines.append(f"\n[{key}]")
            for subkey, subvalue in sorted(value.items()):
                if not isinstance(subvalue, (dict, list)):
                    lines.append(f"{subkey} = {_toml_value(subvalue)}")
            # Handle nested tables
            for subkey, subvalue in sorted(value.items()):
                if isinstance(subvalue, dict):
                    lines.append(f"\n[{key}.{subkey}]")
                    for k, v in sorted(subvalue.items()):
                        if not isinstance(v, (dict, list)):
                            lines.append(f"{k} = {_toml_value(v)}")
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Array of tables
            for item in value:
                lines.append(f"\n[[{key}]]")
                for k, v in sorted(item.items()):
                    if not isinstance(v, (dict, list)):
                        lines.append(f"{k} = {_toml_value(v)}")

    return "\n".join(lines)


def _toml_value(value):
    """Format a value for TOML output.

    Args:
        value: Value to format

    Returns:
        String representation suitable for TOML
    """
    if value is None:
        return '""'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        items = [_toml_value(item) for item in value]
        return "[" + ", ".join(items) + "]"
    else:
        return str(value)


def to_dotenv(config, prefix=""):
    """Serialize configuration to dotenv format.

    Flattens nested dictionaries into KEY=value pairs. Nested keys are
    joined with underscores. Lists are not supported (will be JSON-encoded).

    Args:
        config: Configuration dictionary
        prefix: Optional prefix for all keys (e.g., "APP_")

    Returns:
        Dotenv format string (one KEY=value per line)

    Example:
        {"db": {"host": "localhost", "port": 5432}}
        becomes:
        DB_HOST=localhost
        DB_PORT=5432
    """
    flat = _flatten_dict(config)
    lines = []

    for key, value in sorted(flat.items()):
        env_key = prefix + key.upper()
        env_value = _dotenv_value(value)
        lines.append(f"{env_key}={env_value}")

    return "\n".join(lines)


def _flatten_dict(d, parent_key="", sep="_"):
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Current parent key path
        sep: Separator for joining keys (default: "_")

    Returns:
        Flattened dictionary with joined keys
    """
    items = []

    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(_flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))

    return dict(items)


def _dotenv_value(value):
    """Format a value for dotenv output.

    Args:
        value: Value to format

    Returns:
        String representation suitable for dotenv format
    """
    if value is None:
        return ""
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        # Quote if contains spaces or special characters
        if " " in value or any(c in value for c in ["#", "=", "\n"]):
            return f'"{value}"'
        return value
    elif isinstance(value, (list, dict)):
        # Encode complex types as JSON
        return json.dumps(value)
    else:
        return str(value)


def export(config, format="json", **kwargs):
    """Export configuration to specified format.

    Args:
        config: Configuration dictionary
        format: Output format ("json", "yaml", "toml", or "dotenv")
        **kwargs: Format-specific options passed to the serializer

    Returns:
        Serialized configuration string

    Raises:
        SerializerError: If format is unknown or serialization fails
    """
    format = format.lower()

    if format == "json":
        return to_json(config, **kwargs)
    elif format == "yaml":
        return to_yaml(config, **kwargs)
    elif format == "toml":
        return to_toml(config, **kwargs)
    elif format == "dotenv":
        return to_dotenv(config, **kwargs)
    else:
        raise SerializerError(f"Unknown format: {format}")
