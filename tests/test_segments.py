"""Tests for segment metadata functionality."""

from __future__ import annotations

from pyqt6_editor.core import (
    DocumentManager,
    DynamicFunction,
    EditorCore,
    SegmentMetadata,
    TextSegment,
    ViewMode,
)


class TestSegmentMetadata:
    """Test SegmentMetadata class."""

    def test_init_defaults(self) -> None:
        """Test SegmentMetadata initialization with defaults."""
        metadata = SegmentMetadata(id="test_segment")
        assert metadata.id == "test_segment"
        assert metadata.locked is False
        assert metadata.double_width is False
        assert metadata.dynamic is None

    def test_init_with_values(self) -> None:
        """Test SegmentMetadata initialization with specific values."""
        dynamic_func = DynamicFunction(function="test_func", deps=["dep1", "dep2"])
        metadata = SegmentMetadata(
            id="test_segment",
            locked=True,
            double_width=True,
            dynamic=dynamic_func
        )
        assert metadata.id == "test_segment"
        assert metadata.locked is True
        assert metadata.double_width is True
        assert metadata.dynamic == dynamic_func

    def test_is_dynamic_property(self) -> None:
        """Test is_dynamic property."""
        # Not dynamic
        metadata = SegmentMetadata(id="test")
        assert metadata.is_dynamic is False

        # Dynamic
        dynamic_func = DynamicFunction(function="test_func", deps=[])
        metadata.dynamic = dynamic_func
        assert metadata.is_dynamic is True

    def test_is_locked_property(self) -> None:
        """Test is_locked property."""
        # Not locked, not dynamic
        metadata = SegmentMetadata(id="test")
        assert metadata.is_locked is False

        # Explicitly locked
        metadata.locked = True
        assert metadata.is_locked is True

        # Reset and test dynamic locking
        metadata.locked = False
        dynamic_func = DynamicFunction(function="test_func", deps=[])
        metadata.dynamic = dynamic_func
        assert metadata.is_locked is True  # Dynamic segments are always locked


class TestDynamicFunction:
    """Test DynamicFunction class."""

    def test_init(self) -> None:
        """Test DynamicFunction initialization."""
        func = DynamicFunction(function="calculate", deps=["field1", "field2"])
        assert func.function == "calculate"
        assert func.deps == ["field1", "field2"]

    def test_empty_deps(self) -> None:
        """Test DynamicFunction with empty dependencies."""
        func = DynamicFunction(function="static_value", deps=[])
        assert func.function == "static_value"
        assert func.deps == []


class TestTextSegment:
    """Test TextSegment class."""

    def test_init_basic(self) -> None:
        """Test TextSegment basic initialization."""
        metadata = SegmentMetadata(id="test")
        segment = TextSegment(content="Hello World", metadata=metadata)

        assert segment.content == "Hello World"
        assert segment.metadata == metadata
        assert segment.start_pos == 0
        assert segment.end_pos == 11  # Auto-calculated from content length

    def test_init_with_positions(self) -> None:
        """Test TextSegment initialization with explicit positions."""
        metadata = SegmentMetadata(id="test")
        segment = TextSegment(
            content="Hello",
            metadata=metadata,
            start_pos=10,
            end_pos=15
        )

        assert segment.start_pos == 10
        assert segment.end_pos == 15

    def test_post_init_position_calculation(self) -> None:
        """Test automatic position calculation in __post_init__."""
        metadata = SegmentMetadata(id="test")
        segment = TextSegment(content="Test", metadata=metadata, start_pos=5)

        assert segment.start_pos == 5
        assert segment.end_pos == 9  # 5 + len("Test")


