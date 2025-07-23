"""
Chrome browser implementation for choosr.

This module provides a concrete implementation of the Browser interface
for Google Chrome, based on the existing Chrome-specific code in choosr.py.
"""

import json
import logging
import os
import subprocess
from typing import List, Optional

from browser import Browser, Profile, ProfileIcon


class ChromeBrowser(Browser):
    """Google Chrome browser implementation."""
    
    @property
    def name(self) -> str:
        """Return the browser name."""
        return "chrome"
    
    @property
    def display_name(self) -> str:
        """Return the user-friendly browser name."""
        return "Google Chrome"
    
    @property
    def executable_path(self) -> str:
        """Return the path to the Chrome executable."""
        return "/usr/bin/google-chrome"
    
    def discover_profiles(self) -> List[Profile]:
        """
        Discover all available Chrome profiles.
        
        Based on get_chrome_profiles() from choosr.py.
        Reads profile information from Chrome's Local State file.
        """
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
                    # Get profile icon information
                    profile_icon = self._get_profile_icon_from_info(profile_info)
                    
                    profiles.append(Profile(
                        id=profile_dir,
                        name=display_name,
                        browser=self.name,
                        is_private=False,
                        metadata={'directory': profile_dir},
                        icon=profile_icon
                    ))
                    
        except (json.JSONDecodeError, OSError) as e:
            logging.error("Error reading Chrome Local State: %s", e)
        
        return profiles
    
    def get_private_mode_profile(self) -> Profile:
        """
        Get the Chrome incognito mode profile.
        """
        return Profile(
            id="incognito",
            name="Incognito Mode",
            browser=self.name,
            is_private=True,
            metadata={'directory': None}
        )
    
    def launch(self, profile: Profile, url: Optional[str] = None) -> None:
        """
        Launch Chrome with the specified profile and optional URL.
        
        Based on launch_chrome() from choosr.py.
        Handles both regular profiles and incognito mode.
        """
        command = [self.executable_path]
        
        # Handle incognito mode (when profile directory is None)
        if profile.is_private or profile.metadata.get('directory') is None:
            command.append("--incognito")
            logging.info("Launching Chrome in incognito mode")
        else:
            profile_dir = profile.metadata.get('directory', profile.id)
            command.append(f"--profile-directory={profile_dir}")
            logging.info("Launching Chrome with profile directory: %s", profile_dir)
        
        if url is not None:
            command.append(url)
        
        logging.info("Chrome launch command: %s", str(command))
        subprocess.run(command, check=False)
    
    def is_available(self) -> bool:
        """
        Check if Chrome is available on the system.
        
        Returns True if the Chrome executable exists and is accessible.
        """
        return os.path.isfile(self.executable_path) and os.access(self.executable_path, os.X_OK)
    
    def get_config_directory(self) -> str:
        """
        Get the Chrome configuration directory.
        
        Returns the path to Chrome's configuration directory.
        """
        return os.path.expanduser("~/.config/google-chrome")
    
    def get_local_state_file(self) -> str:
        """
        Get the path to Chrome's Local State file.
        
        Returns the full path to the Local State file.
        """
        return os.path.join(self.get_config_directory(), "Local State")
    
    def profile_exists(self, profile_id: str) -> bool:
        """
        Check if a profile directory exists.
        
        Args:
            profile_id: The profile directory name to check
            
        Returns:
            True if the profile directory exists.
        """
        if profile_id == "incognito":
            return True  # Incognito mode is always available
        
        profile_path = os.path.join(self.get_config_directory(), profile_id)
        return os.path.isdir(profile_path)
    
    def get_profile_path(self, profile_id: str) -> Optional[str]:
        """
        Get the full filesystem path for a profile.
        
        Args:
            profile_id: The profile directory name
            
        Returns:
            Full path to the profile directory, or None for incognito mode.
        """
        if profile_id == "incognito":
            return None
        
        return os.path.join(self.get_config_directory(), profile_id)
    
    def get_browser_icon(self) -> Optional[str]:
        """
        Get the Chrome browser icon.
        
        Returns path to Chrome icon or None if not found.
        """
        # Common Chrome icon locations
        icon_paths = [
            "/usr/share/icons/hicolor/256x256/apps/google-chrome.png",
            "/usr/share/pixmaps/google-chrome.png",
            "/opt/google/chrome/product_logo_256.png"
        ]
        
        for path in icon_paths:
            if os.path.isfile(path):
                return path
        return None
    
    def get_private_mode_icon(self) -> Optional[str]:
        """
        Get the Chrome incognito mode icon.
        
        For Chrome, this would typically be a modified version of the main icon.
        """
        # Chrome doesn't have a separate incognito icon file typically
        # We'll use the main icon and let the UI modify it visually
        return self.get_browser_icon()
    
    def get_profile_icon(self, profile: Profile) -> ProfileIcon:
        """
        Get icon information for a Chrome profile.
        
        Chrome stores profile avatar and theme information in Local State.
        """
        if profile.is_private:
            return ProfileIcon(
                avatar_icon="incognito",
                background_color="#5F6368",  # Chrome incognito gray
                text_color="#FFFFFF"
            )
        
        if profile.icon:
            return profile.icon
        
        # Fallback: try to get fresh data from Local State
        return self._get_profile_icon_from_local_state(profile.id)
    
    def _get_profile_icon_from_info(self, profile_info: dict) -> ProfileIcon:
        """
        Extract profile icon information from Chrome's profile info.
        
        Chrome stores avatar_icon and theme_colors in the profile info.
        """
        # Chrome avatar icon identifiers
        avatar_icon = profile_info.get('avatar_icon', 'chrome-avatar-generic')
        
        # Chrome theme colors
        theme_colors = profile_info.get('theme_colors', {})
        background_color = None
        text_color = None
        
        if theme_colors:
            # Chrome stores theme colors as signed integers, convert to hex
            if 'theme_frame' in theme_colors:
                color_int = theme_colors['theme_frame']
                if color_int < 0:  # Handle negative integers
                    color_int = color_int + 2**32
                background_color = f"#{color_int:06X}"
            
            if 'theme_text' in theme_colors:
                color_int = theme_colors['theme_text'] 
                if color_int < 0:
                    color_int = color_int + 2**32
                text_color = f"#{color_int:06X}"
        
        # Chrome avatar icon mapping
        chrome_colors = {
            'chrome-avatar-generic': "#4285F4",
            'chrome-avatar-1': "#EA4335",
            'chrome-avatar-2': "#34A853", 
            'chrome-avatar-3': "#FBBC04",
            'chrome-avatar-4': "#FF6D01",
            'chrome-avatar-5': "#9AA0A6",
            'chrome-avatar-6': "#4285F4",
            'chrome-avatar-7': "#0F9D58",
            'chrome-avatar-8': "#F4B400",
            'chrome-avatar-9': "#DB4437",
            'chrome-avatar-10': "#673AB7",
            'chrome-avatar-11': "#FF5722",
            'chrome-avatar-12': "#607D8B",
            'chrome-avatar-13': "#795548",
            'chrome-avatar-14': "#3F51B5",
            'chrome-avatar-15': "#E91E63",
            'chrome-avatar-16': "#00BCD4",
            'chrome-avatar-17': "#CDDC39",
            'chrome-avatar-18': "#FF9800",
            'chrome-avatar-19': "#9C27B0",
            'chrome-avatar-20': "#2196F3",
            'chrome-avatar-21': "#009688",
            'chrome-avatar-22': "#8BC34A",
            'chrome-avatar-23': "#FFC107",
            'chrome-avatar-24': "#FF5722",
            'chrome-avatar-25': "#6D4C41",
            'chrome-avatar-26': "#546E7A"
        }
        
        # Use theme color if available, otherwise use avatar color
        if not background_color:
            background_color = chrome_colors.get(avatar_icon, "#4285F4")
        
        if not text_color:
            text_color = "#FFFFFF"
        
        return ProfileIcon(
            avatar_icon=avatar_icon,
            background_color=background_color,
            text_color=text_color
        )
    
    def _get_profile_icon_from_local_state(self, profile_id: str) -> ProfileIcon:
        """
        Get profile icon information directly from Local State file.
        """
        local_state_file = self.get_local_state_file()
        if not os.path.exists(local_state_file):
            return ProfileIcon()  # Return default
        
        try:
            with open(local_state_file, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            profile_info_cache = local_state.get('profile', {}).get('info_cache', {})
            profile_info = profile_info_cache.get(profile_id, {})
            
            return self._get_profile_icon_from_info(profile_info)
            
        except (json.JSONDecodeError, OSError) as e:
            logging.error("Error reading Chrome Local State for icons: %s", e)
            return ProfileIcon()  # Return default
