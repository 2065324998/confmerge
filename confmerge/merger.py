"""Deep merge functionality for nested configuration dictionaries.

Supports three list merge strategies:
- 'extend': append override items to base list (default)
- 'replace': override list completely replaces base list
- 'unique': combine lists, removing duplicates while preserving order

Override dicts can include a '_list_strategy' key to control list merge
behavior for that level and below.

Merge behavior is also affected by namespace policies (see policies.py):
- Security/auth keys use restrictive-only merging
- Feature flags use cascade merging (any-false-wins)
- All other keys use standard last-writer-wins
"""

from copy import deepcopy

from confmerge.policies import (
    MergePolicy,
    get_policy_for_key,
    is_more_restrictive,
)


def deep_merge(base, override, list_strategy="extend"):
    """Deep merge override dict into base dict.

    Returns a new dict (base is deep-copied, override is not modified).
    Nested dicts are merged recursively. Lists are merged according to
    the specified strategy. Namespace policies are applied automatically.
    """
    result = deepcopy(base)
    _deep_merge(result, override, list_strategy, _key_path="")
    return result


def _deep_merge(target, override, list_strategy="extend", _key_path=""):
    """Internal recursive merge. Modifies target in-place.

    Tracks the dotted key path for policy lookups during recursion.
    """
    # Check for inline strategy directive
    strategy = override.pop("_list_strategy", list_strategy)

    for key in override:
        if key == "_list_strategy":
            continue

        current_path = f"{_key_path}.{key}" if _key_path else key
        policy = get_policy_for_key(current_path)

        if key not in target:
            target[key] = override[key]
        elif override[key] is None:
            # Explicit None always wins (disable a section)
            target[key] = None
        elif target[key] is None:
            # None means explicitly disabled; only non-empty values re-enable
            if override[key]:
                target[key] = override[key]
        elif isinstance(target[key], dict) and isinstance(override[key], dict):
            _deep_merge(target[key], override[key], strategy, current_path)
        elif isinstance(target[key], list) and isinstance(override[key], list):
            _merge_lists(target, key, override[key], strategy, policy)
        else:
            _merge_scalar(target, key, override[key], policy)

    return target


def _merge_lists(target, key, override_list, strategy, policy):
    """Merge two lists according to the strategy and policy."""
    if policy == MergePolicy.RESTRICTIVE:
        # For restrictive keys, list override must be a subset (narrowing)
        if is_more_restrictive(override_list, target[key]):
            target[key] = list(override_list)
        # else: reject the override, keep the base list
    elif strategy == "replace":
        target[key] = list(override_list)
    elif strategy == "unique":
        target[key] = list(dict.fromkeys(target[key] + override_list))
    else:
        target[key].extend(override_list)


def _merge_scalar(target, key, override_value, policy):
    """Merge a scalar value according to the namespace policy."""
    if policy == MergePolicy.RESTRICTIVE:
        # Only allow the override if it's more restrictive
        if is_more_restrictive(override_value, target[key]):
            target[key] = override_value
        # else: reject the override, keep the more restrictive base
    elif policy == MergePolicy.FEATURE_CASCADE:
        # Feature flag cascade: override takes precedence
        target[key] = override_value
    else:
        # Standard merge: last writer wins
        target[key] = override_value


def merge_configs(*configs, list_strategy="extend"):
    """Merge multiple configuration dicts in priority order.

    Later configs take precedence over earlier ones. Returns a new dict.
    Namespace policies are applied at each merge step.
    """
    if not configs:
        return {}
    result = deepcopy(configs[0])
    for override in configs[1:]:
        _deep_merge(result, override, list_strategy)
    return result
