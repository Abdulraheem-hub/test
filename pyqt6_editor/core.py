"""Core editor logic - GUI-independent classes for testability."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from enum import Enum
from typing import Any, Optional


class ViewMode(Enum):
    """Editor view modes."""

    STYLED = "styled"
    SOURCE = "source"


class DocumentManager:
    """Manages document content and XML operations."""

    def __init__(self) -> None:
        """Initialize document manager."""
        self._content: str = ""
        self._file_path: Optional[str] = None
        self._modified: bool = False

    @property
    def content(self) -> str:
        """Get current document content."""
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        """Set document content and mark as modified."""
        if self._content != value:
            self._content = value
            self._modified = True

    @property
    def file_path(self) -> Optional[str]:
        """Get current file path."""
        return self._file_path

    @property
    def is_modified(self) -> bool:
        """Check if document has been modified."""
        return self._modified

    def set_file_path(self, path: str) -> None:
        """Set the file path."""
        self._file_path = path

    def mark_saved(self) -> None:
        """Mark document as saved (not modified)."""
        self._modified = False

    def load_from_file(self, file_path: str) -> None:
        """Load content from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self._content = f.read()
            self._file_path = file_path
            self._modified = False
        except (OSError, UnicodeDecodeError) as e:
            raise FileLoadError(f"Failed to load file {file_path}: {e}") from e

    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """Save content to file."""
        target_path = file_path or self._file_path
        if not target_path:
            raise FileSaveError("No file path specified")

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(self._content)
            self._file_path = target_path
            self._modified = False
        except OSError as e:
            raise FileSaveError(f"Failed to save file {target_path}: {e}") from e

    def format_xml(self) -> str:
        """Format XML content with proper indentation."""
        if not self._content.strip():
            return self._content

        try:
            # Parse and format XML
            root = ET.fromstring(self._content)
            ET.indent(root, space="  ", level=0)
            return ET.tostring(root, encoding="unicode", xml_declaration=True)
        except ET.ParseError as e:
            raise XMLFormatError(f"Invalid XML content: {e}") from e

    def validate_xml(self) -> tuple[bool, Optional[str]]:
        """Validate XML content."""
        if not self._content.strip():
            return True, None

        try:
            ET.fromstring(self._content)
            return True, None
        except ET.ParseError as e:
            return False, str(e)

    def get_xml_structure(self) -> dict[str, Any]:
        """Get XML structure for styled view."""
        if not self._content.strip():
            return {}

        try:
            root = ET.fromstring(self._content)
            return self._element_to_dict(root)
        except ET.ParseError:
            return {}

    def _element_to_dict(self, element: ET.Element) -> dict[str, Any]:
        """Convert XML element to dictionary representation."""
        result: dict[str, Any] = {
            "tag": element.tag,
            "attributes": dict(element.attrib),
            "text": element.text.strip() if element.text else "",
            "children": [],
        }

        for child in element:
            result["children"].append(self._element_to_dict(child))

        return result


class EditorCore:
    """Core editor functionality coordinator."""

    def __init__(self) -> None:
        """Initialize editor core."""
        self.document_manager = DocumentManager()
        self._current_mode = ViewMode.STYLED
        self._view_mode_callbacks: list[callable] = []

    @property
    def current_mode(self) -> ViewMode:
        """Get current view mode."""
        return self._current_mode

    def set_mode(self, mode: ViewMode) -> None:
        """Set view mode and notify callbacks."""
        if self._current_mode != mode:
            self._current_mode = mode
            self._notify_mode_change()

    def register_mode_change_callback(self, callback: callable) -> None:
        """Register callback for mode changes."""
        self._view_mode_callbacks.append(callback)

    def _notify_mode_change(self) -> None:
        """Notify all registered callbacks of mode change."""
        for callback in self._view_mode_callbacks:
            try:
                callback(self._current_mode)
            except Exception:
                # Silently ignore callback errors to prevent cascading failures
                pass

    def new_document(self) -> None:
        """Create a new document."""
        self.document_manager._content = ""
        self.document_manager._file_path = None
        self.document_manager._modified = False

    def get_display_content(self) -> str:
        """Get content formatted for current view mode."""
        if self._current_mode == ViewMode.SOURCE:
            return self.document_manager.content
        else:
            # For styled view, we'll return the raw content for now
            # GUI components will handle the styling
            return self.document_manager.content

    def can_switch_to_styled(self) -> tuple[bool, Optional[str]]:
        """Check if we can switch to styled view."""
        is_valid, error = self.document_manager.validate_xml()
        if not is_valid:
            return False, f"Invalid XML: {error}"
        return True, None


# Custom exception classes
class EditorError(Exception):
    """Base exception for editor errors."""

    pass


class FileLoadError(EditorError):
    """Exception raised when file loading fails."""

    pass


class FileSaveError(EditorError):
    """Exception raised when file saving fails."""

    pass


class XMLFormatError(EditorError):
    """Exception raised when XML formatting fails."""

    pass