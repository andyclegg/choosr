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

from browser import Browser, Profile


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
                    profiles.append(Profile(
                        id=profile_dir,
                        name=display_name,
                        browser=self.name,
                        is_private=False,
                        metadata={'directory': profile_dir}
                    ))
                    
        except (json.JSONDecodeError, OSError) as e:
            logging.error("Error reading Chrome Local State: %s", e)
        
        return profiles
    
    def get_private_mode_profile(self) -> Profile:
        """
        Get the Chrome incognito mode profile.
        
        Based on the special "Chrome Incognito Mode" profile from choosr.py.
        """
        return Profile(
            id="incognito",
            name="Chrome Incognito Mode",
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