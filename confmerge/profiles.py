"""Profile management for configuration environments.

Profiles allow defining named configuration sets (dev, staging, production)
with inheritance. A profile can extend another profile, creating inheritance
chains. The ProfileRegistry handles profile resolution and cycle detection.
"""

from copy import deepcopy


class ProfileError(Exception):
    """Raised when profile operations fail."""
    pass


class Profile:
    """Represents a named configuration profile.

    A profile can extend another profile, inheriting its configuration.
    The extends chain is resolved during profile retrieval.
    """

    def __init__(self, name, config=None, extends=None):
        """Initialize a profile.

        Args:
            name: Profile identifier (e.g., 'dev', 'staging', 'production')
            config: Configuration dictionary for this profile
            extends: Name of parent profile to inherit from (optional)
        """
        self.name = name
        self.config = config or {}
        self.extends = extends

    def __repr__(self):
        extends_str = f" extends {self.extends}" if self.extends else ""
        return f"<Profile {self.name}{extends_str}>"


class ProfileRegistry:
    """Registry for managing configuration profiles.

    Handles profile registration, retrieval, and inheritance chain resolution.
    Detects circular inheritance and provides clear error messages.
    """

    def __init__(self):
        """Initialize an empty profile registry."""
        self._profiles = {}

    def register(self, name, config=None, extends=None):
        """Register a new profile.

        Args:
            name: Profile identifier
            config: Configuration dictionary for this profile
            extends: Name of parent profile to inherit from (optional)

        Returns:
            The registered Profile object

        Raises:
            ProfileError: If the profile name is invalid
        """
        if not name or not isinstance(name, str):
            raise ProfileError("Profile name must be a non-empty string")

        profile = Profile(name, config, extends)
        self._profiles[name] = profile
        return profile

    def get(self, name, resolve=True):
        """Retrieve a profile by name.

        Args:
            name: Profile identifier
            resolve: If True, resolve inheritance chain and return merged config.
                    If False, return the profile object as-is.

        Returns:
            If resolve=True: merged configuration dictionary
            If resolve=False: Profile object

        Raises:
            ProfileError: If profile not found or inheritance chain is invalid
        """
        if name not in self._profiles:
            raise ProfileError(f"Profile '{name}' not found")

        profile = self._profiles[name]

        if not resolve:
            return profile

        return self.resolve(name)

    def resolve(self, name):
        """Resolve a profile's full configuration including inheritance.

        Walks the inheritance chain from root to leaf, merging configurations
        at each level. Later profiles override earlier ones.

        Args:
            name: Profile identifier to resolve

        Returns:
            Merged configuration dictionary with all inherited values

        Raises:
            ProfileError: If profile not found or circular inheritance detected
        """
        if name not in self._profiles:
            raise ProfileError(f"Profile '{name}' not found")

        # Collect inheritance chain
        chain = self._get_inheritance_chain(name)

        # Merge configs from root to leaf
        result = {}
        for profile_name in chain:
            profile = self._profiles[profile_name]
            result = self._merge_configs(result, profile.config)

        return result

    def _get_inheritance_chain(self, name):
        """Build the inheritance chain from root to leaf.

        Args:
            name: Profile identifier

        Returns:
            List of profile names from root ancestor to target profile

        Raises:
            ProfileError: If circular inheritance is detected
        """
        chain = []
        visited = set()
        current = name

        while current is not None:
            if current in visited:
                cycle_path = " -> ".join(chain + [current])
                raise ProfileError(
                    f"Circular profile inheritance detected: {cycle_path}"
                )

            if current not in self._profiles:
                raise ProfileError(
                    f"Profile '{current}' referenced by extends but not registered"
                )

            visited.add(current)
            chain.append(current)
            current = self._profiles[current].extends

        # Reverse to get root-to-leaf order
        return list(reversed(chain))

    def _merge_configs(self, base, override):
        """Merge two configuration dictionaries.

        Simple recursive merge. Override values take precedence.
        This is a simplified merge suitable for profile inheritance.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            New merged dictionary
        """
        result = deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = deepcopy(value)

        return result

    def list_profiles(self):
        """List all registered profile names.

        Returns:
            List of profile names sorted alphabetically
        """
        return sorted(self._profiles.keys())

    def has_profile(self, name):
        """Check if a profile is registered.

        Args:
            name: Profile identifier

        Returns:
            True if profile exists, False otherwise
        """
        return name in self._profiles

    def unregister(self, name):
        """Remove a profile from the registry.

        Args:
            name: Profile identifier

        Returns:
            True if profile was removed, False if it didn't exist
        """
        if name in self._profiles:
            del self._profiles[name]
            return True
        return False

    def clear(self):
        """Remove all profiles from the registry."""
        self._profiles.clear()


# Global default registry instance
_default_registry = ProfileRegistry()


def register_profile(name, config=None, extends=None):
    """Register a profile in the default global registry.

    Args:
        name: Profile identifier
        config: Configuration dictionary for this profile
        extends: Name of parent profile to inherit from (optional)

    Returns:
        The registered Profile object
    """
    return _default_registry.register(name, config, extends)


def get_profile(name, resolve=True):
    """Retrieve a profile from the default global registry.

    Args:
        name: Profile identifier
        resolve: If True, resolve inheritance chain

    Returns:
        Resolved configuration dictionary or Profile object
    """
    return _default_registry.get(name, resolve)


def list_profiles():
    """List all profiles in the default global registry.

    Returns:
        List of profile names sorted alphabetically
    """
    return _default_registry.list_profiles()
