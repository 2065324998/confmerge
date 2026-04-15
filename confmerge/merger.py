"""Deep merge functionality for nested configuration dictionaries.

Supports three list merge strategies:
- 'extend': append override items to base list (default)
- 'replace': override list completely replaces base list
- 'unique': combine lists, removing duplicates while preserving order

Override dicts can include a '_list_strategy' key to control list merge
behavior for that level and below.
"""

from copy import deepcopy


def deep_merge(base, override, list_strategy="extend"):
    """Deep merge override dict into base dict.

    Returns a new dict (base is deep-copied, override is not modified).
    Nested dicts are merged recursively. Lists are merged according to
    the specified strategy.
    """
    result = deepcopy(base)
    _deep_merge(result, override, list_strategy)
    return result


def _deep_merge(target, override, list_strategy="extend"):
    """Internal recursive merge. Modifies target in-place."""
    # Check for inline strategy directive
    strategy = override.pop("_list_strategy", list_strategy)

    for key in override:
        if key not in target:
            target[key] = override[key]
        elif override[key] is None:
            target[key] = None
        elif target[key] is None:
            # None means explicitly disabled; only non-empty values re-enable
            if override[key]:
                target[key] = override[key]
        elif isinstance(target[key], dict) and isinstance(override[key], dict):
            _deep_merge(target[key], override[key], list_strategy)
        elif isinstance(target[key], list) and isinstance(override[key], list):
            if strategy == "replace":
                target[key] = list(override[key])
            elif strategy == "unique":
                target[key] = list(dict.fromkeys(target[key] + override[key]))
            else:
                target[key].extend(override[key])
        else:
            target[key] = override[key]

    return target


def merge_configs(*configs, list_strategy="extend"):
    """Merge multiple configuration dicts in priority order.

    Later configs take precedence over earlier ones. Returns a new dict.
    """
    if not configs:
        return {}
    result = deepcopy(configs[0])
    for override in configs[1:]:
        _deep_merge(result, override, list_strategy)
    return result
