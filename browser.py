"""
Browser abstraction layer for choosr.

This module provides abstract base classes and data structures for supporting
multiple browsers in choosr. Each browser implementation should inherit from
the Browser class and implement the required methods.
"""

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class ProfileIcon:
    """Represents a profile icon with color and avatar information."""

    avatar_icon: Optional[str] = None  # Icon identifier/path
    background_color: Optional[str] = None  # Hex color code
    text_color: Optional[str] = None  # Hex color for text
    icon_data: Optional[bytes] = None  # Raw icon data if available
    icon_file_path: Optional[str] = (
        None  # Path to actual icon file (e.g., profile picture)
    )

    def __post_init__(self):
        # Set default colors if not provided
        if self.background_color is None:
            self.background_color = "#4285F4"  # Default blue
        if self.text_color is None:
            self.text_color = "#FFFFFF"  # Default white

    def to_dict(self) -> Dict:
        """Convert ProfileIcon to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ProfileIcon":
        """Create ProfileIcon from dictionary."""
        return cls(**data)


@dataclass
class Profile:
    """Represents a browser profile."""

    id: str  # Browser-specific profile identifier
    name: str  # User-friendly display name
    browser: str  # Browser type (chrome, firefox, etc.)
    is_private: bool = False  # Whether this is a private/incognito profile
    email: Optional[str] = None  # Associated email address
    icon: Optional[ProfileIcon] = None  # Profile icon information

    def to_dict(self) -> Dict:
        """Convert Profile to dictionary for serialization."""
        data = asdict(self)
        if self.icon:
            data["icon"] = self.icon.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "Profile":
        """Create Profile from dictionary."""
        icon_data = data.pop("icon", None)
        profile = cls(**data)
        if icon_data:
            profile.icon = ProfileIcon.from_dict(icon_data)
        return profile


class ProfileCache:
    """Caches browser profile data to improve performance."""

    def __init__(self, cache_file: str = None):
        """Initialize profile cache.

        Args:
            cache_file: Path to cache file. Defaults to ~/.choosr-cache.json
        """
        if cache_file is None:
            cache_file = os.path.expanduser("~/.choosr-cache.json")
        self.cache_file = cache_file
        self._cache_data = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache data from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._cache_data = {}

    def _save_cache(self) -> None:
        """Save cache data to disk."""
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir:  # Only create directory if there is one
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache_data, f, indent=2)
        except OSError:
            pass  # Silently fail if can't write cache

    def get_cached_profiles(
        self, browser_name: str, source_files: List[str]
    ) -> Optional[List[Profile]]:
        """Get cached profiles if cache is still valid.

        Args:
            browser_name: Name of the browser
            source_files: List of files that profiles depend on

        Returns:
            List of cached profiles if valid, None if cache is invalid or missing
        """
        cache_key = f"{browser_name}_profiles"

        if cache_key not in self._cache_data:
            return None

        cached_entry = self._cache_data[cache_key]
        cached_time = cached_entry.get("timestamp", 0)

        # Check if any source file is newer than cache
        for source_file in source_files:
            if os.path.exists(source_file):
                file_mtime = os.path.getmtime(source_file)
                if file_mtime > cached_time:
                    return None  # Cache is stale

        # Deserialize profiles
        try:
            profile_data = cached_entry.get("profiles", [])
            return [Profile.from_dict(p) for p in profile_data]
        except (KeyError, TypeError):
            return None

    def cache_profiles(
        self, browser_name: str, profiles: List[Profile], source_files: List[str]
    ) -> None:
        """Cache profiles for a browser.

        Args:
            browser_name: Name of the browser
            profiles: List of profiles to cache
            source_files: List of files that profiles depend on (for invalidation)
        """
        cache_key = f"{browser_name}_profiles"

        # Use the latest modification time from source files
        latest_mtime = 0
        for source_file in source_files:
            if os.path.exists(source_file):
                latest_mtime = max(latest_mtime, os.path.getmtime(source_file))

        # If no source files exist, use current time
        if latest_mtime == 0:
            latest_mtime = time.time()

        self._cache_data[cache_key] = {
            "timestamp": latest_mtime,
            "profiles": [p.to_dict() for p in profiles],
            "source_files": source_files,
        }

        self._save_cache()

    def invalidate_browser(self, browser_name: str) -> None:
        """Invalidate cache for a specific browser.

        Args:
            browser_name: Name of the browser to invalidate
        """
        cache_key = f"{browser_name}_profiles"
        if cache_key in self._cache_data:
            del self._cache_data[cache_key]
            self._save_cache()

    def clear_all(self) -> None:
        """Clear all cached data."""
        self._cache_data = {}
        self._save_cache()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics for debugging."""
        stats = {}
        for key, value in self._cache_data.items():
            if key.endswith("_profiles"):
                browser_name = key[:-9]  # Remove '_profiles' suffix
                stats[browser_name] = {
                    "profile_count": len(value.get("profiles", [])),
                    "timestamp": value.get("timestamp", 0),
                    "source_files": value.get("source_files", []),
                }
        return stats


