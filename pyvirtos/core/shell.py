"""Advanced Shell with pipes and redirects support."""

import logging
from typing import List, Optional, Tuple, Dict, Any
from io import StringIO

logger = logging.getLogger("pyvirtos.shell")


class ShellParser:
    """Parses shell commands with pipes and redirects."""

    def __init__(self):
        """Initialize parser."""
        self.commands: List[Dict[str, Any]] = []
        self.redirect_output: Optional[str] = None
        self.redirect_append: bool = False

    def parse(self, command_line: str) -> bool:
        """Parse a command line.

        Args:
            command_line: Full command line string

        Returns:
            True if parsing successful
        """
        self.commands.clear()
        self.redirect_output = None
        self.redirect_append = False

        # Handle output redirection
        if ">>" in command_line:
            command_line, self.redirect_output = command_line.split(">>", 1)
            self.redirect_append = True
            self.redirect_output = self.redirect_output.strip()
        elif ">" in command_line:
            command_line, self.redirect_output = command_line.split(">", 1)
            self.redirect_append = False
            self.redirect_output = self.redirect_output.strip()

        # Split by pipes
        pipe_commands = command_line.split("|")

        for pipe_cmd in pipe_commands:
            pipe_cmd = pipe_cmd.strip()
            if not pipe_cmd:
                continue

            # Parse individual command
            parts = self._tokenize(pipe_cmd)
            if not parts:
                continue

            cmd_dict = {
                "command": parts[0],
                "args": parts[1:],
                "flags": self._extract_flags(parts[1:]),
            }
            self.commands.append(cmd_dict)

        return len(self.commands) > 0

    def _tokenize(self, cmd: str) -> List[str]:
        """Tokenize a command string.

        Args:
            cmd: Command string

        Returns:
            List of tokens
        """
        tokens = []
        current = ""
        in_quotes = False

        for char in cmd:
            if char == '"':
                in_quotes = not in_quotes
            elif char == " " and not in_quotes:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += char

        if current:
            tokens.append(current)

        return tokens

    def _extract_flags(self, args: List[str]) -> Dict[str, bool]:
        """Extract flags from arguments.

        Args:
            args: Argument list

        Returns:
            Dictionary of flags
        """
        flags = {}
        for arg in args:
            if arg.startswith("--"):
                flag_name = arg[2:]
                flags[flag_name] = True
        return flags

    def get_commands(self) -> List[Dict[str, Any]]:
        """Get parsed commands.

        Returns:
            List of command dictionaries
        """
        return self.commands

    def has_pipes(self) -> bool:
        """Check if command has pipes.

        Returns:
            True if multiple commands
        """
        return len(self.commands) > 1

    def has_redirect(self) -> bool:
        """Check if command has output redirect.

        Returns:
            True if redirect specified
        """
        return self.redirect_output is not None


