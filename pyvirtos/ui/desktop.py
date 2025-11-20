"""Desktop window manager and main GUI for PyVirtOS."""

import sys
from typing import Dict, Optional, Tuple

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QColor
from PySide6.QtCore import Signal, QObject

from pyvirtos.core.kernel import Kernel


class DesktopSignals(QObject):
    """Signals for desktop events."""

    app_launched = Signal(str)  # app_name
    app_closed = Signal(str)  # app_name


class SystemTray(QFrame):
    """System tray showing time and system info."""

    def __init__(self, kernel: Kernel):
        """Initialize system tray.

        Args:
            kernel: Kernel instance
        """
        super().__init__()
        self.kernel = kernel
        self.setStyleSheet(
            "QFrame { background-color: #2c3e50; color: white; padding: 10px; }"
        )
        self.setMaximumHeight(50)

        layout = QHBoxLayout()

        # Time label
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Courier", 12, QFont.Bold))
        layout.addWidget(self.time_label)

        # System info
        self.info_label = QLabel("PyVirtOS")
        self.info_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.info_label)

        layout.addStretch()

        # User menu button
        self.user_button = QPushButton("root")
        self.user_button.setMaximumWidth(100)
        layout.addWidget(self.user_button)

        self.setLayout(layout)

    def update_time(self) -> None:
        """Update time display."""
        import time

        current_time = time.strftime("%H:%M:%S")
        self.time_label.setText(current_time)

        # Update system info
        if self.kernel.running:
            info = self.kernel.get_system_info()
            uptime_ms = info["uptime_ms"]
            uptime_s = int(uptime_ms / 1000)
            self.info_label.setText(
                f"PyVirtOS | Uptime: {uptime_s}s | Processes: {info['total_processes']}"
            )


class Dock(QFrame):
    """Application dock/launcher."""

    def __init__(self, parent_desktop=None):
        """Initialize dock.
        
        Args:
            parent_desktop: Reference to parent Desktop window
        """
        super().__init__()
        self.parent_desktop = parent_desktop
        self.setStyleSheet(
            "QFrame { background-color: #34495e; border-top: 1px solid #2c3e50; }"
        )
        self.setMaximumHeight(80)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # App launcher buttons
        apps = [
            ("Explorer", "📁"),
            ("Terminal", "⌨️"),
            ("Task Manager", "⚙️"),
            ("Settings", "🔧"),
        ]

        for app_name, icon_text in apps:
            btn = QPushButton(f"{icon_text}\n{app_name}")
            btn.setMinimumSize(QSize(70, 70))
            btn.setMaximumSize(QSize(70, 70))
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 9px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f618d;
                }
            """
            )
            btn.clicked.connect(lambda checked, app=app_name: self._on_app_clicked(app))
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)

    def _on_app_clicked(self, app_name: str) -> None:
        """Handle app launcher click.

        Args:
            app_name: Name of application to launch
        """
        if self.parent_desktop:
            self.parent_desktop.launch_app(app_name)


class Desktop(QMainWindow):
    """Main desktop window."""

    def __init__(self, kernel: Kernel):
        """Initialize desktop.

        Args:
            kernel: Kernel instance
        """
        super().__init__()
        self.kernel = kernel
        self.signals = DesktopSignals()
        self.open_windows: Dict[str, QWidget] = {}

        # Setup main window
        self.setWindowTitle("PyVirtOS - Virtual Operating System")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # System tray
        self.tray = SystemTray(kernel)
        layout.addWidget(self.tray)

        # Desktop area with welcome message
        self.desktop_area = QFrame()
        self.desktop_area.setStyleSheet("QFrame { background-color: #1a1a1a; }")
        desktop_layout = QVBoxLayout()
        desktop_layout.setContentsMargins(0, 0, 0, 0)
        
        # Welcome label
        welcome_label = QLabel("Welcome to PyVirtOS\n\nClick an icon in the dock below to launch an application")
        welcome_label.setFont(QFont("Arial", 14))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("QLabel { color: #7f8c8d; }")
        desktop_layout.addStretch()
        desktop_layout.addWidget(welcome_label)
        desktop_layout.addStretch()
        
        self.desktop_area.setLayout(desktop_layout)
        layout.addWidget(self.desktop_area, 1)

        # Dock (pass self reference so it can launch apps)
        self.dock = Dock(parent_desktop=self)
        layout.addWidget(self.dock)

        central.setLayout(layout)

        # Setup timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._on_timer)
        self.update_timer.start(100)  # Update every 100ms

        # Setup kernel tick timer
        self.kernel_timer = QTimer()
        self.kernel_timer.timeout.connect(self._on_kernel_tick)
        self.kernel_timer.start(50)  # Kernel tick every 50ms

        # Apply stylesheet
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1a1a1a;
                color: white;
            }
            QPushButton {
                color: white;
                font-weight: bold;
            }
        """
        )

    def _on_timer(self) -> None:
        """Handle UI update timer."""
        self.tray.update_time()

    def _on_kernel_tick(self) -> None:
        """Handle kernel tick."""
        if self.kernel.running:
            # Run kernel tick synchronously (non-blocking in GUI context)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If event loop is running, schedule as task
                    asyncio.create_task(self.kernel.tick())
                else:
                    # Otherwise run synchronously
                    loop.run_until_complete(self.kernel.tick())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self.kernel.tick())

    def launch_app(self, app_name: str) -> None:
        """Launch an application.

        Args:
            app_name: Name of application to launch
        """
        if app_name == "Explorer":
            from pyvirtos.ui.explorer_view import ExplorerWindow

            window = ExplorerWindow(self.kernel)
            window.show()
            self.open_windows[app_name] = window
        elif app_name == "Terminal":
            from pyvirtos.ui.terminal_view import TerminalWindow

            window = TerminalWindow(self.kernel)
            window.show()
            self.open_windows[app_name] = window
        elif app_name == "Task Manager":
            from pyvirtos.ui.task_manager_view import TaskManagerWindow

            window = TaskManagerWindow(self.kernel)
            window.show()
            self.open_windows[app_name] = window

        self.signals.app_launched.emit(app_name)

    def closeEvent(self, event) -> None:
        """Handle window close event.

        Args:
            event: Close event
        """
        self.kernel.stop()
        self.update_timer.stop()
        self.kernel_timer.stop()
        event.accept()


async def run_desktop(kernel: Kernel) -> int:
    """Run the desktop GUI.

    Args:
        kernel: Kernel instance

    Returns:
        Application exit code
    """
    app = QApplication.instance() or QApplication(sys.argv)

    await kernel.start()

    desktop = Desktop(kernel)
    desktop.show()

    return app.exec()
