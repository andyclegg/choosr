"""Tests for Qt interface."""


class TestShowErrorDialog:
    def test_show_error_dialog_does_not_crash(self, qtbot):
        """Error dialog should display without crashing."""
        from qt_interface import show_error_dialog

        # This should not raise an exception
        # We can't easily verify the dialog appeared, but we can verify no crash
        show_error_dialog("Test Error", "This is a test error message")

    def test_show_error_dialog_with_empty_message(self, qtbot):
        """Error dialog should handle empty message."""
        from qt_interface import show_error_dialog

        show_error_dialog("Error", "")


class TestThemeDetection:
    def test_detect_system_theme_returns_string(self, qtbot):
        """Theme detection should return 'light' or 'dark'."""
        from qt_interface import ProfileSelectorController

        controller = ProfileSelectorController()
        theme = controller._detect_system_theme()

        assert theme in ("light", "dark")
