"""Tests for advanced PyVirtOS features."""

import pytest
from pathlib import Path
from pyvirtos.core.app_manager import AppManager, AppMetadata, AppState
from pyvirtos.core.theme import ThemeManager, Theme, ThemeColors
from pyvirtos.core.snapshot import SnapshotManager
from pyvirtos.core.shell import ShellParser, ShellExecutor
from pyvirtos.core.kernel import Kernel
from pyvirtos.core.filesystem import VirtualFilesystem
from pyvirtos.core.users import UserManager
from pyvirtos.core.scheduler import RoundRobinScheduler


class TestAppManager:
    """Test app manager functionality."""

    def test_app_manager_initialization(self, tmp_path):
        """Test app manager initialization."""
        app_manager = AppManager(tmp_path)
        assert app_manager is not None
        assert len(app_manager.get_installed_apps()) == 0

    def test_launch_app(self, tmp_path):
        """Test launching an app."""
        app_manager = AppManager(tmp_path)
        
        # Create a test app
        app_dir = tmp_path / "TestApp"
        app_dir.mkdir()
        
        metadata = {
            "name": "TestApp",
            "version": "1.0",
            "entry": "main.py",
            "permissions": ["filesystem"]
        }
        
        with open(app_dir / "metadata.json", "w") as f:
            import json
            json.dump(metadata, f)
        
        # Rescan apps
        app_manager._scan_apps()
        
        # Launch app
        instance = app_manager.launch_app("TestApp", pid=1)
        assert instance is not None
        assert instance.app_name == "TestApp"
        assert instance.state == AppState.RUNNING

    def test_suspend_resume_app(self, tmp_path):
        """Test suspending and resuming an app."""
        app_manager = AppManager(tmp_path)
        
        # Create test app
        app_dir = tmp_path / "TestApp"
        app_dir.mkdir()
        
        metadata = {
            "name": "TestApp",
            "version": "1.0",
            "entry": "main.py"
        }
        
        with open(app_dir / "metadata.json", "w") as f:
            import json
            json.dump(metadata, f)
        
        app_manager._scan_apps()
        instance = app_manager.launch_app("TestApp", pid=1)
        
        # Suspend
        assert app_manager.suspend_app(instance.app_id)
        assert instance.state == AppState.SUSPENDED
        
        # Resume
        assert app_manager.resume_app(instance.app_id)
        assert instance.state == AppState.RUNNING


class TestThemeManager:
    """Test theme manager functionality."""

    def test_theme_manager_initialization(self, tmp_path):
        """Test theme manager initialization."""
        theme_manager = ThemeManager(tmp_path)
        assert theme_manager is not None
        assert len(theme_manager.get_themes()) > 0

    def test_get_builtin_themes(self, tmp_path):
        """Test getting built-in themes."""
        theme_manager = ThemeManager(tmp_path)
        themes = theme_manager.get_themes()
        
        theme_names = [t.name for t in themes]
        assert "NeonDark" in theme_names
        assert "Ocean" in theme_names
        assert "Forest" in theme_names
        assert "Sunset" in theme_names

    def test_set_theme(self, tmp_path):
        """Test setting current theme."""
        theme_manager = ThemeManager(tmp_path)
        
        assert theme_manager.set_theme("Ocean")
        current = theme_manager.get_current_theme()
        assert current.name == "Ocean"

    def test_create_custom_theme(self, tmp_path):
        """Test creating a custom theme."""
        theme_manager = ThemeManager(tmp_path)
        
        colors = {
            "background": "#000000",
            "foreground": "#ffffff",
            "accent": "#ff0000",
        }
        
        assert theme_manager.create_theme("CustomTheme", colors, "My custom theme")
        theme = theme_manager.get_theme("CustomTheme")
        assert theme is not None
        assert theme.name == "CustomTheme"

    def test_get_stylesheet(self, tmp_path):
        """Test getting Qt stylesheet."""
        theme_manager = ThemeManager(tmp_path)
        theme_manager.set_theme("NeonDark")
        
        stylesheet = theme_manager.get_stylesheet()
        assert stylesheet is not None
        assert "QMainWindow" in stylesheet
        assert "#0f0f0f" in stylesheet  # NeonDark background


