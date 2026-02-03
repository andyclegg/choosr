# Quality Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add logging, platform abstraction, error handling, GUI timeout, Qt tests, config validation, and documentation.

**Architecture:** Create new modules for logging (`logging_config.py`) and platform abstraction (`platform_support.py`). Modify browser implementations to use platform abstraction and return launch success/failure. Add proper event loop handling to Qt interface.

**Tech Stack:** Python 3.9+, PySide6, pytest, pytest-qt

---

## Task 1: Create Logging Module

**Files:**
- Create: `logging_config.py`
- Create: `tests/test_logging_config.py`

**Step 1: Write the failing test**

```python
# tests/test_logging_config.py
"""Tests for logging configuration."""

import logging
import os
from unittest.mock import patch

import pytest


class TestSetupLogging:
    def test_default_level_is_warning(self):
        """Default log level should be WARNING."""
        from logging_config import setup_logging, get_logger

        setup_logging()
        logger = get_logger()
        assert logger.level == logging.WARNING

    def test_debug_flag_sets_debug_level(self):
        """--debug flag should set DEBUG level."""
        from logging_config import setup_logging, get_logger

        setup_logging(debug=True)
        logger = get_logger()
        assert logger.level == logging.DEBUG

    def test_env_var_sets_debug_level(self):
        """CHOOSR_DEBUG=1 should set DEBUG level."""
        from logging_config import setup_logging, get_logger

        with patch.dict(os.environ, {"CHOOSR_DEBUG": "1"}):
            setup_logging()
            logger = get_logger()
            assert logger.level == logging.DEBUG

    def test_logger_name_is_choosr(self):
        """Logger should be named 'choosr'."""
        from logging_config import get_logger

        logger = get_logger()
        assert logger.name == "choosr"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_logging_config.py -v`
Expected: FAIL with "No module named 'logging_config'"

**Step 3: Write minimal implementation**

```python
# logging_config.py
"""
Logging configuration for choosr.

Provides a consistent logging setup across all modules with support for
debug mode via --debug flag or CHOOSR_DEBUG environment variable.
"""

import logging
import os
import sys

_logger = None


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging for choosr.

    Args:
        debug: If True, set log level to DEBUG. Also checks CHOOSR_DEBUG env var.
    """
    global _logger

    # Check environment variable
    env_debug = os.environ.get("CHOOSR_DEBUG", "").lower() in ("1", "true", "yes")

    level = logging.DEBUG if (debug or env_debug) else logging.WARNING

    # Create logger
    _logger = logging.getLogger("choosr")
    _logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    _logger.handlers.clear()

    # Create stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter("[choosr] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    _logger.addHandler(handler)


def get_logger() -> logging.Logger:
    """
    Get the choosr logger.

    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is None:
        setup_logging()
    return _logger
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_logging_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add logging_config.py tests/test_logging_config.py && git commit -m "feat: add logging configuration module"
```

---

## Task 2: Create Platform Abstraction Module

**Files:**
- Create: `platform_support.py`
- Create: `tests/test_platform_support.py`

**Step 1: Write the failing test**

```python
# tests/test_platform_support.py
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
            # Need to reimport to get fresh platform detection
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
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_platform_support.py -v`
Expected: FAIL with "No module named 'platform_support'"

**Step 3: Write minimal implementation**

```python
# platform_support.py
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
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_platform_support.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add platform_support.py tests/test_platform_support.py && git commit -m "feat: add platform abstraction module"
```

---

## Task 3: Integrate Platform Abstraction into Chrome Browser

**Files:**
- Modify: `chrome.py`
- Modify: `tests/test_chrome.py`

**Step 1: Write the failing test**

Add to `tests/test_chrome.py`:

