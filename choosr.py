#!/usr/bin/env python3
import fnmatch
import tldextract
import urllib
import subprocess
import sys
import logging
logging.basicConfig(level=logging.INFO, filename='log.txt')

def launch_chrome(profile_dir, url=None):
    # Profile dirs are in ~/.var/app/com.google.Chrome/config/google-chrome/
    command = ["/usr/bin/flatpak","run","--branch=stable","--arch=x86_64","--command=/app/bin/chrome","--file-forwarding","com.google.Chrome",f"--profile-directory={profile_dir}"]
    if url is not None:
        command.append(url)
    logging.info("%s", str(command))
    subprocess.run(command)

def get_matchers(filename):
    return open(filename, 'rt').read().splitlines()


def main():
    profile = "Default"

    if len(sys.argv) == 1:
        logging.info("No URL provided - launching Chrome")
        launch_chrome(profile)

    url = sys.argv[1]
    parsed = tldextract.extract(url)
    domain = parsed.registered_domain
    logging.info(f"{url=} => {parsed=} => {domain=}")

    for match_glob in get_matchers("work.txt"):
        if fnmatch.fnmatch(domain, match_glob):
            profile = "Profile 2"
            logging.info(f"{url} matched {match_glob} -> {profile}")

    launch_chrome(profile, url=url)

if __name__ == "__main__":
    main()
