"""GUI components for PyQt6 Editor."""

from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QKeySequence,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .core import EditorCore, ViewMode


class XMLSyntaxHighlighter(QSyntaxHighlighter):
    """Simple XML syntax highlighter."""

    def __init__(self, parent: QTextDocument | None = None) -> None:
        """Initialize highlighter."""
        super().__init__(parent)

        # Define formats
        self.xml_keyword_format = QTextCharFormat()
        self.xml_keyword_format.setForeground(Qt.GlobalColor.blue)
        self.xml_keyword_format.setFontWeight(QFont.Weight.Bold)

        self.xml_value_format = QTextCharFormat()
        self.xml_value_format.setForeground(Qt.GlobalColor.darkGreen)

        self.xml_comment_format = QTextCharFormat()
        self.xml_comment_format.setForeground(Qt.GlobalColor.gray)
        self.xml_comment_format.setFontItalic(True)

    def highlightBlock(self, text: str) -> None:
        """Highlight XML syntax in the given text block."""
        # Simple XML tag highlighting
        import re

        # Highlight XML tags
        tag_pattern = r'<[^>]+>'
        for match in re.finditer(tag_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.xml_keyword_format)

        # Highlight XML comments
        comment_pattern = r'<!--.*?-->'
        for match in re.finditer(comment_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.xml_comment_format)


class LineNumberArea(QWidget):
    """Line number area widget for the editor."""

    def __init__(self, editor: EditorWidget) -> None:
        """Initialize line number area."""
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        """Return the size hint for the line number area."""
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        """Paint the line numbers."""
        self.editor.line_number_area_paint_event(event)


class EditorWidget(QPlainTextEdit):
    """Custom editor widget for styled view with line numbers and overwrite mode."""

    MAX_LINE_LENGTH = 80

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize editor widget."""
        super().__init__(parent)
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(40)

        # Create line number area
        self.line_number_area = LineNumberArea(self)

        # Connect signals for line number updates
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        # Initialize line number area
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self) -> int:
        """Calculate the width needed for line numbers."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        """Update the width of the line number area."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy) -> None:
        """Update the line number area when scrolling."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        """Handle resize events to update line number area."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event) -> None:
        """Paint the line numbers."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(0, int(top), self.line_number_area.width(), self.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self) -> None:
        """Highlight the current line."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event) -> None:
        """Handle key press events for overwrite mode and line length constraints."""
        key = event.key()
        text = event.text()
        cursor = self.textCursor()

        # Allow navigation keys to work normally
        navigation_keys = {
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
            Qt.Key.Key_Tab, Qt.Key.Key_Backtab
        }

        if key in navigation_keys:
            super().keyPressEvent(event)
            return

        # Allow Enter/Return to insert new lines normally
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            super().keyPressEvent(event)
            return

        # Handle Backspace and Delete
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            # For now, allow normal backspace/delete behavior
            # TODO: Add locked segment protection when needed
            super().keyPressEvent(event)
            return

        # Handle text input (overwrite mode with constraints)
        if text and text.isprintable():
            self._handle_text_input(text, cursor)
            return

        # For all other keys, use default behavior
        super().keyPressEvent(event)

    def _handle_text_input(self, text: str, cursor: QTextCursor) -> None:
        """Handle text input in overwrite mode with line length constraints."""
        # Get current line information
        current_block = cursor.block()
        line_text = current_block.text()
        cursor_position_in_line = cursor.positionInBlock()

        # Check line length constraint first
        if len(line_text) >= self.MAX_LINE_LENGTH and cursor_position_in_line >= self.MAX_LINE_LENGTH:
            # Block typing beyond 80 characters
            return

        # Implement overwrite mode
        if cursor_position_in_line < len(line_text):
            # We're in the middle of the line - overwrite the character
            cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(text)
        else:
            # We're at the end of existing text - allow typing if within line limit
            if len(line_text) < self.MAX_LINE_LENGTH:
                cursor.insertText(text)
            # If we're exactly at the end of an 80-character line, block further typing

    def set_content(self, content: str) -> None:
        """Set editor content."""
        self.setPlainText(content)

    def get_content(self) -> str:
        """Get editor content."""
        return self.toPlainText()