```python
class TestChromePlatformAbstraction:
    def test_uses_platform_for_executable(self, mocker):
        """Chrome should use platform abstraction for executable path."""
        from platform_support import LinuxPlatform
        mock_platform = mocker.patch("chrome.get_current_platform")
        mock_platform.return_value = LinuxPlatform()

        from chrome import ChromeBrowser
        browser = ChromeBrowser()

        assert browser.executable_path == "/usr/bin/google-chrome"
        mock_platform.assert_called()

    def test_uses_platform_for_config_dir(self, mocker):
        """Chrome should use platform abstraction for config directory."""
        from platform_support import LinuxPlatform
        mock_platform = mocker.patch("chrome.get_current_platform")
        mock_platform.return_value = LinuxPlatform()

        from chrome import ChromeBrowser
        browser = ChromeBrowser()

        assert "google-chrome" in browser.get_config_directory()
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_chrome.py::TestChromePlatformAbstraction -v`
Expected: FAIL (no import of platform_support in chrome.py)

**Step 3: Modify chrome.py to use platform abstraction**

Update imports at top of `chrome.py`:

```python
from platform_support import get_current_platform
```

Update `executable_path` property:

```python
@property
def executable_path(self) -> str:
    """Return the path to the Chrome executable."""
    return get_current_platform().get_chrome_executable()
```

Update `get_config_directory` method:

```python
def get_config_directory(self) -> str:
    """
    Get the Chrome configuration directory.

    Returns the path to Chrome's configuration directory.
    """
    return str(get_current_platform().get_chrome_config_dir())
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_chrome.py -v`
Expected: PASS (all Chrome tests)

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add chrome.py tests/test_chrome.py && git commit -m "refactor: use platform abstraction in Chrome browser"
```

---

## Task 4: Integrate Platform Abstraction into Firefox Browser

**Files:**
- Modify: `firefox.py`
- Modify: `tests/test_firefox.py`

**Step 1: Write the failing test**

Add to `tests/test_firefox.py`:

```python
class TestFirefoxPlatformAbstraction:
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
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_firefox.py::TestFirefoxPlatformAbstraction -v`
Expected: FAIL

**Step 3: Modify firefox.py to use platform abstraction**

Update imports at top of `firefox.py`:

```python
from platform_support import get_current_platform
```

Update `executable_path` property:

```python
@property
def executable_path(self) -> str:
    """Return the path to the Firefox executable."""
    return get_current_platform().get_firefox_executable()
