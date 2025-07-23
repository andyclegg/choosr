"""
Qt/QML interface for choosr profile selection.

This module provides a modern, beautiful Qt/QML-based interface to replace
the Tkinter GUI, with support for profile icons and improved user experience.
"""

import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any

try:
    from PySide6.QtCore import QObject, Signal, Slot, QUrl, QTimer, Qt
    from PySide6.QtGui import QGuiApplication, QIcon, QPalette
    from PySide6.QtQml import qmlRegisterType, QmlElement
    from PySide6.QtQuick import QQuickView
    QML_AVAILABLE = True
except ImportError:
    # Fallback when PySide6 is not available
    QML_AVAILABLE = False
    QObject = object
    Signal = lambda: None
    Slot = lambda *args, **kwargs: lambda f: f

from browser import browser_registry, Profile


class ProfileSelectorController(QObject):
    """Qt controller for the profile selector interface."""
    
    # Signals
    profileSelected = Signal(str, str, bool)  # profile_name, domain_pattern, save_choice
    cancelled = Signal()
    
    def __init__(self):
        super().__init__()
        self._profiles = []
        self._url = ""
        self._domain = ""
        self._view = None
        
    def _detect_system_theme(self) -> str:
        """Detect if the system is using light or dark theme."""
        if not QML_AVAILABLE:
            return "light"  # Default fallback
            
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
        bg_brightness = (bg_color.red() * 0.299 + bg_color.green() * 0.587 + bg_color.blue() * 0.114)
        text_brightness = (text_color.red() * 0.299 + text_color.green() * 0.587 + text_color.blue() * 0.114)
        
        # If background is darker than text, it's likely a dark theme
        return "dark" if bg_brightness < text_brightness else "light"
        
    def show_profile_selector(self, url: str, domain: str, profiles: Dict[str, Any]) -> Optional[Tuple[str, str, bool]]:
        """
        Show the Qt/QML profile selector interface.
        
        Args:
            url: The URL being opened
            domain: The extracted domain
            profiles: Dictionary of profile configurations
            
        Returns:
            Tuple of (profile_name, domain_pattern, save_choice) or None if cancelled
        """
        if not QML_AVAILABLE:
            logging.error("Qt/QML not available, falling back to console interface")
            return self._console_fallback(url, domain, profiles)
        
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
        logging.info("Detected system theme: %s", system_theme)
        
        # Create QML view
        self._view = QQuickView()
        self._view.setResizeMode(QQuickView.SizeRootObjectToView)
        
        # Set window properties
        self._view.setFlags(self._view.flags() | Qt.WindowStaysOnTopHint)
        self._view.setModality(Qt.ApplicationModal)
        self._view.setTitle("Choose Profile")
        
        # Register this controller with QML
        self._view.rootContext().setContextProperty("controller", self)
        
        # Set initial properties
        qml_file = os.path.join(os.path.dirname(__file__), "ProfileSelector.qml")
        self._view.setSource(QUrl.fromLocalFile(qml_file))
        
        if self._view.status() == QQuickView.Error:
            logging.error("Failed to load QML file: %s", qml_file)
            return self._console_fallback(url, domain, profiles)
        
        # Get root object and set properties
        root = self._view.rootObject()
        if root:
            root.setProperty("currentUrl", url)
            root.setProperty("currentDomain", domain)
            root.setProperty("domainPattern", domain)
            root.setProperty("profileData", profile_data)
            root.setProperty("systemTheme", system_theme)
            
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
        """Convert profile configurations to QML-friendly format with icons."""
        profile_data = []
        
        # Sort profiles with private profiles last
        regular_profiles = []
        private_profiles = []
        
        for name, config in profiles.items():
            if config.get('is_private', False):
                private_profiles.append((name, config))
            else:
                regular_profiles.append((name, config))
        
        regular_profiles.sort(key=lambda x: x[0])
        private_profiles.sort(key=lambda x: x[0])
        sorted_profiles = regular_profiles + private_profiles
        
        for profile_name, profile_config in sorted_profiles:
            browser_type = profile_config.get('browser', 'unknown')
            is_private = profile_config.get('is_private', False)
            
            # Get browser and profile icon information
            browser = browser_registry.get_browser(browser_type)
            browser_display = browser.display_name if browser else browser_type.title()
            
            # Create a Profile object to get icon information
            profile = Profile(
                id=profile_config.get('profile_id', profile_name),
                name=profile_name,
                browser=browser_type,
                is_private=is_private,
                metadata=profile_config.get('metadata', {})
            )
            
            # Get icon information
            browser_icon_path = None
            background_color = "#4285F4"
            text_color = "#FFFFFF"
            
            if browser:
                browser_icon_path = browser.get_browser_icon()
                if is_private:
                    browser_icon_path = browser.get_private_mode_icon()
                
                profile_icon = browser.get_profile_icon(profile)
                background_color = profile_icon.background_color or "#4285F4"
                text_color = profile_icon.text_color or "#FFFFFF"
            
            profile_data.append({
                'name': profile_name,
                'browser': browser_type,
                'browserDisplayName': browser_display,
                'isPrivate': is_private,
                'browserIcon': browser_icon_path or "",
                'backgroundColor': background_color,
                'textColor': text_color,
                'profileId': profile_config.get('profile_id', profile_name)
            })
        
        return profile_data
    
    @Slot(str, str, bool)
    def _on_profile_selected(self, profile_name: str, domain_pattern: str, save_choice: bool):
        """Handle profile selection from QML."""
        self._result = (profile_name, domain_pattern, save_choice)
        logging.info("QML Profile selected: %s, pattern: %s, save: %s", 
                    profile_name, domain_pattern, save_choice)
    
    @Slot()
    def _on_cancelled(self):
        """Handle cancellation from QML."""
        self._cancelled = True
        logging.info("QML Profile selection cancelled")
    
    def _console_fallback(self, url: str, domain: str, profiles: Dict[str, Any]) -> Optional[Tuple[str, str, bool]]:
        """Fallback console interface when Qt is not available."""
        print(f"\nChoose a profile for: {url}")
        print(f"Domain: {domain}")
        print("\nAvailable profiles:")
        
        profile_list = []
        for i, (name, config) in enumerate(profiles.items(), 1):
            browser_type = config.get('browser', 'unknown')
            is_private = config.get('is_private', False)
            browser = browser_registry.get_browser(browser_type)
            browser_display = browser.display_name if browser else browser_type.title()
            
            private_indicator = " (Private)" if is_private else ""
            print(f"{i:2d}. {name} [{browser_display}]{private_indicator}")
            profile_list.append(name)
        
        # Get user selection
        try:
            while True:
                choice = input(f"\nSelect profile (1-{len(profile_list)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    return None
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(profile_list):
                        selected_profile = profile_list[index]
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a number or 'q' to quit.")
            
            # Get domain pattern
            domain_pattern = input(f"Domain pattern to save (default: {domain}): ").strip()
            if not domain_pattern:
                domain_pattern = domain
            
            # Ask about saving
            save_choice = input("Save this choice for future use? (y/N): ").strip().lower().startswith('y')
            
            return (selected_profile, domain_pattern, save_choice)
            
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled by user")
            return None


# Global instance for use by choosr.py
qt_controller = ProfileSelectorController()


def show_qt_profile_selector(url: str, domain: str, profiles: Dict[str, Any]) -> Optional[Tuple[str, str, bool]]:
    """
    Show the Qt/QML profile selector.
    
    This is the main entry point that choosr.py will use to replace the Tkinter interface.
    
    Args:
        url: The URL being opened
        domain: The extracted domain  
        profiles: Dictionary of profile configurations from config file
        
    Returns:
        Tuple of (profile_name, domain_pattern, save_choice) or None if cancelled
    """
    return qt_controller.show_profile_selector(url, domain, profiles)