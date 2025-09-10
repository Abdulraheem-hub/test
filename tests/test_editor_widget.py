"""Tests for EditorWidget functionality."""

from __future__ import annotations

from unittest.mock import patch

import pytest

# Mark all tests in this module as GUI tests (will be skipped in headless environment)
pytestmark = pytest.mark.gui


# Only import GUI components if we're running GUI tests
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QKeyEvent

    from pyqt6_editor.gui import EditorWidget
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


@pytest.mark.skipif(not GUI_AVAILABLE, reason="GUI not available in headless environment")
class TestEditorWidget:
    """Test EditorWidget class functionality."""

    def test_max_line_length_constant(self) -> None:
        """Test that MAX_LINE_LENGTH is set correctly."""
        assert EditorWidget.MAX_LINE_LENGTH == 80

    @pytest.fixture
    def editor_widget(self) -> EditorWidget:
        """Create an EditorWidget instance for testing."""
        return EditorWidget()

    def test_line_number_area_width(self, editor_widget: EditorWidget) -> None:
        """Test line number area width calculation."""
        # For single digit line numbers
        width = editor_widget.line_number_area_width()
        assert width > 0

        # Mock a document with many lines to test multi-digit calculation
        with patch.object(editor_widget, 'blockCount', return_value=100):
            width_100 = editor_widget.line_number_area_width()
            assert width_100 > width  # Should be wider for 3-digit line numbers

    def test_overwrite_mode_basic(self, editor_widget: EditorWidget) -> None:
        """Test basic overwrite mode functionality."""
        # Set initial content
        editor_widget.set_content("Hello World")

        # Position cursor at character 'e' (position 1)
        cursor = editor_widget.textCursor()
        cursor.setPosition(1)
        editor_widget.setTextCursor(cursor)

        # Simulate typing 'a' which should overwrite 'e'
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a")
        editor_widget.keyPressEvent(key_event)

        # The 'e' should be replaced with 'a'
        assert editor_widget.get_content() == "Hallo World"

    def test_overwrite_mode_end_of_line_block(self, editor_widget: EditorWidget) -> None:
        """Test that typing beyond existing text at end of line is blocked."""
        # Set initial content
        editor_widget.set_content("Hello")

        # Position cursor at the end (after 'o')
        cursor = editor_widget.textCursor()
        cursor.setPosition(5)
        editor_widget.setTextCursor(cursor)

        # Simulate typing 'X' which should be blocked
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "x")
        editor_widget.keyPressEvent(key_event)

        # Content should remain unchanged
        assert editor_widget.get_content() == "Hello"

    def test_line_length_constraint(self, editor_widget: EditorWidget) -> None:
        """Test 80-character line length constraint."""
        # Create a line with exactly 80 characters
        long_line = "a" * 80
        editor_widget.set_content(long_line)

        # Position cursor at the end
        cursor = editor_widget.textCursor()
        cursor.setPosition(80)
        editor_widget.setTextCursor(cursor)

        # Try to type another character - should be blocked
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "x")
        editor_widget.keyPressEvent(key_event)

        # Content should remain unchanged
        assert editor_widget.get_content() == long_line
        assert len(editor_widget.get_content()) == 80

    def test_navigation_keys_work_normally(self, editor_widget: EditorWidget) -> None:
        """Test that navigation keys work normally."""
        editor_widget.set_content("Hello\nWorld")

        # Position cursor at start
        cursor = editor_widget.textCursor()
        cursor.setPosition(0)
        editor_widget.setTextCursor(cursor)

        # Test right arrow key
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        editor_widget.keyPressEvent(key_event)

        # Cursor should have moved
        new_position = editor_widget.textCursor().position()
        assert new_position == 1

    def test_enter_key_works_normally(self, editor_widget: EditorWidget) -> None:
        """Test that Enter key inserts new lines normally."""
        editor_widget.set_content("Hello")

        # Position cursor at end
        cursor = editor_widget.textCursor()
        cursor.setPosition(5)
        editor_widget.setTextCursor(cursor)

        # Press Enter
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        editor_widget.keyPressEvent(key_event)

        # Should have a new line
        content = editor_widget.get_content()
        assert "\n" in content
        assert content == "Hello\n"

    def test_backspace_works_normally(self, editor_widget: EditorWidget) -> None:
        """Test that Backspace works normally."""
        editor_widget.set_content("Hello")

        # Position cursor at end
        cursor = editor_widget.textCursor()
        cursor.setPosition(5)
        editor_widget.setTextCursor(cursor)

        # Press Backspace
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        editor_widget.keyPressEvent(key_event)

        # Last character should be deleted
        assert editor_widget.get_content() == "Hell"

    def test_multiline_overwrite_mode(self, editor_widget: EditorWidget) -> None:
        """Test overwrite mode works correctly with multiple lines."""
        editor_widget.set_content("Hello\nWorld\nTest")

        # Position cursor at 'W' in "World" (line 2, position 0)
        cursor = editor_widget.textCursor()
        cursor.setPosition(6)  # After "Hello\n"
        editor_widget.setTextCursor(cursor)

        # Type 'X' to overwrite 'W'
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "X")
        editor_widget.keyPressEvent(key_event)

        # Should overwrite 'W' with 'X'
        assert editor_widget.get_content() == "Hello\nXorld\nTest"

    def test_set_and_get_content(self, editor_widget: EditorWidget) -> None:
        """Test content setting and getting."""
        test_content = "Test content\nSecond line"
        editor_widget.set_content(test_content)
        assert editor_widget.get_content() == test_content

    def test_line_within_80_chars_allows_typing(self, editor_widget: EditorWidget) -> None:
        """Test that typing is allowed within 80 character limit."""
        # Create a line with 79 characters
        short_line = "a" * 79
        editor_widget.set_content(short_line)

        # Position cursor at the end
        cursor = editor_widget.textCursor()
        cursor.setPosition(79)
        editor_widget.setTextCursor(cursor)

        # Try to type one more character - should be allowed
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "x")
        editor_widget.keyPressEvent(key_event)

        # Should have 80 characters now
        assert len(editor_widget.get_content()) == 80
        assert editor_widget.get_content().endswith("x")