```

Update `get_config_directory` method:

```python
def get_config_directory(self) -> str:
    """
    Get the Firefox configuration directory.

    Returns the path to Firefox's configuration directory.
    """
    return str(get_current_platform().get_firefox_config_dir())
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_firefox.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add firefox.py tests/test_firefox.py && git commit -m "refactor: use platform abstraction in Firefox browser"
```

---

## Task 5: Add Launch Error Handling to Chrome Browser

**Files:**
- Modify: `chrome.py`
- Modify: `tests/test_chrome.py`

**Step 1: Write the failing test**

Add to `tests/test_chrome.py`:

```python
class TestChromeLaunchErrorHandling:
    def test_launch_returns_true_on_success(self, mocker):
        """launch() should return True when subprocess succeeds."""
        mock_run = mocker.patch("chrome.subprocess.run")
        mock_run.return_value.returncode = 0

        from chrome import ChromeBrowser
        from browser import Profile

        browser = ChromeBrowser()
        profile = Profile(id="Default", name="Default", browser="chrome")

        result = browser.launch(profile, "https://example.com")
        assert result is True

    def test_launch_returns_false_on_failure(self, mocker):
        """launch() should return False when subprocess fails."""
        mock_run = mocker.patch("chrome.subprocess.run")
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error: browser crashed"

        from chrome import ChromeBrowser
        from browser import Profile

        browser = ChromeBrowser()
        profile = Profile(id="Default", name="Default", browser="chrome")

        result = browser.launch(profile, "https://example.com")
        assert result is False

    def test_launch_logs_error_on_failure(self, mocker, caplog):
        """launch() should log error when subprocess fails."""
        import logging

        mock_run = mocker.patch("chrome.subprocess.run")
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "browser crashed"

        from chrome import ChromeBrowser
        from browser import Profile
        from logging_config import setup_logging

        setup_logging(debug=True)

        browser = ChromeBrowser()
        profile = Profile(id="Default", name="Default", browser="chrome")

        with caplog.at_level(logging.ERROR, logger="choosr"):
            browser.launch(profile, "https://example.com")

        assert "browser crashed" in caplog.text or "failed" in caplog.text.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_chrome.py::TestChromeLaunchErrorHandling -v`
Expected: FAIL (launch returns None, not bool)

**Step 3: Modify chrome.py launch method**

```python
def launch(self, profile: Profile, url: Optional[str] = None) -> bool:
    """
    Launch Chrome with the specified profile and optional URL.

    Args:
        profile: Profile object to launch with
        url: Optional URL to open

    Returns:
        True if launch succeeded, False otherwise.
    """
    from logging_config import get_logger
    logger = get_logger()

    command = [self.executable_path]

    # Handle incognito mode (when profile directory is None)
    if profile.is_private:
        command.append("--incognito")
    else:
        command.append(f"--profile-directory={profile.id}")

    if url is not None:
        command.append(url)

    logger.debug("Launching Chrome: %s", " ".join(command))

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("Chrome launch failed (exit code %d): %s",
                     result.returncode, result.stderr)
        return False

    logger.info("Launched Chrome profile '%s'", profile.name)
    return True
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_chrome.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add chrome.py tests/test_chrome.py && git commit -m "feat: add launch error handling to Chrome browser"
```

---

## Task 6: Add Launch Error Handling to Firefox Browser

**Files:**
- Modify: `firefox.py`
- Modify: `tests/test_firefox.py`

**Step 1: Write the failing test**

Add to `tests/test_firefox.py`:

```python
class TestFirefoxLaunchErrorHandling:
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
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_firefox.py::TestFirefoxLaunchErrorHandling -v`
Expected: FAIL

**Step 3: Modify firefox.py launch method**

```python
def launch(self, profile: Profile, url: Optional[str] = None) -> bool:
    """
    Launch Firefox with the specified profile and optional URL.

    Args:
        profile: Profile object to launch with
        url: Optional URL to open

    Returns:
        True if launch succeeded, False otherwise.
    """
    from logging_config import get_logger
    logger = get_logger()

    command = [self.executable_path]

    # Handle private browsing mode
    if profile.is_private:
        command.append("--private-window")
    else:
        # Use profile name for regular profiles
        command.extend(["-P", profile.id])

    if url is not None:
        command.append(url)

    logger.debug("Launching Firefox: %s", " ".join(command))

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("Firefox launch failed (exit code %d): %s",
                     result.returncode, result.stderr)
        return False

    logger.info("Launched Firefox profile '%s'", profile.name)
    return True
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_firefox.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add firefox.py tests/test_firefox.py && git commit -m "feat: add launch error handling to Firefox browser"
```

---

## Task 7: Update Browser Abstract Class for Return Type

**Files:**
- Modify: `browser.py`

**Step 1: Update the abstract method signature**

Change the `launch` method in the `Browser` abstract class:

```python
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
```

**Step 2: Run all tests to verify nothing broke**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add browser.py && git commit -m "refactor: update Browser.launch() to return bool"
```

---

## Task 8: Add Cache Write Logging

**Files:**
- Modify: `browser.py`

**Step 1: Update _save_cache to log warnings**

```python
def _save_cache(self) -> None:
    """Save cache data to disk."""
    from logging_config import get_logger
    logger = get_logger()

    try:
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir:  # Only create directory if there is one
            os.makedirs(cache_dir, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache_data, f, indent=2)
        logger.debug("Saved profile cache to %s", self.cache_file)
    except OSError as e:
        logger.warning("Failed to write profile cache: %s", e)
```

**Step 2: Add cache hit/miss logging to get_cached_profiles**

```python
def get_cached_profiles(
    self, browser_name: str, source_files: List[str]
) -> Optional[List[Profile]]:
    """Get cached profiles if cache is still valid."""
    from logging_config import get_logger
    logger = get_logger()

    cache_key = f"{browser_name}_profiles"

    if cache_key not in self._cache_data:
        logger.debug("Cache miss for %s (no cache entry)", browser_name)
        return None

    cached_entry = self._cache_data[cache_key]
    cached_time = cached_entry.get("timestamp", 0)

    # Check if any source file is newer than cache
    for source_file in source_files:
        if os.path.exists(source_file):
            file_mtime = os.path.getmtime(source_file)
            if file_mtime > cached_time:
                logger.debug("Cache miss for %s (source file changed)", browser_name)
                return None

    # Deserialize profiles
    try:
        profile_data = cached_entry.get("profiles", [])
        profiles = [Profile.from_dict(p) for p in profile_data]
        logger.debug("Cache hit for %s (%d profiles)", browser_name, len(profiles))
        return profiles
    except (KeyError, TypeError):
        logger.debug("Cache miss for %s (invalid cache data)", browser_name)
        return None
```

