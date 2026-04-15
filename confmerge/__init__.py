"""Hierarchical configuration merging for Python applications.

Supports deep merging from multiple sources (defaults, files, environment
variables) with configurable list merge strategies and type coercion.
"""

from confmerge.merger import deep_merge, merge_configs
from confmerge.coerce import coerce_value
from confmerge.loader import load_file
from confmerge.sources import load_env
from confmerge.interpolate import interpolate
from confmerge.pipeline import load_config
from confmerge.schema import validate, SchemaError
from confmerge.policies import (
    MergePolicy,
    get_policy_for_key,
    is_more_restrictive,
)
from confmerge.profiles import (
    ProfileRegistry,
    Profile,
    ProfileError,
    register_profile,
    get_profile,
    list_profiles,
)
from confmerge.watchers import ConfigWatcher, WatcherError, watch_file
from confmerge.serializer import (
    to_json,
    to_yaml,
    to_toml,
    to_dotenv,
    export,
    SerializerError,
)
from confmerge.validators import (
    validate_port,
    validate_port_range,
    validate_url,
    validate_email,
    validate_path_exists,
    validate_enum,
    validate_range,
    ValidatorRegistry,
    ValidationError,
    create_validator,
)

__version__ = "0.3.1"

__all__ = [
    "deep_merge",
    "merge_configs",
    "coerce_value",
    "load_file",
    "load_env",
    "interpolate",
    "load_config",
    "validate",
    "SchemaError",
    # Policies
    "MergePolicy",
    "get_policy_for_key",
    "is_more_restrictive",
    # Profiles
    "ProfileRegistry",
    "Profile",
    "ProfileError",
    "register_profile",
    "get_profile",
    "list_profiles",
    # Watchers
    "ConfigWatcher",
    "WatcherError",
    "watch_file",
    # Serializer
    "to_json",
    "to_yaml",
    "to_toml",
    "to_dotenv",
    "export",
    "SerializerError",
    # Validators
    "validate_port",
    "validate_port_range",
    "validate_url",
    "validate_email",
    "validate_path_exists",
    "validate_enum",
    "validate_range",
    "ValidatorRegistry",
    "ValidationError",
    "create_validator",
]
