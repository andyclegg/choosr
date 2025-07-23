"""
Firefox browser implementation for choosr.

This module provides a concrete implementation of the Browser interface
for Mozilla Firefox, handling profile discovery through profiles.ini
and launching with Firefox-specific command-line arguments.
"""

import configparser
import logging
import os
import subprocess
from typing import List, Optional

from browser import Browser, Profile, ProfileIcon


class FirefoxBrowser(Browser):
    """Mozilla Firefox browser implementation."""
    
    @property
    def name(self) -> str:
        """Return the browser name."""
        return "firefox"
    
    @property
    def display_name(self) -> str:
        """Return the user-friendly browser name."""
        return "Mozilla Firefox"
    
    @property
    def executable_path(self) -> str:
        """Return the path to the Firefox executable."""
        return "/usr/bin/firefox"
    
    def discover_profiles(self) -> List[Profile]:
        """
        Discover all available Firefox profiles.
        
        Firefox stores profile information in profiles.ini file using INI format.
        Each profile has a directory and display name.
        """
        firefox_config_dir = self.get_config_directory()
        profiles = []
        
        if not os.path.exists(firefox_config_dir):
            logging.warning("Firefox config directory not found at %s", firefox_config_dir)
            return profiles
        
        # Read profile information from profiles.ini file
        profiles_ini_file = self.get_profiles_ini_file()
        if not os.path.exists(profiles_ini_file):
            logging.warning("Firefox profiles.ini file not found at %s", profiles_ini_file)
            return profiles
        
        try:
            config = configparser.ConfigParser()
            config.read(profiles_ini_file)
            
            # Firefox profiles.ini format:
            # [Profile0]
            # Name=default
            # IsRelative=1
            # Path=abc123.default
            # Default=1
            
            for section_name in config.sections():
                if section_name.startswith('Profile'):
                    section = config[section_name]
                    
                    profile_name = section.get('Name', section_name)
                    
                    if profile_name:
                        profiles.append(Profile(
                            id=profile_name,
                            name=profile_name,
                            browser=self.name,
                            is_private=False
                        ))
                    
        except (configparser.Error, OSError) as e:
            logging.error("Error reading Firefox profiles.ini: %s", e)
        
        return profiles
    
    def get_private_mode_profile(self) -> Profile:
        """
        Get the Firefox private browsing mode profile.
        
        Firefox private browsing is launched with --private-window flag.
        """
        return Profile(
            id="private",
            name="Private Window",
            browser=self.name,
            is_private=True,
        )
    
    def launch(self, profile: Profile, url: Optional[str] = None) -> None:
        """
        Launch Firefox with the specified profile and optional URL.
        
        Firefox uses different command-line arguments:
        - Profile: firefox -P "profile_name"
        - Private: firefox --private-window [url]
        """
        command = [self.executable_path]
        
        # Handle private browsing mode
        if profile.is_private:
            command.append("--private-window")
            logging.info("Launching Firefox in private browsing mode")
        else:
            # Use profile name for regular profiles
            command.extend(["-P", profile.id])
            logging.info("Launching Firefox with profile: %s", profile.id)
        
        if url is not None:
            command.append(url)
        
        logging.info("Firefox launch command: %s", str(command))
        subprocess.run(command, check=False)
    
    def is_available(self) -> bool:
        """
        Check if Firefox is available on the system.
        
        Returns True if the Firefox executable exists and is accessible.
        """
        return os.path.isfile(self.executable_path) and os.access(self.executable_path, os.X_OK)
    
    def get_config_directory(self) -> str:
        """
        Get the Firefox configuration directory.
        
        Returns the path to Firefox's configuration directory.
        """
        return os.path.expanduser("~/.mozilla/firefox")
    
    def get_profiles_ini_file(self) -> str:
        """
        Get the path to Firefox's profiles.ini file.
        
        Returns the full path to the profiles.ini file.
        """
        return os.path.join(self.get_config_directory(), "profiles.ini")
    
    def profile_exists(self, profile_id: str) -> bool:
        """
        Check if a profile exists.
        
        Args:
            profile_id: The profile name to check
            
        Returns:
            True if the profile exists.
        """
        if profile_id == "private":
            return True  # Private mode is always available
        
        # Check if profile exists in profiles.ini
        profiles = self.discover_profiles()
        return any(p.id == profile_id for p in profiles)
    
    
    def get_default_profile(self) -> Optional[Profile]:
        """
        Get the default Firefox profile.
        
        Returns:
            The default profile, or the first available profile.
        """
        profiles_ini_file = self.get_profiles_ini_file()
        if not os.path.exists(profiles_ini_file):
            return None
        
        try:
            config = configparser.ConfigParser()
            config.read(profiles_ini_file)
            
            # Look for default profile
            for section_name in config.sections():
                if section_name.startswith('Profile'):
                    section = config[section_name]
                    if section.getboolean('Default', False):
                        profile_name = section.get('Name', section_name)
                        return self.get_profile_by_id(profile_name)
            
            # If no default found, return first profile
            profiles = self.discover_profiles()
            return profiles[0] if profiles else None
            
        except (configparser.Error, OSError) as e:
            logging.error("Error finding default Firefox profile: %s", e)
            return None
    
    def get_browser_icon(self) -> Optional[str]:
        """
        Get the Firefox browser icon.
        
        Returns path to Firefox icon or None if not found.
        """
        # Common Firefox icon locations
        icon_paths = [
            "/usr/share/icons/hicolor/256x256/apps/firefox.png",
            "/usr/share/pixmaps/firefox.png",
            "/usr/lib/firefox/browser/chrome/icons/default/default256.png"
        ]
        
        for path in icon_paths:
            if os.path.isfile(path):
                return path
        return None
    
    def get_private_mode_icon(self) -> Optional[str]:
        """
        Get the Firefox private browsing mode icon.
        
        Firefox typically uses a modified version of the main icon.
        """
        # Firefox doesn't have a separate private browsing icon file typically
        # We'll use the main icon and let the UI modify it visually
        return self.get_browser_icon()
    
    def get_profile_icon(self, profile: Profile) -> ProfileIcon:
        """
        Get icon information for a Firefox profile.
        
        Firefox doesn't have the same rich profile theming as Chrome,
        so we'll provide sensible defaults with Firefox branding colors.
        """
        if profile.is_private:
            return ProfileIcon(
                avatar_icon="firefox-private",
                background_color="#592ACB",  # Firefox private browsing purple
                text_color="#FFFFFF"
            )
        
        # Firefox profile colors based on Firefox branding
        firefox_colors = [
            "#FF6611",  # Firefox orange
            "#0060DF",  # Firefox blue  
            "#20123A",  # Firefox dark purple
            "#592ACB",  # Firefox purple
            "#00C8D7",  # Firefox cyan
            "#FF4F5E",  # Firefox red
            "#0090ED",  # Firefox light blue
            "#7542E5",  # Firefox violet
        ]
        
        # Use profile name hash to pick a consistent color
        color_index = hash(profile.id) % len(firefox_colors)
        background_color = firefox_colors[color_index]
        
        return ProfileIcon(
            avatar_icon=f"firefox-avatar-{color_index}",
            background_color=background_color,
            text_color="#FFFFFF"
        )
