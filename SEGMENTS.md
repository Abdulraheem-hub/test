# Segment Metadata System

This document describes the complete segment metadata system implemented for the PyQt6 Editor.

## Overview

The segment metadata system allows structuring text into segments with various attributes including locking, dynamic content, and special formatting. This enables fine-grained control over editing permissions and content rendering in the styled view.

## Features

### ✅ Segment Attributes

Each segment can have the following attributes:

- **`id`**: Unique identifier for the segment
- **`locked`**: Boolean indicating if the segment can be edited
- **`double_width`**: Boolean for special width formatting
- **`dynamic`**: Object with function name and dependencies for computed values

### ✅ Locked Segment Protection

- **Visual Highlighting**: Locked segments are highlighted with a light gray background
- **Edit Protection**: Keyboard input is blocked for locked segments
- **Delete Protection**: Backspace and delete operations are prevented in locked segments
- **Auto-locking**: Dynamic segments are automatically locked

### ✅ Dynamic Segment Evaluation

- **Function Registration**: Register dynamic functions with the document manager
- **Dependency Tracking**: Functions can specify dependencies on other segments
- **Built-in Functions**: Pre-registered formula functions for common calculations
- **Real-time Updates**: Content updates when dependencies change
- **Error Handling**: Graceful error reporting for invalid functions or data

#### Built-in Formula Functions

**`difference(id1, id2)`**: Calculates numeric difference between two segments
```xml
<!-- SEGMENT: id="result", dynamic="difference:price,discount" -->
<total>{{calculated_difference}}</total>
```

**`digits_to_words(id)`**: Converts each digit of a number to its word representation
```xml
<!-- SEGMENT: id="year_words", dynamic="digits_to_words:year" -->
<year_text>{{digit_words}}</year_text>
```

### ✅ XML Integration

Segments are defined using XML comments in the document:

```xml
<!-- SEGMENT: id="segment_name", locked="true", dynamic="func_name:dep1,dep2" -->
<content>Your content here</content>
```

## Usage Examples

### Basic Locked Segment

```xml
<!-- SEGMENT: id="header", locked="true" -->
<title>This title cannot be edited</title>
```

### Dynamic Segment with Dependencies

```xml
<!-- SEGMENT: id="total", dynamic="difference:price,quantity" -->
<total>{{calculated_difference}}</total>
```

### Formula Function Examples

```xml
<!-- Calculate difference between two numbers -->
<!-- SEGMENT: id="price" -->
<price>100</price>
<!-- SEGMENT: id="discount" -->
<discount>15</discount>
<!-- SEGMENT: id="final_price", dynamic="difference:price,discount" -->
<final_price>{{computed}}</final_price>

<!-- Convert digits to words -->
<!-- SEGMENT: id="year" -->
<year>2024</year>
<!-- SEGMENT: id="year_words", dynamic="digits_to_words:year" -->
<year_words>{{computed}}</year_words>
```

### Double-width Segment

```xml
<!-- SEGMENT: id="wide_content", double_width="true" -->
<display>This content uses double-width formatting</display>
```

### Regular Editable Segment

```xml
<!-- SEGMENT: id="description", locked="false" -->
<description>Users can freely edit this content</description>
```

## API Reference

### Core Classes

#### `SegmentMetadata`
```python
@dataclass
class SegmentMetadata:
    id: str
    locked: bool = False
    double_width: bool = False
    dynamic: DynamicFunction | None = None
```

#### `DynamicFunction`
```python
@dataclass
class DynamicFunction:
    function: str
    deps: list[str]
```

#### `TextSegment`
```python
@dataclass
class TextSegment:
    content: str
    metadata: SegmentMetadata
    start_pos: int = 0
    end_pos: int = 0
```

### DocumentManager Methods

- `get_segment_at_position(position: int) -> TextSegment | None`
- `is_position_locked(position: int) -> bool`
- `register_dynamic_function(name: str, func: Callable) -> None`
- `evaluate_dynamic_segment(segment: TextSegment) -> str`
- `update_segment_content(segment_id: str, new_content: str) -> bool`

### EditorCore Methods

- `can_edit_at_position(position: int) -> bool`
- `get_segments_info() -> list[dict[str, Any]]`

## Implementation Details

### Core Logic (pyqt6_editor/core.py)

- **Segment Data Structures**: New dataclasses for segment metadata
- **XML Comment Parsing**: Regex-based parsing of segment definitions
- **Position-based Validation**: Check edit permissions by document position
- **Dynamic Function Registry**: Register and evaluate dynamic functions

### GUI Integration (pyqt6_editor/gui.py)

- **Visual Highlighting**: QTextEdit.ExtraSelection for locked segments
- **Edit Protection**: Enhanced keyPressEvent handling
- **Real-time Updates**: Automatic segment highlight refresh

### Testing (tests/test_segments.py)

- **31 comprehensive tests** covering all functionality
- **Edge case validation** for XML parsing
- **Position-based testing** for edit protection
- **Dynamic evaluation scenarios**

## Performance

- **Efficient Parsing**: Segments are parsed once when content changes
- **Fast Position Lookup**: O(n) segment lookup where n is number of segments
- **Minimal Overhead**: No performance impact on regular text editing
- **Memory Efficient**: Segments store positions, not duplicate content

## Future Enhancements

- **Enhanced Double-width Rendering**: Visual formatting for double-width segments
- **Additional Formula Functions**: Support for more mathematical operations (sum, multiply, etc.)
- **Complex Expressions**: Support for formula expressions with multiple operations
- **Segment Validation**: Schema validation for segment definitions
- **Export/Import**: Serialize segment metadata to external formats

## Example Integration

```python
from pyqt6_editor.core import EditorCore, ViewMode

# Create editor with segment support
core = EditorCore()

# Load XML with segment metadata
xml_content = '''
<!-- SEGMENT: id="title", locked="true" -->
<title>Protected Title</title>

<!-- SEGMENT: id="total", dynamic="sum:a,b" -->
<total>{{result}}</total>
'''

core.document_manager.content = xml_content

# Register dynamic function
def sum_function():
    return "42"

core.document_manager.register_dynamic_function("sum", sum_function)

# Check editing permissions
can_edit = core.can_edit_at_position(50)  # False if position is locked

# Get segment information for GUI
segments_info = core.get_segments_info()
```

This segment metadata system provides powerful control over content editing while maintaining the clean architecture and testability of the PyQt6 Editor.