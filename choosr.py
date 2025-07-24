#!/usr/bin/env python3
import argparse
import fnmatch
import os
import sys

import tldextract
import yaml

from browser import browser_registry, Profile
from chrome import ChromeBrowser
from firefox import FirefoxBrowser
from qt_interface import show_qt_profile_selector

def initialize_browsers():
    """Initialize and register all available browsers."""
    # Register Chrome browser
    chrome = ChromeBrowser()
    browser_registry.register(chrome)
    
    # Register Firefox browser
    firefox = FirefoxBrowser()
    browser_registry.register(firefox)
    
    available_browsers = browser_registry.get_available_browsers()

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
    chrome = browser_registry.get_browser('chrome')
    if chrome:
        default_profiles = chrome.discover_profiles()
        if default_profiles:
            chrome.launch(default_profiles[0], url)

def load_config():
    """Load choosr configuration from YAML file."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    
    if not os.path.exists(config_path):
        return {'browser_profiles': {}, 'urls': []}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config or {'browser_profiles': {}, 'urls': []}
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file {config_path}")
        print(f"YAML parsing error: {e}")
        print("Please check the file syntax and fix any formatting issues.")
        print("You can regenerate the config file with: choosr init")
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
    new_match = {
        'match': domain,
        'profile': profile_name
    }
    
    config.setdefault('urls', []).append(new_match)
    
    @_handle_yaml_write_error(config_path, "configuration")
    def write_config():
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    write_config()




def get_all_browser_profiles():
    """Get all profiles from all available browsers."""
    profiles = []
    for browser in browser_registry.get_available_browsers():
        browser_profiles = browser.get_all_profiles()
        profiles.extend(browser_profiles)
    return profiles


def init_config():
    """Initialize choosr config file if it doesn't exist."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    
    if os.path.exists(config_path):
        # Try to load existing config to check if it's valid
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"Config file already exists at {config_path}")
            return
        except yaml.YAMLError:
            print(f"Existing config file at {config_path} contains invalid YAML.")
            response = input("Do you want to overwrite it? (y/N): ").strip().lower()
            if not response.startswith('y'):
                print("Config file initialization cancelled.")
                return
            print("Overwriting corrupted config file...")
    
    # Get all profiles from all available browsers
    all_profiles = get_all_browser_profiles()
    
    # Create config structure with profile names as keys
    config = {
        'browser_profiles': {},
        'urls': []
    }
    
    # Add each profile with name as key
    for profile in all_profiles:
        config['browser_profiles'][profile.name] = {
            'browser': profile.browser,
            'profile_id': profile.id,
            'is_private': profile.is_private,
        }
    
    @_handle_yaml_write_error(config_path, "configuration")
    def write_config():
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"Created config file at {config_path}")
        
        # Count profiles by browser
        browser_counts = {}
        for profile in all_profiles:
            browser_counts[profile.browser] = browser_counts.get(profile.browser, 0) + 1
        
        for browser_name, count in browser_counts.items():
            browser = browser_registry.get_browser(browser_name)
            browser_display = browser.display_name if browser else browser_name
            print(f"Found {count} {browser_display} profiles")
    
    write_config()


def handle_url(url):
    """Handle URL opening with profile selection."""
    config = load_config()
    
    parsed = tldextract.extract(url)
    domain = parsed.registered_domain

    # Find matching profile from config
    selected_profile_name = None
    selected_profile_dir = "Default"
    
    for url_config in config.get('urls', []):
        match_pattern = url_config.get('match', '')
        profile_name = url_config.get('profile', '')
        
        if fnmatch.fnmatch(domain, match_pattern):
            selected_profile_name = profile_name
            break
    
    # If no match found, show GUI selector
    if not selected_profile_name:
        browser_profiles = config.get('browser_profiles', {})
        if browser_profiles:
            selection_result = show_qt_profile_selector(url, domain, browser_profiles)
            
            if selection_result:
                selected_profile_name, domain_pattern, save_choice = selection_result
                
                # Only save to config if user chose "Remember choice and launch"
                if save_choice:
                    save_url_match(domain_pattern, selected_profile_name)
            else:
                return
    
    # Launch browser with selected profile
    if selected_profile_name:
        launch_browser(selected_profile_name, url=url)
    else:
        # Fallback to first available profile
        all_profiles = get_all_browser_profiles()
        if all_profiles:
            default_profile = all_profiles[0]
            launch_browser(default_profile.name, url=url)


def main():
    """Main entry point for choosr application."""
    # Initialize browser registry
    initialize_browsers()
    
    parser = argparse.ArgumentParser(description="Browser profile chooser")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init subcommand
    subparsers.add_parser("init", help="Initialize choosr config file")
    url_parser = subparsers.add_parser("url", help="Launch a URL")
    
    # URL argument for url subcommand
    url_parser.add_argument("url", help="URL to open")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_config()
    elif args.command == "url":
        handle_url(args.url)
    else:
        # No command provided - show help
        parser.print_help()

if __name__ == "__main__":
    main()
