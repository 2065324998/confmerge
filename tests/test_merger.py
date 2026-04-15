"""Tests for deep merge functionality."""

from confmerge.merger import deep_merge, merge_configs


class TestDeepMerge:
    def test_merge_scalar_values(self):
        base = {"a": 1, "b": "hello"}
        override = {"a": 2}
        result = deep_merge(base, override)
        assert result["a"] == 2
        assert result["b"] == "hello"

    def test_merge_nested_dicts(self):
        base = {"db": {"host": "localhost", "port": 5432}}
        override = {"db": {"port": 5433}}
        result = deep_merge(base, override)
        assert result["db"]["host"] == "localhost"
        assert result["db"]["port"] == 5433

    def test_merge_adds_new_keys(self):
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_merge_lists_extend_default(self):
        base = {"items": [1, 2]}
        override = {"items": [3, 4]}
        result = deep_merge(base, override)
        assert result["items"] == [1, 2, 3, 4]

    def test_merge_lists_replace(self):
        base = {"items": [1, 2]}
        override = {"items": [3, 4]}
        result = deep_merge(base, override, list_strategy="replace")
        assert result["items"] == [3, 4]

    def test_merge_lists_unique(self):
        base = {"items": [1, 2, 3]}
        override = {"items": [2, 3, 4]}
        result = deep_merge(base, override, list_strategy="unique")
        assert result["items"] == [1, 2, 3, 4]

    def test_merge_strategy_from_metadata(self):
        """_list_strategy key in override controls list merge behavior."""
        base = {"items": [1, 2]}
        override = {"_list_strategy": "replace", "items": [3, 4]}
        result = deep_merge(base, override)
        assert result["items"] == [3, 4]

    def test_merge_strategy_key_not_in_result(self):
        """_list_strategy metadata should not appear in merged output."""
        base = {"items": [1, 2]}
        override = {"_list_strategy": "replace", "items": [3, 4]}
        result = deep_merge(base, override)
        assert "_list_strategy" not in result

    def test_merge_none_not_overwritten_by_empty(self):
        """None (explicitly disabled) should not be re-enabled by empty dict."""
        base = {"feature": None}
        override = {"feature": {}}
        result = deep_merge(base, override)
        assert result["feature"] is None

    def test_merge_override_with_none(self):
        """Overriding with None should disable the feature."""
        base = {"feature": {"enabled": True, "timeout": 30}}
        override = {"feature": None}
        result = deep_merge(base, override)
        assert result["feature"] is None

    def test_merge_deeply_nested(self):
        base = {"a": {"b": {"c": {"d": 1}}}}
        override = {"a": {"b": {"c": {"d": 2, "e": 3}}}}
        result = deep_merge(base, override)
        assert result["a"]["b"]["c"] == {"d": 2, "e": 3}

    def test_merge_empty_override(self):
        base = {"a": 1, "b": 2}
        result = deep_merge(base, {})
        assert result == {"a": 1, "b": 2}

    def test_merge_empty_base(self):
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_merge_preserves_base(self):
        """deep_merge should not modify the original base dict."""
        base = {"a": 1, "nested": {"b": 2}}
        original_base = {"a": 1, "nested": {"b": 2}}
        deep_merge(base, {"a": 99, "nested": {"b": 99}})
        assert base == original_base


class TestMergeConfigs:
    def test_merge_multiple_configs(self):
        result = merge_configs(
            {"a": 1, "b": 2},
            {"b": 3, "c": 4},
            {"c": 5, "d": 6},
        )
        assert result == {"a": 1, "b": 3, "c": 5, "d": 6}

    def test_merge_configs_empty(self):
        assert merge_configs() == {}

    def test_merge_configs_single(self):
        result = merge_configs({"a": 1})
        assert result == {"a": 1}
