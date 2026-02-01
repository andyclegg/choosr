"""
Chrome browser implementation for choosr.

This module provides a concrete implementation of the Browser interface
for Google Chrome, based on the existing Chrome-specific code in choosr.py.
"""

import json
import os
import subprocess
from typing import List, Optional

from browser import Browser, Profile, ProfileIcon


class ChromeBrowser(Browser):
    """Google Chrome browser implementation."""

    def __init__(self):
        super().__init__()

    # Chrome avatar icon color mapping
    AVATAR_COLORS = {
        "chrome-avatar-generic": "#4285F4",
        "chrome://theme/IDR_PROFILE_AVATAR_26": "#546E7A",
        "chrome://theme/IDR_PROFILE_AVATAR_0": "#EA4335",
        "chrome://theme/IDR_PROFILE_AVATAR_1": "#34A853",
        "chrome://theme/IDR_PROFILE_AVATAR_2": "#FBBC04",
        "chrome://theme/IDR_PROFILE_AVATAR_3": "#FF6D01",
        "chrome://theme/IDR_PROFILE_AVATAR_4": "#9AA0A6",
        "chrome://theme/IDR_PROFILE_AVATAR_5": "#4285F4",
        "chrome://theme/IDR_PROFILE_AVATAR_6": "#0F9D58",
        "chrome://theme/IDR_PROFILE_AVATAR_7": "#F4B400",
        "chrome://theme/IDR_PROFILE_AVATAR_8": "#DB4437",
        "chrome://theme/IDR_PROFILE_AVATAR_9": "#673AB7",
        "chrome://theme/IDR_PROFILE_AVATAR_10": "#FF5722",
        "chrome://theme/IDR_PROFILE_AVATAR_11": "#607D8B",
        "chrome://theme/IDR_PROFILE_AVATAR_12": "#795548",
        "chrome://theme/IDR_PROFILE_AVATAR_13": "#3F51B5",
        "chrome://theme/IDR_PROFILE_AVATAR_14": "#E91E63",
        "chrome://theme/IDR_PROFILE_AVATAR_15": "#00BCD4",
        "chrome://theme/IDR_PROFILE_AVATAR_16": "#CDDC39",
        "chrome://theme/IDR_PROFILE_AVATAR_17": "#FF9800",
        "chrome://theme/IDR_PROFILE_AVATAR_18": "#9C27B0",
        "chrome://theme/IDR_PROFILE_AVATAR_19": "#2196F3",
        "chrome://theme/IDR_PROFILE_AVATAR_20": "#009688",
        "chrome://theme/IDR_PROFILE_AVATAR_21": "#8BC34A",
        "chrome://theme/IDR_PROFILE_AVATAR_22": "#FFC107",
        "chrome://theme/IDR_PROFILE_AVATAR_23": "#FF5722",
        "chrome://theme/IDR_PROFILE_AVATAR_24": "#6D4C41",
        "chrome://theme/IDR_PROFILE_AVATAR_25": "#546E7A",
    }

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
            return profiles

        # Read profile information from Local State file
        local_state_file = os.path.join(chrome_config_dir, "Local State")
        if not os.path.exists(local_state_file):
            return profiles

        try:
            with open(local_state_file, "r", encoding="utf-8") as f:
                local_state = json.load(f)

            # Get profile info from Local State
            profile_info_cache = local_state.get("profile", {}).get("info_cache", {})

            for profile_dir, profile_info in profile_info_cache.items():
                # Verify the profile directory actually exists
                profile_path = os.path.join(chrome_config_dir, profile_dir)
                if os.path.isdir(profile_path):
                    name = profile_info.get("name", profile_dir)
                    email = profile_info.get("user_name")
                    # Get profile icon information
                    profile_icon = self._get_profile_icon_from_info(
                        profile_info, profile_dir
                    )

                    profiles.append(
                        Profile(
                            id=profile_dir,
                            name=name,
                            browser=self.name,
                            is_private=False,
                            email=email,
                            icon=profile_icon,
                        )
                    )

        except (json.JSONDecodeError, OSError):
            pass

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
        )

    def launch(self, profile: Profile, url: Optional[str] = None) -> None:
        """
        Launch Chrome with the specified profile and optional URL.

        Based on launch_chrome() from choosr.py.
        Handles both regular profiles and incognito mode.
        """
        command = [self.executable_path]

        # Handle incognito mode (when profile directory is None)
        if profile.is_private:
            command.append("--incognito")
        else:
            command.append(f"--profile-directory={profile.id}")

        if url is not None:
            command.append(url)

        subprocess.run(command, check=False)

    def is_available(self) -> bool:
        """
        Check if Chrome is available on the system.

        Returns True if the Chrome executable exists and is accessible.
        """
        return os.path.isfile(self.executable_path) and os.access(
            self.executable_path, os.X_OK
        )

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

    def get_source_files(self) -> List[str]:
        """
        Return list of files that Chrome profile discovery depends on.

        Returns:
            List of file paths for cache invalidation.
        """
        return [self.get_local_state_file()]

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
            "/opt/google/chrome/product_logo_256.png",
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
                text_color="#FFFFFF",
            )

        if profile.icon:
            return profile.icon

        # Fallback: try to get fresh data from Local State
        return self._get_profile_icon_from_local_state(profile.id)

    def _get_profile_icon_from_info(
        self, profile_info: dict, profile_id: str
    ) -> ProfileIcon:
        """
        Extract profile icon information from Chrome's profile info.

        Chrome stores avatar_icon, theme_colors, and gaia picture info.
        """
        # Try to get actual profile picture file first
        icon_file_path = self._get_profile_picture_path(profile_info, profile_id)

        # Chrome avatar icon identifiers
        avatar_icon = profile_info.get("avatar_icon", "chrome-avatar-generic")

        # Chrome theme colors
        theme_colors = profile_info.get("theme_colors", {})
        background_color = None
        text_color = None

        if theme_colors:
            # Chrome stores theme colors as signed integers, convert to hex
            if "theme_frame" in theme_colors:
                background_color = self._convert_chrome_color_to_hex(
                    theme_colors["theme_frame"]
                )

            if "theme_text" in theme_colors:
                text_color = self._convert_chrome_color_to_hex(
                    theme_colors["theme_text"]
                )

        # Try to extract background color from profile_highlight_color or profile_color_seed
        if not background_color:
            if "profile_highlight_color" in profile_info:
                background_color = self._convert_chrome_color_to_hex(
                    profile_info["profile_highlight_color"]
                )
            elif "default_avatar_fill_color" in profile_info:
                background_color = self._convert_chrome_color_to_hex(
                    profile_info["default_avatar_fill_color"]
                )

        # Use theme color if available, otherwise use avatar color (fallback)
        if not background_color:
            background_color = self.AVATAR_COLORS.get(avatar_icon, "#4285F4")

        if not text_color:
            text_color = "#FFFFFF"

        return ProfileIcon(
            avatar_icon=avatar_icon,
            background_color=background_color,
            text_color=text_color,
            icon_file_path=icon_file_path,
        )

    def _get_profile_icon_from_local_state(self, profile_id: str) -> ProfileIcon:
        """
        Get profile icon information directly from Local State file.
        """
        local_state_file = self.get_local_state_file()
        if not os.path.exists(local_state_file):
            return ProfileIcon()  # Return default

        try:
            with open(local_state_file, "r", encoding="utf-8") as f:
                local_state = json.load(f)

            profile_info_cache = local_state.get("profile", {}).get("info_cache", {})
            profile_info = profile_info_cache.get(profile_id, {})

            return self._get_profile_icon_from_info(profile_info, profile_id)

        except (json.JSONDecodeError, OSError):
            return ProfileIcon()  # Return default

    def _get_profile_picture_path(
        self, profile_info: dict, profile_id: str
    ) -> Optional[str]:
        """
        Get the path to the profile picture file.

        Chrome stores profile pictures in several possible locations:
        1. Google Profile Picture.png in the profile directory (for Google accounts)
        2. Avatar image in Accounts/Avatar Images/ directory (for Google accounts)
        3. Default avatar based on avatar_icon setting
        """
        chrome_config_dir = self.get_config_directory()

        # Method 1: Check for Google Profile Picture.png in profile directory
        profile_picture_path = os.path.join(
            chrome_config_dir, profile_id, "Google Profile Picture.png"
        )
        if os.path.isfile(profile_picture_path):
            return profile_picture_path

        # Method 2: Check Avatar Images directory using gaia_id
        gaia_id = profile_info.get("gaia_id")
        if gaia_id:
            avatar_image_path = os.path.join(
                chrome_config_dir, profile_id, "Accounts", "Avatar Images", gaia_id
            )
            if os.path.isfile(avatar_image_path):
                return avatar_image_path

        # Method 3: No actual image file found
        return None

    def _convert_chrome_color_to_hex(self, color_int):
        """Convert Chrome's signed integer color to hex string."""
        if color_int < 0:  # Handle negative integers
            color_int = color_int + 2**32
        return f"#{color_int:06X}"
