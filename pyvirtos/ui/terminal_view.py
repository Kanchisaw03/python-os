"""Terminal emulator window for PyVirtOS."""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QTextCursor

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.filesystem import VirtualFilesystem
from pyvirtos.core.shell import ShellExecutor, ShellParser

logger = logging.getLogger("pyvirtos.terminal")


class TerminalWindow(QMainWindow):
    """Terminal emulator window."""

    def __init__(self, kernel: Kernel):
        """Initialize terminal window.

        Args:
            kernel: Kernel instance
        """
        super().__init__()
        self.kernel = kernel
        self.vfs: Optional[VirtualFilesystem] = kernel.get_service("filesystem")
        self.users = kernel.get_service("users")
        self.scheduler = kernel.get_service("scheduler")
        self.app_manager = kernel.get_service("app_manager")
        self.current_user_uid = 0  # Default to root
        self.current_user_gid = 0
        self.current_path = "/"
        
        # Initialize advanced shell executor
        from pyvirtos.core.shell import ShellExecutor
        self.shell_executor = ShellExecutor(self.vfs, self.users, self.scheduler, self.app_manager)
        self.shell_executor.current_dir = self.current_path
        self.shell_executor.kernel = kernel  # Pass kernel for advanced features

        self.setWindowTitle("Terminal - PyVirtOS")
        self.setGeometry(300, 300, 800, 600)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Courier", 10))
        self.output.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: none;
            }
        """
        )
        layout.addWidget(self.output)

        # Input area
        input_layout = QHBoxLayout()

        self.prompt_label = QLabel(f"root@pyvirtos:{self.current_path}$ ")
        self.prompt_label.setFont(QFont("Courier", 10))
        self.prompt_label.setStyleSheet("color: #00ff00;")
        input_layout.addWidget(self.prompt_label)

        self.input_field = QLineEdit()
        self.input_field.setFont(QFont("Courier", 10))
        self.input_field.setStyleSheet(
            """
            QLineEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #00ff00;
                padding: 5px;
            }
        """
        )
        self.input_field.returnPressed.connect(self._on_command_entered)
        self.input_field.setFocus()
        input_layout.addWidget(self.input_field)

        # Send button
        send_btn = QPushButton("Send")
        send_btn.setFont(QFont("Courier", 10))
        send_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00ff00;
                color: #1e1e1e;
                border: none;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc00;
            }
        """
        )
        send_btn.clicked.connect(self._on_command_entered)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        central.setLayout(layout)

        # Print welcome message
        self._print_output("=" * 60)
        self._print_output("PyVirtOS Terminal - Advanced Shell")
        self._print_output("=" * 60)
        self._print_output("")
        self._print_output("Advanced Features Available:")
        self._print_output("  • Pipes: ls /home | grep alice")
        self._print_output("  • Redirects: echo hello > file.txt")
        self._print_output("  • Themes: theme set Ocean")
        self._print_output("  • Snapshots: snapshot save mystate")
        self._print_output("  • Apps: app list")
        self._print_output("  • Processes: ps --json")
        self._print_output("")
        self._print_output("Type 'help' for all commands")
        self._print_output("=" * 60)
        self._print_output("")

    def _print_output(self, text: str) -> None:
        """Print text to output area.

        Args:
            text: Text to print
        """
        self.output.append(text)
        # Auto-scroll to bottom
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output.setTextCursor(cursor)

    def _on_command_entered(self) -> None:
        """Handle command entry."""
        command = self.input_field.text().strip()
        self.input_field.clear()

        if not command:
            return

        # Print command
        self._print_output(f"root@pyvirtos:{self.current_path}$ {command}")

        # Execute using advanced shell
        try:
            if not self.shell_executor:
                self._print_output("Error: Shell executor not initialized")
                return
                
            output, success = self.shell_executor.execute(command, self.current_user_uid, self.current_user_gid)
            if output:
                self._print_output(output)
            elif not success:
                self._print_output(f"Command failed: {command}")
            
            # Update current directory if changed
            self.current_path = self.shell_executor.current_dir
            self.prompt_label.setText(f"root@pyvirtos:{self.current_path}$ ")
        except Exception as e:
            logger.error(f"Terminal command error: {e}", exc_info=True)
            self._print_output(f"Error: {str(e)}")

    def _execute_command(self, command: str) -> None:
        """Execute a command using advanced shell.

        Args:
            command: Command to execute
        """
        # This method is deprecated - all commands go through _on_command_entered
        pass

    def _cmd_help(self) -> None:
        """Show help message."""
        help_text = """
PyVirtOS Terminal - Advanced Shell

File Operations:
  ls [path]              - List directory
  cd <path>              - Change directory
  pwd                    - Print working directory
  cat <file>             - Display file
  touch <file>           - Create file
  mkdir <dir>            - Create directory
  echo <text>            - Print text

Process Management:
  ps [--json]            - List processes
  kill <pid>             - Kill process

System Info:
  whoami                 - Current user
  sysinfo                - System information

Advanced Features:
  theme list             - List available themes
  theme set <name>       - Switch theme
  snapshot save <name>   - Save OS state
  snapshot load <name>   - Restore OS state
  snapshot list          - List snapshots
  app list               - List installed apps
  app launch <name>      - Launch app

Shell Features:
  Pipes: command1 | command2
  Redirects: command > file or command >> file
  Flags: command --json

Utilities:
  clear                  - Clear screen
  exit                   - Exit terminal
"""
        self._print_output(help_text)

    def _cmd_ls(self, args: list) -> None:
        """List directory contents."""
        if not self.vfs:
            self._print_output("Filesystem not available")
            return

        path = args[0] if args else self.current_path
        contents = self.vfs.listdir(path, self.current_user_uid, self.current_user_gid)

        if contents is None:
            self._print_output(f"ls: cannot access '{path}': No such file or directory")
            return

        if not contents:
            self._print_output("(empty directory)")
            return

        for name in sorted(contents):
            if path == "/":
                full_path = f"/{name}"
            else:
                full_path = f"{path}/{name}"

            stat = self.vfs.stat(
                full_path, self.current_user_uid, self.current_user_gid
            )
            if stat:
                file_type = "d" if stat["type"] == "directory" else "-"
                size = stat["size"]
                self._print_output(f"{file_type} {name:30} {size:10} bytes")

    def _cmd_cd(self, args: list) -> None:
        """Change directory."""
        if not args:
            self._print_output("cd: missing operand")
            return

        if not self.vfs:
            self._print_output("Filesystem not available")
            return

        path = args[0]

        # Handle relative paths
        if path == "..":
            if self.current_path != "/":
                self.current_path = str(self.current_path.rsplit("/", 1)[0])
                if not self.current_path:
                    self.current_path = "/"
        elif path == "/":
            self.current_path = "/"
        else:
            if path.startswith("/"):
                new_path = path
            else:
                if self.current_path == "/":
                    new_path = f"/{path}"
                else:
                    new_path = f"{self.current_path}/{path}"

            stat = self.vfs.stat(
                new_path, self.current_user_uid, self.current_user_gid
            )
            if stat and stat["type"] == "directory":
                self.current_path = new_path
            else:
                self._print_output(f"cd: '{path}': No such directory")
                return

        self.prompt_label.setText(f"root@pyvirtos:{self.current_path}$ ")

    def _cmd_pwd(self) -> None:
        """Print working directory."""
        self._print_output(self.current_path)

    def _cmd_cat(self, args: list) -> None:
        """Display file contents."""
        if not args:
            self._print_output("cat: missing operand")
            return

        if not self.vfs:
            self._print_output("Filesystem not available")
            return

        path = args[0]
        if not path.startswith("/"):
            if self.current_path == "/":
                path = f"/{path}"
            else:
                path = f"{self.current_path}/{path}"

        data = self.vfs.read(path, self.current_user_uid, self.current_user_gid)
        if data is None:
            self._print_output(f"cat: '{path}': No such file or permission denied")
        else:
            try:
                self._print_output(data.decode("utf-8"))
            except UnicodeDecodeError:
                self._print_output(f"cat: '{path}': Binary file")

    def _cmd_touch(self, args: list) -> None:
        """Create empty file."""
        if not args:
            self._print_output("touch: missing operand")
            return

        if not self.vfs:
            self._print_output("Filesystem not available")
            return

        path = args[0]
        if not path.startswith("/"):
            if self.current_path == "/":
                path = f"/{path}"
            else:
                path = f"{self.current_path}/{path}"

        if self.vfs.touch(path, self.current_user_uid, self.current_user_gid):
            self._print_output(f"Created: {path}")
        else:
            self._print_output(f"touch: cannot create '{path}'")

    def _cmd_mkdir(self, args: list) -> None:
        """Create directory."""
        if not args:
            self._print_output("mkdir: missing operand")
            return

        if not self.vfs:
            self._print_output("Filesystem not available")
            return

        path = args[0]
        if not path.startswith("/"):
            if self.current_path == "/":
                path = f"/{path}"
            else:
                path = f"{self.current_path}/{path}"

        if self.vfs.mkdir(path, self.current_user_uid, self.current_user_gid):
            self._print_output(f"Created directory: {path}")
        else:
            self._print_output(f"mkdir: cannot create '{path}'")

    def _cmd_echo(self, args: list) -> None:
        """Print text."""
        if not args:
            self._print_output("")
        else:
            self._print_output(" ".join(args))