class TestSnapshotManager:
    """Test snapshot manager functionality."""

    def test_snapshot_manager_initialization(self, tmp_path):
        """Test snapshot manager initialization."""
        snapshot_manager = SnapshotManager(tmp_path)
        assert snapshot_manager is not None
        assert len(snapshot_manager.list_snapshots()) == 0

    def test_save_snapshot(self, tmp_path):
        """Test saving a snapshot."""
        kernel = Kernel()
        snapshot_manager = SnapshotManager(tmp_path, kernel)
        
        # Create basic services
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        kernel.register_service("filesystem", vfs)
        
        users_db = tmp_path / "users.db"
        users = UserManager(users_db)
        kernel.register_service("users", users)
        
        scheduler = RoundRobinScheduler()
        kernel.register_service("scheduler", scheduler)
        
        # Save snapshot
        assert snapshot_manager.save_snapshot("test_snapshot", "Test snapshot")
        
        snapshots = snapshot_manager.list_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0].name == "test_snapshot"

    def test_delete_snapshot(self, tmp_path):
        """Test deleting a snapshot."""
        kernel = Kernel()
        snapshot_manager = SnapshotManager(tmp_path, kernel)
        
        # Create basic services
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        kernel.register_service("filesystem", vfs)
        
        # Save snapshot
        snapshot_manager.save_snapshot("test_snapshot")
        assert len(snapshot_manager.list_snapshots()) == 1
        
        # Delete snapshot
        assert snapshot_manager.delete_snapshot("test_snapshot")
        assert len(snapshot_manager.list_snapshots()) == 0


class TestShellParser:
    """Test shell command parser."""

    def test_parse_simple_command(self):
        """Test parsing simple command."""
        parser = ShellParser()
        assert parser.parse("ls /home")
        
        commands = parser.get_commands()
        assert len(commands) == 1
        assert commands[0]["command"] == "ls"
        assert "/home" in commands[0]["args"]

    def test_parse_command_with_flags(self):
        """Test parsing command with flags."""
        parser = ShellParser()
        assert parser.parse("ls --json /home")
        
        commands = parser.get_commands()
        assert "json" in commands[0]["flags"]

    def test_parse_piped_commands(self):
        """Test parsing piped commands."""
        parser = ShellParser()
        assert parser.parse("ls /home | grep alice")
        
        assert parser.has_pipes()
        commands = parser.get_commands()
        assert len(commands) == 2
        assert commands[0]["command"] == "ls"
        assert commands[1]["command"] == "grep"

    def test_parse_output_redirect(self):
        """Test parsing output redirect."""
        parser = ShellParser()
        assert parser.parse("echo hello > output.txt")
        
        assert parser.has_redirect()
        assert parser.redirect_output == "output.txt"
        assert not parser.redirect_append

    def test_parse_append_redirect(self):
        """Test parsing append redirect."""
        parser = ShellParser()
        assert parser.parse("echo hello >> output.txt")
        
        assert parser.has_redirect()
        assert parser.redirect_output == "output.txt"
        assert parser.redirect_append


class TestShellExecutor:
    """Test shell command executor."""

    def test_executor_initialization(self, tmp_path):
        """Test executor initialization."""
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        
        users_db = tmp_path / "users.db"
        users = UserManager(users_db)
        
        scheduler = RoundRobinScheduler()
        
        executor = ShellExecutor(vfs, users, scheduler)
        assert executor is not None

    def test_execute_help_command(self, tmp_path):
        """Test executing help command."""
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        
        users_db = tmp_path / "users.db"
        users = UserManager(users_db)
        
        scheduler = RoundRobinScheduler()
        
        executor = ShellExecutor(vfs, users, scheduler)
        output, success = executor.execute("help")
        
        assert success
        assert "commands" in output.lower()

    def test_execute_pwd_command(self, tmp_path):
        """Test executing pwd command."""
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        
        users_db = tmp_path / "users.db"
        users = UserManager(users_db)
        
        scheduler = RoundRobinScheduler()
        
        executor = ShellExecutor(vfs, users, scheduler)
        output, success = executor.execute("pwd")
        
        assert success
        assert output == "/"

    def test_execute_echo_command(self, tmp_path):
        """Test executing echo command."""
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        
        users_db = tmp_path / "users.db"
        users = UserManager(users_db)
        
        scheduler = RoundRobinScheduler()
        
        executor = ShellExecutor(vfs, users, scheduler)
        output, success = executor.execute("echo hello world")
        
        assert success
        assert "hello world" in output

    def test_execute_piped_commands(self, tmp_path):
        """Test executing piped commands."""
        vfs_dir = tmp_path / "vfs"
        vfs = VirtualFilesystem(vfs_dir)
        
        users_db = tmp_path / "users.db"
        users = UserManager(users_db)
        
        scheduler = RoundRobinScheduler()
        
        executor = ShellExecutor(vfs, users, scheduler)
        output, success = executor.execute("echo 'hello world' | grep hello")
        
        assert success
        assert "hello" in output