**Step 3: Run tests**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_cache.py -v`
Expected: PASS

**Step 4: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add browser.py && git commit -m "feat: add logging to profile cache operations"
```

---

## Task 9: Add Error Dialog to Qt Interface

**Files:**
- Modify: `qt_interface.py`
- Create: `tests/test_qt_interface.py`

**Step 1: Write the failing test**

```python
# tests/test_qt_interface.py
"""Tests for Qt interface."""

import pytest


class TestShowErrorDialog:
    def test_show_error_dialog_does_not_crash(self, qtbot):
        """Error dialog should display without crashing."""
        from qt_interface import show_error_dialog

        # This should not raise an exception
        # We can't easily verify the dialog appeared, but we can verify no crash
        show_error_dialog("Test Error", "This is a test error message")

    def test_show_error_dialog_with_empty_message(self, qtbot):
        """Error dialog should handle empty message."""
        from qt_interface import show_error_dialog

        show_error_dialog("Error", "")


class TestThemeDetection:
    def test_detect_system_theme_returns_string(self, qtbot):
        """Theme detection should return 'light' or 'dark'."""
        from qt_interface import ProfileSelectorController

        controller = ProfileSelectorController()
        theme = controller._detect_system_theme()

        assert theme in ("light", "dark")
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_qt_interface.py -v`
Expected: FAIL (no show_error_dialog function)

**Step 3: Add show_error_dialog function to qt_interface.py**

Add after imports:

```python
def show_error_dialog(title: str, message: str) -> None:
    """
    Show an error dialog to the user.

    Works even if the main GUI failed to initialize. Useful for
    reporting errors to users who launched from desktop (no terminal).

    Args:
        title: Dialog title
        message: Error message to display
    """
    from logging_config import get_logger
    logger = get_logger()

    logger.error("%s: %s", title, message)

    try:
        from PySide6.QtWidgets import QMessageBox, QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    except Exception as e:
        # If Qt fails, at least we logged the error
        logger.warning("Could not show error dialog: %s", e)
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_qt_interface.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add qt_interface.py tests/test_qt_interface.py && git commit -m "feat: add error dialog function to Qt interface"
```

---

## Task 10: Add GUI Timeout with QEventLoop

**Files:**
- Modify: `qt_interface.py`
- Modify: `tests/test_qt_interface.py`

**Step 1: Write the failing test**

Add to `tests/test_qt_interface.py`:

```python
class TestProfileSelectorTimeout:
    def test_timeout_returns_none(self, qtbot, mocker):
        """Timeout should return None without hanging."""
        from qt_interface import ProfileSelectorController

        controller = ProfileSelectorController()

        # Mock the view to prevent actual window creation
        mock_view = mocker.MagicMock()
        mock_view.status.return_value = 0  # QQuickView.Ready
        mock_root = mocker.MagicMock()
        mock_view.rootObject.return_value = mock_root

        mocker.patch.object(controller, "_view", mock_view)

        # Set a very short timeout for testing
        controller._timeout_ms = 100

        # This should timeout and return None
        # Note: Full integration test would require more setup
```

**Step 2: Modify show_profile_selector to use QEventLoop with timeout**

Replace the event loop section in `show_profile_selector`:

```python
from PySide6.QtCore import QObject, Signal, Slot, QUrl, QTimer, Qt, QEventLoop

# In show_profile_selector method, replace the while loop with:

        # Create event loop for blocking
        self._event_loop = QEventLoop()
        self._timed_out = False

        # Set timeout (5 minutes default, configurable via env)
        import os
        timeout_ms = int(os.environ.get("CHOOSR_TIMEOUT", "300000"))

        def on_timeout():
            from logging_config import get_logger
            get_logger().warning("Profile selector timed out after %d seconds", timeout_ms // 1000)
            self._timed_out = True
            self._event_loop.quit()

        QTimer.singleShot(timeout_ms, on_timeout)

        # Show window
        self._view.show()

        # Block until selection, cancel, or timeout
        self._event_loop.exec()

        # Clean up
        if self._view:
            self._view.close()
            self._view = None

        if self._timed_out:
            return None

        return self._result
```

