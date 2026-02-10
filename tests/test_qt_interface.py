"""Tests for Qt interface."""


class TestShowErrorDialog:
    def test_show_error_dialog_does_not_crash(self, qtbot, mocker):
        """Error dialog should display without crashing."""
        # Mock QMessageBox to prevent actual dialog display
        mock_msgbox_class = mocker.patch("PySide6.QtWidgets.QMessageBox")
        mock_instance = mocker.MagicMock()
        mock_msgbox_class.return_value = mock_instance

        from qt_interface import show_error_dialog

        show_error_dialog("Test Error", "This is a test error message")

        # Verify QMessageBox was configured correctly
        mock_instance.setIcon.assert_called_once()
        mock_instance.setWindowTitle.assert_called_once_with("Test Error")
        mock_instance.setText.assert_called_once_with("This is a test error message")
        mock_instance.exec.assert_called_once()

    def test_show_error_dialog_with_empty_message(self, qtbot, mocker):
        """Error dialog should handle empty message."""
        # Mock QMessageBox to prevent actual dialog display
        mock_msgbox_class = mocker.patch("PySide6.QtWidgets.QMessageBox")
        mock_instance = mocker.MagicMock()
        mock_msgbox_class.return_value = mock_instance

        from qt_interface import show_error_dialog

        show_error_dialog("Error", "")

        # Verify it handled empty message
        mock_instance.setText.assert_called_once_with("")
        mock_instance.exec.assert_called_once()


class TestThemeDetection:
    def test_detect_system_theme_returns_string(self, qtbot):
        """Theme detection should return 'light' or 'dark'."""
        from qt_interface import ProfileSelectorController

        controller = ProfileSelectorController()
        theme = controller._detect_system_theme()

        assert theme in ("light", "dark")
