#!/usr/bin/env python3
import argparse
import fnmatch
import logging
import os
import subprocess
import sys

import tldextract

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


def init_config():
    """Initialize choosr config file if it doesn't exist."""
    config_path = os.path.expanduser("~/.choosr.yaml")
    
    if os.path.exists(config_path):
        print(f"Config file already exists at {config_path}")
        return
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("")  # Create empty file
        print(f"Created config file at {config_path}")
        logging.info("Created config file at %s", config_path)
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