class TestDocumentManagerSegments:
    """Test DocumentManager segment functionality."""

    def test_init_segments(self) -> None:
        """Test DocumentManager initializes with empty segments."""
        dm = DocumentManager()
        assert dm.segments == []

    def test_content_setter_triggers_parsing(self) -> None:
        """Test that setting content triggers segment parsing."""
        dm = DocumentManager()
        dm.content = "Hello World"

        # Should have created a default segment
        segments = dm.segments
        assert len(segments) == 1
        assert segments[0].content == "Hello World"
        assert segments[0].metadata.id == "default_segment"

    def test_empty_content_no_segments(self) -> None:
        """Test that empty content creates no segments."""
        dm = DocumentManager()
        dm.content = ""
        assert dm.segments == []

        dm.content = "   "  # Whitespace only
        assert dm.segments == []

    def test_get_segment_at_position(self) -> None:
        """Test getting segment at specific position."""
        dm = DocumentManager()
        dm.content = "Hello World"

        # Position within segment
        segment = dm.get_segment_at_position(5)
        assert segment is not None
        assert segment.metadata.id == "default_segment"

        # Position at start
        segment = dm.get_segment_at_position(0)
        assert segment is not None

        # Position at end (should not match)
        segment = dm.get_segment_at_position(11)
        assert segment is None

        # Position beyond content
        segment = dm.get_segment_at_position(20)
        assert segment is None

    def test_is_position_locked(self) -> None:
        """Test checking if position is locked."""
        dm = DocumentManager()
        dm.content = "Hello World"

        # Default segment is not locked
        assert dm.is_position_locked(5) is False

        # Position outside segments is not locked
        assert dm.is_position_locked(20) is False

    def test_register_dynamic_function(self) -> None:
        """Test registering dynamic functions."""
        dm = DocumentManager()

        def test_func():
            return "test_result"

        dm.register_dynamic_function("test_func", test_func)
        assert "test_func" in dm._dynamic_functions
        assert dm._dynamic_functions["test_func"] == test_func

    def test_evaluate_dynamic_segment(self) -> None:
        """Test evaluating dynamic segments."""
        dm = DocumentManager()

        # Non-dynamic segment
        metadata = SegmentMetadata(id="normal")
        segment = TextSegment(content="Normal text", metadata=metadata)
        result = dm.evaluate_dynamic_segment(segment)
        assert result == "Normal text"

        # Dynamic segment
        dynamic_func = DynamicFunction(function="test_func", deps=[])
        metadata = SegmentMetadata(id="dynamic", dynamic=dynamic_func)
        segment = TextSegment(content="Original", metadata=metadata)
        result = dm.evaluate_dynamic_segment(segment)
        assert result == "[DYNAMIC: test_func]"

    def test_update_segment_content(self) -> None:
        """Test updating segment content."""
        dm = DocumentManager()
        dm.content = "Hello World"

        # Update unlocked segment should succeed
        success = dm.update_segment_content("default_segment", "New content")
        assert success is True
        assert dm.is_modified is True

        # Try to update non-existent segment
        success = dm.update_segment_content("non_existent", "Content")
        assert success is False

    def test_update_locked_segment_content(self) -> None:
        """Test that locked segments cannot be updated."""
        dm = DocumentManager()

        # Create a locked segment manually
        metadata = SegmentMetadata(id="locked_segment", locked=True)
        segment = TextSegment(content="Locked content", metadata=metadata)
        dm._segments = [segment]

        # Try to update locked segment should fail
        success = dm.update_segment_content("locked_segment", "New content")
        assert success is False


class TestEditorCoreSegments:
    """Test EditorCore segment functionality."""

    def test_new_document_clears_segments(self) -> None:
        """Test that new document clears segments."""
        core = EditorCore()
        core.document_manager.content = "Test content"
        assert len(core.document_manager.segments) == 1

        core.new_document()
        assert len(core.document_manager.segments) == 0

    def test_get_styled_content_no_segments(self) -> None:
        """Test getting styled content with no segments."""
        core = EditorCore()
        core.set_mode(ViewMode.STYLED)
        core.document_manager.content = ""

        content = core.get_display_content()
        assert content == ""

    def test_get_styled_content_with_segments(self) -> None:
        """Test getting styled content with segments."""
        core = EditorCore()
        core.set_mode(ViewMode.STYLED)
        core.document_manager.content = "Hello World"

        content = core.get_display_content()
        assert content == "Hello World"

    def test_get_source_content(self) -> None:
        """Test getting source content (unchanged behavior)."""
        core = EditorCore()
        core.set_mode(ViewMode.SOURCE)
        core.document_manager.content = "Hello World"

        content = core.get_display_content()
        assert content == "Hello World"

    def test_can_edit_at_position(self) -> None:
        """Test checking edit permissions at position."""
        core = EditorCore()
        core.document_manager.content = "Hello World"

        # Normal position should be editable
        assert core.can_edit_at_position(5) is True

        # Position outside content should be editable
        assert core.can_edit_at_position(20) is True

    def test_get_segments_info(self) -> None:
        """Test getting segment information for GUI."""
        core = EditorCore()
        core.document_manager.content = "Hello World"

        segments_info = core.get_segments_info()
        assert len(segments_info) == 1

        info = segments_info[0]
        assert info["id"] == "default_segment"
        assert info["start_pos"] == 0
        assert info["end_pos"] == 11
        assert info["is_locked"] is False
        assert info["is_dynamic"] is False
        assert info["double_width"] is False
        assert info["content"] == "Hello World"

    def test_get_segments_info_empty(self) -> None:
        """Test getting segment information with no segments."""
        core = EditorCore()
        core.document_manager.content = ""

        segments_info = core.get_segments_info()
        assert segments_info == []


