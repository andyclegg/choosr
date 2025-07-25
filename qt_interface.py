"""
Qt/QML interface for choosr profile selection.

This module provides a modern, beautiful Qt/QML-based interface with
support for profile icons, system theme detection, and improved user experience.
Requires PySide6 as a hard dependency.
"""

import os
import sys
from typing import List, Optional, Tuple, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot, QUrl, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPalette
from PySide6.QtQuick import QQuickView

from browser import browser_registry, Profile


class ProfileSelectorView(QQuickView):
    """Custom QQuickView that emits a signal when closed."""

    windowClosed = Signal()

    def __init__(self):
        super().__init__()

    def closeEvent(self, event):
        """Handle window close event."""
        self.windowClosed.emit()
        super().closeEvent(event)


class ProfileSelectorController(QObject):
    """Qt controller for the profile selector interface."""

    # Signals
    profileSelected = Signal(
        str, str, bool
    )  # profile_name, domain_pattern, save_choice
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._profiles = []
        self._url = ""
        self._domain = ""
        self._view = None

    def _detect_system_theme(self) -> str:
        """Detect if the system is using light or dark theme."""
        app = QGuiApplication.instance()
        if app is None:
            return "light"

        # Get system palette
        palette = app.palette()

        # Check if the window background is darker than the window text
        # This is a common way to detect dark themes
        bg_color = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.WindowText)

        # Calculate brightness using standard luminance formula
        bg_brightness = (
            bg_color.red() * 0.299 + bg_color.green() * 0.587 + bg_color.blue() * 0.114
        )
        text_brightness = (
            text_color.red() * 0.299
            + text_color.green() * 0.587
            + text_color.blue() * 0.114
        )

        # If background is darker than text, it's likely a dark theme
        return "dark" if bg_brightness < text_brightness else "light"

    def show_profile_selector(
        self, url: str, domain: str, profiles: Dict[str, Any]
    ) -> Optional[Tuple[str, str, bool]]:
        """
        Show the Qt/QML profile selector interface.

        Args:
            url: The URL being opened
            domain: The extracted domain
            profiles: Dictionary of profile configurations

        Returns:
            Tuple of (profile_name, domain_pattern, save_choice) or None if cancelled
        """

        self._url = url
        self._domain = domain
        self._result = None
        self._cancelled = False

        # Convert profiles to QML-friendly format with icon information
        profile_data = self._prepare_profile_data(profiles)

        # Create Qt application if it doesn't exist
        app = QGuiApplication.instance()
        if app is None:
            app = QGuiApplication(sys.argv)

        # Detect system theme
        system_theme = self._detect_system_theme()

        # Get screen dimensions - use availableGeometry for proper scaling and taskbar handling
        screen = app.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_height = screen_geometry.height()

        # Create QML view
        self._view = ProfileSelectorView()
        self._view.setResizeMode(QQuickView.SizeRootObjectToView)

        # Set window properties
        self._view.setFlags(self._view.flags() | Qt.WindowStaysOnTopHint)
        self._view.setModality(Qt.ApplicationModal)
        self._view.setTitle("Choose Profile")

        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "choosr-icon.svg")
        if os.path.exists(icon_path):
            self._view.setIcon(QIcon(icon_path))

        # Connect window close handling
        def handle_window_close():
            self._cancelled = True

        self._view.windowClosed.connect(handle_window_close)

        # Register this controller with QML
        self._view.rootContext().setContextProperty("controller", self)

        # Set initial properties
        qml_file = os.path.join(os.path.dirname(__file__), "ProfileSelector.qml")
        self._view.setSource(QUrl.fromLocalFile(qml_file))

        if self._view.status() == QQuickView.Error:
            return None

        # Get root object and set properties
        root = self._view.rootObject()
        if root:
            root.setProperty("currentUrl", url)
            root.setProperty("currentDomain", domain)
            root.setProperty("domainPattern", domain)
            root.setProperty("profileData", profile_data)
            root.setProperty("systemTheme", system_theme)
            root.setProperty("screenHeight", screen_height)

            # Connect signals
            root.profileSelected.connect(self._on_profile_selected)
            root.cancelled.connect(self._on_cancelled)

        # Show window
        self._view.show()

        # Process events until result is available
        while self._result is None and not self._cancelled:
            app.processEvents()
            QTimer.singleShot(10, lambda: None)  # Small delay to prevent busy waiting

        # Clean up
        if self._view:
            self._view.close()
            self._view = None

        return self._result

    def _prepare_profile_data(self, profiles: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert profile configurations to browser-grouped QML-friendly format with icons."""
        # Group profiles by browser
        browser_groups = {}

        for profile_name, profile_config in profiles.items():
            browser_type = profile_config.get("browser", "unknown")
            is_private = profile_config.get("is_private", False)

            # Get browser and profile icon information
            browser = browser_registry.get_browser(browser_type)
            browser_display = browser.display_name if browser else browser_type.title()

            # Create a Profile object to get icon information
            profile = Profile(
                id=profile_config.get("profile_id", profile_name),
                name=profile_name,
                browser=browser_type,
                is_private=is_private,
            )

            # Get icon information
            browser_icon_path = None
            background_color = "#4285F4"
            text_color = "#FFFFFF"
            icon_file_path = None

            if browser:
                browser_icon_path = browser.get_browser_icon()
                if is_private:
                    browser_icon_path = browser.get_private_mode_icon()

                profile_icon = browser.get_profile_icon(profile)
                background_color = profile_icon.background_color or "#4285F4"
                text_color = profile_icon.text_color or "#FFFFFF"
                icon_file_path = profile_icon.icon_file_path

            profile_data = {
                "name": profile_name,
                "browser": browser_type,
                "browserDisplayName": browser_display,
                "isPrivate": is_private,
                "browserIcon": browser_icon_path or "",
                "backgroundColor": background_color,
                "textColor": text_color,
                "iconFilePath": icon_file_path or "",
                "profileId": profile_config.get("profile_id", profile_name),
            }

            # Group by browser display name
            if browser_display not in browser_groups:
                browser_groups[browser_display] = {"regular": [], "private": []}

            if is_private:
                browser_groups[browser_display]["private"].append(profile_data)
            else:
                browser_groups[browser_display]["regular"].append(profile_data)

        # Sort profiles within each browser group and convert to QML-friendly format
        result = []
        for browser_name, groups in browser_groups.items():
            # Sort regular profiles alphabetically
            groups["regular"].sort(key=lambda x: x["name"].lower())
            # Combine with private profiles at the end
            browser_profiles = groups["regular"] + groups["private"]

            result.append({"browserName": browser_name, "profiles": browser_profiles})

        return result

    @Slot(str, str, bool)
    def _on_profile_selected(
        self, profile_name: str, domain_pattern: str, save_choice: bool
    ):
        """Handle profile selection from QML."""
        self._result = (profile_name, domain_pattern, save_choice)

    @Slot()
    def _on_cancelled(self):
        """Handle cancellation from QML."""
        self._cancelled = True


# Global instance for use by choosr.py
qt_controller = ProfileSelectorController()


# Direct access to the controller for external use
show_qt_profile_selector = qt_controller.show_profile_selector
