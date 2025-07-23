#!/usr/bin/env python3
import argparse
import fnmatch
import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import tldextract
import yaml

from browser import browser_registry, Profile
from chrome import ChromeBrowser

logging.basicConfig(level=logging.INFO, filename='log.txt')

def initialize_browsers():
    """Initialize and register all available browsers."""
    # Register Chrome browser
    chrome = ChromeBrowser()
    browser_registry.register(chrome)
    logging.info("Registered browsers: %s", [b.display_name for b in browser_registry.get_available_browsers()])

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
    if not profiles:
        messagebox.showerror("Error", "No profiles available")
        return None
    
    result = {'selected_profile': None, 'domain_pattern': None, 'save_choice': False, 'cancelled': False}
    
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
    
    def on_remember_and_launch():
        selection = profile_var.get()
        domain_pattern = domain_var.get().strip()
        if selection and domain_pattern:
            result['selected_profile'] = selection
            result['domain_pattern'] = domain_pattern
            result['save_choice'] = True
        root.quit()
    
    def on_launch_only():
        selection = profile_var.get()
        domain_pattern = domain_var.get().strip()
        if selection and domain_pattern:
            result['selected_profile'] = selection
            result['domain_pattern'] = domain_pattern
            result['save_choice'] = False
        root.quit()
    
    def on_exit():
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
    # Sort profiles with private mode profiles always last
    profile_names = list(profiles.keys())
    regular_profiles = []
    private_profiles = []
    
    # Load browser profiles to check which are private
    config = load_config()
    browser_profiles_config = config.get('browser_profiles', {})
    
    for name in profile_names:
        profile_config = browser_profiles_config.get(name, {})
        if profile_config.get('is_private', False):
            private_profiles.append(name)
        else:
            regular_profiles.append(name)
    
    regular_profiles.sort()
    private_profiles.sort()
    sorted_profiles = regular_profiles + private_profiles
    
    for profile_name in sorted_profiles:
        # Use different styling for private mode profiles
        profile_config = browser_profiles_config.get(profile_name, {})
        is_private = profile_config.get('is_private', False)
        browser_type = profile_config.get('browser', 'unknown')
        
        # Get browser display name
        browser = browser_registry.get_browser(browser_type)
        browser_display = browser.display_name if browser else browser_type.title()
        
        # Format profile text with browser type
        profile_text = f"{profile_name} [{browser_display}]"
        
        if is_private:
            # Create a frame to hold both radio button and colored text
            incognito_frame = ttk.Frame(profile_container)
            incognito_frame.pack(anchor="w", pady=2, fill="x")
            
            radio_button = ttk.Radiobutton(
                incognito_frame,
                text="",  # Empty text, we'll add colored label separately
                variable=profile_var,
                value=profile_name,
                padding="5"
            )
            radio_button.pack(side="left")
            
            # Add red colored label next to the radio button
            incognito_label = tk.Label(
                incognito_frame,
                text=profile_text,
                foreground="red",
                font=('Arial', 9)
            )
            # Try to match the background color of the parent
            try:
                parent_bg = incognito_frame.cget("background")
                incognito_label.configure(background=parent_bg)
            except tk.TclError:
                # If we can't get the background, use default
                pass
            incognito_label.pack(side="left", padx=(2, 0))
            
            # Make clicking the label also select the radio button
            def select_private(event=None, name=profile_name):
                profile_var.set(name)
            incognito_label.bind("<Button-1>", select_private)
        else:
            radio_button = ttk.Radiobutton(
                profile_container,
                text=profile_text,
                variable=profile_var,
                value=profile_name,
                padding="5"
            )
            radio_button.pack(anchor="w", pady=2)
    
    # Buttons
    button_frame = ttk.Frame(root, padding="10")
    button_frame.pack(fill="x", side="bottom")
    
    # Create three buttons with appropriate spacing
    ttk.Button(button_frame, text="Exit", command=on_exit).pack(side="right", padx=(5, 0))
    ttk.Button(button_frame, text="Launch", command=on_launch_only).pack(side="right", padx=(5, 0))
    ttk.Button(button_frame, text="Remember choice and launch", command=on_remember_and_launch).pack(side="right", padx=(5, 0))
    
    # Set first profile as default (first in sorted order, not incognito)
    if sorted_profiles:
        profile_var.set(sorted_profiles[0])
    
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
    
    return result['selected_profile'], result['domain_pattern'], result['save_choice']


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
