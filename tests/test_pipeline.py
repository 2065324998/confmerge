"""Tests for the configuration loading pipeline."""

import os
from unittest import mock

from confmerge.pipeline import load_config


class TestPipeline:
    def test_defaults_only(self):
        defaults = {"app": {"name": "myapp", "port": 8080}}
        with mock.patch.dict(os.environ, {}, clear=True):
            result = load_config(defaults)
        assert result["app"]["name"] == "myapp"
        assert result["app"]["port"] == 8080

    def test_env_overrides_defaults(self):
        """Environment variables with truthy values override defaults."""
        defaults = {"server": {"port": 8080, "host": "localhost"}}
        env = {"APP_SERVER__PORT": "9090"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_config(defaults, env_prefix="APP")
        assert result["server"]["port"] == 9090
        assert result["server"]["host"] == "localhost"

    def test_file_overrides_defaults(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "database:\n  host: production-db\n  port: 5433\n"
        )
        defaults = {"database": {"host": "localhost", "port": 5432, "name": "mydb"}}
        with mock.patch.dict(os.environ, {}, clear=True):
            result = load_config(defaults, config_path=str(config_file))
        assert result["database"]["host"] == "production-db"
        assert result["database"]["port"] == 5433
        assert result["database"]["name"] == "mydb"

    def test_env_overrides_file(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("server:\n  port: 9090\n")
        defaults = {"server": {"port": 8080}}
        env = {"APP_SERVER__PORT": "3000"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = load_config(defaults, config_path=str(config_file))
        assert result["server"]["port"] == 3000

    def test_interpolation_within_merged_config(self, tmp_path):
        """Interpolation should resolve references in the merged config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "database:\n"
            "  host: db.production\n"
            "  port: 5432\n"
            "  url: jdbc://${database.host}:${database.port}/app\n"
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            result = load_config(config_path=str(config_file))
        assert result["database"]["url"] == "jdbc://db.production:5432/app"
