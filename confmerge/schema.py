"""Schema validation for configuration dictionaries.

Validates configuration values against a schema definition that specifies
expected types, required keys, and nested structure.
"""


class SchemaError(Exception):
    """Raised when configuration doesn't match the expected schema."""
    pass


_TYPE_MAP = {
    "string": str,
    "integer": int,
    "float": (int, float),
    "boolean": bool,
    "list": list,
    "dict": dict,
}


def validate(config, schema):
    """Validate a configuration dict against a schema.

    Schema format:
        {
            "type": "dict",
            "properties": {
                "host": {"type": "string", "required": True},
                "port": {"type": "integer"},
            }
        }

    Raises SchemaError if validation fails.
    """
    _validate_node(config, schema, path="")


def _validate_node(value, schema, path):
    """Recursively validate a config node against its schema."""
    expected_type = schema.get("type")

    if expected_type and expected_type in _TYPE_MAP:
        allowed = _TYPE_MAP[expected_type]
        if value is not None and not isinstance(value, allowed):
            raise SchemaError(
                f"Expected {expected_type} at '{path}', "
                f"got {type(value).__name__}"
            )

    if expected_type == "dict" and isinstance(value, dict):
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            prop_path = f"{path}.{prop_name}" if path else prop_name
            if prop_name in value:
                _validate_node(value[prop_name], prop_schema, prop_path)
            elif prop_schema.get("required"):
                raise SchemaError(f"Missing required key '{prop_path}'")

    if expected_type == "list" and isinstance(value, list):
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(value):
                _validate_node(item, items_schema, f"{path}[{i}]")