class Browser(ABC):
    """Abstract base class for browser implementations."""

    def __init__(self):
        self._cache = ProfileCache()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the browser name (e.g., 'chrome', 'firefox')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the user-friendly browser name (e.g., 'Google Chrome', 'Mozilla Firefox')."""
        pass

    @property
    @abstractmethod
    def executable_path(self) -> str:
        """Return the path to the browser executable."""
        pass

    @abstractmethod
    def discover_profiles(self) -> List[Profile]:
        """
        Discover all available profiles for this browser.

        Returns:
            List of Profile objects representing available profiles.
            Should not include the private mode profile.
        """
        pass

    @abstractmethod
    def get_private_mode_profile(self) -> Profile:
        """
        Get the private/incognito mode profile for this browser.

        Returns:
            Profile object representing private browsing mode.
        """
        pass

    @abstractmethod
    def launch(self, profile: Profile, url: Optional[str] = None) -> bool:
        """
        Launch the browser with the specified profile and optional URL.

        Args:
            profile: Profile object to launch with
            url: Optional URL to open

        Returns:
            True if launch succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this browser is available on the system.

        Returns:
            True if the browser executable exists and is accessible.
        """
        pass

    @abstractmethod
    def get_browser_icon(self) -> Optional[str]:
        """
        Get the browser's main icon.

        Returns:
            Path to browser icon file, or None if not available.
        """
        pass

    @abstractmethod
    def get_private_mode_icon(self) -> Optional[str]:
        """
        Get the browser's private/incognito mode icon.

        Returns:
            Path to private mode icon file, or None if not available.
        """
        pass

    @abstractmethod
    def get_profile_icon(self, profile: Profile) -> ProfileIcon:
        """
        Get icon information for a specific profile.

        Args:
            profile: The profile to get icon information for

        Returns:
            ProfileIcon with color and avatar information.
        """
        pass

    @abstractmethod
    def get_source_files(self) -> List[str]:
        """
        Return list of files that profile discovery depends on.

        Used for cache invalidation - when these files change,
        cached profiles should be refreshed.

        Returns:
            List of file paths that profiles depend on.
        """
        pass

    def cached_discover_profiles(self) -> List[Profile]:
        """
        Discover profiles using cache when possible.

        This method tries to return cached profiles first. If cache is invalid
        or missing, it calls discover_profiles() and caches the result.

        Returns:
            List of Profile objects representing available profiles.
        """
        source_files = self.get_source_files()

        # Try to get cached profiles
        cached_profiles = self._cache.get_cached_profiles(self.name, source_files)
        if cached_profiles is not None:
            return cached_profiles

        # Cache miss or invalid - discover fresh profiles
        fresh_profiles = self.discover_profiles()

        # Cache the fresh profiles
        self._cache.cache_profiles(self.name, fresh_profiles, source_files)

        return fresh_profiles

    def get_all_profiles(self) -> List[Profile]:
        """
        Get all profiles including the private mode profile.

        Returns:
            List of all profiles with private mode profile at the end.
        """
        return self.cached_discover_profiles() + [self.get_private_mode_profile()]

    def invalidate_cache(self) -> None:
        """Invalidate cached profile data for this browser."""
        self._cache.invalidate_browser(self.name)

    def get_profile_by_id(self, profile_id: str) -> Optional[Profile]:
        """
        Find a profile by its ID.

        Args:
            profile_id: The profile ID to search for

        Returns:
            Profile object if found, None otherwise.
        """
        for profile in self.get_all_profiles():
            if profile.id == profile_id:
                return profile
        return None

    def get_profile_by_name(self, profile_name: str) -> Optional[Profile]:
        """
        Find a profile by its display name.

        Args:
            profile_name: The profile name to search for

        Returns:
            Profile object if found, None otherwise.
        """
        for profile in self.get_all_profiles():
            if profile.name == profile_name:
                return profile
        return None


class BrowserRegistry:
    """Registry for managing multiple browser implementations."""

    def __init__(self):
        self._browsers: Dict[str, Browser] = {}

    def register(self, browser: Browser) -> None:
        """Register a browser implementation."""
        self._browsers[browser.name] = browser

    def get_browser(self, name: str) -> Optional[Browser]:
        """Get a browser by name."""
        return self._browsers.get(name)

    def get_available_browsers(self) -> List[Browser]:
        """Get all available browsers on the system."""
        return [
            browser for browser in self._browsers.values() if browser.is_available()
        ]

    def get_all_profiles(self) -> List[Profile]:
        """Get all profiles from all available browsers."""
        profiles = []
        for browser in self.get_available_browsers():
            profiles.extend(browser.get_all_profiles())
        return profiles

    def discover_all_profiles(self) -> Dict[str, List[Profile]]:
        """
        Discover profiles from all available browsers.

        Returns:
            Dictionary mapping browser names to their profile lists.
        """
        result = {}
        for browser in self.get_available_browsers():
            result[browser.name] = browser.get_all_profiles()
        return result

    def clear_all_caches(self) -> None:
        """Clear profile caches for all browsers."""
        for browser in self._browsers.values():
            browser.invalidate_cache()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics from all browsers."""
        if not self._browsers:
            return {}

        # Get cache stats from the first browser (they share the same cache)
        first_browser = next(iter(self._browsers.values()))
        return first_browser._cache.get_cache_stats()


# Global browser registry instance
browser_registry = BrowserRegistry()
