"""File explorer view for PyVirtOS."""

from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidget,
    QListWidgetItem,
    QToolBar,
    QPushButton,
    QLineEdit,
    QLabel,
    QSplitter,
    QFileDialog,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.filesystem import VirtualFilesystem


class ExplorerWindow(QMainWindow):
    """File explorer window."""

    def __init__(self, kernel: Kernel):
        """Initialize explorer window.

        Args:
            kernel: Kernel instance
        """
        super().__init__()
        self.kernel = kernel
        self.vfs: Optional[VirtualFilesystem] = kernel.get_service("filesystem")
        self.current_user_uid = 0  # Default to root
        self.current_user_gid = 0
        self.current_path = "/"

        self.setWindowTitle("File Explorer - PyVirtOS")
        self.setGeometry(200, 200, 900, 600)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)

        self.path_input = QLineEdit()
        self.path_input.setText(self.current_path)
        self.path_input.returnPressed.connect(self._on_path_changed)
        toolbar.addWidget(QLabel("Path:"))
        toolbar.addWidget(self.path_input)

        toolbar.addSeparator()

        new_folder_btn = QPushButton("New Folder")
        new_folder_btn.clicked.connect(self._on_new_folder)
        toolbar.addWidget(new_folder_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        toolbar.addWidget(refresh_btn)

        layout.addWidget(toolbar)

        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: directory tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Folders")
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self._populate_tree()
        splitter.addWidget(self.tree)

        # Right panel: file list
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        splitter.addWidget(self.file_list)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)

        central.setLayout(layout)

        self._refresh_file_list()

    def _populate_tree(self) -> None:
        """Populate directory tree."""
        if not self.vfs:
            return

        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "/")
        root_item.setData(0, Qt.UserRole, "/")
        self._populate_tree_recursive(root_item, "/")

    def _populate_tree_recursive(self, parent_item: QTreeWidgetItem, path: str) -> None:
        """Recursively populate tree.

        Args:
            parent_item: Parent tree item
            path: Current path
        """
        if not self.vfs:
            return

        contents = self.vfs.listdir(path, self.current_user_uid, self.current_user_gid)
        if not contents:
            return

        for name in contents:
            if path == "/":
                full_path = f"/{name}"
            else:
                full_path = f"{path}/{name}"

            stat = self.vfs.stat(full_path, self.current_user_uid, self.current_user_gid)
            if stat and stat["type"] == "directory":
                item = QTreeWidgetItem(parent_item)
                item.setText(0, name)
                item.setData(0, Qt.UserRole, full_path)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle tree item click.

        Args:
            item: Clicked item
            column: Column index
        """
        path = item.data(0, Qt.UserRole)
        if path:
            self.current_path = path
            self.path_input.setText(path)
            self._refresh_file_list()

    def _refresh_file_list(self) -> None:
        """Refresh file list for current path."""
        if not self.vfs:
            return

        self.file_list.clear()

        contents = self.vfs.listdir(
            self.current_path, self.current_user_uid, self.current_user_gid
        )
        if not contents:
            self.status_label.setText(f"Empty directory: {self.current_path}")
            return

        for name in contents:
            if self.current_path == "/":
                full_path = f"/{name}"
            else:
                full_path = f"{self.current_path}/{name}"

            stat = self.vfs.stat(
                full_path, self.current_user_uid, self.current_user_gid
            )
            if stat:
                file_type = "📁" if stat["type"] == "directory" else "📄"
                size_str = f" ({stat['size']} bytes)" if stat["size"] > 0 else ""
                item_text = f"{file_type} {name}{size_str}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, full_path)
                self.file_list.addItem(item)

        self.status_label.setText(
            f"{len(contents)} items in {self.current_path}"
        )

    def _on_file_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle file double click.

        Args:
            item: Clicked item
        """
        path = item.data(Qt.UserRole)
        if not path or not self.vfs:
            return

        stat = self.vfs.stat(path, self.current_user_uid, self.current_user_gid)
        if stat and stat["type"] == "directory":
            self.current_path = path
            self.path_input.setText(path)
            self._refresh_file_list()
        elif stat and stat["type"] == "file":
            # Open file in text editor
            from pyvirtos.ui.text_editor import TextEditorWindow
            editor = TextEditorWindow(self.kernel, path)
            editor.show()

    def _on_path_changed(self) -> None:
        """Handle path input change."""
        new_path = self.path_input.text()
        if self.vfs:
            stat = self.vfs.stat(new_path, self.current_user_uid, self.current_user_gid)
            if stat and stat["type"] == "directory":
                self.current_path = new_path
                self._refresh_file_list()
            else:
                self.status_label.setText(f"Invalid path: {new_path}")
                self.path_input.setText(self.current_path)

    def _on_new_folder(self) -> None:
        """Create new folder."""
        if not self.vfs:
            return

        # Simple implementation - create folder with timestamp
        import time

        folder_name = f"new_folder_{int(time.time())}"
        if self.current_path == "/":
            new_path = f"/{folder_name}"
        else:
            new_path = f"{self.current_path}/{folder_name}"

        if self.vfs.mkdir(new_path, self.current_user_uid, self.current_user_gid):
            self.status_label.setText(f"Created: {new_path}")
            self._refresh_file_list()
        else:
            self.status_label.setText(f"Failed to create folder")

    def _on_refresh(self) -> None:
        """Refresh file list."""
        self._refresh_file_list()
