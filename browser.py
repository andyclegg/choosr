"""
Browser abstraction layer for choosr.

This module provides abstract base classes and data structures for supporting
multiple browsers in choosr. Each browser implementation should inherit from
the Browser class and implement the required methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class Profile:
    """Represents a browser profile."""
    id: str                    # Browser-specific profile identifier
    name: str                  # User-friendly display name  
    browser: str               # Browser type (chrome, firefox, etc.)
    is_private: bool = False   # Whether this is a private/incognito profile
    metadata: Dict[str, Any] = None  # Browser-specific metadata
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Browser(ABC):
    """Abstract base class for browser implementations."""
    
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
    def launch(self, profile: Profile, url: Optional[str] = None) -> None:
        """
        Launch the browser with the specified profile and optional URL.
        
        Args:
            profile: Profile object to launch with
            url: Optional URL to open
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
    
    def get_all_profiles(self) -> List[Profile]:
        """
        Get all profiles including the private mode profile.
        
        Returns:
            List of all profiles with private mode profile at the end.
        """
        profiles = self.discover_profiles()
        private_profile = self.get_private_mode_profile()
        return profiles + [private_profile]
    
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
        return [browser for browser in self._browsers.values() if browser.is_available()]
    
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


# Global browser registry instance
browser_registry = BrowserRegistry()
