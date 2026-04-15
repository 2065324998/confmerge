"""Custom validation rules beyond basic schema types.

Provides validators for common patterns like port ranges, URLs, emails,
file paths, and enum values. Includes a ValidatorRegistry for composing
multiple validators together.
"""

import re
from pathlib import Path


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_port(value, min_port=1, max_port=65535):
    """Validate that a value is a valid port number.

    Args:
        value: Value to validate
        min_port: Minimum valid port (default: 1)
        max_port: Maximum valid port (default: 65535)

    Returns:
        True if valid

    Raises:
        ValidationError: If value is not a valid port
    """
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Port must be an integer, got {type(value).__name__}")

    if not (min_port <= port <= max_port):
        raise ValidationError(
            f"Port {port} out of range [{min_port}, {max_port}]"
        )

    return True


def validate_port_range(value):
    """Validate a port or port range string.

    Accepts single ports (e.g., "8080") or ranges (e.g., "8000-8100").

    Args:
        value: Port or port range string

    Returns:
        True if valid

    Raises:
        ValidationError: If value is not a valid port or range
    """
    if isinstance(value, int):
        return validate_port(value)

    if not isinstance(value, str):
        raise ValidationError(
            f"Port range must be string or int, got {type(value).__name__}"
        )

    # Check for range format
    if "-" in value:
        parts = value.split("-")
        if len(parts) != 2:
            raise ValidationError(f"Invalid port range format: {value}")

        try:
            start = int(parts[0])
            end = int(parts[1])
        except ValueError:
            raise ValidationError(f"Invalid port range format: {value}")

        validate_port(start)
        validate_port(end)

        if start > end:
            raise ValidationError(f"Invalid port range: start > end ({start} > {end})")
    else:
        validate_port(int(value))

    return True


def validate_url(value, schemes=None):
    """Validate that a value is a well-formed URL.

    Args:
        value: Value to validate
        schemes: List of allowed schemes (e.g., ["http", "https"])
                If None, all schemes are allowed.

    Returns:
        True if valid

    Raises:
        ValidationError: If value is not a valid URL
    """
    if not isinstance(value, str):
        raise ValidationError(f"URL must be a string, got {type(value).__name__}")

    # Basic URL pattern check
    url_pattern = re.compile(
        r"^(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*):\/\/"  # scheme
        r"(?P<host>[^\s\/:?#]+)"  # host
        r"(?::(?P<port>\d+))?"  # optional port
        r"(?P<path>\/[^\s?#]*)?"  # optional path
        r"(?:\?(?P<query>[^\s#]*))?"  # optional query
        r"(?:#(?P<fragment>[^\s]*))?$"  # optional fragment
    )

    match = url_pattern.match(value)
    if not match:
        raise ValidationError(f"Invalid URL format: {value}")

    # Check scheme if restrictions specified
    if schemes is not None:
        scheme = match.group("scheme").lower()
        if scheme not in schemes:
            raise ValidationError(
                f"URL scheme '{scheme}' not in allowed schemes: {schemes}"
            )

    return True


def validate_email(value):
    """Validate that a value is a well-formed email address.

    Args:
        value: Value to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If value is not a valid email
    """
    if not isinstance(value, str):
        raise ValidationError(f"Email must be a string, got {type(value).__name__}")

    # Basic email pattern (not RFC-compliant, but good enough for config validation)
    email_pattern = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    if not email_pattern.match(value):
        raise ValidationError(f"Invalid email format: {value}")

    return True


def validate_path_exists(value, must_be_file=False, must_be_dir=False):
    """Validate that a path exists on the filesystem.

    Args:
        value: Path string to validate
        must_be_file: If True, path must be a file (not directory)
        must_be_dir: If True, path must be a directory (not file)

    Returns:
        True if valid

    Raises:
        ValidationError: If path doesn't exist or doesn't match requirements
    """
    if not isinstance(value, (str, Path)):
        raise ValidationError(
            f"Path must be string or Path object, got {type(value).__name__}"
        )

    path = Path(value)

    if not path.exists():
        raise ValidationError(f"Path does not exist: {value}")

    if must_be_file and not path.is_file():
        raise ValidationError(f"Path is not a file: {value}")

    if must_be_dir and not path.is_dir():
        raise ValidationError(f"Path is not a directory: {value}")

    return True


def validate_enum(value, allowed_values):
    """Validate that a value is in a set of allowed values.

    Args:
        value: Value to validate
        allowed_values: List/set/tuple of allowed values

    Returns:
        True if valid

    Raises:
        ValidationError: If value is not in allowed set
    """
    if value not in allowed_values:
        raise ValidationError(
            f"Value '{value}' not in allowed values: {allowed_values}"
        )

    return True


def validate_range(value, min_value=None, max_value=None):
    """Validate that a numeric value is within a range.

    Args:
        value: Numeric value to validate
        min_value: Minimum allowed value (inclusive, optional)
        max_value: Maximum allowed value (inclusive, optional)

    Returns:
        True if valid

    Raises:
        ValidationError: If value is out of range
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Range validation requires numeric value, got {type(value).__name__}"
        )

    if min_value is not None and num < min_value:
        raise ValidationError(f"Value {num} below minimum {min_value}")

    if max_value is not None and num > max_value:
        raise ValidationError(f"Value {num} above maximum {max_value}")

    return True


class ValidatorRegistry:
    """Registry for composing multiple validators together.

    Allows registering multiple validation functions and running them
    all against a value.
    """

    def __init__(self):
        """Initialize an empty validator registry."""
        self._validators = []

    def add(self, validator, *args, **kwargs):
        """Add a validator function to the registry.

        Args:
            validator: Validation function (should raise ValidationError on failure)
            *args: Positional arguments to pass to validator
            **kwargs: Keyword arguments to pass to validator

        Returns:
            Self for method chaining
        """
        self._validators.append((validator, args, kwargs))
        return self

    def validate(self, value):
        """Run all registered validators against a value.

        Args:
            value: Value to validate

        Returns:
            True if all validators pass

        Raises:
            ValidationError: If any validator fails (first failure wins)
        """
        for validator, args, kwargs in self._validators:
            validator(value, *args, **kwargs)

        return True

    def clear(self):
        """Remove all validators from the registry."""
        self._validators.clear()

    def __len__(self):
        """Return the number of registered validators."""
        return len(self._validators)


def create_validator(*validators):
    """Create a ValidatorRegistry with the given validators.

    Convenience function for creating a registry with multiple validators.

    Args:
        *validators: Tuples of (validator_func, args, kwargs) or just validator_func

    Returns:
        ValidatorRegistry instance

    Example:
        validator = create_validator(
            (validate_range, (), {"min_value": 0, "max_value": 100}),
            validate_port
        )
    """
    registry = ValidatorRegistry()

    for item in validators:
        if isinstance(item, tuple):
            validator, *rest = item
            args = rest[0] if rest else ()
            kwargs = rest[1] if len(rest) > 1 else {}
            registry.add(validator, *args, **kwargs)
        else:
            registry.add(item)

    return registry
