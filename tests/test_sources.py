"""Tests for environment variable configuration loading."""

import os
from unittest import mock

from confmerge.sources import load_env, _env_to_key, _set_nested


class TestEnvLoading:
    def test_load_env_basic(self):
        env = {"MYAPP_NAME": "testapp", "MYAPP_REGION": "us-east-1"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_env("MYAPP")
        assert result["name"] == "testapp"
        assert result["region"] == "us-east-1"

    def test_load_env_nested_keys(self):
        env = {"MYAPP_DATABASE__HOST": "db.local", "MYAPP_DATABASE__PORT": "5432"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_env("MYAPP")
        assert result["database"]["host"] == "db.local"
        assert result["database"]["port"] == 5432

    def test_load_env_with_prefix(self):
        env = {
            "MYAPP_DEBUG": "true",
            "OTHER_DEBUG": "false",
            "UNRELATED": "value",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_env("MYAPP")
        assert result == {"debug": True}

    def test_load_env_ignores_unrelated(self):
        env = {"HOME": "/home/user", "PATH": "/usr/bin", "SHELL": "/bin/bash"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_env("APP")
        assert result == {}

    def test_load_env_coerces_integers(self):
        env = {"SRV_PORT": "8080", "SRV_WORKERS": "4"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_env("SRV")
        assert result["port"] == 8080
        assert result["workers"] == 4

    def test_load_env_coerces_booleans(self):
        """Truthy boolean env vars should be coerced correctly."""
        env = {"CFG_ENABLED": "true", "CFG_ACTIVE": "yes"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_env("CFG")
        assert result["enabled"] is True
        assert result["active"] is True


class TestEnvToKey:
    def test_simple_key(self):
        assert _env_to_key("APP_NAME", "APP") == "name"

    def test_nested_key(self):
        assert _env_to_key("APP_DATABASE__HOST", "APP") == "database.host"

    def test_deep_nesting(self):
        assert _env_to_key("APP_A__B__C", "APP") == "a.b.c"

    def test_preserves_single_underscore(self):
        assert _env_to_key("APP_MY_VAR", "APP") == "my_var"


class TestSetNested:
    def test_creates_intermediate_dicts(self):
        config = {}
        _set_nested(config, "a.b.c", "value")
        assert config == {"a": {"b": {"c": "value"}}}

    def test_simple_key(self):
        config = {}
        _set_nested(config, "name", "myapp")
        assert config == {"name": "myapp"}

    def test_preserves_existing_structure(self):
        config = {"a": {"existing": 1}}
        _set_nested(config, "a.new_key", "value")
        assert config == {"a": {"existing": 1, "new_key": "value"}}
