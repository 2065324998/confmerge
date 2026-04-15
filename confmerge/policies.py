"""Merge policy definitions for configuration namespaces.

Different configuration namespaces follow different merge rules to enforce
organizational policies:

- Security/auth/TLS keys use "restrictive-only" merging: overrides can
  tighten settings but never loosen them. For example, a team cannot
  increase session timeouts beyond the organization's default.

- Feature flag keys use "cascade" merging: if a feature is disabled at
  any configuration level, it stays disabled regardless of what lower-
  priority sources specify. This prevents accidental feature enablement.

- All other keys use standard deep merge (last writer wins).
"""

from enum import Enum


class MergePolicy(Enum):
    """Merge policy types for configuration namespaces."""
    STANDARD = "standard"
    RESTRICTIVE = "restrictive"
    FEATURE_CASCADE = "feature_cascade"


# Namespace-to-policy mapping. Keys are prefixes matched against the
# top-level namespace of dotted key paths.
NAMESPACE_POLICIES = {
    "security": MergePolicy.RESTRICTIVE,
    "auth": MergePolicy.RESTRICTIVE,
    "tls": MergePolicy.RESTRICTIVE,
    "compliance": MergePolicy.RESTRICTIVE,
    "features": MergePolicy.FEATURE_CASCADE,
}


def get_policy_for_key(key_path):
    """Determine the merge policy for a given dotted key path.

    Looks up the top-level namespace (the part before the first dot)
    and returns the corresponding merge policy. Returns STANDARD if
    no specific policy is configured.

    Examples:
        get_policy_for_key("security.session_timeout") -> RESTRICTIVE
        get_policy_for_key("features.beta.enabled") -> FEATURE_CASCADE
        get_policy_for_key("database.host") -> STANDARD
    """
    top_namespace = key_path.split(".")[0]
    return NAMESPACE_POLICIES.get(top_namespace, MergePolicy.STANDARD)


def is_more_restrictive(override_value, base_value):
    """Check if the override value is at least as restrictive as the base.

    Used for security/auth/TLS namespace merging. An override is only
    allowed if it makes the setting more restrictive (or equally
    restrictive).

    Restrictiveness rules by type:
    - Booleans: True (enabled/required) is more restrictive than False.
      Example: require_mfa=True is more restrictive than require_mfa=False.
    - Numbers: Lower values are more restrictive (shorter timeouts,
      fewer retries, smaller batch sizes).
    - Lists: Subsets are more restrictive (fewer allowed items).
    - Other types: Always allowed (no restriction semantics defined).

    Returns True if the override should be accepted, False if it should
    be rejected in favor of the base value.
    """
    # Mixed types: allow the override (can't compare meaningfully)
    if type(override_value) != type(base_value):
        return True

    # Booleans: True (enabled/required) is more restrictive than False.
    # Must check bool BEFORE int/float because bool is a subclass of int.
    if isinstance(override_value, bool):
        return override_value >= base_value

    # Numbers: Lower values are more restrictive (shorter timeouts,
    # fewer retries, smaller batch sizes).
    if isinstance(override_value, (int, float)):
        return override_value <= base_value

    # Lists: override must be a subset of base (narrowing is restrictive)
    if isinstance(override_value, list):
        return set(override_value).issubset(set(base_value))

    # Strings and other types: always allow
    return True
