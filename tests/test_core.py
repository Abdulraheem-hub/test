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


class TestXEditFormat:
    """Test .xedit file format functionality."""

    def test_save_to_xedit_format(self) -> None:
        """Test saving content to .xedit XML format."""
        dm = DocumentManager()
        test_content = """<!-- SEGMENT: id="title", locked="true" -->
<title>Test Document</title>
<!-- SEGMENT: id="content", locked="false" -->
<content>Some content here</content>"""

        dm.content = test_content

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False) as tmp_file:
            tmp_file_name = tmp_file.name

        try:
            dm.save_to_xedit_file(tmp_file_name)

            # Verify file was created and has XML structure
            with open(tmp_file_name, encoding="utf-8") as f:
                saved_content = f.read()

            # Should be valid XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(saved_content)

            # Check structure
            assert root.tag == "xedit"
            assert root.get("version") == "1.0"

            # Should have metadata and document elements
            assert root.find("metadata") is not None
            document_elem = root.find("document")
            assert document_elem is not None
            assert document_elem.text == test_content

        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

    def test_load_from_xedit_format(self) -> None:
        """Test loading content from .xedit XML format."""
        test_content = """<!-- SEGMENT: id="title", locked="true" -->
<title>Test Document</title>"""

        # Create a valid .xedit file with CDATA
        xedit_xml = f"""<?xml version='1.0' encoding='unicode'?>
<xedit version="1.0">
  <metadata />
  <document><![CDATA[{test_content}]]></document>
</xedit>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(xedit_xml)
            tmp_file.flush()
            tmp_file_name = tmp_file.name

        try:
            dm = DocumentManager()
            dm.load_from_xedit_file(tmp_file_name)

            # Content should be extracted correctly
            assert dm.content == test_content
            assert dm.file_path == tmp_file_name
            assert not dm.is_modified

            # Segments should be parsed
            assert len(dm.segments) == 1
            segment = dm.segments[0]
            assert segment.metadata.id == "title"
            assert segment.metadata.locked is True

        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

    def test_xedit_round_trip(self) -> None:
        """Test save and load round trip maintains content integrity."""
        original_content = """<!-- SEGMENT: id="header", locked="true" -->
<header>Document Header</header>
<!-- SEGMENT: id="body", locked="false", double_width="true" -->
<body>Document body with some content</body>
<!-- SEGMENT: id="total", dynamic="calculate_sum:a,b" -->
<total>{{computed_value}}</total>"""

        dm = DocumentManager()
        dm.content = original_content

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False) as tmp_file:
            tmp_file_name = tmp_file.name

        try:
            # Save to .xedit
            dm.save_to_xedit_file(tmp_file_name)

            # Load from .xedit
            dm2 = DocumentManager()
            dm2.load_from_xedit_file(tmp_file_name)

            # Content should be identical
            assert dm2.content == original_content

            # Segments should be parsed correctly
            assert len(dm2.segments) == 3

            # Check specific segments
            segments_by_id = {seg.metadata.id: seg for seg in dm2.segments}

            assert "header" in segments_by_id
            assert segments_by_id["header"].metadata.locked is True

            assert "body" in segments_by_id
            assert segments_by_id["body"].metadata.locked is False
            assert segments_by_id["body"].metadata.double_width is True

            assert "total" in segments_by_id
            assert segments_by_id["total"].metadata.is_dynamic is True
            assert segments_by_id["total"].metadata.dynamic.function == "calculate_sum"
            assert segments_by_id["total"].metadata.dynamic.deps == ["a", "b"]

        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

    def test_auto_detect_xedit_format_save(self) -> None:
        """Test auto-detection of .xedit format on save."""
        dm = DocumentManager()
        dm.content = "<test>content</test>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False) as tmp_file:
            tmp_file_name = tmp_file.name

        try:
            # Use generic save_to_file, should auto-detect .xedit format
            dm.save_to_file(tmp_file_name)

            # Should create valid .xedit XML
            with open(tmp_file_name, encoding="utf-8") as f:
                content = f.read()

            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            assert root.tag == "xedit"

        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

    def test_auto_detect_xedit_format_load(self) -> None:
        """Test auto-detection of .xedit format on load."""
        test_content = "<test>content</test>"
        xedit_xml = f"""<?xml version='1.0' encoding='unicode'?>
<xedit version="1.0">
  <metadata />
  <document><![CDATA[{test_content}]]></document>
</xedit>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(xedit_xml)
            tmp_file.flush()
            tmp_file_name = tmp_file.name

        try:
            dm = DocumentManager()
            # Use generic load_from_file, should auto-detect .xedit format
            dm.load_from_file(tmp_file_name)

            assert dm.content == test_content

        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

    def test_load_invalid_xedit_file(self) -> None:
        """Test loading invalid .xedit file raises appropriate error."""
        # Test 1: Invalid XML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write("not valid xml")
            tmp_file.flush()
            tmp_file_name = tmp_file.name

        try:
            dm = DocumentManager()
            with pytest.raises(FileLoadError, match="Failed to load .xedit file"):
                dm.load_from_xedit_file(tmp_file_name)
        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

        # Test 2: Wrong root element
        invalid_xml = """<?xml version='1.0' encoding='unicode'?>
<wrong_root>
  <document>content</document>
</wrong_root>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(invalid_xml)
            tmp_file.flush()
            tmp_file_name = tmp_file.name

        try:
            dm = DocumentManager()
            with pytest.raises(FileLoadError, match="root element must be 'xedit'"):
                dm.load_from_xedit_file(tmp_file_name)
        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)

        # Test 3: Missing document element
        invalid_xml = """<?xml version='1.0' encoding='unicode'?>
<xedit version="1.0">
  <metadata />
</xedit>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xedit", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(invalid_xml)
            tmp_file.flush()
            tmp_file_name = tmp_file.name

        try:
            dm = DocumentManager()
            with pytest.raises(FileLoadError, match="missing 'document' element"):
                dm.load_from_xedit_file(tmp_file_name)
        finally:
            if os.path.exists(tmp_file_name):
                os.unlink(tmp_file_name)
