# PyQt6 Editor

PyQt6 Editor is a modern dual-view editor application built with PyQt6, featuring testable architecture with GUI-independent core logic, XML support with syntax highlighting and validation, and contemporary Python development standards.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test the Repository

```bash
# REQUIRED: Install uv package manager first (if not available)
pip install uv

# Install all dependencies - NEVER CANCEL: Takes 1-2 minutes. Set timeout to 180+ seconds.
uv sync

# Install development dependencies for linting and type checking
uv add --dev ruff mypy pytest-cov
```

### Running Tests - NEVER CANCEL: All tests complete in under 1 second

```bash
# Run all tests (33 tests, ~0.6 seconds)
uv run pytest

# Run only core logic tests (29 tests, ~0.3 seconds, no GUI required)
uv run pytest tests/test_core.py

# Run non-GUI tests only (33 tests, ~0.3 seconds)
uv run pytest -m "not gui"

# Run with coverage reporting (~0.5 seconds)
uv run pytest --cov=pyqt6_editor

# Run with HTML coverage report
uv run pytest --cov=pyqt6_editor --cov-report=html
```

### Code Quality and Validation

```bash
# Linting with ruff (~0.04 seconds) - All linting issues resolved
uv run ruff check .

# Auto-fix any new linting issues
uv run ruff check . --fix

# Type checking with mypy (~3.7 seconds) - Currently has 28 type errors in GUI components
uv run mypy pyqt6_editor/

# Format code
uv run ruff format .
```

### Running the Application

**IMPORTANT**: The GUI application cannot run in headless environments due to missing libEGL.so.1. This is expected and normal.

```bash
# Attempt to run the application (will fail in headless environment)
uv run python main.py

# Alternative entry point
uv run pyqt6-editor
```

Error message in headless environment:
```
ImportError: libEGL.so.1: cannot open shared object file: No such file or directory
```

## Validation

### Always Run These Commands After Making Changes

1. **Test core functionality** (most important - tests complete in under 1 second):
   ```bash
   uv run pytest tests/test_core.py
   ```

2. **Run full test suite**:
   ```bash
   uv run pytest
   ```

3. **Check code quality** before committing:
   ```bash
   # Check for any new linting issues  
   uv run ruff check .
   
   # Auto-fix any issues found
   uv run ruff check . --fix
   
   # Type checking (optional - has known issues in GUI components)
   uv run mypy pyqt6_editor/
   ```

### Core Functionality Validation Scenarios

Always test these core scenarios manually after making changes to ensure the application works correctly:

```python
# Create this test script to validate core functionality
from pyqt6_editor.core import DocumentManager, EditorCore, ViewMode

# Test 1: Basic XML editing workflow
core = EditorCore()
core.document_manager.content = """<?xml version="1.0"?>
<root>
    <child attribute="value">Content</child>
</root>"""

# Test 2: XML validation
is_valid, error = core.document_manager.validate_xml()
assert is_valid == True

# Test 3: View mode switching
core.set_mode(ViewMode.SOURCE)
can_switch, error = core.can_switch_to_styled()
assert can_switch == True

# Test 4: Invalid XML handling
core.document_manager.content = "<root><unclosed>"
can_switch, error = core.can_switch_to_styled()
assert can_switch == False
assert "Invalid XML" in error
```

## Architecture and Key Components

### Core Components (GUI-Independent, Fully Testable)
- **`pyqt6_editor/core.py`**: Contains DocumentManager, EditorCore, ViewMode
  - `DocumentManager`: File operations, XML parsing, content management
  - `EditorCore`: Editor functionality coordinator, view mode switching
  - `ViewMode`: Enum for STYLED/SOURCE view modes

### GUI Components (PyQt6-Dependent)
- **`pyqt6_editor/gui.py`**: MainWindow, EditorWidget, SourceView, XMLSyntaxHighlighter
- **`pyqt6_editor/main.py`**: Application entry point

### Test Structure
- **`tests/test_core.py`**: Core logic tests (29 tests, no GUI dependencies)
- **`tests/test_imports.py`**: Import and basic functionality tests (4 tests)
- **`tests/conftest.py`**: Test configuration, sets QT_QPA_PLATFORM='offscreen'

## Timing Expectations and Timeout Values

**CRITICAL**: Set appropriate timeouts for all commands. NEVER CANCEL builds or long-running commands.

| Command | Expected Time | Recommended Timeout |
|---------|---------------|-------------------|
| `uv sync` | 1-2 minutes | 180+ seconds |
| `uv run pytest` | 0.6 seconds | 30 seconds |
| `uv run pytest tests/test_core.py` | 0.3 seconds | 30 seconds |
| `uv run pytest --cov=pyqt6_editor` | 0.5 seconds | 30 seconds |
| `uv run ruff check .` | 0.04 seconds | 30 seconds |
| `uv run mypy pyqt6_editor/` | 3.7 seconds | 60 seconds |

## Common Issues and Troubleshooting

### Known Issues

1. **Linting**: All ruff linting issues have been resolved
   - **Note**: There's a deprecation warning about pyproject.toml configuration structure (can be ignored)

2. **Type Checking**: 28 mypy errors in GUI components due to PyQt6 type annotations
   - **Known Issue**: This is acceptable - GUI components have complex PyQt6 types

3. **GUI in Headless Environment**: Cannot run GUI in headless/CI environments
   - **Expected**: This is normal behavior due to missing display libraries

### Development Workflow

1. **Make Changes**: Focus on core logic in `pyqt6_editor/core.py` when possible (fully testable)
2. **Test Immediately**: Run `uv run pytest tests/test_core.py` (under 1 second)
3. **Full Testing**: Run `uv run pytest` to ensure all tests pass
4. **Code Quality**: Run `uv run ruff check . --fix` before committing
5. **Validation**: Test core functionality scenarios manually

### File Organization

```
pyqt6_editor/
├── pyqt6_editor/           # Main package
│   ├── __init__.py         # Package initialization
│   ├── core.py             # Core business logic (GUI-independent)
│   ├── gui.py              # PyQt6 GUI components
│   └── main.py             # Application entry point
├── tests/                  # Test suite
│   ├── conftest.py         # Test configuration
│   ├── test_core.py        # Core logic tests (most important)
│   └── test_imports.py     # Import tests
├── main.py                 # Entry point script
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lock file
```

## Key Design Principles

1. **Testability**: Core logic completely separated from GUI for easy unit testing
2. **Type Safety**: Comprehensive type hints throughout (some PyQt6 issues remain)
3. **Error Handling**: Graceful error handling with custom exception classes
4. **Extensibility**: Modular design allows easy feature additions

## Coverage Information

- **Overall Coverage**: 35% (acceptable due to untestable GUI components)
- **Core Logic Coverage**: 99% (excellent - this is what matters)
- **GUI Coverage**: 2% (expected - difficult to test GUI components)

Always prioritize testing core logic changes over GUI changes, as core logic is where business value and correctness matter most.