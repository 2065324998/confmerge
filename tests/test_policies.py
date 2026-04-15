"""Tests for merge policy definitions and restrictiveness checks."""

from confmerge.policies import (
    MergePolicy,
    get_policy_for_key,
    is_more_restrictive,
)
from confmerge.merger import deep_merge


class TestGetPolicyForKey:
    def test_security_namespace(self):
        assert get_policy_for_key("security.session_timeout") == MergePolicy.RESTRICTIVE

    def test_auth_namespace(self):
        assert get_policy_for_key("auth.providers") == MergePolicy.RESTRICTIVE

    def test_tls_namespace(self):
        assert get_policy_for_key("tls.min_version") == MergePolicy.RESTRICTIVE

    def test_features_namespace(self):
        assert get_policy_for_key("features.beta.enabled") == MergePolicy.FEATURE_CASCADE

    def test_standard_namespace(self):
        assert get_policy_for_key("database.host") == MergePolicy.STANDARD

    def test_unknown_namespace(self):
        assert get_policy_for_key("custom.setting") == MergePolicy.STANDARD

    def test_top_level_key(self):
        assert get_policy_for_key("debug") == MergePolicy.STANDARD


class TestIsMoreRestrictive:
    """Tests for the restrictiveness comparison logic.

    IMPORTANT: These tests validate the CORRECT behavior of the
    boolean comparison. Booleans and numerics have DIFFERENT
    restrictiveness semantics — do not conflate them.
    """

    def test_boolean_enable_is_more_restrictive(self):
        """Enabling a security requirement IS more restrictive."""
        assert is_more_restrictive(True, False) is True

    def test_boolean_disable_is_less_restrictive(self):
        """Disabling a security requirement is NOT more restrictive."""
        assert is_more_restrictive(False, True) is False

    def test_boolean_same_value_allowed(self):
        """Same boolean value is equally restrictive (allowed)."""
        assert is_more_restrictive(True, True) is True
        assert is_more_restrictive(False, False) is True

    def test_list_subset_is_more_restrictive(self):
        """A subset of allowed items IS more restrictive."""
        assert is_more_restrictive(["a"], ["a", "b", "c"]) is True

    def test_list_superset_is_less_restrictive(self):
        """A superset of allowed items is NOT more restrictive."""
        assert is_more_restrictive(["a", "b", "c", "d"], ["a", "b"]) is False

    def test_list_same_items_allowed(self):
        """Same list is equally restrictive (allowed)."""
        assert is_more_restrictive(["a", "b"], ["a", "b"]) is True

    def test_mixed_types_always_allowed(self):
        """Mixed types can't be compared, so allow the override."""
        assert is_more_restrictive("high", 5) is True
        assert is_more_restrictive(True, "yes") is True

    def test_strings_always_allowed(self):
        """String overrides are always allowed (no ordering)."""
        assert is_more_restrictive("aes-256", "aes-128") is True
        assert is_more_restrictive("TLSv1.2", "TLSv1.3") is True


class TestRestrictiveMerge:
    """Tests for restrictive merge behavior through deep_merge."""

    def test_security_boolean_enable_mfa(self):
        """Enabling MFA (True) should override disabled (False)."""
        result = deep_merge(
            {"security": {"require_mfa": False}},
            {"security": {"require_mfa": True}},
        )
        assert result["security"]["require_mfa"] is True

    def test_security_boolean_reject_disable_mfa(self):
        """Disabling MFA (False) should NOT override enabled (True)."""
        result = deep_merge(
            {"security": {"require_mfa": True}},
            {"security": {"require_mfa": False}},
        )
        assert result["security"]["require_mfa"] is True

    def test_security_list_narrows_origins(self):
        """Narrowing allowed origins should be accepted."""
        result = deep_merge(
            {"security": {"allowed_origins": ["a.com", "b.com", "c.com"]}},
            {"security": {"allowed_origins": ["a.com"]}},
        )
        assert result["security"]["allowed_origins"] == ["a.com"]

    def test_security_list_rejects_widening(self):
        """Widening allowed origins should be rejected."""
        result = deep_merge(
            {"security": {"allowed_origins": ["a.com"]}},
            {"security": {"allowed_origins": ["a.com", "b.com", "evil.com"]}},
        )
        assert result["security"]["allowed_origins"] == ["a.com"]

    def test_security_string_override_allowed(self):
        """String security values can always be overridden."""
        result = deep_merge(
            {"security": {"cipher_suite": "AES-128-GCM"}},
            {"security": {"cipher_suite": "AES-256-GCM"}},
        )
        assert result["security"]["cipher_suite"] == "AES-256-GCM"

    def test_standard_key_not_affected_by_policy(self):
        """Non-security keys should use standard last-writer-wins."""
        result = deep_merge(
            {"database": {"timeout": 5}},
            {"database": {"timeout": 30}},
        )
        assert result["database"]["timeout"] == 30


class TestFeatureCascadeMerge:
    """Tests for feature flag merge behavior."""

    def test_feature_non_boolean_config_overrides(self):
        """Non-boolean feature config should use standard override."""
        result = deep_merge(
            {"features": {"beta": {"config": {"timeout": 30}}}},
            {"features": {"beta": {"config": {"timeout": 60}}}},
        )
        assert result["features"]["beta"]["config"]["timeout"] == 60

    def test_feature_new_key_added(self):
        """New feature keys should be added normally."""
        result = deep_merge(
            {"features": {"alpha": {"enabled": True}}},
            {"features": {"beta": {"enabled": True}}},
        )
        assert result["features"]["alpha"]["enabled"] is True
        assert result["features"]["beta"]["enabled"] is True
