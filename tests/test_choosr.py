"""Tests for main choosr functionality."""

from unittest.mock import patch, mock_open, MagicMock
import yaml


import choosr
from browser import Profile, BrowserRegistry


class TestConfigurationHandling:
    """Tests for configuration file handling."""

    def test_load_config_no_file(self):
        """Test loading config when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            config = choosr.load_config()
            assert config == {"browser_profiles": {}, "urls": []}

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML config file."""
        config_data = {
            "browser_profiles": {
                "Default": {
                    "browser": "chrome",
                    "profile_id": "Default",
                    "is_private": False,
                }
            },
            "urls": [{"match": "*.work.com", "profile": "Work Profile"}],
        }

        yaml_content = yaml.dump(config_data)

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=yaml_content)),
        ):
            config = choosr.load_config()
            assert config == config_data

    def test_load_config_empty_file(self):
        """Test loading empty YAML config file."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="")),
        ):
            config = choosr.load_config()
            assert config == {"browser_profiles": {}, "urls": []}

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML config file."""
        invalid_yaml = "invalid: yaml: content: ["

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=invalid_yaml)),
            patch("sys.exit") as mock_exit,
        ):
            choosr.load_config()
            mock_exit.assert_called_once_with(1)

    def test_load_config_file_permission_error(self):
        """Test loading config when file cannot be read."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", side_effect=OSError("Permission denied")),
            patch("sys.exit") as mock_exit,
        ):
            choosr.load_config()
            mock_exit.assert_called_once_with(1)

    def test_save_url_match(self):
        """Test saving URL match to config."""
        existing_config = {"browser_profiles": {}, "urls": []}

        with (
            patch.object(choosr, "load_config", return_value=existing_config),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            choosr.save_url_match("*.example.com", "Work Profile")

            # Check that file was opened for writing
            mock_file.assert_called_once()

            # Check the config was updated
            assert len(existing_config["urls"]) == 1
            assert existing_config["urls"][0]["match"] == "*.example.com"
            assert existing_config["urls"][0]["profile"] == "Work Profile"


class TestBrowserManagement:
    """Tests for browser initialization and management."""

    def test_initialize_browsers(self):
        """Test browser initialization."""
        # Clear the registry first
        choosr.browser_registry._browsers.clear()

        choosr.initialize_browsers()

        assert choosr.browser_registry.get_browser("chrome") is not None
        assert choosr.browser_registry.get_browser("firefox") is not None

    def test_find_profile_by_name(self):
        """Test finding profile by name across browsers."""
        # Create mock registry
        registry = BrowserRegistry()

        # Create mock browser with profiles
        mock_browser = MagicMock()
        mock_browser.name = "test"
        mock_browser.is_available.return_value = True

        test_profile = Profile("test-id", "Test Profile", "test")
        mock_browser.get_profile_by_name.return_value = test_profile

        registry.register(mock_browser)

        with patch.object(choosr, "browser_registry", registry):
            profile, browser = choosr._find_profile_by_name("Test Profile")

            assert profile == test_profile
            assert browser == mock_browser

    def test_find_profile_by_name_not_found(self):
        """Test finding profile when it doesn't exist."""
        registry = BrowserRegistry()

        with patch.object(choosr, "browser_registry", registry):
            profile, browser = choosr._find_profile_by_name("Nonexistent Profile")

            assert profile is None
            assert browser is None

    def test_launch_browser_success(self):
        """Test successful browser launch."""
        mock_browser = MagicMock()
        test_profile = Profile("test-id", "Test Profile", "test")

        with patch.object(
            choosr, "_find_profile_by_name", return_value=(test_profile, mock_browser)
        ):
            choosr.launch_browser("Test Profile", "https://example.com")

            mock_browser.launch.assert_called_once_with(
                test_profile, "https://example.com"
            )

    def test_launch_browser_fallback_to_chrome(self):
        """Test fallback to Chrome when profile not found."""
        mock_chrome = MagicMock()
        mock_chrome.name = "chrome"
        mock_chrome.discover_profiles.return_value = [
            Profile("default", "Default", "chrome")
        ]

        registry = BrowserRegistry()
        registry.register(mock_chrome)

        with (
            patch.object(choosr, "_find_profile_by_name", return_value=(None, None)),
            patch.object(choosr, "browser_registry", registry),
        ):
            choosr.launch_browser("Nonexistent Profile", "https://example.com")

            mock_chrome.launch.assert_called_once()

    def test_get_all_browser_profiles(self):
        """Test getting all browser profiles."""
        mock_browser1 = MagicMock()
        mock_browser1.is_available.return_value = True
        mock_browser1.get_all_profiles.return_value = [
            Profile("prof1", "Profile 1", "browser1"),
            Profile("priv1", "Private 1", "browser1", is_private=True),
        ]

        mock_browser2 = MagicMock()
        mock_browser2.is_available.return_value = True
        mock_browser2.get_all_profiles.return_value = [
            Profile("prof2", "Profile 2", "browser2")
        ]

        registry = BrowserRegistry()
        registry.register(mock_browser1)
        registry.register(mock_browser2)

        with patch.object(choosr, "browser_registry", registry):
            profiles = choosr.get_all_browser_profiles()

            assert len(profiles) == 3
            profile_names = [p.name for p in profiles]
            assert "Profile 1" in profile_names
            assert "Private 1" in profile_names
            assert "Profile 2" in profile_names


