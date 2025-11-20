"""Simple text editor for PyVirtOS."""

from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.filesystem import VirtualFilesystem


class TextEditorWindow(QMainWindow):
    """Simple text editor window."""

    def __init__(self, kernel: Kernel, filepath: str):
        """Initialize text editor.

        Args:
            kernel: Kernel instance
            filepath: Path to file to edit
        """
        super().__init__()
        self.kernel = kernel
        self.vfs: Optional[VirtualFilesystem] = kernel.get_service("filesystem")
        self.filepath = filepath
        self.current_user_uid = 0
        self.current_user_gid = 0
        self.modified = False

        self.setWindowTitle(f"Text Editor - {filepath}")
        self.setGeometry(300, 300, 800, 600)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # File path label
        path_label = QLabel(f"File: {filepath}")
        path_label.setFont(QFont("Courier", 9))
        layout.addWidget(path_label)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier", 11))
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)

        # Button layout
        button_layout = QHBoxLayout()

        # Save button
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        # Save As button
        save_as_btn = QPushButton("💾 Save As")
        save_as_btn.clicked.connect(self._on_save_as)
        button_layout.addWidget(save_as_btn)

        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.clicked.connect(self._on_close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        central.setLayout(layout)

        # Load file content
        self._load_file()

    def _load_file(self) -> None:
        """Load file content."""
        if not self.vfs:
            QMessageBox.warning(self, "Error", "Filesystem not available")
            return

        try:
            content = self.vfs.read(self.filepath, self.current_user_uid, self.current_user_gid)
            if content:
                self.text_edit.setPlainText(content)
            self.modified = False
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")

    def _on_text_changed(self) -> None:
        """Handle text change."""
        self.modified = True
        self.setWindowTitle(f"Text Editor - {self.filepath} *")

    def _on_save(self) -> None:
        """Save file."""
        if not self.vfs:
            QMessageBox.warning(self, "Error", "Filesystem not available")
            return

        try:
            content = self.text_edit.toPlainText()
            self.vfs.write(
                self.filepath,
                content,
                uid=self.current_user_uid,
                gid=self.current_user_gid,
            )
            self.modified = False
            self.setWindowTitle(f"Text Editor - {self.filepath}")
            QMessageBox.information(self, "Success", f"File saved: {self.filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")

    def _on_save_as(self) -> None:
        """Save file as."""
        from PySide6.QtWidgets import QInputDialog

        new_path, ok = QInputDialog.getText(
            self, "Save As", "New file path:", text=self.filepath
        )
        if ok and new_path:
            self.filepath = new_path
            self._on_save()

    def _on_close(self) -> None:
        """Close editor."""
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.close()
