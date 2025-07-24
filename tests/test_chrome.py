"""Tests for Chrome browser implementation."""

import json
import os
import tempfile
from unittest.mock import patch, mock_open

import pytest

from chrome import ChromeBrowser
from browser import Profile, ProfileIcon


class TestChromeBrowser:
    """Tests for ChromeBrowser class."""

    def test_basic_properties(self):
        """Test basic Chrome browser properties."""
        chrome = ChromeBrowser()
        assert chrome.name == "chrome"
        assert chrome.display_name == "Google Chrome"
        assert chrome.executable_path == "/usr/bin/google-chrome"

    def test_private_mode_profile(self):
        """Test getting private mode profile."""
        chrome = ChromeBrowser()
        private = chrome.get_private_mode_profile()
        
        assert private.id == "incognito"
        assert private.name == "Incognito Mode"
        assert private.browser == "chrome"
        assert private.is_private is True

    @patch('os.path.isfile')
    @patch('os.access')
    def test_is_available(self, mock_access, mock_isfile):
        """Test Chrome availability check."""
        chrome = ChromeBrowser()
        
        # Chrome is available
        mock_isfile.return_value = True
        mock_access.return_value = True
        assert chrome.is_available() is True
        
        # Chrome executable doesn't exist
        mock_isfile.return_value = False
        assert chrome.is_available() is False
        
        # Chrome exists but not executable
        mock_isfile.return_value = True
        mock_access.return_value = False
        assert chrome.is_available() is False

    def test_config_paths(self):
        """Test Chrome configuration paths."""
        chrome = ChromeBrowser()
        
        config_dir = chrome.get_config_directory()
        assert config_dir.endswith("/.config/google-chrome")
        
        local_state = chrome.get_local_state_file()
        assert local_state.endswith("/.config/google-chrome/Local State")

    @patch('os.path.exists')
    def test_discover_profiles_no_config(self, mock_exists):
        """Test profile discovery when config directory doesn't exist."""
        chrome = ChromeBrowser()
        mock_exists.return_value = False
        
        profiles = chrome.discover_profiles()
        assert profiles == []

    @patch('os.path.exists')
    def test_discover_profiles_no_local_state(self, mock_exists):
        """Test profile discovery when Local State file doesn't exist."""
        chrome = ChromeBrowser()
        
        def exists_side_effect(path):
            if path.endswith(".config/google-chrome"):
                return True
            if path.endswith("Local State"):
                return False
            return False
        
        mock_exists.side_effect = exists_side_effect
        
        profiles = chrome.discover_profiles()
        assert profiles == []

    def test_discover_profiles_with_mock_data(self):
        """Test profile discovery with mock Chrome data."""
        chrome = ChromeBrowser()
        
        # Mock Local State data
        local_state_data = {
            "profile": {
                "info_cache": {
                    "Default": {
                        "name": "Default Profile",
                        "avatar_icon": "chrome-avatar-generic"
                    },
                    "Profile 1": {
                        "name": "Work Profile",
                        "avatar_icon": "chrome://theme/IDR_PROFILE_AVATAR_1",
                        "theme_colors": {
                            "theme_frame": -14654801,  # Negative integer color
                            "theme_text": -1
                        }
                    }
                }
            }
        }
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.isdir') as mock_isdir, \
             patch('builtins.open', mock_open(read_data=json.dumps(local_state_data))):
            
            # Mock paths exist
            mock_exists.return_value = True
            mock_isdir.return_value = True
            
            profiles = chrome.discover_profiles()
            
            assert len(profiles) == 2
            
            # Check Default profile
            default = next(p for p in profiles if p.id == "Default")
            assert default.name == "Default Profile"
            assert default.browser == "chrome"
            assert default.is_private is False
            
            # Check Work profile
            work = next(p for p in profiles if p.id == "Profile 1")
            assert work.name == "Work Profile"
            assert work.browser == "chrome"
            assert work.is_private is False

    def test_profile_exists(self):
        """Test profile existence checking."""
        chrome = ChromeBrowser()
        
        # Incognito always exists
        assert chrome.profile_exists("incognito") is True
        
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.return_value = True
            assert chrome.profile_exists("Default") is True
            
            mock_isdir.return_value = False
            assert chrome.profile_exists("NonExistent") is False

    def test_get_profile_path(self):
        """Test getting profile filesystem paths."""
        chrome = ChromeBrowser()
        
        # Incognito has no path
        assert chrome.get_profile_path("incognito") is None
        
        # Regular profile has path
        path = chrome.get_profile_path("Default")
        assert path.endswith("/.config/google-chrome/Default")

    @patch('os.path.isfile')
    def test_get_browser_icon(self, mock_isfile):
        """Test getting Chrome browser icon."""
        chrome = ChromeBrowser()
        
        # First path exists
        def mock_isfile_side_effect(path):
            return path == "/usr/share/icons/hicolor/256x256/apps/google-chrome.png"
        
        mock_isfile.side_effect = mock_isfile_side_effect
        icon = chrome.get_browser_icon()
        assert icon == "/usr/share/icons/hicolor/256x256/apps/google-chrome.png"
        
        # No icon found - reset the side effect
        mock_isfile.side_effect = None
        mock_isfile.return_value = False
        icon = chrome.get_browser_icon()
        assert icon is None

    def test_get_private_mode_icon(self):
        """Test getting Chrome private mode icon."""
        chrome = ChromeBrowser()
        
        with patch.object(chrome, 'get_browser_icon', return_value="/path/to/icon.png"):
            private_icon = chrome.get_private_mode_icon()
            assert private_icon == "/path/to/icon.png"

    def test_get_profile_icon_private(self):
        """Test getting profile icon for private mode."""
        chrome = ChromeBrowser()
        private_profile = Profile("incognito", "Incognito", "chrome", is_private=True)
        
        icon = chrome.get_profile_icon(private_profile)
        assert isinstance(icon, ProfileIcon)
        assert icon.avatar_icon == "incognito"
        assert icon.background_color == "#5F6368"
        assert icon.text_color == "#FFFFFF"

    def test_get_profile_icon_with_existing_icon(self):
        """Test getting profile icon when profile already has one."""
        chrome = ChromeBrowser()
        existing_icon = ProfileIcon(avatar_icon="existing", background_color="#123456")
        profile = Profile("test", "Test", "chrome", icon=existing_icon)
        
        icon = chrome.get_profile_icon(profile)
        assert icon == existing_icon

    def test_color_conversion(self):
        """Test Chrome color conversion from signed int to hex."""
        chrome = ChromeBrowser()
        
        # Positive number
        assert chrome._convert_chrome_color_to_hex(255) == "#0000FF"
        
        # Negative number (needs conversion)
        assert chrome._convert_chrome_color_to_hex(-1) == "#FFFFFFFF"
        
        # Zero
        assert chrome._convert_chrome_color_to_hex(0) == "#000000"

    def test_avatar_colors_constant(self):
        """Test that avatar colors constant is properly defined."""
        chrome = ChromeBrowser()
        
        assert "chrome-avatar-generic" in chrome.AVATAR_COLORS
        assert chrome.AVATAR_COLORS["chrome-avatar-generic"] == "#4285F4"
        assert len(chrome.AVATAR_COLORS) > 20  # Should have many avatar colors

    @patch('subprocess.run')
    def test_launch_regular_profile(self, mock_run):
        """Test launching Chrome with regular profile."""
        chrome = ChromeBrowser()
        profile = Profile("Default", "Default Profile", "chrome")
        
        chrome.launch(profile, "https://example.com")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/usr/bin/google-chrome" in args
        assert "--profile-directory=Default" in args
        assert "https://example.com" in args

    @patch('subprocess.run')
    def test_launch_incognito_profile(self, mock_run):
        """Test launching Chrome in incognito mode."""
        chrome = ChromeBrowser()
        profile = Profile("incognito", "Incognito Mode", "chrome", is_private=True)
        
        chrome.launch(profile, "https://example.com")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/usr/bin/google-chrome" in args
        assert "--incognito" in args
        assert "https://example.com" in args

    @patch('subprocess.run')
    def test_launch_without_url(self, mock_run):
        """Test launching Chrome without URL."""
        chrome = ChromeBrowser()
        profile = Profile("Default", "Default Profile", "chrome")
        
        chrome.launch(profile)
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/usr/bin/google-chrome" in args
        assert "--profile-directory=Default" in args
        # URL should not be in args
        assert len([arg for arg in args if arg.startswith("http")]) == 0

    def test_get_profile_picture_path(self):
        """Test getting profile picture path."""
        chrome = ChromeBrowser()
        
        profile_info = {"gaia_id": "123456789"}
        
        with patch('os.path.isfile') as mock_isfile:
            # Google Profile Picture exists
            def mock_isfile_side_effect(path):
                return "Google Profile Picture.png" in path
            
            mock_isfile.side_effect = mock_isfile_side_effect
            path = chrome._get_profile_picture_path(profile_info, "Default")
            assert path.endswith("Default/Google Profile Picture.png")
            
            # No picture found - reset the mock properly
            mock_isfile.side_effect = None
            mock_isfile.return_value = False
            path = chrome._get_profile_picture_path(profile_info, "Default")
            assert path is None

    def test_get_profile_icon_from_local_state_error(self):
        """Test handling errors when reading Local State for icons."""
        chrome = ChromeBrowser()
        
        with patch('os.path.exists', return_value=False):
            icon = chrome._get_profile_icon_from_local_state("Default")
            assert isinstance(icon, ProfileIcon)
            # Should return default icon
            assert icon.background_color == "#4285F4"

    def test_get_profile_icon_from_info_theme_colors(self):
        """Test extracting profile icon from Chrome profile info with theme colors."""
        chrome = ChromeBrowser()
        
        profile_info = {
            "name": "Test Profile",
            "avatar_icon": "chrome://theme/IDR_PROFILE_AVATAR_5",
            "theme_colors": {
                "theme_frame": 16711680,  # Red
                "theme_text": 0  # Black
            }
        }
        
        with patch.object(chrome, '_get_profile_picture_path', return_value=None):
            icon = chrome._get_profile_icon_from_info(profile_info, "Profile1")
            
            assert icon.avatar_icon == "chrome://theme/IDR_PROFILE_AVATAR_5"
            assert icon.background_color == "#FF0000"  # Red
            assert icon.text_color == "#000000"  # Black