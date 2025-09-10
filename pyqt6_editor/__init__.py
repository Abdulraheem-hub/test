"""PyQt6 Editor - Modern dual-view editor with testable architecture."""

__version__ = "0.1.0"
__author__ = "PyQt6 Editor Team"

from .core import DocumentManager, EditorCore, ViewMode

__all__ = ["DocumentManager", "EditorCore", "ViewMode"]