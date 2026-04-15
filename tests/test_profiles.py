"""Tests for profile management."""

import pytest
from confmerge.profiles import (
    Profile,
    ProfileRegistry,
    ProfileError,
    register_profile,
    get_profile,
)


class TestProfile:
    def test_create_profile_without_extends(self):
        profile = Profile("dev", {"debug": True})
        assert profile.name == "dev"
        assert profile.config == {"debug": True}
        assert profile.extends is None

    def test_create_profile_with_extends(self):
        profile = Profile("dev", {"debug": True}, extends="base")
        assert profile.name == "dev"
        assert profile.extends == "base"

    def test_profile_repr(self):
        profile = Profile("dev", {}, extends="base")
        assert "dev" in repr(profile)
        assert "base" in repr(profile)


class TestProfileRegistry:
    def test_register_profile(self):
        registry = ProfileRegistry()
        profile = registry.register("dev", {"debug": True})
        assert profile.name == "dev"
        assert registry.has_profile("dev")

    def test_register_profile_invalid_name(self):
        registry = ProfileRegistry()
        with pytest.raises(ProfileError, match="non-empty string"):
            registry.register("")

        with pytest.raises(ProfileError, match="non-empty string"):
            registry.register(None)

    def test_get_profile_not_found(self):
        registry = ProfileRegistry()
        with pytest.raises(ProfileError, match="not found"):
            registry.get("nonexistent")

    def test_get_profile_without_resolve(self):
        registry = ProfileRegistry()
        registry.register("dev", {"debug": True})
        profile = registry.get("dev", resolve=False)
        assert isinstance(profile, Profile)
        assert profile.name == "dev"

    def test_resolve_single_profile(self):
        registry = ProfileRegistry()
        registry.register("dev", {"debug": True, "port": 8080})
        config = registry.resolve("dev")
        assert config == {"debug": True, "port": 8080}

    def test_resolve_with_inheritance(self):
        registry = ProfileRegistry()
        registry.register("base", {"host": "localhost", "port": 5000})
        registry.register("dev", {"debug": True}, extends="base")
        config = registry.resolve("dev")
        assert config == {"host": "localhost", "port": 5000, "debug": True}

    def test_resolve_override_parent_values(self):
        registry = ProfileRegistry()
        registry.register("base", {"port": 5000, "debug": False})
        registry.register("dev", {"debug": True}, extends="base")
        config = registry.resolve("dev")
        assert config["debug"] is True
        assert config["port"] == 5000

    def test_resolve_multi_level_inheritance(self):
        registry = ProfileRegistry()
        registry.register("base", {"a": 1, "b": 2})
        registry.register("staging", {"b": 20, "c": 3}, extends="base")
        registry.register("dev", {"c": 30, "d": 4}, extends="staging")
        config = registry.resolve("dev")
        assert config == {"a": 1, "b": 20, "c": 30, "d": 4}

    def test_resolve_circular_inheritance(self):
        registry = ProfileRegistry()
        registry.register("a", {}, extends="b")
        registry.register("b", {}, extends="c")
        registry.register("c", {}, extends="a")
        with pytest.raises(ProfileError, match="Circular"):
            registry.resolve("a")

    def test_resolve_missing_parent(self):
        registry = ProfileRegistry()
        registry.register("dev", {"debug": True}, extends="nonexistent")
        with pytest.raises(ProfileError, match="not registered"):
            registry.resolve("dev")

    def test_list_profiles(self):
        registry = ProfileRegistry()
        registry.register("dev", {})
        registry.register("prod", {})
        registry.register("staging", {})
        profiles = registry.list_profiles()
        assert profiles == ["dev", "prod", "staging"]

    def test_has_profile(self):
        registry = ProfileRegistry()
        registry.register("dev", {})
        assert registry.has_profile("dev")
        assert not registry.has_profile("prod")

    def test_unregister_profile(self):
        registry = ProfileRegistry()
        registry.register("dev", {})
        assert registry.unregister("dev")
        assert not registry.has_profile("dev")
        assert not registry.unregister("nonexistent")

    def test_clear_registry(self):
        registry = ProfileRegistry()
        registry.register("dev", {})
        registry.register("prod", {})
        registry.clear()
        assert registry.list_profiles() == []

    def test_nested_config_merge(self):
        registry = ProfileRegistry()
        registry.register("base", {"db": {"host": "localhost", "port": 5432}})
        registry.register("dev", {"db": {"port": 5433}}, extends="base")
        config = registry.resolve("dev")
        assert config["db"]["host"] == "localhost"
        assert config["db"]["port"] == 5433


class TestGlobalFunctions:
    def test_register_and_get_profile(self):
        # Note: Uses global registry, so may interact with other tests
        # In real scenarios, you'd want to reset the global registry
        profile = register_profile("test_global", {"value": 42})
        assert profile.name == "test_global"
        config = get_profile("test_global")
        assert config["value"] == 42
