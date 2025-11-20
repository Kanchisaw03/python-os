"""Task manager view for PyVirtOS."""

from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.scheduler import Scheduler


class TaskManagerWindow(QMainWindow):
    """Task manager window."""

    def __init__(self, kernel: Kernel):
        """Initialize task manager window.

        Args:
            kernel: Kernel instance
        """
        super().__init__()
        self.kernel = kernel
        self.scheduler: Optional[Scheduler] = kernel.get_service("scheduler")

        self.setWindowTitle("Task Manager - PyVirtOS")
        self.setGeometry(400, 400, 1000, 600)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # Info bar
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Processes: 0 | CPU Usage: 0%")
        self.info_label.setFont(QFont("Arial", 10))
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Process table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["PID", "Name", "User", "State", "CPU Time (ms)", "Memory (KB)", "Priority"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Button bar
        button_layout = QHBoxLayout()

        kill_btn = QPushButton("Kill Process")
        kill_btn.clicked.connect(self._on_kill_process)
        button_layout.addWidget(kill_btn)

        suspend_btn = QPushButton("Suspend")
        suspend_btn.clicked.connect(self._on_suspend_process)
        button_layout.addWidget(suspend_btn)

        resume_btn = QPushButton("Resume")
        resume_btn.clicked.connect(self._on_resume_process)
        button_layout.addWidget(resume_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        central.setLayout(layout)

        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_refresh)
        self.refresh_timer.start(500)  # Refresh every 500ms

        # Initial refresh
        self._on_refresh()

    def _on_refresh(self) -> None:
        """Refresh process list."""
        if not self.scheduler:
            return

        processes = self.scheduler.get_task_list()

        # Update table
        self.table.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            # PID
            pid_item = QTableWidgetItem(str(proc.pid))
            self.table.setItem(row, 0, pid_item)

            # Name
            name_item = QTableWidgetItem(proc.name)
            self.table.setItem(row, 1, name_item)

            # User
            user_item = QTableWidgetItem(proc.owner_user)
            self.table.setItem(row, 2, user_item)

            # State
            state_item = QTableWidgetItem(proc.state.name)
            self.table.setItem(row, 3, state_item)

            # CPU Time
            cpu_item = QTableWidgetItem(str(proc.cpu_time))
            self.table.setItem(row, 4, cpu_item)

            # Memory
            mem_item = QTableWidgetItem(str(proc.memory_used // 1024))
            self.table.setItem(row, 5, mem_item)

            # Priority
            priority_item = QTableWidgetItem(str(proc.priority))
            self.table.setItem(row, 6, priority_item)

        # Update info
        total_cpu_time = sum(p.cpu_time for p in processes)
        self.info_label.setText(
            f"Processes: {len(processes)} | Total CPU Time: {total_cpu_time}ms"
        )

    def _on_kill_process(self) -> None:
        """Kill selected process."""
        if not self.scheduler:
            return

        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        pid_item = self.table.item(row, 0)
        if pid_item:
            pid = int(pid_item.text())
            proc = self.scheduler.get_process(pid)
            if proc:
                proc.kill()
                self._on_refresh()

    def _on_suspend_process(self) -> None:
        """Suspend selected process."""
        if not self.scheduler:
            return

        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        pid_item = self.table.item(row, 0)
        if pid_item:
            pid = int(pid_item.text())
            proc = self.scheduler.get_process(pid)
            if proc:
                proc.sleep(1000)
                self._on_refresh()

    def _on_resume_process(self) -> None:
        """Resume selected process."""
        if not self.scheduler:
            return

        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        pid_item = self.table.item(row, 0)
        if pid_item:
            pid = int(pid_item.text())
            proc = self.scheduler.get_process(pid)
            if proc:
                from pyvirtos.core.process import ProcState

                if proc.state == ProcState.SLEEPING:
                    proc.state = ProcState.READY
                self._on_refresh()

    def closeEvent(self, event) -> None:
        """Handle window close event.

        Args:
            event: Close event
        """
        self.refresh_timer.stop()
        event.accept()