Also update `_on_profile_selected` and `_on_cancelled`:

```python
@Slot(str, str, bool)
def _on_profile_selected(
    self, profile_name: str, domain_pattern: str, save_choice: bool
):
    """Handle profile selection from QML."""
    self._result = (profile_name, domain_pattern, save_choice)
    if self._event_loop:
        self._event_loop.quit()

@Slot()
def _on_cancelled(self):
    """Handle cancellation from QML."""
    self._cancelled = True
    if self._event_loop:
        self._event_loop.quit()
```

And update `handle_window_close`:

```python
def handle_window_close():
    self._cancelled = True
    if self._event_loop:
        self._event_loop.quit()
```

**Step 3: Run tests**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_qt_interface.py -v`
Expected: PASS

**Step 4: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add qt_interface.py tests/test_qt_interface.py && git commit -m "feat: replace busy-wait with QEventLoop and timeout"
```

---

## Task 11: Add Configuration Validation

**Files:**
- Modify: `choosr.py`
- Modify: `tests/test_choosr.py`

**Step 1: Write the failing test**

Add to `tests/test_choosr.py`:

```python
class TestConfigValidation:
    def test_validate_config_valid(self):
        """Valid config should return empty warnings list."""
        from choosr import validate_config

        config = {
            "browser_profiles": {
                "chrome-default": {"browser": "chrome", "name": "Default"}
            },
            "urls": [
                {"match": "*.example.com", "profile": "chrome-default"}
            ]
        }
        available_profiles = {"chrome-default"}

        warnings = validate_config(config, available_profiles)
        assert warnings == []

    def test_validate_config_missing_profile(self):
        """Config referencing missing profile should warn."""
        from choosr import validate_config

        config = {
            "browser_profiles": {},
            "urls": [
                {"match": "*.example.com", "profile": "nonexistent"}
            ]
        }
        available_profiles = set()

        warnings = validate_config(config, available_profiles)
        assert any("nonexistent" in w for w in warnings)

    def test_validate_config_invalid_pattern(self):
        """Config with invalid glob pattern should warn."""
        from choosr import validate_config

        config = {
            "browser_profiles": {
                "chrome-default": {"browser": "chrome", "name": "Default"}
            },
            "urls": [
                {"match": "[invalid", "profile": "chrome-default"}
            ]
        }
        available_profiles = {"chrome-default"}

        warnings = validate_config(config, available_profiles)
        assert any("invalid" in w.lower() or "pattern" in w.lower() for w in warnings)
```

**Step 2: Run test to verify it fails**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_choosr.py::TestConfigValidation -v`
Expected: FAIL (no validate_config function)

**Step 3: Add validate_config function to choosr.py**

```python
def validate_config(config: dict, available_profiles: set) -> list:
    """
    Validate configuration and return list of warnings.

    Args:
        config: The loaded configuration dictionary
        available_profiles: Set of valid profile keys

    Returns:
        List of warning messages (empty if config is valid)
    """
    from logging_config import get_logger
    logger = get_logger()
    warnings = []

    # Validate URL entries
    for url_entry in config.get("urls", []):
        profile_key = url_entry.get("profile", "")
        match_pattern = url_entry.get("match", "")

        # Check profile exists
        if profile_key and profile_key not in available_profiles:
            msg = f"URL pattern '{match_pattern}' references unknown profile '{profile_key}'"
            warnings.append(msg)
            logger.warning(msg)

        # Check pattern is valid
        if match_pattern and not _is_valid_glob_pattern(match_pattern):
            msg = f"Invalid glob pattern: '{match_pattern}'"
            warnings.append(msg)
            logger.warning(msg)

    return warnings


