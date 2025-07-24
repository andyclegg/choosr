"""Tests for browser abstraction layer."""

import pytest

from browser import Profile, ProfileIcon, BrowserRegistry, Browser


class MockBrowser(Browser):
    """Mock browser implementation for testing."""

    def __init__(self, name="mock", display_name="Mock Browser", available=True):
        self._name = name
        self._display_name = display_name
        self._available = available
        self._profiles = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def executable_path(self) -> str:
        return "/usr/bin/mock-browser"

    def discover_profiles(self):
        return self._profiles

    def get_private_mode_profile(self):
        return Profile(
            id="private",
            name="Private Mode",
            browser=self.name,
            is_private=True
        )

    def launch(self, profile, url=None):
        pass

    def is_available(self) -> bool:
        return self._available

    def get_browser_icon(self):
        return "/usr/share/icons/mock-browser.png"

    def get_private_mode_icon(self):
        return "/usr/share/icons/mock-browser-private.png"

    def get_profile_icon(self, profile):
        return ProfileIcon(
            avatar_icon="mock-avatar",
            background_color="#FF0000",
            text_color="#FFFFFF"
        )

    def add_profile(self, profile):
        """Helper method to add profiles for testing."""
        self._profiles.append(profile)


class TestProfileIcon:
    """Tests for ProfileIcon dataclass."""

    def test_default_values(self):
        """Test ProfileIcon with default values."""
        icon = ProfileIcon()
        assert icon.avatar_icon is None
        assert icon.background_color == "#4285F4"  # Default blue
        assert icon.text_color == "#FFFFFF"  # Default white
        assert icon.icon_data is None
        assert icon.icon_file_path is None

    def test_custom_values(self):
        """Test ProfileIcon with custom values."""
        icon = ProfileIcon(
            avatar_icon="custom-avatar",
            background_color="#FF0000",
            text_color="#000000",
            icon_data=b"icon_data",
            icon_file_path="/path/to/icon.png"
        )
        assert icon.avatar_icon == "custom-avatar"
        assert icon.background_color == "#FF0000"
        assert icon.text_color == "#000000"
        assert icon.icon_data == b"icon_data"
        assert icon.icon_file_path == "/path/to/icon.png"

    def test_partial_colors(self):
        """Test ProfileIcon with partial color specification."""
        icon = ProfileIcon(background_color="#00FF00")
        assert icon.background_color == "#00FF00"
        assert icon.text_color == "#FFFFFF"  # Should get default


class TestProfile:
    """Tests for Profile dataclass."""

    def test_basic_profile(self):
        """Test basic profile creation."""
        profile = Profile(
            id="test-profile",
            name="Test Profile",
            browser="test-browser"
        )
        assert profile.id == "test-profile"
        assert profile.name == "Test Profile"
        assert profile.browser == "test-browser"
        assert profile.is_private is False
        assert profile.icon is None

    def test_private_profile(self):
        """Test private profile creation."""
        icon = ProfileIcon(avatar_icon="private-icon")
        profile = Profile(
            id="private",
            name="Private Mode",
            browser="test-browser",
            is_private=True,
            icon=icon
        )
        assert profile.is_private is True
        assert profile.icon == icon


class TestBrowserRegistry:
    """Tests for BrowserRegistry."""

    def test_empty_registry(self):
        """Test empty browser registry."""
        registry = BrowserRegistry()
        assert registry.get_available_browsers() == []
        assert registry.get_all_profiles() == []
        assert registry.get_browser("nonexistent") is None

    def test_register_browser(self):
        """Test registering a browser."""
        registry = BrowserRegistry()
        browser = MockBrowser()
        
        registry.register(browser)
        assert registry.get_browser("mock") == browser

    def test_get_available_browsers(self):
        """Test getting available browsers."""
        registry = BrowserRegistry()
        available_browser = MockBrowser("available", "Available Browser", True)
        unavailable_browser = MockBrowser("unavailable", "Unavailable Browser", False)
        
        registry.register(available_browser)
        registry.register(unavailable_browser)
        
        available = registry.get_available_browsers()
        assert len(available) == 1
        assert available[0] == available_browser

    def test_get_all_profiles(self):
        """Test getting all profiles from all browsers."""
        registry = BrowserRegistry()
        browser1 = MockBrowser("browser1")
        browser2 = MockBrowser("browser2")
        
        profile1 = Profile("prof1", "Profile 1", "browser1")
        profile2 = Profile("prof2", "Profile 2", "browser1")
        profile3 = Profile("prof3", "Profile 3", "browser2")
        
        browser1.add_profile(profile1)
        browser1.add_profile(profile2)
        browser2.add_profile(profile3)
        
        registry.register(browser1)
        registry.register(browser2)
        
        all_profiles = registry.get_all_profiles()
        # Should include regular profiles + private profiles from each browser
        assert len(all_profiles) == 5  # 3 regular + 2 private
        
        # Check that all regular profiles are included
        profile_names = [p.name for p in all_profiles]
        assert "Profile 1" in profile_names
        assert "Profile 2" in profile_names
        assert "Profile 3" in profile_names
        assert "Private Mode" in profile_names  # Should appear twice

    def test_discover_all_profiles(self):
        """Test discovering profiles grouped by browser."""
        registry = BrowserRegistry()
        browser1 = MockBrowser("browser1")
        browser2 = MockBrowser("browser2")
        
        profile1 = Profile("prof1", "Profile 1", "browser1")
        browser1.add_profile(profile1)
        
        registry.register(browser1)
        registry.register(browser2)
        
        discovered = registry.discover_all_profiles()
        assert "browser1" in discovered
        assert "browser2" in discovered
        
        # browser1 should have 2 profiles (1 regular + 1 private)
        assert len(discovered["browser1"]) == 2
        # browser2 should have 1 profile (just private)
        assert len(discovered["browser2"]) == 1


class TestBrowserMethods:
    """Tests for Browser abstract class methods."""

    def test_get_all_profiles(self):
        """Test get_all_profiles includes private profile."""
        browser = MockBrowser()
        regular_profile = Profile("regular", "Regular Profile", "mock")
        browser.add_profile(regular_profile)
        
        all_profiles = browser.get_all_profiles()
        assert len(all_profiles) == 2
        
        # Regular profile should be first
        assert all_profiles[0] == regular_profile
        # Private profile should be last
        assert all_profiles[1].is_private is True

    def test_get_profile_by_id(self):
        """Test finding profile by ID."""
        browser = MockBrowser()
        profile1 = Profile("id1", "Profile 1", "mock")
        profile2 = Profile("id2", "Profile 2", "mock")
        browser.add_profile(profile1)
        browser.add_profile(profile2)
        
        assert browser.get_profile_by_id("id1") == profile1
        assert browser.get_profile_by_id("id2") == profile2
        assert browser.get_profile_by_id("nonexistent") is None
        
        # Should also find private profile
        private = browser.get_profile_by_id("private")
        assert private is not None
        assert private.is_private is True

    def test_get_profile_by_name(self):
        """Test finding profile by name."""
        browser = MockBrowser()
        profile1 = Profile("id1", "Profile 1", "mock")
        profile2 = Profile("id2", "Profile 2", "mock")
        browser.add_profile(profile1)
        browser.add_profile(profile2)
        
        assert browser.get_profile_by_name("Profile 1") == profile1
        assert browser.get_profile_by_name("Profile 2") == profile2
        assert browser.get_profile_by_name("Nonexistent") is None
        
        # Should also find private profile
        private = browser.get_profile_by_name("Private Mode")
        assert private is not None
        assert private.is_private is True