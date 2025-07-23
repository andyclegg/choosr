#!/usr/bin/env python3
import argparse
import fnmatch
import json
import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

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
    if not profiles:
        messagebox.showerror("Error", "No profiles available")
        return None
    
    result = {'selected_profile': None, 'domain_pattern': None, 'cancelled': False}
    
    def check_domain_match():
        """Check if the domain pattern matches the original URL and show warning."""
        pattern = domain_var.get().strip()
        if pattern and not fnmatch.fnmatch(domain, pattern):
            warning_label.config(text="⚠️ Pattern doesn't match the current URL", foreground="red")
        else:
            warning_label.config(text="", foreground="black")
    
    def on_domain_change(*args):
        """Called when domain entry is modified."""
        root.after_idle(check_domain_match)
    
    def on_select():
        selection = profile_var.get()
        domain_pattern = domain_var.get().strip()
        if selection and domain_pattern:
            result['selected_profile'] = selection
            result['domain_pattern'] = domain_pattern
        root.quit()
    
    def on_cancel():
        result['cancelled'] = True
        root.quit()
    
    def on_window_close():
        # Handle window close (X button)
        result['cancelled'] = True
        root.quit()
    
    root = tk.Tk()
    root.title("Choose Profile")
    
    # Calculate window height based on number of profiles
    # Account for: URL section (~80px) + domain edit (~70px) + profile label (~30px) + buttons (~60px) + padding (~40px)
    base_height = 280  # Fixed UI elements (reduced after removing domain display)
    profile_height = 35  # Height per profile option (including padding)
    num_profiles = len(profiles)
    calculated_height = base_height + (num_profiles * profile_height)
    
    # Set reasonable limits
    window_height = max(400, min(calculated_height, 700))  # Min 400px, max 700px
    window_width = 500  # Width for domain editing
    
    root.geometry(f"{window_width}x{window_height}")
    root.resizable(False, False)
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # Center the window
    try:
        root.eval('tk::PlaceWindow . center')
    except tk.TclError:
        # Fallback if PlaceWindow is not available
        pass
    
    # URL display
    url_frame = ttk.Frame(root, padding="10")
    url_frame.pack(fill="x")
    
    ttk.Label(url_frame, text="Choose a profile for:", font=('Arial', 10, 'bold')).pack()
    ttk.Label(url_frame, text=url, font=('Arial', 9), foreground="blue").pack(pady=(5, 0))
    
    # Domain editing section
    domain_edit_frame = ttk.Frame(url_frame)
    domain_edit_frame.pack(fill="x", pady=(10, 0))
    
    ttk.Label(domain_edit_frame, text="Pattern to save:", font=('Arial', 9, 'bold')).pack(anchor="w")
    
    domain_var = tk.StringVar(value=domain)
    domain_var.trace_add('write', on_domain_change)
    
    domain_entry = ttk.Entry(domain_edit_frame, textvariable=domain_var, font=('Arial', 9))
    domain_entry.pack(fill="x", pady=(2, 0))
    
    # Warning label
    warning_label = ttk.Label(domain_edit_frame, text="", font=('Arial', 8))
    warning_label.pack(anchor="w", pady=(2, 5))
    
    # Profile selection with scrollable frame
    profile_outer_frame = ttk.Frame(root, padding="10")
    profile_outer_frame.pack(fill="both", expand=True)
    
    ttk.Label(profile_outer_frame, text="Select Profile:", font=('Arial', 10, 'bold')).pack(anchor="w")
    
    # Create scrollable frame if there are many profiles
    if num_profiles > 14:  # Use scrollbar if more than 14 profiles
        # Create canvas and scrollbar
        canvas = tk.Canvas(profile_outer_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(profile_outer_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, pady=(5, 0))
        scrollbar.pack(side="right", fill="y", pady=(5, 0))
        
        profile_container = scrollable_frame
    else:
        # Use regular frame for fewer profiles
        profile_container = ttk.Frame(profile_outer_frame)
        profile_container.pack(fill="both", expand=True, pady=(5, 0))
    
    profile_var = tk.StringVar()
    
    # Create radio buttons for each profile
    for profile_name in sorted(profiles.keys()):
        ttk.Radiobutton(
            profile_container,
            text=profile_name,
            variable=profile_var,
            value=profile_name,
            padding="5"
        ).pack(anchor="w", pady=2)
    
    # Buttons
    button_frame = ttk.Frame(root, padding="10")
    button_frame.pack(fill="x", side="bottom")
    
    ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=(5, 0))
    ttk.Button(button_frame, text="OK", command=on_select).pack(side="right")
    
    # Set first profile as default
    if profiles:
        profile_var.set(list(sorted(profiles.keys()))[0])
    
    try:
        root.mainloop()
    except tk.TclError:
        # Handle any Tkinter errors gracefully
        result['cancelled'] = True
    finally:
        try:
            root.destroy()
        except tk.TclError:
            # Window may already be destroyed
            pass
    
    # Return None if cancelled or closed
    if result['cancelled']:
        return None
    
    return result['selected_profile'], result['domain_pattern']


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
    
    # If no match found, show GUI selector
    if not selected_profile_name:
        browser_profiles = config.get('browser_profiles', {})
        if browser_profiles:
            logging.info("No match found for %s, showing profile selector", domain)
            selection_result = show_profile_selector(url, domain, browser_profiles)
            
            if selection_result:
                selected_profile_name, domain_pattern = selection_result
                # Save the selection to config with the edited domain pattern
                save_url_match(domain_pattern, selected_profile_name)
                logging.info("User selected profile: %s for pattern: %s", selected_profile_name, domain_pattern)
            else:
                logging.info("User cancelled profile selection")
                return
        else:
            logging.warning("No profiles configured")
    
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
