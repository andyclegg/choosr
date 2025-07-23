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


def get_chrome_profiles():
    """Query Chrome profiles from the filesystem."""
    chrome_config_dir = os.path.expanduser("~/.config/google-chrome")
    profiles = []
    
    if not os.path.exists(chrome_config_dir):
        logging.warning("Chrome config directory not found at %s", chrome_config_dir)
        return profiles
    
    # Read profile information from Local State file
    local_state_file = os.path.join(chrome_config_dir, "Local State")
    if not os.path.exists(local_state_file):
        logging.warning("Chrome Local State file not found at %s", local_state_file)
        return profiles
    
    try:
        with open(local_state_file, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
            
        # Get profile info from Local State
        profile_info_cache = local_state.get('profile', {}).get('info_cache', {})
        
        for profile_dir, profile_info in profile_info_cache.items():
            # Verify the profile directory actually exists
            profile_path = os.path.join(chrome_config_dir, profile_dir)
            if os.path.isdir(profile_path):
                display_name = profile_info.get('name', profile_dir)
                profiles.append({
                    'directory': profile_dir,
                    'name': display_name
                })
                
    except (json.JSONDecodeError, OSError) as e:
        logging.error("Error reading Chrome Local State: %s", e)
    
    return profiles


def init_config():
    """Initialize choosr config file if it doesn't exist."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    
    if os.path.exists(config_path):
        print(f"Config file already exists at {config_path}")
        return
    
    # Get Chrome profiles
    chrome_profiles = get_chrome_profiles()
    
    # Create config structure with profile names as keys
    config = {
        'browser_profiles': {},
        'urls': []
    }
    
    # Add each Chrome profile with name as key
    for profile in chrome_profiles:
        config['browser_profiles'][profile['name']] = {
            'directory': profile['directory'],
            'browser': 'chrome'
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
    
    # Get profile directory from browser_profiles config
    if selected_profile_name and selected_profile_name in config.get('browser_profiles', {}):
        profile_info = config['browser_profiles'][selected_profile_name]
        selected_profile_dir = profile_info.get('directory', 'Default')
        logging.info("Using profile directory: %s", selected_profile_dir)
    else:
        logging.info("No matching profile found, using Default")

    launch_chrome(selected_profile_dir, url=url)


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
