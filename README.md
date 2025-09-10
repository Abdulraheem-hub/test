# PyQt6 Editor

A modern dual-view editor application built with PyQt6, featuring testable architecture and contemporary Python development standards.

## Features

- **Dual View Modes**: Switch between Styled View and Source View
- **XML Support**: Syntax highlighting, validation, and formatting
- **Modern Architecture**: GUI-independent core logic for maximum testability
- **Type Safety**: Full type hints throughout the codebase
- **Modern Tooling**: Uses `uv` for fast, reliable dependency management

## Quick Start

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (installed automatically if not present)

### Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd pyqt6-editor

# Install uv (if not already installed)
pip install uv

# Install dependencies and run
uv run python main.py
```

### Development Setup

```bash
# Install development dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pyqt6_editor

# Run only core logic tests (no GUI required)
uv run pytest tests/test_core.py

# Run linting
uv run ruff check .

# Run type checking
uv run mypy pyqt6_editor/
```

## Architecture

### Core Components

The application is architected with clear separation between GUI and business logic:

#### Core Logic (GUI-Independent)
- **`DocumentManager`**: Handles file operations, XML parsing, and content management
- **`EditorCore`**: Coordinates editor functionality and view mode switching
- **`ViewMode`**: Enum defining available view modes (STYLED, SOURCE)

#### GUI Components (PyQt6-Dependent)
- **`MainWindow`**: Main application window with menus and toolbars
- **`EditorWidget`**: Custom editor for styled view
- **`SourceView`**: Plain text editor with XML syntax highlighting
- **`XMLSyntaxHighlighter`**: Provides XML syntax highlighting

### Design Principles

1. **Testability**: Core logic separated from GUI for easy unit testing
2. **Type Safety**: Comprehensive type hints throughout
3. **Error Handling**: Graceful error handling with custom exception classes
4. **Extensibility**: Modular design allows easy feature additions

## Usage

### Basic Operations

- **New Document**: `Ctrl+N` or File → New
- **Open Document**: `Ctrl+O` or File → Open
- **Save Document**: `Ctrl+S` or File → Save
- **Save As**: `Ctrl+Shift+S` or File → Save As

### View Modes

- **Styled View**: `Ctrl+1` - Custom editor with enhanced features
- **Source View**: `Ctrl+2` - Raw XML with syntax highlighting

### XML Operations

- **Format XML**: `Ctrl+F` - Auto-format XML with proper indentation
- **Validation**: Automatic XML validation when switching to styled view

## Testing

The application includes comprehensive tests covering all core functionality:

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/test_core.py      # Core logic tests
uv run pytest -m "not gui"           # Non-GUI tests only
uv run pytest -m gui                 # GUI tests only

# Run with verbose output
uv run pytest -v

# Run with coverage reporting
uv run pytest --cov=pyqt6_editor --cov-report=html
```

### Test Architecture

- **Core Tests**: Test business logic without GUI dependencies
- **GUI Tests**: Test GUI components using mocking to avoid display requirements
- **Integration Tests**: Test interaction between components

## Project Structure

```
pyqt6_editor/
├── pyqt6_editor/           # Main package
│   ├── __init__.py         # Package initialization
│   ├── core.py             # Core business logic
│   ├── gui.py              # PyQt6 GUI components
│   └── main.py             # Application entry point
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   ├── test_core.py        # Core logic tests
│   └── test_gui.py         # GUI component tests
├── main.py                 # Entry point script
├── pyproject.toml          # Project configuration
├── uv.lock                 # Dependency lock file
└── README.md               # This file
```

## Configuration

The project uses `pyproject.toml` for configuration:

- **Dependencies**: Managed via `uv`
- **Testing**: Configured for `pytest` with coverage
- **Linting**: Configured for `ruff`
- **Type Checking**: Configured for `mypy`

## Contributing

1. **Setup**: Follow the development setup instructions above
2. **Testing**: Ensure all tests pass before submitting changes
3. **Code Style**: Follow the existing code style and type hints
4. **Documentation**: Update documentation for new features

### Code Style Guidelines

- Use type hints for all function parameters and return values
- Follow PEP 8 naming conventions
- Write docstrings for all public methods and classes
- Separate GUI logic from business logic
- Write tests for all new functionality

## License

MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Enhanced XML editing features
- [ ] Plugin system for extensibility
- [ ] Multiple document tabs
- [ ] Theme customization
- [ ] Advanced find/replace functionality