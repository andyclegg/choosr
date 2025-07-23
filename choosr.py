#!/usr/bin/env python3
import argparse
import fnmatch
import json
import logging
import os
import subprocess
import sys

import tldextract
import yaml

logging.basicConfig(level=logging.INFO, filename='log.txt')

def launch_chrome(profile_dir, url=None):
    """Launch Chrome with the specified profile directory and optional URL."""
    # Profile dirs are in ~/.var/app/com.google.Chrome/config/google-chrome/
    command = [
        "/usr/bin/flatpak",
        "run",
        "--branch=stable",
        "--arch=x86_64",
        "--command=/app/bin/chrome",
        "--file-forwarding",
        "com.google.Chrome",
        f"--profile-directory={profile_dir}"
    ]
    if url is not None:
        command.append(url)
    logging.info("%s", str(command))
    subprocess.run(command, check=False)

def get_matchers(filename):
    """Read URL matchers from file."""
    try:
        with open(filename, 'rt', encoding='utf-8') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        logging.warning("Matcher file %s not found", filename)
        return []


def get_chrome_profiles():
    """Query Chrome profiles from the filesystem."""
    chrome_config_dir = os.path.expanduser("~/.config/google-chrome")
    profiles = []
    
    if not os.path.exists(chrome_config_dir):
        logging.warning("Chrome config directory not found at %s", chrome_config_dir)
        return profiles
    
    try:
        # Look for profile directories
        for item in os.listdir(chrome_config_dir):
            profile_path = os.path.join(chrome_config_dir, item)
            if os.path.isdir(profile_path):
                # Check if it's a profile directory (has Preferences file)
                prefs_file = os.path.join(profile_path, "Preferences")
                if os.path.exists(prefs_file):
                    profile_name = item
                    display_name = item
                    
                    # Try to get the display name from Preferences
                    try:
                        with open(prefs_file, 'r', encoding='utf-8') as f:
                            prefs = json.load(f)
                            profile_info = prefs.get('profile', {})
                            if 'name' in profile_info:
                                display_name = profile_info['name']
                    except (json.JSONDecodeError, OSError):
                        # Fall back to directory name if we can't read preferences
                        pass
                    
                    profiles.append({
                        'directory': profile_name,
                        'name': display_name
                    })
    except OSError as e:
        logging.error("Error reading Chrome profiles: %s", e)
    
    return profiles


def init_config():
    """Initialize choosr config file if it doesn't exist."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    
    if os.path.exists(config_path):
        print(f"Config file already exists at {config_path}")
        return
    
    # Get Chrome profiles
    chrome_profiles = get_chrome_profiles()
    
    # Create config structure
    config = {
        'browser_profiles': {
            'chrome': chrome_profiles
        }
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"Created config file at {config_path}")
        if chrome_profiles:
            print(f"Found {len(chrome_profiles)} Chrome profiles")
        else:
            print("No Chrome profiles found")
        logging.info("Created config file at %s with %d Chrome profiles", config_path, len(chrome_profiles))
    except OSError as e:
        print(f"Error creating config file: {e}")
        logging.error("Error creating config file: %s", e)


def handle_url(url):
    """Handle URL opening with profile selection."""
    profile = "Default"
    
    parsed = tldextract.extract(url)
    domain = parsed.registered_domain
    logging.info("url=%s => parsed=%s => domain=%s", url, parsed, domain)

    for match_glob in get_matchers("work.txt"):
        if fnmatch.fnmatch(domain, match_glob):
            profile = "Profile 5"
            logging.info("%s matched %s -> %s", url, match_glob, profile)
            break

    launch_chrome(profile, url=url)


def main():
    """Main entry point for choosr application."""
    parser = argparse.ArgumentParser(description="Browser profile chooser")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init subcommand
    subparsers.add_parser("init", help="Initialize choosr config file")
    
    # URL argument for default behavior
    parser.add_argument("url", nargs="?", help="URL to open")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_config()
    elif args.url:
        handle_url(args.url)
    else:
        # No URL provided - launch Chrome with default profile
        logging.info("No URL provided - launching Chrome")
        launch_chrome("Default")

if __name__ == "__main__":
    main()
