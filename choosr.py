#!/usr/bin/env python3
import argparse
import fnmatch
import os
import sys

import tldextract
import yaml

from browser import browser_registry
from chrome import ChromeBrowser
from firefox import FirefoxBrowser


def initialize_browsers():
    """Initialize and register all available browsers."""
    # Register Chrome browser
    chrome = ChromeBrowser()
    browser_registry.register(chrome)

    # Register Firefox browser
    firefox = FirefoxBrowser()
    browser_registry.register(firefox)


def _normalize_key(text):
    """Normalize text for use as a config key."""
    import re

    # Lowercase and replace non-alphanumeric with hyphens
    key = re.sub(r"[^a-z0-9]+", "-", text.lower())
    # Remove leading/trailing hyphens
    return key.strip("-")


def _generate_profile_key(profile):
    """Generate a unique config key for a profile based on browser/name/email."""
    parts = [profile.browser, profile.name]
    if profile.email:
        parts.append(profile.email)
    return _normalize_key("-".join(parts))


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
        # Check for unclosed brackets - fnmatch treats them as literals
        # but they likely indicate a user error
        bracket_depth = 0
        i = 0
        while i < len(pattern):
            char = pattern[i]
            if char == "[":
                # Check if it's an escaped bracket or start of character class
                bracket_depth += 1
            elif char == "]" and bracket_depth > 0:
                bracket_depth -= 1
            i += 1
        if bracket_depth != 0:
            return False
        return True
    except Exception:
        return False


def _find_profile_by_name(profile_name):
    """Find profile by name across all browsers."""
    # First try browser-specific lookup (more efficient)
    for browser in browser_registry.get_available_browsers():
        profile = browser.get_profile_by_name(profile_name)
        if profile:
            return profile, browser

    # Fallback: search all profiles
    all_profiles = browser_registry.get_all_profiles()
    for profile in all_profiles:
        if profile.name == profile_name:
            browser = browser_registry.get_browser(profile.browser)
            if browser:
                return profile, browser

    return None, None


def launch_browser(profile_name, url=None):
    """Launch browser with the specified profile and optional URL."""
    profile, browser = _find_profile_by_name(profile_name)

    if profile and browser:
        browser.launch(profile, url)
        return
    # Fallback to default Chrome profile
    chrome = browser_registry.get_browser("chrome")
    if chrome:
        default_profiles = chrome.discover_profiles()
        if default_profiles:
            chrome.launch(default_profiles[0], url)


def launch_browser_by_config_key(config_key, url=None):
    """Launch browser using a config key to look up profile settings."""
    from browser import Profile

    config = load_config()
    profile_config = config.get("browser_profiles", {}).get(config_key)

    if not profile_config:
        return

    browser_name = profile_config.get("browser")
    browser = browser_registry.get_browser(browser_name)

    if not browser:
        return

    profile = Profile(
        id=profile_config.get("profile_id", config_key),
        name=profile_config.get("name", config_key),
        browser=browser_name,
        is_private=profile_config.get("is_private", False),
        email=profile_config.get("email"),
    )

    browser.launch(profile, url)


