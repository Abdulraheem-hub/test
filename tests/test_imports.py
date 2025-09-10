"""Test for module imports and basic functionality."""

from __future__ import annotations


def test_core_module_import():
    """Test that core module can be imported."""
    from pyqt6_editor.core import DocumentManager, EditorCore, ViewMode

    # Verify classes can be instantiated
    dm = DocumentManager()
    core = EditorCore()

    assert dm is not None
    assert core is not None
    assert ViewMode.STYLED.value == "styled"


def test_gui_module_import_mock():
    """Test that GUI module handles import gracefully."""
    # Just test that we can import without crashing the test
    try:
        from pyqt6_editor import gui
        assert gui is not None
    except ImportError as e:
        # Expected if PyQt6 is not available - this is fine for this test
        assert "PyQt6" in str(e) or "libEGL" in str(e) or "EGL" in str(e)


def test_main_module_import_mock():
    """Test that main module handles import gracefully."""
    try:
        from pyqt6_editor import main
        assert main is not None
    except ImportError as e:
        # Expected if PyQt6 is not available - this is fine for this test
        assert "PyQt6" in str(e) or "libEGL" in str(e) or "EGL" in str(e)


def test_package_initialization():
    """Test package can be imported."""
    import pyqt6_editor

    assert pyqt6_editor.__version__ == "0.1.0"
    assert hasattr(pyqt6_editor, 'DocumentManager')
    assert hasattr(pyqt6_editor, 'EditorCore')
    assert hasattr(pyqt6_editor, 'ViewMode')
