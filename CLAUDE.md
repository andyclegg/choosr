# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Choosr is a browser profile selector application that allows users to choose which browser profile to use when opening URLs. It acts as a default browser handler that presents a GUI for selecting between different browser profiles from Chrome and Firefox.

## Development Commands

**Install dependencies:**
```bash
poetry install
```

**Install as system application:**
```bash
./install.sh          # Install choosr system-wide
./uninstall.sh        # Remove installation
```

**Run during development:**
```bash
poetry run choosr init      # Initialize config file
poetry run choosr url <URL> # Launch URL with profile selector
```

**Test the application:**
```bash
poetry run choosr --help    # Show help
~/.local/share/choosr/choosr-launcher url <URL>  # Test installed version
```

## Architecture

### Core Components

**Main Entry Point (`choosr.py`):**
- Application entry point with command-line argument parsing
- Handles URL routing and profile selection logic
- Manages YAML configuration file at `~/.choosr.yaml`
- Coordinates between browser implementations and Qt interface

**Browser Abstraction (`browser.py`):**
- Defines abstract `Browser` class and `Profile` dataclass
- Provides `BrowserRegistry` for managing multiple browser implementations
- Contains `ProfileIcon` class for profile theming information
- Global `browser_registry` instance used throughout the application

**Browser Implementations:**
- `chrome.py`: Chrome browser support, reads profile data from Chrome's `Local State` JSON file
- `firefox.py`: Firefox browser support, reads profile data from `profiles.ini` INI file

**Qt Interface (`qt_interface.py`):**
- Modern Qt/QML-based profile selector GUI
- `ProfileSelectorController` handles Qt application lifecycle
- System theme detection for light/dark mode support
- Exports `show_qt_profile_selector()` function used by main application

**QML UI (`ProfileSelector.qml`):**
- Modern, responsive profile selector interface
- Supports both light and dark themes
- Displays profiles grouped by browser with icons and colors
- Domain pattern editing with validation

### Key Design Patterns

**Plugin Architecture:** Browser implementations extend the abstract `Browser` class, making it easy to add support for new browsers.

**Configuration Management:** Uses YAML for user configuration stored at `~/.choosr.yaml` with automatic profile discovery and URL pattern matching.

**GUI Integration:** Qt/QML interface is cleanly separated from core logic and can be replaced with other UI frameworks.

## Installation & Configuration

**Installation files:**
- `install.sh`: Bash script that properly installs choosr system-wide
- `uninstall.sh`: Removes choosr installation
- Creates launcher script in `~/.local/share/choosr/choosr-launcher`
- Installs desktop file to `~/.local/share/applications/choosr.desktop`

**User config file location:** `~/.choosr.yaml`

The application auto-discovers browser profiles and creates the config file with `choosr init`.

**Setting as default browser:** After installation, use `xdg-settings set default-web-browser choosr.desktop`

## Browser Profile Discovery

**Chrome:** Reads `~/.config/google-chrome/Local State` JSON file for profile information including names, avatars, and theme colors.

**Firefox:** Reads `~/.mozilla/firefox/profiles.ini` INI file for profile names and directories.

Both browsers support private/incognito mode profiles that are handled specially.