def load_config():
    """Load choosr configuration from YAML file, creating it if it doesn't exist."""
    config_path = os.path.expanduser("~/.choosr.yaml")

    if not os.path.exists(config_path):
        # Auto-create config file if it doesn't exist
        _create_initial_config(config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config or {"browser_profiles": {}, "urls": []}
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file {config_path}")
        print(f"YAML parsing error: {e}")
        print("Please check the file syntax and fix any formatting issues.")
        sys.exit(1)
    except OSError as e:
        print(f"Error: Cannot read config file {config_path}")
        print(f"File system error: {e}")
        sys.exit(1)


def _handle_yaml_write_error(config_path, operation_description):
    """Common error handling for YAML write operations."""

    def error_handler(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except yaml.YAMLError as e:
                print(f"Error: Cannot write YAML to config file {config_path}")
                print(f"YAML serialization error: {e}")
                print(f"The {operation_description} could not be saved.")
            except OSError as e:
                print(f"Error: Cannot write to config file {config_path}")
                print(f"File system error: {e}")
                print("Please check file permissions and disk space.")

        return wrapper

    return error_handler


def save_url_match(domain, profile_name):
    """Save a new URL match to the config file."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    config = load_config()

    # Add new URL match
    new_match = {"match": domain, "profile": profile_name}

    config.setdefault("urls", []).append(new_match)

    @_handle_yaml_write_error(config_path, "configuration")
    def write_config():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    write_config()


def get_all_browser_profiles():
    """Get all profiles from all available browsers."""
    profiles = []
    for browser in browser_registry.get_available_browsers():
        browser_profiles = browser.get_all_profiles()
        profiles.extend(browser_profiles)
    return profiles


def _create_initial_config(config_path):
    """Create initial config file with discovered browser profiles."""
    # Get all profiles from all available browsers
    all_profiles = get_all_browser_profiles()

    # Create config structure with unique keys for each profile
    config = {"browser_profiles": {}, "urls": []}

    for profile in all_profiles:
        key = _generate_profile_key(profile)
        entry = {
            "browser": profile.browser,
            "profile_id": profile.id,
            "name": profile.name,
            "is_private": profile.is_private,
        }
        if profile.email:
            entry["email"] = profile.email
        config["browser_profiles"][key] = entry

    @_handle_yaml_write_error(config_path, "configuration")
    def write_config():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    write_config()


def handle_url(url):
    """Handle URL opening with profile selection."""
    config = load_config()

    parsed = tldextract.extract(url)
    domain = parsed.top_domain_under_public_suffix

    # Find matching profile from config
    selected_profile_key = None

    for url_config in config.get("urls", []):
        match_pattern = url_config.get("match", "")
        profile_key = url_config.get("profile", "")

        if fnmatch.fnmatch(domain, match_pattern):
            selected_profile_key = profile_key
            break

    # If no match found, show GUI selector
    if not selected_profile_key:
        browser_profiles = config.get("browser_profiles", {})
        if browser_profiles:
            # Lazy import this, only when needed
            from qt_interface import show_qt_profile_selector

            selection_result = show_qt_profile_selector(url, domain, browser_profiles)

            if selection_result:
                selected_profile_key, domain_pattern, save_choice = selection_result

                # Only save to config if user chose "Remember choice and launch"
                if save_choice:
                    save_url_match(domain_pattern, selected_profile_key)
            else:
                return

    # Launch browser with selected profile
    if selected_profile_key:
        launch_browser_by_config_key(selected_profile_key, url=url)
    else:
        # Fallback to first available profile
        all_profiles = get_all_browser_profiles()
        if all_profiles:
            default_profile = all_profiles[0]
            launch_browser(default_profile.name, url=url)


def rescan_browsers():
    """Rescan browsers, update profiles, and clean up invalid URL entries."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    config = load_config()

    # Clear profile caches to force fresh discovery
    browser_registry.clear_all_caches()

    # Get fresh profile data from all browsers
    all_profiles = get_all_browser_profiles()

    # Create new browser_profiles section
    new_browser_profiles = {}
    for profile in all_profiles:
        key = _generate_profile_key(profile)
        entry = {
            "browser": profile.browser,
            "profile_id": profile.id,
            "name": profile.name,
            "is_private": profile.is_private,
        }
        if profile.email:
            entry["email"] = profile.email
        new_browser_profiles[key] = entry

    # Replace the browser_profiles section
    config["browser_profiles"] = new_browser_profiles

    # Clean up invalid URL entries
    valid_profile_keys = set(new_browser_profiles.keys())
    original_url_count = len(config.get("urls", []))

    config["urls"] = [
        url_entry
        for url_entry in config.get("urls", [])
        if url_entry.get("profile") in valid_profile_keys
    ]

    cleaned_url_count = len(config["urls"])
    removed_urls = original_url_count - cleaned_url_count

    # Save updated config
    @_handle_yaml_write_error(config_path, "configuration")
    def write_config():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    write_config()

    # Report results
    browser_counts = {}
    for profile in all_profiles:
        browser_counts[profile.browser] = browser_counts.get(profile.browser, 0) + 1

    print(f"Updated browser profiles in {config_path}")
    for browser_name, count in browser_counts.items():
        browser = browser_registry.get_browser(browser_name)
        browser_display = browser.display_name if browser else browser_name
        print(f"Found {count} {browser_display} profiles")

    if removed_urls > 0:
        print(f"Removed {removed_urls} URL entries pointing to non-existent profiles")
    else:
        print("All URL entries are valid")


def main():
    """Main entry point for choosr application."""
    # Initialize browser registry
    initialize_browsers()

    parser = argparse.ArgumentParser(description="Browser profile chooser")

    # Add global options
    parser.add_argument(
        "--rescan-browsers",
        action="store_true",
        help="Rescan browsers and update profile configuration",
    )

    # URL as positional argument
    parser.add_argument("url", nargs="?", help="URL to open")

    args = parser.parse_args()

    if args.rescan_browsers:
        rescan_browsers()
    elif args.url:
        handle_url(args.url)
    else:
        # No URL provided - show help
        parser.print_help()


if __name__ == "__main__":
    main()
