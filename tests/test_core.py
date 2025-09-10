"""Tests for core editor logic."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import Mock

import pytest

from pyqt6_editor.core import (
    DocumentManager,
    EditorCore,
    FileLoadError,
    FileSaveError,
    ViewMode,
    XMLFormatError,
)


class TestDocumentManager:
    """Test DocumentManager class."""

    def test_init(self) -> None:
        """Test DocumentManager initialization."""
        dm = DocumentManager()
        assert dm.content == ""
        assert dm.file_path is None
        assert not dm.is_modified

    def test_content_property(self) -> None:
        """Test content property getter and setter."""
        dm = DocumentManager()

        # Setting content should mark as modified
        dm.content = "test content"
        assert dm.content == "test content"
        assert dm.is_modified

        # Setting same content should not mark as modified again
        dm._modified = False
        dm.content = "test content"
        assert not dm.is_modified

        # Setting different content should mark as modified
        dm.content = "new content"
        assert dm.is_modified

    def test_file_path_operations(self) -> None:
        """Test file path operations."""
        dm = DocumentManager()

        assert dm.file_path is None

        dm.set_file_path("/test/path.xml")
        assert dm.file_path == "/test/path.xml"

    def test_mark_saved(self) -> None:
        """Test mark_saved functionality."""
        dm = DocumentManager()
        dm.content = "test"
        assert dm.is_modified

        dm.mark_saved()
        assert not dm.is_modified

    def test_load_from_file(self) -> None:
        """Test loading content from file."""
        dm = DocumentManager()

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("<root>test content</root>")
            temp_path = f.name

        try:
            dm.load_from_file(temp_path)
            assert dm.content == "<root>test content</root>"
            assert dm.file_path == temp_path
            assert not dm.is_modified
        finally:
            os.unlink(temp_path)

    def test_load_from_nonexistent_file(self) -> None:
        """Test loading from non-existent file."""
        dm = DocumentManager()

        with pytest.raises(FileLoadError):
            dm.load_from_file("/nonexistent/file.xml")

    def test_save_to_file(self) -> None:
        """Test saving content to file."""
        dm = DocumentManager()
        dm.content = "<root>test save</root>"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            temp_path = f.name

        try:
            dm.save_to_file(temp_path)

            # Check file was saved correctly
            with open(temp_path) as f:
                saved_content = f.read()
            assert saved_content == "<root>test save</root>"
            assert dm.file_path == temp_path
            assert not dm.is_modified
        finally:
            os.unlink(temp_path)

    def test_save_without_path(self) -> None:
        """Test saving without specifying path."""
        dm = DocumentManager()
        dm.content = "test"

        with pytest.raises(FileSaveError):
            dm.save_to_file()

    def test_save_with_existing_path(self) -> None:
        """Test saving with existing file path."""
        dm = DocumentManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            temp_path = f.name

        try:
            dm.set_file_path(temp_path)
            dm.content = "<root>test existing path</root>"

            # Save without specifying path (should use existing path)
            dm.save_to_file()

            with open(temp_path) as f:
                saved_content = f.read()
            assert saved_content == "<root>test existing path</root>"
        finally:
            os.unlink(temp_path)

    def test_format_xml_valid(self) -> None:
        """Test XML formatting with valid XML."""
        dm = DocumentManager()
        dm.content = "<root><child>content</child></root>"

        formatted = dm.format_xml()
        assert "<?xml version='1.0' encoding='utf-8'?>" in formatted
        assert "<root>" in formatted
        assert "<child>content</child>" in formatted

    def test_format_xml_empty(self) -> None:
        """Test XML formatting with empty content."""
        dm = DocumentManager()
        dm.content = ""

        formatted = dm.format_xml()
        assert formatted == ""

    def test_format_xml_invalid(self) -> None:
        """Test XML formatting with invalid XML."""
        dm = DocumentManager()
        dm.content = "<root><unclosed>"

        with pytest.raises(XMLFormatError):
            dm.format_xml()

    def test_validate_xml_valid(self) -> None:
        """Test XML validation with valid XML."""
        dm = DocumentManager()
        dm.content = "<root><child>content</child></root>"

        is_valid, error = dm.validate_xml()
        assert is_valid
        assert error is None

    def test_validate_xml_empty(self) -> None:
        """Test XML validation with empty content."""
        dm = DocumentManager()
        dm.content = ""

        is_valid, error = dm.validate_xml()
        assert is_valid
        assert error is None

    def test_validate_xml_invalid(self) -> None:
        """Test XML validation with invalid XML."""
        dm = DocumentManager()
        dm.content = "<root><unclosed>"

        is_valid, error = dm.validate_xml()
        assert not is_valid
        assert error is not None
        assert "element" in error.lower() or "found" in error.lower()

    def test_get_xml_structure_valid(self) -> None:
        """Test getting XML structure from valid XML."""
        dm = DocumentManager()
        dm.content = '<root attr="value"><child>text</child></root>'

        structure = dm.get_xml_structure()
        assert structure["tag"] == "root"
        assert structure["attributes"] == {"attr": "value"}
        assert len(structure["children"]) == 1
        assert structure["children"][0]["tag"] == "child"
        assert structure["children"][0]["text"] == "text"

    def test_get_xml_structure_empty(self) -> None:
        """Test getting XML structure from empty content."""
        dm = DocumentManager()
        dm.content = ""

        structure = dm.get_xml_structure()
        assert structure == {}

    def test_get_xml_structure_invalid(self) -> None:
        """Test getting XML structure from invalid XML."""
        dm = DocumentManager()
        dm.content = "<root><unclosed>"

        structure = dm.get_xml_structure()
        assert structure == {}


class TestEditorCore:
    """Test EditorCore class."""

    def test_init(self) -> None:
        """Test EditorCore initialization."""
        core = EditorCore()
        assert isinstance(core.document_manager, DocumentManager)
        assert core.current_mode == ViewMode.STYLED
        assert len(core._view_mode_callbacks) == 0

    def test_set_mode(self) -> None:
        """Test setting view mode."""
        core = EditorCore()

        # Mock callback
        callback = Mock()
        core.register_mode_change_callback(callback)

        # Change mode
        core.set_mode(ViewMode.SOURCE)
        assert core.current_mode == ViewMode.SOURCE
        callback.assert_called_once_with(ViewMode.SOURCE)

        # Setting same mode shouldn't trigger callback
        callback.reset_mock()
        core.set_mode(ViewMode.SOURCE)
        callback.assert_not_called()

    def test_mode_change_callbacks(self) -> None:
        """Test mode change callback system."""
        core = EditorCore()

        # Multiple callbacks
        callback1 = Mock()
        callback2 = Mock()
        core.register_mode_change_callback(callback1)
        core.register_mode_change_callback(callback2)

        core.set_mode(ViewMode.SOURCE)

        callback1.assert_called_once_with(ViewMode.SOURCE)
        callback2.assert_called_once_with(ViewMode.SOURCE)

    def test_mode_change_callback_error_handling(self) -> None:
        """Test that callback errors don't break mode switching."""
        core = EditorCore()

        # Callback that raises exception
        def error_callback(mode):
            raise Exception("Callback error")

        # Normal callback
        normal_callback = Mock()

        core.register_mode_change_callback(error_callback)
        core.register_mode_change_callback(normal_callback)

        # Mode change should succeed despite error in first callback
        core.set_mode(ViewMode.SOURCE)
        assert core.current_mode == ViewMode.SOURCE
        normal_callback.assert_called_once_with(ViewMode.SOURCE)

    def test_new_document(self) -> None:
        """Test creating new document."""
        core = EditorCore()

        # Set some initial state
        core.document_manager.content = "existing content"
        core.document_manager.set_file_path("/some/path.xml")
        core.document_manager._modified = True

        # Create new document
        core.new_document()

        assert core.document_manager.content == ""
        assert core.document_manager.file_path is None
        assert not core.document_manager.is_modified

    def test_get_display_content_styled(self) -> None:
        """Test getting display content in styled mode."""
        core = EditorCore()
        core.document_manager.content = "<root>test</root>"
        core.set_mode(ViewMode.STYLED)

        content = core.get_display_content()
        assert content == "<root>test</root>"

    def test_get_display_content_source(self) -> None:
        """Test getting display content in source mode."""
        core = EditorCore()
        core.document_manager.content = "<root>test</root>"
        core.set_mode(ViewMode.SOURCE)

        content = core.get_display_content()
        assert content == "<root>test</root>"

    def test_can_switch_to_styled_valid_xml(self) -> None:
        """Test switching to styled view with valid XML."""
        core = EditorCore()
        core.document_manager.content = "<root><child>content</child></root>"

        can_switch, error = core.can_switch_to_styled()
        assert can_switch
        assert error is None

    def test_can_switch_to_styled_invalid_xml(self) -> None:
        """Test switching to styled view with invalid XML."""
        core = EditorCore()
        core.document_manager.content = "<root><unclosed>"

        can_switch, error = core.can_switch_to_styled()
        assert not can_switch
        assert error is not None
        assert "Invalid XML" in error

    def test_can_switch_to_styled_empty_content(self) -> None:
        """Test switching to styled view with empty content."""
        core = EditorCore()
        core.document_manager.content = ""

        can_switch, error = core.can_switch_to_styled()
        assert can_switch
        assert error is None

    def test_grid_visibility_initial_state(self) -> None:
        """Test initial grid visibility state."""
        core = EditorCore()
        assert core.grid_visible is False

    def test_toggle_grid(self) -> None:
        """Test grid toggle functionality."""
        core = EditorCore()

        # Initially should be False
        assert core.grid_visible is False

        # Toggle to True
        core.toggle_grid()
        assert core.grid_visible is True

        # Toggle back to False
        core.toggle_grid()
        assert core.grid_visible is False

    def test_grid_change_callbacks(self) -> None:
        """Test grid change callback functionality."""
        core = EditorCore()
        callback1 = Mock()
        callback2 = Mock()

        core.register_grid_change_callback(callback1)
        core.register_grid_change_callback(callback2)

        # Toggle grid - should trigger callbacks
        core.toggle_grid()

        callback1.assert_called_once_with(True)
        callback2.assert_called_once_with(True)

        # Reset mocks
        callback1.reset_mock()
        callback2.reset_mock()

        # Toggle again - should trigger callbacks again
        core.toggle_grid()

        callback1.assert_called_once_with(False)
        callback2.assert_called_once_with(False)

    def test_grid_change_callback_error_handling(self) -> None:
        """Test grid change callback error handling."""
        core = EditorCore()

        # Callback that raises exception
        def error_callback(visible):
            raise Exception("Callback error")

        # Normal callback
        normal_callback = Mock()

        core.register_grid_change_callback(error_callback)
        core.register_grid_change_callback(normal_callback)

        # Grid toggle should succeed despite error in first callback
        core.toggle_grid()
        assert core.grid_visible is True
        normal_callback.assert_called_once_with(True)


class TestViewMode:
    """Test ViewMode enum."""

    def test_view_mode_values(self) -> None:
        """Test ViewMode enum values."""
        assert ViewMode.STYLED.value == "styled"
        assert ViewMode.SOURCE.value == "source"

        # Test enum comparison
        assert ViewMode.STYLED != ViewMode.SOURCE
        assert ViewMode.STYLED == ViewMode.STYLED
