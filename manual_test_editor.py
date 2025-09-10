#!/usr/bin/env python3
"""Manual test script to validate EditorWidget functionality.

This script can be run in an environment with GUI support to manually test
the EditorWidget enhancements.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

    from pyqt6_editor.gui import EditorWidget

    class TestWindow(QMainWindow):
        """Test window for EditorWidget."""

        def __init__(self):
            super().__init__()
            self.setWindowTitle("EditorWidget Test - Line Numbers & Overwrite Mode")
            self.setGeometry(100, 100, 800, 600)

            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Add instructions
            instructions = QLabel("""
EditorWidget Test Instructions:

1. Line Numbers: Should be visible on the left side
2. Overwrite Mode: Typing should overwrite existing characters
3. 80-Character Limit: Cannot type beyond 80 characters per line
4. End-of-Line Block: Cannot type beyond existing text at end of line
5. Navigation: Arrow keys, Home, End should work normally
6. Enter: Should insert new lines normally
7. Backspace/Delete: Should work normally

Try typing to test the overwrite behavior!
            """)
            instructions.setWordWrap(True)
            layout.addWidget(instructions)

            # Add the editor widget
            self.editor = EditorWidget()

            # Set some initial content for testing
            initial_content = """<root>
    <element attribute="value">Sample text for testing</element>
    <another>Short line</another>
    <test>This is a longer line that approaches the 80-character limit for testing</test>
</root>"""
            self.editor.set_content(initial_content)
            layout.addWidget(self.editor)

            # Focus on the editor
            self.editor.setFocus()

    def main():
        """Run the test application."""
        app = QApplication(sys.argv)
        window = TestWindow()
        window.show()

        print("Manual test window opened. Test the following features:")
        print("1. Line numbers are visible")
        print("2. Overwrite mode (typing replaces characters)")
        print("3. 80-character line limit")
        print("4. Blocked typing at end of lines beyond existing text")
        print("5. Normal navigation and editing behaviors")

        return app.exec()

    if __name__ == "__main__":
        sys.exit(main())

except ImportError as e:
    print(f"GUI not available: {e}")
    print("This script requires a GUI environment to run.")
    print("The EditorWidget implementation is ready but cannot be tested in headless mode.")
    sys.exit(1)
