"""Tests for variable interpolation in configuration values."""

import pytest

from confmerge.interpolate import interpolate


class TestInterpolate:
    def test_simple_reference(self):
        config = {"host": "localhost", "url": "${host}"}
        result = interpolate(config)
        assert result["url"] == "localhost"

    def test_nested_reference(self):
        config = {
            "database": {"host": "db.local", "port": 5432},
            "connection": "${database.host}",
        }
        result = interpolate(config)
        assert result["connection"] == "db.local"

    def test_multiple_refs_in_value(self):
        config = {
            "host": "localhost",
            "port": 8080,
            "url": "http://${host}:${port}/api",
        }
        result = interpolate(config)
        assert result["url"] == "http://localhost:8080/api"

    def test_missing_key_returns_empty(self):
        config = {"url": "http://${host}:${port}"}
        result = interpolate(config)
        assert result["url"] == "http://:"

    def test_no_references_unchanged(self):
        config = {"host": "localhost", "port": 8080}
        result = interpolate(config)
        assert result == {"host": "localhost", "port": 8080}

    def test_non_string_values_unchanged(self):
        config = {"port": 8080, "debug": True, "ratio": 0.5}
        result = interpolate(config)
        assert result == {"port": 8080, "debug": True, "ratio": 0.5}

    def test_cycle_detection_raises(self):
        config = {"a": "${b}", "b": "${a}"}
        with pytest.raises(ValueError, match="Circular reference"):
            interpolate(config)

    def test_deeply_nested_reference(self):
        config = {
            "services": {
                "api": {"host": "api.local"},
                "web": {"backend": "${services.api.host}"},
            }
        }
        result = interpolate(config)
        assert result["services"]["web"]["backend"] == "api.local"

    def test_chained_references(self):
        config = {"a": "hello", "b": "${a}", "c": "${b}"}
        result = interpolate(config)
        assert result["c"] == "hello"

    def test_self_reference_raises(self):
        config = {"a": "${a}"}
        with pytest.raises(ValueError, match="Circular reference"):
            interpolate(config)
