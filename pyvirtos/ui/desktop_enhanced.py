"""Enhanced desktop with theme support, system tray, dock, and context menu."""

import sys
import time
import psutil
from typing import Dict, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMenu,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, QSize, QPoint
from PySide6.QtGui import QFont, QColor, QPixmap, QBrush
from PySide6.QtCore import Signal, QObject

from pyvirtos.core.kernel import Kernel


class DesktopSignals(QObject):
    """Signals for desktop events."""

    app_launched = Signal(str)
    app_closed = Signal(str)
    theme_changed = Signal(str)


class SystemTray(QFrame):
    """Enhanced system tray with time, CPU, RAM, and notifications."""

    def __init__(self, kernel: Kernel):
        """Initialize system tray."""
        super().__init__()
        self.kernel = kernel
        self.theme_manager = kernel.get_service("theme_manager")
        self.setMaximumHeight(50)
        self.setMinimumHeight(50)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(20)

        # Time label
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Courier", 11, QFont.Bold))
        layout.addWidget(self.time_label)

        # CPU usage
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setFont(QFont("Courier", 10))
        layout.addWidget(self.cpu_label)

        # RAM usage
        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setFont(QFont("Courier", 10))
        layout.addWidget(self.ram_label)

        # Notifications icon
        self.notif_label = QLabel("🔔 0")
        self.notif_label.setFont(QFont("Courier", 10))
        layout.addWidget(self.notif_label)

        layout.addStretch()

        # Theme indicator
        self.theme_label = QLabel("Theme: NeonDark")
        self.theme_label.setFont(QFont("Courier", 9))
        layout.addWidget(self.theme_label)

        self.setLayout(layout)

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_info)
        self.timer.start(1000)

        self._update_theme_colors()

    def _update_info(self) -> None:
        """Update time and system info."""
        # Update time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)

        # Update CPU (simulated)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")

        # Update RAM (simulated)
        ram_percent = psutil.virtual_memory().percent
        self.ram_label.setText(f"RAM: {ram_percent:.1f}%")

    def _update_theme_colors(self) -> None:
        """Update colors based on current theme."""
        if not self.theme_manager:
            return

        theme = self.theme_manager.current_theme
        if theme and hasattr(theme, 'colors'):
            bg_color = theme.colors.surface
            text_color = theme.colors.text_primary
            self.setStyleSheet(
                f"QFrame {{ background-color: {bg_color}; color: {text_color}; }}"
            )

            # Update label colors
            for label in [
                self.time_label,
                self.cpu_label,
                self.ram_label,
                self.notif_label,
                self.theme_label,
            ]:
                label.setStyleSheet(f"QLabel {{ color: {text_color}; }}")

    def update_theme(self) -> None:
        """Update theme colors."""
        self._update_theme_colors()