class TestSegmentParsing:
    """Test segment parsing from XML comments."""

    def test_parse_simple_segment_comment(self) -> None:
        """Test parsing a simple segment comment."""
        dm = DocumentManager()

        # Test with simple segment comment
        content = '''<!-- SEGMENT: id="test_segment", locked="true" -->
<element>Content here</element>'''

        dm.content = content
        segments = dm.segments

        assert len(segments) == 1
        assert segments[0].metadata.id == "test_segment"
        assert segments[0].metadata.locked is True
        assert segments[0].metadata.double_width is False
        assert segments[0].metadata.dynamic is None

    def test_parse_dynamic_segment_comment(self) -> None:
        """Test parsing a dynamic segment comment."""
        dm = DocumentManager()

        content = '''<!-- SEGMENT: id="dynamic_seg", dynamic="calc_func:dep1,dep2" -->
<value>{{result}}</value>'''

        dm.content = content
        segments = dm.segments

        assert len(segments) == 1
        segment = segments[0]
        assert segment.metadata.id == "dynamic_seg"
        assert segment.metadata.is_dynamic is True
        assert segment.metadata.is_locked is True  # Dynamic segments are auto-locked
        assert segment.metadata.dynamic.function == "calc_func"
        assert segment.metadata.dynamic.deps == ["dep1", "dep2"]

    def test_parse_multiple_segments(self) -> None:
        """Test parsing multiple segments."""
        dm = DocumentManager()

        content = '''<!-- SEGMENT: id="seg1", locked="true" -->
<title>Locked Title</title>

<!-- SEGMENT: id="seg2", double_width="true" -->
<content>Wide content</content>

<!-- SEGMENT: id="seg3", dynamic="compute:field1" -->
<result>{{value}}</result>'''

        dm.content = content
        segments = dm.segments

        assert len(segments) == 3

        # Check first segment
        assert segments[0].metadata.id == "seg1"
        assert segments[0].metadata.locked is True

        # Check second segment
        assert segments[1].metadata.id == "seg2"
        assert segments[1].metadata.double_width is True

        # Check third segment
        assert segments[2].metadata.id == "seg3"
        assert segments[2].metadata.is_dynamic is True

    def test_parse_no_segments_fallback(self) -> None:
        """Test fallback to default segment when no segment comments found."""
        dm = DocumentManager()

        content = '''<document>
<title>Regular XML without segment comments</title>
<content>Some content here</content>
</document>'''

        dm.content = content
        segments = dm.segments

        assert len(segments) == 1
        assert segments[0].metadata.id == "default_segment"
        assert segments[0].metadata.locked is False
        assert segments[0].content == content

    def test_parse_segment_definition_parsing(self) -> None:
        """Test the segment definition parsing logic."""
        dm = DocumentManager()

        # Test various attribute combinations
        test_cases = [
            ('id="test"', {"id": "test"}),
            ('id="test", locked="true"', {"id": "test", "locked": "true"}),
            ('id="test", double_width="true", locked="false"',
             {"id": "test", "double_width": "true", "locked": "false"}),
            ('id="dyn", dynamic="func:dep1,dep2"',
             {"id": "dyn", "dynamic": "func:dep1,dep2"}),
        ]

        for definition, expected_attrs in test_cases:
            metadata = dm._parse_segment_definition(definition)
            assert metadata is not None
            assert metadata.id == expected_attrs["id"]

            if "locked" in expected_attrs:
                assert metadata.locked == (expected_attrs["locked"] == "true")

            if "double_width" in expected_attrs:
                assert metadata.double_width == (expected_attrs["double_width"] == "true")

            if "dynamic" in expected_attrs:
                assert metadata.dynamic is not None
                dynamic_def = expected_attrs["dynamic"]
                if ":" in dynamic_def:
                    func_name, deps_str = dynamic_def.split(":", 1)
                    expected_deps = [dep.strip() for dep in deps_str.split(",")]
                    assert metadata.dynamic.function == func_name
                    assert metadata.dynamic.deps == expected_deps

    def test_parse_invalid_segment_definition(self) -> None:
        """Test parsing invalid segment definitions."""
        dm = DocumentManager()

        # Test missing id
        metadata = dm._parse_segment_definition('locked="true"')
        assert metadata is None

        # Test empty definition
        metadata = dm._parse_segment_definition('')
        assert metadata is None
