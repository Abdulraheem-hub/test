"""Core editor logic - GUI-independent classes for testability."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ViewMode(Enum):
    """Editor view modes."""

    STYLED = "styled"
    SOURCE = "source"


@dataclass
class DynamicFunction:
    """Represents a dynamic function with dependencies."""

    function: str
    deps: list[str]


@dataclass
class SegmentMetadata:
    """Metadata for a text segment."""

    id: str
    locked: bool = False
    double_width: bool = False
    dynamic: DynamicFunction | None = None

    @property
    def is_dynamic(self) -> bool:
        """Check if segment is dynamic."""
        return self.dynamic is not None

    @property
    def is_locked(self) -> bool:
        """Check if segment is locked (either explicitly or because it's dynamic)."""
        return self.locked or self.is_dynamic


@dataclass
class TextSegment:
    """Represents a text segment with content and metadata."""

    content: str
    metadata: SegmentMetadata
    start_pos: int = 0
    end_pos: int = 0

    def __post_init__(self) -> None:
        """Update positions based on content if not set."""
        if self.end_pos == 0:
            self.end_pos = self.start_pos + len(self.content)


class DocumentManager:
    """Manages document content and XML operations."""

    def __init__(self) -> None:
        """Initialize document manager."""
        self._content: str = ""
        self._file_path: str | None = None
        self._modified: bool = False
        self._segments: list[TextSegment] = []
        self._dynamic_functions: dict[str, Callable] = {}

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
            # Re-parse segments when content changes
            self._parse_segments()

    @property
    def file_path(self) -> str | None:
        """Get current file path."""
        return self._file_path

    @property
    def is_modified(self) -> bool:
        """Check if document has been modified."""
        return self._modified

    @property
    def segments(self) -> list[TextSegment]:
        """Get document segments."""
        return self._segments.copy()

    def set_file_path(self, path: str) -> None:
        """Set the file path."""
        self._file_path = path

    def mark_saved(self) -> None:
        """Mark document as saved (not modified)."""
        self._modified = False

    def load_from_file(self, file_path: str) -> None:
        """Load content from file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                self._content = f.read()
            self._file_path = file_path
            self._modified = False
            self._parse_segments()
        except (OSError, UnicodeDecodeError) as e:
            raise FileLoadError(f"Failed to load file {file_path}: {e}") from e

    def save_to_file(self, file_path: str | None = None) -> None:
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

    def validate_xml(self) -> tuple[bool, str | None]:
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

    def _parse_segments(self) -> None:
        """Parse content to extract segments with metadata."""
        self._segments.clear()

        if not self._content.strip():
            return

        # Try to parse segment metadata from XML comments
        # Look for comments like: <!-- SEGMENT: id="seg1", locked=true, dynamic="func:deps" -->
        import re

        segments_found = []
        segment_pattern = r'<!--\s*SEGMENT:\s*([^>]+)\s*-->'

        # Find all segment declarations
        for match in re.finditer(segment_pattern, self._content):
            segment_def = match.group(1)
            metadata = self._parse_segment_definition(segment_def)
            if metadata:
                segments_found.append((match.end(), metadata))

        if not segments_found:
            # No explicit segments found, create default segment for entire content
            self._create_default_segment()
        else:
            # Create segments based on the found metadata
            self._create_segments_from_metadata(segments_found)

    def _parse_segment_definition(self, segment_def: str) -> SegmentMetadata | None:
        """Parse segment definition from comment text."""
        import re

        # Parse attributes: id="value", locked=true, etc.
        attr_pattern = r'(\w+)=["\'](.*?)["\']'
        attrs = dict(re.findall(attr_pattern, segment_def))

        if 'id' not in attrs:
            return None

        # Parse attributes
        segment_id = attrs['id']
        locked = attrs.get('locked', 'false').lower() == 'true'
        double_width = attrs.get('double_width', 'false').lower() == 'true'

        # Parse dynamic function
        dynamic = None
        if 'dynamic' in attrs:
            dynamic_def = attrs['dynamic']
            if ':' in dynamic_def:
                func_name, deps_str = dynamic_def.split(':', 1)
                deps = [dep.strip() for dep in deps_str.split(',') if dep.strip()]
            else:
                func_name = dynamic_def
                deps = []
            dynamic = DynamicFunction(function=func_name, deps=deps)

        return SegmentMetadata(
            id=segment_id,
            locked=locked,
            double_width=double_width,
            dynamic=dynamic
        )

    def _create_default_segment(self) -> None:
        """Create a single default segment for all content."""
        segment_id = "default_segment"
        metadata = SegmentMetadata(id=segment_id)
        segment = TextSegment(
            content=self._content,
            metadata=metadata,
            start_pos=0,
            end_pos=len(self._content)
        )
        self._segments.append(segment)

    def _create_segments_from_metadata(self, segments_found: list[tuple[int, SegmentMetadata]]) -> None:
        """Create segments from parsed metadata."""
        for i, (comment_end_pos, metadata) in enumerate(segments_found):
            # Find the end of current segment (next segment comment or end of content)
            if i + 1 < len(segments_found):
                next_comment_start = self._content.find('<!-- SEGMENT:', comment_end_pos)
                segment_end = next_comment_start if next_comment_start != -1 else len(self._content)
            else:
                segment_end = len(self._content)

            # Extract segment content (excluding the comment itself)
            segment_content = self._content[comment_end_pos:segment_end].strip()

            if segment_content:
                segment = TextSegment(
                    content=segment_content,
                    metadata=metadata,
                    start_pos=comment_end_pos,
                    end_pos=segment_end
                )
                self._segments.append(segment)

    def get_segment_at_position(self, position: int) -> TextSegment | None:
        """Get the segment at the given position in the document."""
        for segment in self._segments:
            if segment.start_pos <= position < segment.end_pos:
                return segment
        return None

    def is_position_locked(self, position: int) -> bool:
        """Check if a position in the document is locked."""
        segment = self.get_segment_at_position(position)
        return segment.metadata.is_locked if segment else False

    def register_dynamic_function(self, name: str, func: Callable) -> None:
        """Register a dynamic function for use in segments."""
        self._dynamic_functions[name] = func

    def evaluate_dynamic_segment(self, segment: TextSegment) -> str:
        """Evaluate a dynamic segment and return its computed content."""
        if not segment.metadata.is_dynamic or not segment.metadata.dynamic:
            return segment.content

        # For now, return the original content
        # This would be enhanced to actually evaluate the function
        return f"[DYNAMIC: {segment.metadata.dynamic.function}]"

    def update_segment_content(self, segment_id: str, new_content: str) -> bool:
        """Update content of a segment if it's not locked."""
        for segment in self._segments:
            if segment.metadata.id == segment_id:
                if segment.metadata.is_locked:
                    return False
                segment.content = new_content
                # Update document content - simplified for now
                self._modified = True
                return True
        return False


class EditorCore:
    """Core editor functionality coordinator."""

    def __init__(self) -> None:
        """Initialize editor core."""
        self.document_manager = DocumentManager()
        self._current_mode = ViewMode.STYLED
        self._view_mode_callbacks: list[callable] = []
        self._grid_visible = False
        self._grid_callbacks: list[callable] = []

    @property
    def current_mode(self) -> ViewMode:
        """Get current view mode."""
        return self._current_mode

    @property
    def grid_visible(self) -> bool:
        """Get grid visibility state."""
        return self._grid_visible

    def set_mode(self, mode: ViewMode) -> None:
        """Set view mode and notify callbacks."""
        if self._current_mode != mode:
            self._current_mode = mode
            self._notify_mode_change()

    def register_mode_change_callback(self, callback: callable) -> None:
        """Register callback for mode changes."""
        self._view_mode_callbacks.append(callback)

    def register_grid_change_callback(self, callback: callable) -> None:
        """Register callback for grid visibility changes."""
        self._grid_callbacks.append(callback)

    def toggle_grid(self) -> None:
        """Toggle grid visibility."""
        self._grid_visible = not self._grid_visible
        self._notify_grid_change()

    def _notify_mode_change(self) -> None:
        """Notify all registered callbacks of mode change."""
        for callback in self._view_mode_callbacks:
            try:
                callback(self._current_mode)
            except Exception:
                # Silently ignore callback errors to prevent cascading failures
                pass

    def _notify_grid_change(self) -> None:
        """Notify all registered callbacks of grid visibility change."""
        for callback in self._grid_callbacks:
            try:
                callback(self._grid_visible)
            except Exception:
                # Silently ignore callback errors to prevent cascading failures
                pass

    def new_document(self) -> None:
        """Create a new document."""
        self.document_manager._content = ""
        self.document_manager._file_path = None
        self.document_manager._modified = False
        self.document_manager._segments.clear()

    def get_display_content(self) -> str:
        """Get content formatted for current view mode."""
        if self._current_mode == ViewMode.SOURCE:
            return self.document_manager.content
        else:
            # For styled view, process segments and apply dynamic content
            return self._get_styled_content()

    def _get_styled_content(self) -> str:
        """Get content for styled view with segment processing."""
        if not self.document_manager.segments:
            return self.document_manager.content

        # Process dynamic segments
        processed_content = ""
        for segment in self.document_manager.segments:
            if segment.metadata.is_dynamic:
                processed_content += self.document_manager.evaluate_dynamic_segment(segment)
            else:
                processed_content += segment.content

        return processed_content

    def can_edit_at_position(self, position: int) -> bool:
        """Check if editing is allowed at the given position."""
        return not self.document_manager.is_position_locked(position)

    def get_segments_info(self) -> list[dict[str, Any]]:
        """Get information about all segments for GUI rendering."""
        segments_info = []
        for segment in self.document_manager.segments:
            segments_info.append({
                "id": segment.metadata.id,
                "start_pos": segment.start_pos,
                "end_pos": segment.end_pos,
                "is_locked": segment.metadata.is_locked,
                "is_dynamic": segment.metadata.is_dynamic,
                "double_width": segment.metadata.double_width,
                "content": segment.content
            })
        return segments_info

    def can_switch_to_styled(self) -> tuple[bool, str | None]:
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
