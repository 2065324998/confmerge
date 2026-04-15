"""Tests for configuration serialization."""

import json
import pytest
from confmerge.serializer import (
    to_json,
    to_yaml,
    to_toml,
    to_dotenv,
    export,
    SerializerError,
)


class TestJsonSerializer:
    def test_to_json_simple(self):
        config = {"name": "test", "value": 42}
        result = to_json(config)
        parsed = json.loads(result)
        assert parsed == config

    def test_to_json_nested(self):
        config = {"db": {"host": "localhost", "port": 5432}}
        result = to_json(config)
        parsed = json.loads(result)
        assert parsed == config

    def test_to_json_with_list(self):
        config = {"items": [1, 2, 3]}
        result = to_json(config)
        parsed = json.loads(result)
        assert parsed == config

    def test_to_json_not_pretty(self):
        config = {"a": 1, "b": 2}
        result = to_json(config, pretty=False)
        assert "\n" not in result
        assert json.loads(result) == config

    def test_to_json_custom_indent(self):
        config = {"a": {"b": 1}}
        result = to_json(config, indent=4)
        assert "    " in result  # 4 spaces


class TestYamlSerializer:
    def test_to_yaml_simple(self):
        config = {"name": "test", "value": 42}
        result = to_yaml(config)
        assert "name: test" in result
        assert "value: 42" in result

    def test_to_yaml_nested(self):
        config = {"db": {"host": "localhost", "port": 5432}}
        result = to_yaml(config)
        assert "db:" in result
        assert "host: localhost" in result
        assert "port: 5432" in result

    def test_to_yaml_with_list(self):
        config = {"items": [1, 2, 3]}
        result = to_yaml(config)
        assert "items:" in result
        assert "- 1" in result
        assert "- 2" in result
        assert "- 3" in result

    def test_to_yaml_boolean_values(self):
        config = {"enabled": True, "disabled": False}
        result = to_yaml(config)
        assert "enabled: true" in result
        assert "disabled: false" in result

    def test_to_yaml_null_value(self):
        config = {"value": None}
        result = to_yaml(config)
        assert "value: null" in result

    def test_to_yaml_string_quoting(self):
        config = {"key": "value: with colon"}
        result = to_yaml(config)
        assert '"value: with colon"' in result


class TestTomlSerializer:
    def test_to_toml_simple(self):
        config = {"name": "test", "value": 42}
        result = to_toml(config)
        assert 'name = "test"' in result
        assert "value = 42" in result

    def test_to_toml_with_table(self):
        config = {"db": {"host": "localhost", "port": 5432}}
        result = to_toml(config)
        assert "[db]" in result
        assert 'host = "localhost"' in result
        assert "port = 5432" in result

    def test_to_toml_nested_table(self):
        config = {"a": {"b": {"c": 1}}}
        result = to_toml(config)
        assert "[a.b]" in result
        assert "c = 1" in result

    def test_to_toml_boolean_values(self):
        config = {"enabled": True, "disabled": False}
        result = to_toml(config)
        assert "enabled = true" in result
        assert "disabled = false" in result

    def test_to_toml_with_list(self):
        config = {"items": [1, 2, 3]}
        result = to_toml(config)
        assert "items = [1, 2, 3]" in result


class TestDotenvSerializer:
    def test_to_dotenv_simple(self):
        config = {"name": "test", "value": "42"}
        result = to_dotenv(config)
        assert "NAME=test" in result
        assert "VALUE=42" in result

    def test_to_dotenv_nested(self):
        config = {"db": {"host": "localhost", "port": 5432}}
        result = to_dotenv(config)
        assert "DB_HOST=localhost" in result
        assert "DB_PORT=5432" in result

    def test_to_dotenv_with_prefix(self):
        config = {"name": "test"}
        result = to_dotenv(config, prefix="APP_")
        assert "APP_NAME=test" in result

    def test_to_dotenv_boolean_values(self):
        config = {"enabled": True, "disabled": False}
        result = to_dotenv(config)
        assert "ENABLED=true" in result
        assert "DISABLED=false" in result

    def test_to_dotenv_none_value(self):
        config = {"value": None}
        result = to_dotenv(config)
        assert "VALUE=" in result

    def test_to_dotenv_string_with_spaces(self):
        config = {"name": "hello world"}
        result = to_dotenv(config)
        assert 'NAME="hello world"' in result

    def test_to_dotenv_list_as_json(self):
        config = {"items": [1, 2, 3]}
        result = to_dotenv(config)
        assert "ITEMS=[1, 2, 3]" in result or "ITEMS=[1,2,3]" in result

    def test_to_dotenv_deeply_nested(self):
        config = {"a": {"b": {"c": "value"}}}
        result = to_dotenv(config)
        assert "A_B_C=value" in result


class TestExportFunction:
    def test_export_json(self):
        config = {"name": "test"}
        result = export(config, format="json")
        assert json.loads(result) == config

    def test_export_yaml(self):
        config = {"name": "test"}
        result = export(config, format="yaml")
        assert "name: test" in result

    def test_export_toml(self):
        config = {"name": "test"}
        result = export(config, format="toml")
        assert 'name = "test"' in result

    def test_export_dotenv(self):
        config = {"name": "test"}
        result = export(config, format="dotenv")
        assert "NAME=test" in result

    def test_export_unknown_format(self):
        config = {"name": "test"}
        with pytest.raises(SerializerError, match="Unknown format"):
            export(config, format="xml")

    def test_export_case_insensitive(self):
        config = {"name": "test"}
        result = export(config, format="JSON")
        assert json.loads(result) == config
