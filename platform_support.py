"""
Platform support abstraction for choosr.

Centralizes all OS-specific paths and executables to enable future
cross-platform support for Windows and macOS.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path


class PlatformSupport(ABC):
    """Abstract base class for platform-specific support."""

    @abstractmethod
    def get_chrome_executable(self) -> str:
        """Return path to Chrome executable."""
        pass

    @abstractmethod
    def get_chrome_config_dir(self) -> Path:
        """Return path to Chrome configuration directory."""
        pass

    @abstractmethod
    def get_firefox_executable(self) -> str:
        """Return path to Firefox executable."""
        pass

    @abstractmethod
    def get_firefox_config_dir(self) -> Path:
        """Return path to Firefox configuration directory."""
        pass

    @abstractmethod
    def get_cache_dir(self) -> Path:
        """Return path to choosr cache directory."""
        pass


class LinuxPlatform(PlatformSupport):
    """Linux platform support."""

    def get_chrome_executable(self) -> str:
        return "/usr/bin/google-chrome"

    def get_chrome_config_dir(self) -> Path:
        return Path.home() / ".config" / "google-chrome"

    def get_firefox_executable(self) -> str:
        return "/usr/bin/firefox"

    def get_firefox_config_dir(self) -> Path:
        return Path.home() / ".mozilla" / "firefox"

    def get_cache_dir(self) -> Path:
        return Path.home() / ".cache" / "choosr"


class WindowsPlatform(PlatformSupport):
    """Windows platform support (not yet implemented)."""

    def get_chrome_executable(self) -> str:
        raise NotImplementedError("Windows support coming soon")

    def get_chrome_config_dir(self) -> Path:
        raise NotImplementedError("Windows support coming soon")

    def get_firefox_executable(self) -> str:
        raise NotImplementedError("Windows support coming soon")

    def get_firefox_config_dir(self) -> Path:
        raise NotImplementedError("Windows support coming soon")

    def get_cache_dir(self) -> Path:
        raise NotImplementedError("Windows support coming soon")


class MacOSPlatform(PlatformSupport):
    """macOS platform support (not yet implemented)."""

    def get_chrome_executable(self) -> str:
        raise NotImplementedError("macOS support coming soon")

    def get_chrome_config_dir(self) -> Path:
        raise NotImplementedError("macOS support coming soon")

    def get_firefox_executable(self) -> str:
        raise NotImplementedError("macOS support coming soon")

    def get_firefox_config_dir(self) -> Path:
        raise NotImplementedError("macOS support coming soon")

    def get_cache_dir(self) -> Path:
        raise NotImplementedError("macOS support coming soon")


def get_platform() -> PlatformSupport:
    """
    Get the appropriate platform support instance.

    Returns:
        PlatformSupport instance for the current platform.

    Raises:
        NotImplementedError: If the current platform is not supported.
    """
    if sys.platform.startswith("linux"):
        return LinuxPlatform()
    elif sys.platform == "darwin":
        raise NotImplementedError("macOS support coming soon")
    elif sys.platform == "win32":
        raise NotImplementedError("Windows support coming soon")
    else:
        raise NotImplementedError(f"Unsupported platform: {sys.platform}")


# Global instance for convenience
_platform_instance = None


def get_current_platform() -> PlatformSupport:
    """Get cached platform instance."""
    global _platform_instance
    if _platform_instance is None:
        _platform_instance = get_platform()
    return _platform_instance