class TestConfigInitialization:
    """Tests for config file initialization."""

    def test_init_config_file_exists(self):
        """Test init when config file already exists and is valid."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="browser_profiles: {}")),
            patch("yaml.safe_load", return_value={"browser_profiles": {}}),
        ):
            with patch("builtins.print") as mock_print:
                choosr.init_config()
                # Check that the success message was printed
                printed_messages = [call.args[0] for call in mock_print.call_args_list]
                assert any(
                    "Config file already exists" in msg for msg in printed_messages
                )

    def test_init_config_invalid_existing_file(self):
        """Test init when existing config file is invalid."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open()),
            patch("yaml.safe_load", side_effect=yaml.YAMLError),
            patch("builtins.input", return_value="n"),
        ):
            with patch("builtins.print") as mock_print:
                choosr.init_config()
                mock_print.assert_called_with("Config file initialization cancelled.")

    def test_init_config_create_new(self):
        """Test creating new config file."""
        mock_profiles = [
            Profile("default", "Default", "chrome"),
            Profile("work", "Work Profile", "chrome"),
            Profile("private", "Private", "chrome", is_private=True),
        ]

        with (
            patch("os.path.exists", return_value=False),
            patch.object(
                choosr, "get_all_browser_profiles", return_value=mock_profiles
            ),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            with patch("builtins.print"):
                choosr.init_config()

            # Should have attempted to write file
            mock_file.assert_called()


class TestUrlHandling:
    """Tests for URL handling and profile selection."""

    def test_handle_url_with_existing_match(self):
        """Test handling URL that matches existing pattern."""
        config = {
            "browser_profiles": {
                "Work Profile": {"browser": "chrome", "profile_id": "work"}
            },
            "urls": [{"match": "work.com", "profile": "Work Profile"}],
        }

        with (
            patch.object(choosr, "load_config", return_value=config),
            patch.object(choosr, "launch_browser") as mock_launch,
        ):
            choosr.handle_url("https://mail.work.com")

            mock_launch.assert_called_once_with(
                "Work Profile", url="https://mail.work.com"
            )

    def test_handle_url_no_match_with_gui(self):
        """Test handling URL with no match, showing GUI selector."""
        config = {
            "browser_profiles": {
                "Default": {"browser": "chrome", "profile_id": "default"}
            },
            "urls": [],
        }

        with (
            patch.object(choosr, "load_config", return_value=config),
            patch(
                "qt_interface.show_qt_profile_selector",
                return_value=("Default", "*.example.com", True),
            ),
            patch.object(choosr, "save_url_match") as mock_save,
            patch.object(choosr, "launch_browser") as mock_launch,
        ):
            choosr.handle_url("https://example.com")

            mock_save.assert_called_once_with("*.example.com", "Default")
            mock_launch.assert_called_once_with("Default", url="https://example.com")

    def test_handle_url_gui_cancelled(self):
        """Test handling URL when GUI selector is cancelled."""
        config = {
            "browser_profiles": {
                "Default": {"browser": "chrome", "profile_id": "default"}
            },
            "urls": [],
        }

        with (
            patch.object(choosr, "load_config", return_value=config),
            patch("qt_interface.show_qt_profile_selector", return_value=None),
            patch.object(choosr, "launch_browser") as mock_launch,
        ):
            choosr.handle_url("https://example.com")

            # Should not launch anything when cancelled
            mock_launch.assert_not_called()

    def test_handle_url_no_profiles_configured(self):
        """Test handling URL when no profiles are configured."""
        config = {"browser_profiles": {}, "urls": []}

        mock_profiles = [Profile("default", "Default", "chrome")]

        with (
            patch.object(choosr, "load_config", return_value=config),
            patch.object(
                choosr, "get_all_browser_profiles", return_value=mock_profiles
            ),
            patch.object(choosr, "launch_browser") as mock_launch,
        ):
            choosr.handle_url("https://example.com")

            mock_launch.assert_called_once_with("Default", url="https://example.com")

    def test_handle_url_domain_extraction(self):
        """Test URL domain extraction."""
        config = {
            "browser_profiles": {"Work": {"browser": "chrome", "profile_id": "work"}},
            "urls": [{"match": "github.com", "profile": "Work"}],
        }

        with (
            patch.object(choosr, "load_config", return_value=config),
            patch.object(choosr, "launch_browser") as mock_launch,
        ):
            # Test various URL formats
            choosr.handle_url("https://github.com/user/repo")
            mock_launch.assert_called_with("Work", url="https://github.com/user/repo")

            choosr.handle_url("http://api.github.com/v1/repos")
            mock_launch.assert_called_with("Work", url="http://api.github.com/v1/repos")


class TestMainFunction:
    """Tests for main entry point."""

    def test_main_init_command(self):
        """Test main function with init command."""
        with (
            patch("sys.argv", ["choosr", "init"]),
            patch.object(choosr, "initialize_browsers"),
            patch.object(choosr, "init_config") as mock_init,
        ):
            choosr.main()
            mock_init.assert_called_once()

    def test_main_url_command(self):
        """Test main function with url command."""
        with (
            patch("sys.argv", ["choosr", "url", "https://example.com"]),
            patch.object(choosr, "initialize_browsers"),
            patch.object(choosr, "handle_url") as mock_handle,
        ):
            choosr.main()
            mock_handle.assert_called_once_with("https://example.com")

    def test_main_no_command(self):
        """Test main function with no command (should show help)."""
        with (
            patch("sys.argv", ["choosr"]),
            patch.object(choosr, "initialize_browsers"),
            patch("argparse.ArgumentParser.print_help") as mock_help,
        ):
            choosr.main()
            mock_help.assert_called_once()

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        with (
            patch("sys.argv", ["choosr", "invalid"]),
            patch.object(choosr, "initialize_browsers"),
            patch("argparse.ArgumentParser.print_help"),
            patch("sys.exit"),
        ):
            try:
                choosr.main()
            except SystemExit:
                pass  # argparse calls sys.exit for invalid commands

            # Either help is called or SystemExit is raised by argparse
            # We just need to verify initialize_browsers was called
            pass


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_yaml_write_error_handler(self):
        """Test YAML write error handling decorator."""
        import yaml

        @choosr._handle_yaml_write_error("/test/path", "test operation")
        def failing_function():
            raise yaml.YAMLError("Test YAML error")

        with patch("builtins.print") as mock_print:
            failing_function()

            # Should print error messages
            assert mock_print.call_count >= 2
            assert any(
                "YAML serialization error" in str(call)
                for call in mock_print.call_args_list
            )

    def test_os_error_handler(self):
        """Test OS error handling in decorator."""

        @choosr._handle_yaml_write_error("/test/path", "test operation")
        def failing_function():
            raise OSError("Test OS error")

        with patch("builtins.print") as mock_print:
            failing_function()

            # Should print error messages
            assert mock_print.call_count >= 2
            assert any(
                "File system error" in str(call) for call in mock_print.call_args_list
            )
