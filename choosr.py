#!/usr/bin/env python3
import fnmatch
import logging
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


def main():
    """Main entry point for choosr application."""
    profile = "Default"

    if len(sys.argv) == 1:
        logging.info("No URL provided - launching Chrome")
        launch_chrome(profile)
        return

    url = sys.argv[1]
    parsed = tldextract.extract(url)
    domain = parsed.registered_domain
    logging.info("url=%s => parsed=%s => domain=%s", url, parsed, domain)

    for match_glob in get_matchers("work.txt"):
        if fnmatch.fnmatch(domain, match_glob):
            profile = "Profile 5"
            logging.info("%s matched %s -> %s", url, match_glob, profile)
            break

    launch_chrome(profile, url=url)

if __name__ == "__main__":
    main()
