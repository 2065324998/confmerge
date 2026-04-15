"""Tests for custom validation rules."""

import pytest
import tempfile
from pathlib import Path
from confmerge.validators import (
    validate_port,
    validate_port_range,
    validate_url,
    validate_email,
    validate_path_exists,
    validate_enum,
    validate_range,
    ValidatorRegistry,
    ValidationError,
    create_validator,
)


class TestPortValidator:
    def test_validate_port_valid(self):
        assert validate_port(8080)
        assert validate_port(80)
        assert validate_port(65535)

    def test_validate_port_out_of_range(self):
        with pytest.raises(ValidationError, match="out of range"):
            validate_port(0)

        with pytest.raises(ValidationError, match="out of range"):
            validate_port(65536)

    def test_validate_port_invalid_type(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_port("not a number")

    def test_validate_port_custom_range(self):
        assert validate_port(8080, min_port=8000, max_port=9000)

        with pytest.raises(ValidationError, match="out of range"):
            validate_port(7999, min_port=8000, max_port=9000)


class TestPortRangeValidator:
    def test_validate_port_range_single_port(self):
        assert validate_port_range(8080)
        assert validate_port_range("8080")

    def test_validate_port_range_valid_range(self):
        assert validate_port_range("8000-8100")

    def test_validate_port_range_invalid_range(self):
        with pytest.raises(ValidationError, match="Invalid port range"):
            validate_port_range("8100-8000")  # start > end

    def test_validate_port_range_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid port range format"):
            validate_port_range("8000-8100-8200")

        with pytest.raises(ValidationError, match="Invalid port range format"):
            validate_port_range("abc-def")

    def test_validate_port_range_invalid_type(self):
        with pytest.raises(ValidationError, match="must be string or int"):
            validate_port_range([8080])


class TestUrlValidator:
    def test_validate_url_valid_http(self):
        assert validate_url("http://example.com")
        assert validate_url("https://example.com")

    def test_validate_url_with_port(self):
        assert validate_url("http://example.com:8080")

    def test_validate_url_with_path(self):
        assert validate_url("https://example.com/path/to/resource")

    def test_validate_url_with_query(self):
        assert validate_url("https://example.com/path?key=value")

    def test_validate_url_with_fragment(self):
        assert validate_url("https://example.com/path#section")

    def test_validate_url_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid URL format"):
            validate_url("not a url")

        with pytest.raises(ValidationError, match="Invalid URL format"):
            validate_url("example.com")  # missing scheme

    def test_validate_url_scheme_restriction(self):
        assert validate_url("https://example.com", schemes=["https"])

        with pytest.raises(ValidationError, match="not in allowed schemes"):
            validate_url("http://example.com", schemes=["https"])

    def test_validate_url_invalid_type(self):
        with pytest.raises(ValidationError, match="must be a string"):
            validate_url(123)


class TestEmailValidator:
    def test_validate_email_valid(self):
        assert validate_email("user@example.com")
        assert validate_email("test.user@example.co.uk")
        assert validate_email("user+tag@example.com")

    def test_validate_email_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("not an email")

        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@")

        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("@example.com")

    def test_validate_email_invalid_type(self):
        with pytest.raises(ValidationError, match="must be a string"):
            validate_email(123)


class TestPathExistsValidator:
    def test_validate_path_exists_valid(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name

        try:
            assert validate_path_exists(path)
        finally:
            Path(path).unlink()

    def test_validate_path_not_exists(self):
        with pytest.raises(ValidationError, match="does not exist"):
            validate_path_exists("/nonexistent/path")

    def test_validate_path_must_be_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="not a file"):
                validate_path_exists(tmpdir, must_be_file=True)

    def test_validate_path_must_be_dir(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name

        try:
            with pytest.raises(ValidationError, match="not a directory"):
                validate_path_exists(path, must_be_dir=True)
        finally:
            Path(path).unlink()

    def test_validate_path_invalid_type(self):
        with pytest.raises(ValidationError, match="must be string or Path"):
            validate_path_exists(123)


class TestEnumValidator:
    def test_validate_enum_valid(self):
        assert validate_enum("dev", ["dev", "staging", "prod"])
        assert validate_enum(1, [1, 2, 3])

    def test_validate_enum_invalid(self):
        with pytest.raises(ValidationError, match="not in allowed values"):
            validate_enum("test", ["dev", "staging", "prod"])


class TestRangeValidator:
    def test_validate_range_valid(self):
        assert validate_range(5, min_value=0, max_value=10)
        assert validate_range(0, min_value=0)
        assert validate_range(100, max_value=100)

    def test_validate_range_below_minimum(self):
        with pytest.raises(ValidationError, match="below minimum"):
            validate_range(5, min_value=10)

    def test_validate_range_above_maximum(self):
        with pytest.raises(ValidationError, match="above maximum"):
            validate_range(15, max_value=10)

    def test_validate_range_invalid_type(self):
        with pytest.raises(ValidationError, match="requires numeric value"):
            validate_range("not a number", min_value=0)

    def test_validate_range_float_values(self):
        assert validate_range(5.5, min_value=5.0, max_value=6.0)


class TestValidatorRegistry:
    def test_add_single_validator(self):
        registry = ValidatorRegistry()
        registry.add(validate_port)
        assert len(registry) == 1

    def test_validate_with_single_validator(self):
        registry = ValidatorRegistry()
        registry.add(validate_port)
        assert registry.validate(8080)

    def test_validate_failure(self):
        registry = ValidatorRegistry()
        registry.add(validate_port)
        with pytest.raises(ValidationError):
            registry.validate(99999)

    def test_add_multiple_validators(self):
        registry = ValidatorRegistry()
        registry.add(validate_range, min_value=1000, max_value=9999)
        registry.add(validate_port)
        assert len(registry) == 2
        assert registry.validate(8080)

    def test_validate_fails_on_first_error(self):
        registry = ValidatorRegistry()
        registry.add(validate_range, min_value=1000, max_value=9999)
        registry.add(validate_email)  # Will fail if reached

        with pytest.raises(ValidationError, match="below minimum"):
            registry.validate(500)

    def test_clear_validators(self):
        registry = ValidatorRegistry()
        registry.add(validate_port)
        registry.add(validate_email)
        assert len(registry) == 2

        registry.clear()
        assert len(registry) == 0

    def test_method_chaining(self):
        registry = ValidatorRegistry()
        result = registry.add(validate_port).add(validate_range, min_value=8000)
        assert result is registry
        assert len(registry) == 2


class TestCreateValidator:
    def test_create_validator_simple(self):
        validator = create_validator(validate_port)
        assert len(validator) == 1
        assert validator.validate(8080)

    def test_create_validator_with_args(self):
        validator = create_validator(
            (validate_range, (), {"min_value": 8000, "max_value": 9000}),
            validate_port,
        )
        assert len(validator) == 2
        assert validator.validate(8080)

        with pytest.raises(ValidationError):
            validator.validate(7999)