class ShellExecutor:
    """Executes parsed shell commands."""

    def __init__(self, vfs, users, scheduler, app_manager=None):
        """Initialize executor.

        Args:
            vfs: Virtual filesystem
            users: User manager
            scheduler: Process scheduler
            app_manager: App manager (optional)
        """
        self.vfs = vfs
        self.users = users
        self.scheduler = scheduler
        self.app_manager = app_manager
        self.kernel = None  # Will be set by terminal
        self.current_user = "root"
        self.current_dir = "/"
        self.output_buffer = StringIO()

    def execute(self, command_line: str, uid: int = 0, gid: int = 0) -> Tuple[str, bool]:
        """Execute a command line.

        Args:
            command_line: Full command line
            uid: User ID
            gid: Group ID

        Returns:
            Tuple of (output, success)
        """
        parser = ShellParser()
        if not parser.parse(command_line):
            return "Error: Invalid command", False

        # Execute command chain
        output = ""
        success = True

        try:
            commands = parser.get_commands()

            # Execute first command
            if commands:
                output = self._execute_command(
                    commands[0]["command"],
                    commands[0]["args"],
                    commands[0]["flags"],
                    uid,
                    gid,
                )

            # Execute piped commands
            for cmd_dict in commands[1:]:
                # Pass previous output as input to next command
                output = self._execute_piped_command(
                    cmd_dict["command"],
                    cmd_dict["args"],
                    cmd_dict["flags"],
                    output,
                    uid,
                    gid,
                )

            # Handle output redirection
            if parser.has_redirect():
                self._redirect_output(
                    parser.redirect_output,
                    output,
                    parser.redirect_append,
                    uid,
                    gid,
                )
                output = f"Output redirected to {parser.redirect_output}"

        except Exception as e:
            output = f"Error: {str(e)}"
            success = False

        return output, success

    def _execute_command(
        self,
        command: str,
        args: List[str],
        flags: Dict[str, bool],
        uid: int,
        gid: int,
    ) -> str:
        """Execute a single command.

        Args:
            command: Command name
            args: Arguments
            flags: Flags
            uid: User ID
            gid: Group ID

        Returns:
            Command output
        """
        if command == "help":
            return self._cmd_help()
        elif command == "ls":
            return self._cmd_ls(args, flags, uid, gid)
        elif command == "cd":
            return self._cmd_cd(args, uid, gid)
        elif command == "pwd":
            return self.current_dir
        elif command == "cat":
            return self._cmd_cat(args, uid, gid)
        elif command == "touch":
            return self._cmd_touch(args, uid, gid)
        elif command == "mkdir":
            return self._cmd_mkdir(args, uid, gid)
        elif command == "echo":
            return " ".join(args)
        elif command == "clear":
            return ""
        elif command == "ps":
            return self._cmd_ps(flags)
        elif command == "kill":
            return self._cmd_kill(args)
        elif command == "whoami":
            return self.current_user
        elif command == "sysinfo":
            return self._cmd_sysinfo()
        elif command == "theme":
            return self._cmd_theme(args)
        elif command == "snapshot":
            return self._cmd_snapshot(args)
        elif command == "app":
            return self._cmd_app(args)
        else:
            return f"Command not found: {command}"

    def _execute_piped_command(
        self,
        command: str,
        args: List[str],
        flags: Dict[str, bool],
        input_data: str,
        uid: int,
        gid: int,
    ) -> str:
        """Execute a piped command.

        Args:
            command: Command name
            args: Arguments
            flags: Flags
            input_data: Input from previous command
            uid: User ID
            gid: Group ID

        Returns:
            Command output
        """
        # For now, simple pipe support
        if command == "grep":
            if not args:
                return input_data
            pattern = args[0]
            lines = input_data.split("\n")
            return "\n".join([line for line in lines if pattern in line])
        elif command == "wc":
            lines = input_data.split("\n")
            words = sum(len(line.split()) for line in lines)
            chars = len(input_data)
            return f"Lines: {len(lines)}, Words: {words}, Chars: {chars}"
        else:
            return self._execute_command(command, args, flags, uid, gid)

    def _redirect_output(
        self, path: str, output: str, append: bool, uid: int, gid: int
    ) -> None:
        """Redirect output to file.

        Args:
            path: File path
            output: Output to write
            append: Whether to append
            uid: User ID
            gid: Group ID
        """
        if append:
            # Append to file
            existing = self.vfs.read(path, uid, gid)
            if existing:
                output = existing.decode() + "\n" + output
        
        self.vfs.write(path, output.encode(), uid, gid)

    # Command implementations

    def _cmd_help(self) -> str:
        """Help command."""
        return """PyVirtOS Shell Commands:
  ls [path]           - List directory
  cd <path>           - Change directory
  pwd                 - Print working directory
  cat <file>          - Display file
  touch <file>        - Create file
  mkdir <dir>         - Create directory
  echo <text>         - Print text
  ps [--json]         - List processes
  kill <pid>          - Kill process
  whoami              - Current user
  sysinfo             - System info
  theme list          - List themes
  theme set <name>    - Set theme
  snapshot save <name> - Save snapshot
  snapshot load <name> - Load snapshot
  app list            - List apps
  app launch <name>   - Launch app
  
Pipes: command1 | command2
Redirects: command > file or command >> file
"""

    def _cmd_ls(
        self, args: List[str], flags: Dict[str, bool], uid: int, gid: int
    ) -> str:
        """List directory."""
        path = args[0] if args else self.current_dir
        items = self.vfs.listdir(path, uid, gid)
        if items is None:
            return f"Error: Cannot access {path}"
        
        if flags.get("json"):
            import json
            return json.dumps(items)
        
        return "\n".join(items) if items else "(empty)"

    def _cmd_cd(self, args: List[str], uid: int, gid: int) -> str:
        """Change directory."""
        if not args:
            self.current_dir = "/"
            return ""
        
        path = args[0]
        if path == "..":
            parts = self.current_dir.rstrip("/").split("/")
            self.current_dir = "/".join(parts[:-1]) or "/"
        elif path.startswith("/"):
            self.current_dir = path
        else:
            self.current_dir = f"{self.current_dir.rstrip('/')}/{path}"
        
        # Verify directory exists
        stat = self.vfs.stat(self.current_dir, uid, gid)
        if not stat or stat.get("type") != "directory":
            self.current_dir = "/"
            return f"Error: Directory not found"
        
        return ""

    def _cmd_cat(self, args: List[str], uid: int, gid: int) -> str:
        """Display file."""
        if not args:
            return "Error: No file specified"
        
        path = args[0]
        data = self.vfs.read(path, uid, gid)
        if data is None:
            return f"Error: Cannot read {path}"
        
        return data.decode()

    def _cmd_touch(self, args: List[str], uid: int, gid: int) -> str:
        """Create file."""
        if not args:
            return "Error: No file specified"
        
        path = args[0]
        if self.vfs.touch(path, uid, gid):
            return ""
        return f"Error: Cannot create {path}"

    def _cmd_mkdir(self, args: List[str], uid: int, gid: int) -> str:
        """Create directory."""
        if not args:
            return "Error: No directory specified"
        
        path = args[0]
        if self.vfs.mkdir(path, uid, gid):
            return ""
        return f"Error: Cannot create {path}"

    def _cmd_ps(self, flags: Dict[str, bool]) -> str:
        """List processes."""
        processes = self.scheduler.get_task_list()
        if flags.get("json"):
            import json
            return json.dumps([
                {
                    "pid": p.pid,
                    "name": p.name,
                    "state": p.state.value,
                    "cpu_time": p.cpu_time,
                }
                for p in processes
            ])
        
        output = "PID\tNAME\t\tSTATE\t\tCPU_TIME"
        for p in processes:
            output += f"\n{p.pid}\t{p.name}\t\t{p.state.value}\t\t{p.cpu_time}ms"
        return output

    def _cmd_kill(self, args: List[str]) -> str:
        """Kill process."""
        if not args:
            return "Error: No PID specified"
        
        try:
            pid = int(args[0])
            proc = self.scheduler.get_process(pid)
            if proc:
                proc.kill()
                return f"Killed process {pid}"
            return f"Error: Process {pid} not found"
        except ValueError:
            return "Error: Invalid PID"

    def _cmd_sysinfo(self) -> str:
        """System information."""
        return """PyVirtOS System Information:
  OS: PyVirtOS 1.0
  Kernel: Microkernel Architecture
  Shell: PV-Shell
  Status: Running
"""

    def _cmd_theme(self, args: List[str]) -> str:
        """Theme command."""
        if not args:
            return "Usage: theme list | theme set <name>"
        
        if not self.kernel:
            return "Error: Kernel not available"
        
        theme_manager = self.kernel.get_service("theme_manager")
        if not theme_manager:
            return "Error: Theme manager not available"
        
        if args[0] == "list":
            themes = theme_manager.get_available_themes()
            return "Available themes:\n" + "\n".join(f"  - {t}" for t in themes)
        elif args[0] == "set" and len(args) > 1:
            theme_name = args[1]
            theme_manager.set_theme(theme_name)
            return f"Theme set to: {theme_name}"
        
        return "Error: Invalid theme command"

    def _cmd_snapshot(self, args: List[str]) -> str:
        """Snapshot command."""
        if not args:
            return "Usage: snapshot save <name> | snapshot load <name> | snapshot list"
        
        if not self.kernel:
            return "Error: Kernel not available"
        
        snapshot_manager = self.kernel.get_service("snapshot_manager")
        if not snapshot_manager:
            return "Error: Snapshot manager not available"
        
        if args[0] == "list":
            snapshots = snapshot_manager.list_snapshots()
            if not snapshots:
                return "No snapshots available"
            return "Available snapshots:\n" + "\n".join(f"  - {s}" for s in snapshots)
        elif args[0] == "save" and len(args) > 1:
            name = args[1]
            snapshot_manager.save_snapshot(name)
            return f"Snapshot saved: {name}"
        elif args[0] == "load" and len(args) > 1:
            name = args[1]
            snapshot_manager.load_snapshot(name)
            return f"Snapshot loaded: {name}"
        
        return "Error: Invalid snapshot command"

    def _cmd_app(self, args: List[str]) -> str:
        """App command."""
        if not args:
            return "Usage: app list | app launch <name>"
        
        if args[0] == "list":
            if self.app_manager:
                apps = self.app_manager.get_installed_apps()
                return "\n".join([f"  {app.name} v{app.version}" for app in apps])
            return "No apps installed"
        elif args[0] == "launch" and len(args) > 1:
            return f"Launching app: {args[1]}"
        
        return "Error: Invalid app command"
