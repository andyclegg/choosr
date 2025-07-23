#!/usr/bin/env python3
import argparse
import fnmatch
import logging
import os
import sys

import tldextract
import yaml

from browser import browser_registry, Profile
from chrome import ChromeBrowser
from firefox import FirefoxBrowser
from qt_interface import show_qt_profile_selector

logging.basicConfig(level=logging.INFO, filename='log.txt')

def initialize_browsers():
    """Initialize and register all available browsers."""
    # Register Chrome browser
    chrome = ChromeBrowser()
    browser_registry.register(chrome)
    
    # Register Firefox browser
    firefox = FirefoxBrowser()
    browser_registry.register(firefox)
    
    available_browsers = browser_registry.get_available_browsers()
    logging.info("Registered browsers: %s", [b.display_name for b in available_browsers])

def launch_browser(profile_name, url=None):
    """Launch browser with the specified profile and optional URL."""
    # Find the profile in the browser registry
    for browser in browser_registry.get_available_browsers():
        profile = browser.get_profile_by_name(profile_name)
        if profile:
            logging.info("Launching %s with profile: %s", browser.display_name, profile_name)
            browser.launch(profile, url)
            return
    
    # Fallback: try to find any profile with matching name across all browsers
    all_profiles = browser_registry.get_all_profiles()
    for profile in all_profiles:
        if profile.name == profile_name:
            browser = browser_registry.get_browser(profile.browser)
            if browser:
                logging.info("Launching %s with profile: %s", browser.display_name, profile_name)
                browser.launch(profile, url)
                return
    
    logging.error("Profile not found: %s", profile_name)
    # Fallback to default Chrome profile
    chrome = browser_registry.get_browser('chrome')
    if chrome:
        default_profiles = chrome.discover_profiles()
        if default_profiles:
            logging.info("Falling back to default Chrome profile")
            chrome.launch(default_profiles[0], url)

def load_config():
    """Load choosr configuration from YAML file."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    
    if not os.path.exists(config_path):
        logging.warning("Config file not found at %s", config_path)
        return {'browser_profiles': {}, 'urls': []}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config or {'browser_profiles': {}, 'urls': []}
    except (yaml.YAMLError, OSError) as e:
        logging.error("Error reading config file: %s", e)
        return {'browser_profiles': {}, 'urls': []}


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
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        logging.info("Saved URL match: %s -> %s", domain, profile_name)
    except OSError as e:
        logging.error("Error saving config file: %s", e)


def show_profile_selector(url, domain, profiles):
    """Show GUI dialog to select a profile for the URL."""
    return show_qt_profile_selector(url, domain, profiles)


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
        print(f"Config file already exists at {config_path}")
        return
    
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
            'metadata': profile.metadata
        }
    
    try:
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
            
        logging.info("Created config file at %s with %d total profiles", config_path, len(all_profiles))
    except OSError as e:
        print(f"Error creating config file: {e}")
        logging.error("Error creating config file: %s", e)


def handle_url(url):
    """Handle URL opening with profile selection."""
    config = load_config()
    
    parsed = tldextract.extract(url)
    domain = parsed.registered_domain
    logging.info("url=%s => parsed=%s => domain=%s", url, parsed, domain)

    # Find matching profile from config
    selected_profile_name = None
    selected_profile_dir = "Default"
    
    for url_config in config.get('urls', []):
        match_pattern = url_config.get('match', '')
        profile_name = url_config.get('profile', '')
        
        if fnmatch.fnmatch(domain, match_pattern):
            selected_profile_name = profile_name
            logging.info("%s matched %s -> %s", url, match_pattern, profile_name)
            break
    
    # If no match found, show GUI selector
    if not selected_profile_name:
        browser_profiles = config.get('browser_profiles', {})
        if browser_profiles:
            logging.info("No match found for %s, showing profile selector", domain)
            selection_result = show_profile_selector(url, domain, browser_profiles)
            
            if selection_result:
                selected_profile_name, domain_pattern, save_choice = selection_result
                
                # Only save to config if user chose "Remember choice and launch"
                if save_choice:
                    save_url_match(domain_pattern, selected_profile_name)
                    logging.info("User selected profile: %s for pattern: %s (saved to config)", selected_profile_name, domain_pattern)
                else:
                    logging.info("User selected profile: %s for pattern: %s (not saved)", selected_profile_name, domain_pattern)
            else:
                logging.info("User cancelled profile selection")
                return
        else:
            logging.warning("No profiles configured")
    
    # Launch browser with selected profile
    if selected_profile_name:
        launch_browser(selected_profile_name, url=url)
    else:
        logging.info("No profile selected, launching with default")
        # Fallback to first available profile
        all_profiles = get_all_browser_profiles()
        if all_profiles:
            default_profile = all_profiles[0]
            logging.info("Using fallback profile: %s", default_profile.name)
            launch_browser(default_profile.name, url=url)
        else:
            logging.error("No browser profiles available")


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
