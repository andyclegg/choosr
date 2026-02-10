"""Tests for platform support abstraction."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetPlatform:
    def test_linux_returns_linux_platform(self):
        """Linux platform should return LinuxPlatform."""
        with patch.object(sys, "platform", "linux"):
            from platform_support import get_platform, LinuxPlatform

            platform = get_platform()
            assert isinstance(platform, LinuxPlatform)

    def test_darwin_raises_not_implemented(self):
        """macOS platform should raise NotImplementedError."""
        with patch.object(sys, "platform", "darwin"):
            import importlib
            import platform_support

            importlib.reload(platform_support)

            with pytest.raises(NotImplementedError, match="macOS"):
                platform_support.get_platform()

    def test_win32_raises_not_implemented(self):
        """Windows platform should raise NotImplementedError."""
        with patch.object(sys, "platform", "win32"):
            import importlib
            import platform_support

            importlib.reload(platform_support)

            with pytest.raises(NotImplementedError, match="Windows"):
                platform_support.get_platform()


class TestLinuxPlatform:
    def test_chrome_executable(self):
        """Chrome executable should be /usr/bin/google-chrome."""
        from platform_support import LinuxPlatform

        platform = LinuxPlatform()
        assert platform.get_chrome_executable() == "/usr/bin/google-chrome"

    def test_chrome_config_dir(self):
        """Chrome config dir should be ~/.config/google-chrome."""
        from platform_support import LinuxPlatform

        platform = LinuxPlatform()
        expected = Path.home() / ".config" / "google-chrome"
        assert platform.get_chrome_config_dir() == expected

    def test_firefox_executable(self):
        """Firefox executable should be /usr/bin/firefox."""
        from platform_support import LinuxPlatform

        platform = LinuxPlatform()
        assert platform.get_firefox_executable() == "/usr/bin/firefox"

    def test_firefox_config_dir(self):
        """Firefox config dir should be ~/.mozilla/firefox."""
        from platform_support import LinuxPlatform

        platform = LinuxPlatform()
        expected = Path.home() / ".mozilla" / "firefox"
        assert platform.get_firefox_config_dir() == expected

    def test_cache_dir(self):
        """Cache dir should be ~/.cache/choosr."""
        from platform_support import LinuxPlatform

        platform = LinuxPlatform()
        expected = Path.home() / ".cache" / "choosr"
        assert platform.get_cache_dir() == expected