class Dock(QFrame):
    """Enhanced dock with smooth hover animations and app management."""

    def __init__(self, kernel: Kernel, parent_desktop=None):
        """Initialize dock."""
        super().__init__()
        self.kernel = kernel
        self.parent_desktop = parent_desktop
        self.theme_manager = kernel.get_service("theme_manager")
        self.pinned_apps = ["Explorer", "Terminal", "Task Manager"]
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # App launcher buttons
        for app_name in self.pinned_apps:
            btn = self._create_app_button(app_name)
            layout.addWidget(btn)

        layout.addStretch()

        # Add app button
        add_btn = QPushButton("➕")
        add_btn.setMinimumSize(QSize(60, 60))
        add_btn.setMaximumSize(QSize(60, 60))
        add_btn.setFont(QFont("Arial", 16))
        add_btn.clicked.connect(self._on_add_app)
        layout.addWidget(add_btn)

        self.setLayout(layout)
        self._update_theme_colors()

    def _create_app_button(self, app_name: str) -> QPushButton:
        """Create an app button."""
        icons = {
            "Explorer": "📁",
            "Terminal": "⌨️",
            "Task Manager": "⚙️",
            "Settings": "🔧",
        }
        icon = icons.get(app_name, "📦")

        btn = QPushButton(f"{icon}\n{app_name}")
        btn.setMinimumSize(QSize(70, 70))
        btn.setMaximumSize(QSize(70, 70))
        btn.setFont(QFont("Arial", 8))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set initial style
        self._update_button_style(btn)

        # Connect signals
        btn.clicked.connect(lambda: self._on_app_clicked(app_name))
        btn.enterEvent = lambda e: self._on_button_hover(btn, True)
        btn.leaveEvent = lambda e: self._on_button_hover(btn, False)

        return btn

    def _on_button_hover(self, btn: QPushButton, hovering: bool) -> None:
        """Handle button hover."""
        if hovering:
            btn.setMinimumSize(QSize(80, 80))
            btn.setMaximumSize(QSize(80, 80))
        else:
            btn.setMinimumSize(QSize(70, 70))
            btn.setMaximumSize(QSize(70, 70))

    def _update_button_style(self, btn: QPushButton) -> None:
        """Update button style based on theme."""
        if not self.theme_manager:
            return

        theme = self.theme_manager.current_theme
        if theme and hasattr(theme, 'colors'):
            primary = theme.colors.accent
            primary_dark = theme.colors.accent_dark

            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {primary};
                    color: {theme.colors.text_primary};
                    border: none;
                    border-radius: 5px;
                    font-size: 8px;
                }}
                QPushButton:hover {{
                    background-color: {primary_dark};
                }}
                QPushButton:pressed {{
                    background-color: {theme.colors.accent_dark};
                }}
            """
            )

    def _on_app_clicked(self, app_name: str) -> None:
        """Handle app launcher click."""
        if self.parent_desktop:
            self.parent_desktop.launch_app(app_name)

    def _on_add_app(self) -> None:
        """Handle add app button."""
        app_name, ok = QInputDialog.getText(self, "Add App", "App name:")
        if ok and app_name:
            if app_name not in self.pinned_apps:
                self.pinned_apps.append(app_name)
                # Recreate dock
                self._recreate_dock()

    def _recreate_dock(self) -> None:
        """Recreate dock with updated apps."""
        # Clear layout
        while self.layout().count():
            self.layout().takeAt(0).widget().deleteLater()

        # Recreate buttons
        for app_name in self.pinned_apps:
            btn = self._create_app_button(app_name)
            self.layout().insertWidget(len(self.pinned_apps) - 1, btn)

    def _update_theme_colors(self) -> None:
        """Update colors based on theme."""
        if not self.theme_manager:
            return

        theme = self.theme_manager.current_theme
        if theme and hasattr(theme, 'colors'):
            bg_color = theme.colors.surface_light
            self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; }}")

    def update_theme(self) -> None:
        """Update theme."""
        self._update_theme_colors()
        # Update all buttons
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.text() != "➕":
                self._update_button_style(widget)


class Desktop(QMainWindow):
    """Main desktop window with enhanced features."""

    def __init__(self, kernel: Kernel):
        """Initialize desktop."""
        super().__init__()
        self.kernel = kernel
        self.theme_manager = kernel.get_service("theme_manager")
        self.signals = DesktopSignals()
        self.open_windows: Dict[str, QWidget] = {}

        # Setup main window
        self.setWindowTitle("PyVirtOS - Virtual Operating System")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        central.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        central.customContextMenuRequested.connect(self._on_desktop_context_menu)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # System tray
        self.tray = SystemTray(kernel)
        layout.addWidget(self.tray)

        # Desktop area with wallpaper
        self.desktop_area = QFrame()
        self.desktop_area.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.desktop_area.customContextMenuRequested.connect(
            self._on_desktop_context_menu
        )
        self._update_desktop_background()

        desktop_layout = QVBoxLayout()
        desktop_layout.setContentsMargins(0, 0, 0, 0)

        # Welcome label
        welcome_label = QLabel(
            "Welcome to PyVirtOS\n\nRight-click for menu • Click dock icons to launch apps"
        )
        welcome_label.setFont(QFont("Arial", 14))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("QLabel { color: #7f8c8d; }")
        desktop_layout.addStretch()
        desktop_layout.addWidget(welcome_label)
        desktop_layout.addStretch()

        self.desktop_area.setLayout(desktop_layout)
        layout.addWidget(self.desktop_area, 1)

        # Dock
        self.dock = Dock(kernel, parent_desktop=self)
        layout.addWidget(self.dock)

        central.setLayout(layout)

        # Subscribe to theme changes
        if self.theme_manager:
            self.theme_manager.subscribe_theme_change(self._on_theme_changed)

        # Timer for theme updates
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self._check_theme_update)
        self.theme_timer.start(500)

    def _update_desktop_background(self) -> None:
        """Update desktop background based on theme."""
        if not self.theme_manager:
            return

        theme = self.theme_manager.current_theme
        if theme and hasattr(theme, 'colors'):
            bg_color = theme.colors.background
            self.desktop_area.setStyleSheet(f"QFrame {{ background-color: {bg_color}; }}")

    def _on_theme_changed(self, theme) -> None:
        """Handle theme change."""
        self._update_desktop_background()
        self.tray.update_theme()
        self.dock.update_theme()

    def _check_theme_update(self) -> None:
        """Check if theme has changed."""
        if self.theme_manager and hasattr(self.theme_manager, "current_theme"):
            current = self.theme_manager.current_theme
            if current and hasattr(self, "_last_theme"):
                if current != self._last_theme:
                    self._on_theme_changed(current)
            self._last_theme = current

    def _on_desktop_context_menu(self, pos: QPoint) -> None:
        """Handle right-click context menu."""
        menu = QMenu(self)

        # New File
        new_file_action = menu.addAction("📄 New File")
        new_file_action.triggered.connect(self._on_new_file)

        # New Folder
        new_folder_action = menu.addAction("📁 New Folder")
        new_folder_action.triggered.connect(self._on_new_folder)

        menu.addSeparator()

        # Properties
        properties_action = menu.addAction("⚙️ Properties")
        properties_action.triggered.connect(self._on_properties)

        menu.exec(self.mapToGlobal(pos))

    def _on_new_file(self) -> None:
        """Create new file."""
        filename, ok = QInputDialog.getText(self, "New File", "Filename:")
        if ok and filename:
            try:
                vfs = self.kernel.get_service("filesystem")
                if vfs:
                    # Create file in home directory
                    filepath = f"/home/{filename}"
                    vfs.touch(filepath, uid=0, gid=0)
                    QMessageBox.information(self, "Success", f"File created: {filepath}")
                else:
                    QMessageBox.warning(self, "Error", "Filesystem not available")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create file: {str(e)}")

    def _on_new_folder(self) -> None:
        """Create new folder."""
        foldername, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and foldername:
            try:
                vfs = self.kernel.get_service("filesystem")
                if vfs:
                    # Create folder in home directory
                    folderpath = f"/home/{foldername}"
                    vfs.mkdir(folderpath, uid=0, gid=0)
                    QMessageBox.information(self, "Success", f"Folder created: {folderpath}")
                else:
                    QMessageBox.warning(self, "Error", "Filesystem not available")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create folder: {str(e)}")

    def _on_properties(self) -> None:
        """Show desktop properties."""
        theme_name = "Unknown"
        if self.theme_manager and self.theme_manager.current_theme:
            theme_name = self.theme_manager.current_theme.name
        
        QMessageBox.information(
            self,
            "Desktop Properties",
            f"PyVirtOS Desktop\n\nVersion: 1.0\nTheme: {theme_name}",
        )

    def launch_app(self, app_name: str) -> None:
        """Launch an application."""
        if app_name == "Explorer":
            from pyvirtos.ui.explorer_view import ExplorerWindow

            if "Explorer" not in self.open_windows:
                window = ExplorerWindow(self.kernel)
                window.show()
                self.open_windows["Explorer"] = window
            else:
                self.open_windows["Explorer"].raise_()

        elif app_name == "Terminal":
            from pyvirtos.ui.terminal_view import TerminalWindow

            if "Terminal" not in self.open_windows:
                window = TerminalWindow(self.kernel)
                window.show()
                self.open_windows["Terminal"] = window
            else:
                self.open_windows["Terminal"].raise_()

        elif app_name == "Task Manager":
            from pyvirtos.ui.task_manager_view import TaskManagerWindow

            if "Task Manager" not in self.open_windows:
                window = TaskManagerWindow(self.kernel)
                window.show()
                self.open_windows["Task Manager"] = window
            else:
                self.open_windows["Task Manager"].raise_()


async def run_desktop(kernel: Kernel) -> int:
    """Run the desktop GUI.

    Args:
        kernel: Kernel instance

    Returns:
        Exit code
    """
    app = QApplication.instance() or QApplication(sys.argv)

    desktop = Desktop(kernel)
    desktop.show()

    return app.exec()
