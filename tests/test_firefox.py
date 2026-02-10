"""Tests for Firefox browser implementation."""

import configparser
from unittest.mock import patch

from firefox import FirefoxBrowser
from browser import Profile, ProfileIcon


class TestFirefoxPlatformAbstraction:
    """Tests for Firefox platform abstraction integration."""

    def test_uses_platform_for_executable(self, mocker):
        """Firefox should use platform abstraction for executable path."""
        from platform_support import LinuxPlatform

        mock_platform = mocker.patch("firefox.get_current_platform")
        mock_platform.return_value = LinuxPlatform()

        from firefox import FirefoxBrowser

        browser = FirefoxBrowser()

        assert browser.executable_path == "/usr/bin/firefox"
        mock_platform.assert_called()

    def test_uses_platform_for_config_dir(self, mocker):
        """Firefox should use platform abstraction for config directory."""
        from platform_support import LinuxPlatform

        mock_platform = mocker.patch("firefox.get_current_platform")
        mock_platform.return_value = LinuxPlatform()

        from firefox import FirefoxBrowser

        browser = FirefoxBrowser()

        assert "firefox" in browser.get_config_directory()


class TestFirefoxBrowser:
    """Tests for FirefoxBrowser class."""

    def test_basic_properties(self):
        """Test basic Firefox browser properties."""
        firefox = FirefoxBrowser()
        assert firefox.name == "firefox"
        assert firefox.display_name == "Mozilla Firefox"
        assert firefox.executable_path == "/usr/bin/firefox"

    def test_profile_colors_constant(self):
        """Test that profile colors constant is properly defined."""
        firefox = FirefoxBrowser()

        assert len(firefox.PROFILE_COLORS) == 8
        assert "#FF6611" in firefox.PROFILE_COLORS  # Firefox orange
        assert "#0060DF" in firefox.PROFILE_COLORS  # Firefox blue

    def test_private_mode_profile(self):
        """Test getting private mode profile."""
        firefox = FirefoxBrowser()
        private = firefox.get_private_mode_profile()

        assert private.id == "private"
        assert private.name == "Private Window"
        assert private.browser == "firefox"
        assert private.is_private is True

    @patch("os.path.isfile")
    @patch("os.access")
    def test_is_available(self, mock_access, mock_isfile):
        """Test Firefox availability check."""
        firefox = FirefoxBrowser()

        # Firefox is available
        mock_isfile.return_value = True
        mock_access.return_value = True
        assert firefox.is_available() is True

        # Firefox executable doesn't exist
        mock_isfile.return_value = False
        assert firefox.is_available() is False

        # Firefox exists but not executable
        mock_isfile.return_value = True
        mock_access.return_value = False
        assert firefox.is_available() is False

    def test_config_paths(self):
        """Test Firefox configuration paths."""
        firefox = FirefoxBrowser()

        config_dir = firefox.get_config_directory()
        assert config_dir.endswith("/.mozilla/firefox")

        profiles_ini = firefox.get_profiles_ini_file()
        assert profiles_ini.endswith("/.mozilla/firefox/profiles.ini")

    @patch("os.path.exists")
    def test_discover_profiles_no_config(self, mock_exists):
        """Test profile discovery when config directory doesn't exist."""
        firefox = FirefoxBrowser()
        mock_exists.return_value = False

        profiles = firefox.discover_profiles()
        assert profiles == []

    @patch("os.path.exists")
    def test_discover_profiles_no_profiles_ini(self, mock_exists):
        """Test profile discovery when profiles.ini doesn't exist."""
        firefox = FirefoxBrowser()

        def exists_side_effect(path):
            if path.endswith(".mozilla/firefox"):
                return True
            if path.endswith("profiles.ini"):
                return False
            return False

        mock_exists.side_effect = exists_side_effect

        profiles = firefox.discover_profiles()
        assert profiles == []

    def test_discover_profiles_with_mock_data(self):
        """Test profile discovery with mock Firefox profiles.ini data."""
        firefox = FirefoxBrowser()

        with (
            patch("os.path.exists", return_value=True),
            patch.object(firefox, "_parse_profiles_ini") as mock_parse,
        ):
            expected_profiles = [
                Profile("default", "default", "firefox", is_private=False),
                Profile("work", "work", "firefox", is_private=False),
            ]
            mock_parse.return_value = expected_profiles

            profiles = firefox.discover_profiles()

            assert len(profiles) == 2
            assert profiles[0].name == "default"
            assert profiles[1].name == "work"
            assert all(p.browser == "firefox" for p in profiles)
            assert all(not p.is_private for p in profiles)

    def test_parse_profiles_ini(self):
        """Test parsing profiles.ini file content."""
        firefox = FirefoxBrowser()

        profiles_ini_content = """[Profile0]
Name=default
IsRelative=1
Path=abcd1234.default
Default=1

[Profile1]
Name=work
IsRelative=1
Path=efgh5678.work

[General]
StartWithLastProfile=1
"""

        # Create a temporary file-like object
        with patch("configparser.ConfigParser.read"):
            # Mock the configparser to parse our content
            config = configparser.ConfigParser()
            config.read_string(profiles_ini_content)

            with patch("configparser.ConfigParser", return_value=config):
                profiles = firefox._parse_profiles_ini("dummy_path")

                assert len(profiles) == 2

                default_profile = next(p for p in profiles if p.name == "default")
                assert default_profile.id == "default"
                assert default_profile.browser == "firefox"
                assert not default_profile.is_private

                work_profile = next(p for p in profiles if p.name == "work")
                assert work_profile.id == "work"
                assert work_profile.browser == "firefox"
                assert not work_profile.is_private

    def test_profile_exists(self):
        """Test profile existence checking."""
        firefox = FirefoxBrowser()

        # Private always exists
        assert firefox.profile_exists("private") is True

        # Mock profiles.ini content for testing

        with (
            patch("os.path.exists", return_value=True),
            patch("configparser.ConfigParser.read"),
            patch(
                "configparser.ConfigParser.sections",
                return_value=["Profile0", "Profile1"],
            ),
        ):
            # Mock sections
            def mock_getitem(section_name):
                if section_name == "Profile0":
                    return {"Name": "default"}
                elif section_name == "Profile1":
                    return {"Name": "work"}
                return {}

            with patch(
                "configparser.ConfigParser.__getitem__", side_effect=mock_getitem
            ):
                assert firefox.profile_exists("default") is True
                assert firefox.profile_exists("work") is True
                assert firefox.profile_exists("nonexistent") is False

    def test_get_default_profile(self):
        """Test getting default Firefox profile."""
        firefox = FirefoxBrowser()

        with (
            patch("os.path.exists", return_value=True),
            patch("configparser.ConfigParser.read"),
            patch(
                "configparser.ConfigParser.sections",
                return_value=["Profile0", "Profile1"],
            ),
        ):

            def mock_getitem(section_name):
                if section_name == "Profile0":
                    section = {"Name": "default"}
                    # Mock getboolean method
                    section_mock = type("MockSection", (), section)()
                    section_mock.getboolean = lambda key, default=False: (
                        key == "Default"
                    )
                    section_mock.get = lambda key, default=None: section.get(
                        key, default
                    )
                    return section_mock
                elif section_name == "Profile1":
                    section = {"Name": "work"}
                    section_mock = type("MockSection", (), section)()
                    section_mock.getboolean = lambda key, default=False: False
                    section_mock.get = lambda key, default=None: section.get(
                        key, default
                    )
                    return section_mock
                return {}

            with (
                patch(
                    "configparser.ConfigParser.__getitem__", side_effect=mock_getitem
                ),
                patch.object(firefox, "get_profile_by_id") as mock_get_profile,
            ):
                mock_profile = Profile("default", "default", "firefox")
                mock_get_profile.return_value = mock_profile

                default = firefox.get_default_profile()
                assert default == mock_profile
                mock_get_profile.assert_called_once_with("default")

    @patch("os.path.isfile")
    def test_get_browser_icon(self, mock_isfile):
        """Test getting Firefox browser icon."""
        firefox = FirefoxBrowser()

        # First path exists
        def mock_isfile_side_effect(path):
            return path == "/usr/share/icons/hicolor/256x256/apps/firefox.png"

        mock_isfile.side_effect = mock_isfile_side_effect
        icon = firefox.get_browser_icon()
        assert icon == "/usr/share/icons/hicolor/256x256/apps/firefox.png"

        # No icon found - reset the side effect
        mock_isfile.side_effect = None
        mock_isfile.return_value = False
        icon = firefox.get_browser_icon()
        assert icon is None

    def test_get_private_mode_icon(self):
        """Test getting Firefox private mode icon."""
        firefox = FirefoxBrowser()

        with patch.object(
            firefox, "get_browser_icon", return_value="/path/to/icon.png"
        ):
            private_icon = firefox.get_private_mode_icon()
            assert private_icon == "/path/to/icon.png"

    def test_get_profile_icon_private(self):
        """Test getting profile icon for private mode."""
        firefox = FirefoxBrowser()
        private_profile = Profile(
            "private", "Private Window", "firefox", is_private=True
        )

        icon = firefox.get_profile_icon(private_profile)
        assert isinstance(icon, ProfileIcon)
        assert icon.avatar_icon == "firefox-private"
        assert icon.background_color == "#592ACB"  # Firefox private purple
        assert icon.text_color == "#FFFFFF"

    def test_get_profile_icon_regular(self):
        """Test getting profile icon for regular profile."""
        firefox = FirefoxBrowser()
        regular_profile = Profile("test-profile", "Test Profile", "firefox")

        icon = firefox.get_profile_icon(regular_profile)
        assert isinstance(icon, ProfileIcon)
        # Hash result may vary, just check it follows expected pattern
        assert icon.avatar_icon.startswith("firefox-avatar-")
        assert icon.background_color in firefox.PROFILE_COLORS
        assert icon.text_color == "#FFFFFF"

    def test_profile_icon_color_consistency(self):
        """Test that profile icons get consistent colors based on profile ID."""
        firefox = FirefoxBrowser()
        profile = Profile("consistent-id", "Test Profile", "firefox")

        # Get icon multiple times
        icon1 = firefox.get_profile_icon(profile)
        icon2 = firefox.get_profile_icon(profile)

        # Should get same color each time
        assert icon1.background_color == icon2.background_color
        assert icon1.avatar_icon == icon2.avatar_icon

    @patch("subprocess.run")
    def test_launch_regular_profile(self, mock_run):
        """Test launching Firefox with regular profile."""
        firefox = FirefoxBrowser()
        profile = Profile("default", "Default Profile", "firefox")

        firefox.launch(profile, "https://example.com")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/usr/bin/firefox" in args
        assert "-P" in args
        assert "default" in args
        assert "https://example.com" in args

    @patch("subprocess.run")
    def test_launch_private_profile(self, mock_run):
        """Test launching Firefox in private mode."""
        firefox = FirefoxBrowser()
        profile = Profile("private", "Private Window", "firefox", is_private=True)

        firefox.launch(profile, "https://example.com")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/usr/bin/firefox" in args
        assert "--private-window" in args
        assert "https://example.com" in args

    @patch("subprocess.run")
    def test_launch_without_url(self, mock_run):
        """Test launching Firefox without URL."""
        firefox = FirefoxBrowser()
        profile = Profile("default", "Default Profile", "firefox")

        firefox.launch(profile)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/usr/bin/firefox" in args
        assert "-P" in args
        assert "default" in args
        # URL should not be in args
        assert len([arg for arg in args if arg.startswith("http")]) == 0

    def test_get_default_profile_no_config(self):
        """Test getting default profile when config doesn't exist."""
        firefox = FirefoxBrowser()

        with patch("os.path.exists", return_value=False):
            default = firefox.get_default_profile()
            assert default is None

    def test_get_default_profile_error(self):
        """Test getting default profile when there's a config error."""
        firefox = FirefoxBrowser()

        with (
            patch("os.path.exists", return_value=True),
            patch("configparser.ConfigParser.read", side_effect=configparser.Error),
        ):
            default = firefox.get_default_profile()
            assert default is None

    def test_profile_exists_error(self):
        """Test profile existence check when there's a config error."""
        firefox = FirefoxBrowser()

        with (
            patch("os.path.exists", return_value=True),
            patch("configparser.ConfigParser.read", side_effect=configparser.Error),
        ):
            # Should return False on error (except for private which is always True)
            assert firefox.profile_exists("private") is True
            assert firefox.profile_exists("regular") is False


class TestFirefoxLaunchErrorHandling:
    """Tests for Firefox launch error handling."""

    def test_launch_returns_true_on_success(self, mocker):
        """launch() should return True when subprocess succeeds."""
        mock_run = mocker.patch("firefox.subprocess.run")
        mock_run.return_value.returncode = 0

        from firefox import FirefoxBrowser
        from browser import Profile

        browser = FirefoxBrowser()
        profile = Profile(id="default", name="default", browser="firefox")

        result = browser.launch(profile, "https://example.com")
        assert result is True

    def test_launch_returns_false_on_failure(self, mocker):
        """launch() should return False when subprocess fails."""
        mock_run = mocker.patch("firefox.subprocess.run")
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error: browser crashed"

        from firefox import FirefoxBrowser
        from browser import Profile

        browser = FirefoxBrowser()
        profile = Profile(id="default", name="default", browser="firefox")

        result = browser.launch(profile, "https://example.com")
        assert result is False