def _is_valid_glob_pattern(pattern: str) -> bool:
    """
    Check if a pattern is a valid fnmatch glob.

    Args:
        pattern: The glob pattern to validate

    Returns:
        True if pattern is valid, False otherwise
    """
    try:
        fnmatch.translate(pattern)
        return True
    except Exception:
        return False
```

**Step 4: Run test to verify it passes**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest tests/test_choosr.py::TestConfigValidation -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add choosr.py tests/test_choosr.py && git commit -m "feat: add configuration validation"
```

---

## Task 12: Integrate Validation into Config Loading

**Files:**
- Modify: `choosr.py`

**Step 1: Update load_config to validate and warn**

Add validation call after loading config in `load_config`:

```python
def load_config():
    """Load choosr configuration from YAML file, creating it if it doesn't exist."""
    from logging_config import get_logger
    logger = get_logger()

    config_path = os.path.expanduser("~/.choosr.yaml")

    if not os.path.exists(config_path):
        # Auto-create config file if it doesn't exist
        _create_initial_config(config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            config = config or {"browser_profiles": {}, "urls": []}

            # Validate config
            available_profiles = set(config.get("browser_profiles", {}).keys())
            warnings = validate_config(config, available_profiles)

            if warnings:
                logger.warning("Configuration has %d issue(s):", len(warnings))
                for warning in warnings:
                    print(f"  Warning: {warning}", file=sys.stderr)

            return config
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file {config_path}")
        print(f"YAML parsing error: {e}")
        print("Please check the file syntax and fix any formatting issues.")
        sys.exit(1)
    except OSError as e:
        print(f"Error: Cannot read config file {config_path}")
        print(f"File system error: {e}")
        sys.exit(1)
```

