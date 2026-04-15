"""Type coercion for string configuration values.

Converts string representations (typically from environment variables or
command-line arguments) to their appropriate Python types.
"""

_TRUTHY = frozenset({"true", "yes", "on", "1"})
_FALSY = frozenset({"false", "no", "off", "0"})


def coerce_value(value):
    """Coerce a string value to its appropriate Python type.

    Conversion rules (applied in order):
    - Non-string values are returned unchanged
    - Boolean strings (true/false/yes/no/on/off/1/0) -> bool
    - Integer strings -> int
    - Float strings -> float
    - Everything else stays as str

    Note: "null" and "none" are intentionally kept as strings.
    Use explicit None in Python code for null semantics.
    """
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    if not stripped:
        return value

    lower = stripped.lower()

    if lower in _TRUTHY:
        return True
    if lower in _FALSY:
        return False

    try:
        return int(stripped)
    except ValueError:
        pass

    try:
        return float(stripped)
    except ValueError:
        pass

    return value