class SourceView(QPlainTextEdit):
    """Source view with XML syntax highlighting."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize source view."""
        super().__init__(parent)
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(40)

        # Add syntax highlighting
        self.highlighter = XMLSyntaxHighlighter(self.document())

    def set_content(self, content: str) -> None:
        """Set source content."""
        self.setPlainText(content)

    def get_content(self) -> str:
        """Get source content."""
        return self.toPlainText()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()

        # Initialize core editor
        self.editor_core = EditorCore()
        self.editor_core.register_mode_change_callback(self._on_mode_change)

        # Set up UI
        self.setWindowTitle("PyQt6 Editor")
        self.setGeometry(100, 100, 1000, 700)

        # Create widgets
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbars()
        self._setup_connections()

        # Initialize with styled view
        self._update_view_mode()

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create splitter for dual pane view (future feature)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)

        # Create editor widgets
        self.styled_editor = EditorWidget()
        self.source_editor = SourceView()

        # Add both to splitter but hide one initially
        self.splitter.addWidget(self.styled_editor)
        self.splitter.addWidget(self.source_editor)

        # Hide source view initially
        self.source_editor.hide()

    def _setup_menus(self) -> None:
        """Set up menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new document")
        new_action.triggered.connect(self._new_document)
        file_menu.addAction(new_action)
        self.new_action = new_action

        # Open action
        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing document")
        open_action.triggered.connect(self._open_document)
        file_menu.addAction(open_action)
        self.open_action = open_action

        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Save the current document")
        save_action.triggered.connect(self._save_document)
        file_menu.addAction(save_action)
        self.save_action = save_action

        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("Save the document with a new name")
        save_as_action.triggered.connect(self._save_as_document)
        file_menu.addAction(save_as_action)
        self.save_as_action = save_as_action

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Styled view action
        styled_action = QAction("&Styled View", self)
        styled_action.setShortcut(QKeySequence("Ctrl+1"))
        styled_action.setStatusTip("Switch to styled view")
        styled_action.setCheckable(True)
        styled_action.setChecked(True)
        styled_action.triggered.connect(lambda: self._switch_view_mode(ViewMode.STYLED))
        view_menu.addAction(styled_action)
        self.styled_action = styled_action

        # Source view action
        source_action = QAction("S&ource View", self)
        source_action.setShortcut(QKeySequence("Ctrl+2"))
        source_action.setStatusTip("Switch to source view")
        source_action.setCheckable(True)
        source_action.triggered.connect(lambda: self._switch_view_mode(ViewMode.SOURCE))
        view_menu.addAction(source_action)
        self.source_action = source_action

        view_menu.addSeparator()

        # Format XML action
        format_action = QAction("&Format XML", self)
        format_action.setShortcut(QKeySequence("Ctrl+F"))
        format_action.setStatusTip("Format XML with proper indentation")
        format_action.triggered.connect(self._format_xml)
        view_menu.addAction(format_action)
        self.format_action = format_action

    def _setup_toolbars(self) -> None:
        """Set up toolbars."""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setMovable(False)

        # Add file actions to toolbar
        main_toolbar.addAction(self.new_action)
        main_toolbar.addAction(self.open_action)
        main_toolbar.addAction(self.save_action)

        main_toolbar.addSeparator()

        # Add view actions to toolbar
        main_toolbar.addAction(self.styled_action)
        main_toolbar.addAction(self.source_action)

        main_toolbar.addSeparator()

        # Add format action
        main_toolbar.addAction(self.format_action)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Connect editor text changes to document manager
        self.styled_editor.textChanged.connect(self._on_text_changed)
        self.source_editor.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        """Handle text changes in editors."""
        # Get content from current active editor
        current_editor = self._get_current_editor()
        content = current_editor.get_content()

        # Update document manager
        self.editor_core.document_manager.content = content

        # Update window title to show modified status
        self._update_window_title()

    def _get_current_editor(self) -> EditorWidget | SourceView:
        """Get the currently active editor."""
        if self.editor_core.current_mode == ViewMode.STYLED:
            return self.styled_editor
        else:
            return self.source_editor

    def _update_window_title(self) -> None:
        """Update window title with file path and modified status."""
        title = "PyQt6 Editor"

        if self.editor_core.document_manager.file_path:
            title += f" - {self.editor_core.document_manager.file_path}"
        else:
            title += " - Untitled"

        if self.editor_core.document_manager.is_modified:
            title += " *"

        self.setWindowTitle(title)

    def _switch_view_mode(self, mode: ViewMode) -> None:
        """Switch between view modes."""
        # Validate XML if switching to styled view
        if mode == ViewMode.STYLED:
            can_switch, error = self.editor_core.can_switch_to_styled()
            if not can_switch:
                QMessageBox.warning(self, "Invalid XML", f"Cannot switch to styled view:\n{error}")
                return

        # Update core mode
        self.editor_core.set_mode(mode)

    def _on_mode_change(self, mode: ViewMode) -> None:
        """Handle mode change notification from core."""
        self._update_view_mode()
        self._update_menu_checkboxes()

    def _update_view_mode(self) -> None:
        """Update UI based on current view mode."""
        current_editor = self._get_current_editor()
        content = current_editor.get_content()

        if self.editor_core.current_mode == ViewMode.STYLED:
            # Switch to styled view
            self.source_editor.hide()
            self.styled_editor.show()
            if content != self.styled_editor.get_content():
                self.styled_editor.set_content(content)
        else:
            # Switch to source view
            self.styled_editor.hide()
            self.source_editor.show()
            if content != self.source_editor.get_content():
                self.source_editor.set_content(content)

    def _update_menu_checkboxes(self) -> None:
        """Update menu action checkboxes."""
        self.styled_action.setChecked(self.editor_core.current_mode == ViewMode.STYLED)
        self.source_action.setChecked(self.editor_core.current_mode == ViewMode.SOURCE)

    def _new_document(self) -> None:
        """Create new document."""
        if self._check_save_changes():
            self.editor_core.new_document()
            self._get_current_editor().set_content("")
            self._update_window_title()

    def _open_document(self) -> None:
        """Open document from file."""
        if not self._check_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "", "XML Files (*.xml);;All Files (*)"
        )

        if file_path:
            try:
                self.editor_core.document_manager.load_from_file(file_path)
                content = self.editor_core.document_manager.content
                self._get_current_editor().set_content(content)
                self._update_window_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def _save_document(self) -> None:
        """Save current document."""
        if self.editor_core.document_manager.file_path:
            self._save_to_file(self.editor_core.document_manager.file_path)
        else:
            self._save_as_document()

    def _save_as_document(self) -> None:
        """Save document with new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Document", "", "XML Files (*.xml);;All Files (*)"
        )

        if file_path:
            self._save_to_file(file_path)

    def _save_to_file(self, file_path: str) -> None:
        """Save document to specified file."""
        try:
            # Update content from current editor
            current_editor = self._get_current_editor()
            self.editor_core.document_manager.content = current_editor.get_content()

            # Save to file
            self.editor_core.document_manager.save_to_file(file_path)
            self._update_window_title()

            self.statusBar().showMessage(f"Saved to {file_path}", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _format_xml(self) -> None:
        """Format XML content."""
        try:
            formatted = self.editor_core.document_manager.format_xml()
            current_editor = self._get_current_editor()
            current_editor.set_content(formatted)
            self.statusBar().showMessage("XML formatted", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Format Error", f"Failed to format XML:\n{e}")

    def _check_save_changes(self) -> bool:
        """Check if user wants to save changes before proceeding."""
        if not self.editor_core.document_manager.is_modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The document has been modified. Do you want to save your changes?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Save:
            self._save_document()
            return not self.editor_core.document_manager.is_modified
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self._check_save_changes():
            event.accept()
        else:
            event.ignore()
