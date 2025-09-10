"""Main entry point for PyQt6 Editor."""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication

from .gui import MainWindow


def main(argv: Optional[list[str]] = None) -> int:
    """Main application entry point."""
    if argv is None:
        argv = sys.argv
    
    # Create QApplication
    app = QApplication(argv)
    app.setApplicationName("PyQt6 Editor")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("PyQt6 Editor Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())