**Step 2: Run all tests**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add choosr.py && git commit -m "feat: integrate config validation into load_config"
```

---

## Task 13: Add --debug Flag to CLI

**Files:**
- Modify: `choosr.py`

**Step 1: Update argument parser and main function**

```python
def main():
    """Main entry point for choosr application."""
    parser = argparse.ArgumentParser(description="Browser profile chooser")

    # Add global options
    parser.add_argument(
        "--rescan-browsers",
        action="store_true",
        help="Rescan browsers and update profile configuration",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    # URL as positional argument
    parser.add_argument("url", nargs="?", help="URL to open")

    args = parser.parse_args()

    # Setup logging before anything else
    from logging_config import setup_logging
    setup_logging(debug=args.debug)

    # Initialize browser registry
    initialize_browsers()

    if args.rescan_browsers:
        rescan_browsers()
    elif args.url:
        handle_url(args.url)
    else:
        # No URL provided - show help
        parser.print_help()
```

**Step 2: Run tests**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add choosr.py && git commit -m "feat: add --debug flag to CLI"
```

---

## Task 14: Add Launch Failure Error Dialog in choosr.py

**Files:**
- Modify: `choosr.py`

**Step 1: Update launch_browser_by_config_key to show error on failure**

```python
def launch_browser_by_config_key(config_key, url=None):
    """Launch browser using a config key to look up profile settings."""
    from browser import Profile
    from logging_config import get_logger
    logger = get_logger()

    config = load_config()
    profile_config = config.get("browser_profiles", {}).get(config_key)

    if not profile_config:
        logger.error("Profile config not found: %s", config_key)
        return False

    browser_name = profile_config.get("browser")
    browser = browser_registry.get_browser(browser_name)

    if not browser:
        logger.error("Browser not found: %s", browser_name)
        return False

    profile = Profile(
        id=profile_config.get("profile_id", config_key),
        name=profile_config.get("name", config_key),
        browser=browser_name,
        is_private=profile_config.get("is_private", False),
        email=profile_config.get("email"),
    )

    success = browser.launch(profile, url)

    if not success:
        try:
            from qt_interface import show_error_dialog
            show_error_dialog(
                "Launch Failed",
                f"Could not open URL in {profile.name}.\n\n"
                f"Run with --debug for more information."
            )
        except ImportError:
            pass  # Qt not available, error was already logged

    return success
```

**Step 2: Run tests**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add choosr.py && git commit -m "feat: show error dialog on browser launch failure"
```

---

## Task 15: Update README Documentation

**Files:**
- Modify: `README.md`

**Step 1: Add comprehensive documentation**

Replace README.md content:

```markdown
# Choosr

A browser profile selector that lets you choose which browser profile to use when opening URLs. Acts as a default browser handler with a modern Qt/QML interface.

## Installation

```bash
# Install dependencies
uv sync

# Install system-wide
./install.sh

# Set as default browser
xdg-settings set default-web-browser choosr.desktop
```

## Usage

```bash
# Open URL with profile selector
choosr https://example.com

# Rescan browser profiles
choosr --rescan-browsers

# Enable debug logging
choosr --debug https://example.com

# Or use environment variable
CHOOSR_DEBUG=1 choosr https://example.com
```

## Configuration

Choosr stores configuration in `~/.choosr.yaml`. On first run, it auto-discovers browser profiles and creates a default config.

### Config Structure

```yaml
browser_profiles:
  chrome-work:
    browser: chrome
    profile_id: Profile 1
    name: Work
    email: work@company.com
  firefox-personal:
    browser: firefox
    profile_id: default
    name: Personal

urls:
  - match: "*.company.com"
    profile: chrome-work
  - match: "*.github.com"
    profile: chrome-work
  - match: "facebook.com"
    profile: firefox-personal
```

### Pattern Syntax

URL patterns use fnmatch glob syntax:

| Pattern | Matches |
|---------|---------|
| `*.example.com` | `foo.example.com`, `bar.example.com` |
| `example.com` | Only `example.com` exactly |
| `*google*` | Any domain containing "google" |
| `????.com` | Four-letter .com domains |

## Troubleshooting

### Debug Mode

Enable debug logging to see detailed information:

```bash
choosr --debug https://example.com
# or
CHOOSR_DEBUG=1 choosr https://example.com
```

### Profile Not Found

If a profile is missing, rescan browsers:

```bash
choosr --rescan-browsers
```

### Browser Won't Launch

1. Check debug output for error messages
2. Verify the browser is installed: `which google-chrome` or `which firefox`
3. Check profile exists in browser's profile manager

### GUI Doesn't Appear

1. Ensure Qt/PySide6 is installed: `uv sync`
2. Check for errors: `choosr --debug https://example.com`
3. Verify display: `echo $DISPLAY`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CHOOSR_DEBUG` | Set to `1` to enable debug logging |
| `CHOOSR_TIMEOUT` | GUI timeout in milliseconds (default: 300000 = 5 min) |

## Uninstallation

```bash
./uninstall.sh
```

Note: Configuration file `~/.choosr.yaml` is preserved. Delete manually if desired.
```

**Step 2: Commit**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add README.md && git commit -m "docs: add comprehensive documentation"
```

---

## Task 16: Run Full Test Suite and Fix Any Issues

**Files:**
- All modified files

**Step 1: Run full test suite**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run pytest -v`

**Step 2: Run ruff checks**

Run: `cd /home/andy/choosr/.worktrees/quality-overhaul && uv run ruff check . && uv run ruff format --check .`

**Step 3: Fix any issues found**

Address any test failures or linting issues.

**Step 4: Final commit if needed**

```bash
cd /home/andy/choosr/.worktrees/quality-overhaul && git add -A && git commit -m "fix: address test and lint issues"
```

---

## Summary

This plan implements:

1. **Logging system** - `logging_config.py` with debug mode via `--debug` flag or `CHOOSR_DEBUG` env var
2. **Platform abstraction** - `platform_support.py` with Linux implementation and stubs for Windows/macOS
3. **Browser integration** - Chrome and Firefox use platform abstraction
4. **Error handling** - `launch()` returns bool, logs errors, shows GUI dialogs
5. **Cache logging** - Debug logging for cache hits/misses, warnings for write failures
6. **GUI improvements** - Error dialog function, QEventLoop with timeout
7. **Config validation** - Validates profiles and glob patterns on load
8. **CLI improvements** - `--debug` flag
9. **Documentation** - Comprehensive README with config format, troubleshooting, environment variables
10. **Qt tests** - Basic tests for error dialog and theme detection

Total: 16 tasks with TDD approach (test first, then implement, then commit).
