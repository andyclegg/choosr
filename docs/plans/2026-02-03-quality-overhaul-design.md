# Choosr Quality Overhaul Design

## Overview

Address critical gaps identified in codebase assessment:
- Add logging system
- Abstract platform-specific code for future cross-platform support
- Fix error handling (subprocess failures, GUI errors)
- Add GUI timeout
- Add Qt/QML tests
- Add configuration validation
- Improve documentation

## 1. Logging System

**New module:** `logging_config.py`

- Use Python's built-in `logging` module
- Default level: `WARNING`
- Enable debug via: `--debug` flag or `CHOOSR_DEBUG=1` environment variable
- Output: `stderr`
- Format: `[choosr] LEVEL: message`

**Logging points:**
- Profile discovery (debug)
- Cache hits/misses (debug)
- URL matching (debug)
- Browser launch (info)
- Errors (error)

## 2. Platform Abstraction

**New module:** `platform_support.py`

Abstract base class `PlatformSupport` with methods:
- `get_chrome_executable() -> str | None`
- `get_chrome_config_dir() -> Path | None`
- `get_firefox_executable() -> str | None`
- `get_firefox_config_dir() -> Path | None`
- `get_cache_dir() -> Path`

Implementations:
- `LinuxPlatform` - full implementation (current hard-coded paths)
- `WindowsPlatform` - stub raising `NotImplementedError`
- `MacOSPlatform` - stub raising `NotImplementedError`

Factory function `get_platform()` returns appropriate implementation based on `sys.platform`.

## 3. Error Handling & Reporting

### Subprocess launch verification

Change `launch_url()` to return `bool` indicating success:
```python
def launch_url(self, profile: Profile, url: str, private: bool = False) -> bool:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Browser launch failed: %s", result.stderr)
        return False
    return True
```

### GUI error dialogs

New function in `qt_interface.py`:
```python
def show_error_dialog(title: str, message: str) -> None:
    from PySide6.QtWidgets import QMessageBox, QApplication
    app = QApplication.instance() or QApplication([])
    QMessageBox.critical(None, title, message)
```

### Usage

In `choosr.py`, check launch result and show dialog on failure.

Cache write failures: log warning only (non-critical).

## 4. GUI Timeout & Event Loop

Replace busy-wait with `QEventLoop`:

```python
self._event_loop = QEventLoop()
timeout_ms = 300000  # 5 minutes
QTimer.singleShot(timeout_ms, self._on_timeout)
self._event_loop.exec()
```

Callbacks (`_on_selection`, `_on_cancel`, `_on_timeout`) call `self._event_loop.quit()`.

## 5. Qt/QML Testing

**New file:** `tests/test_qt_interface.py`

Test classes:
- `TestThemeDetection` - light/dark detection logic
- `TestProfileSelectorController` - selection callback, cancel callback, timeout
- `TestErrorDialog` - error dialog shows without crash

**Not testing:**
- QML visual rendering
- QML animations
- Keyboard navigation in QML

## 6. Configuration Validation

New function `validate_config(config, available_profiles) -> list[str]`:

Validates:
- Structure: `profiles` must be a dict
- Profile references: warn if profile not found
- Domain patterns: warn if malformed glob
- (Duplicate patterns: warn if same pattern appears twice)

Warnings logged at `WARNING` level. App continues with valid portions.

Helper: `_is_valid_glob_pattern(pattern)` uses `fnmatch.translate()` to validate.

## 7. Documentation

Update `README.md` with:

### Config file format
- YAML structure explanation
- Profile naming (must match discovered profiles)

### Pattern syntax
- fnmatch glob syntax (`*`, `?`, `[abc]`)
- Examples

### Troubleshooting
- Debug mode (`--debug` or `CHOOSR_DEBUG=1`)
- Profile not found (`--rescan-browsers`)
- Browser won't launch (check debug output)

## Implementation Order

1. `logging_config.py` - foundation for all other changes
2. `platform_support.py` - abstraction layer
3. Update `chrome.py` and `firefox.py` to use platform abstraction
4. Update `browser.py` cache to use platform abstraction
5. Error handling in `chrome.py` and `firefox.py` (launch_url returns bool)
6. Error handling in `qt_interface.py` (timeout, error dialog)
7. Config validation in `choosr.py`
8. `tests/test_qt_interface.py`
9. Documentation updates

## Files Changed

- **New:** `logging_config.py`, `platform_support.py`, `tests/test_qt_interface.py`
- **Modified:** `browser.py`, `chrome.py`, `firefox.py`, `qt_interface.py`, `choosr.py`, `README.md`
