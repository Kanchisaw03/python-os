"""App Manager Service for PyVirtOS.

Handles dynamic app loading, validation, and lifecycle management.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("pyvirtos.app_manager")


class AppState(Enum):
    """App lifecycle states."""

    INSTALLED = "installed"
    RUNNING = "running"
    SUSPENDED = "suspended"
    CRASHED = "crashed"


@dataclass
class AppMetadata:
    """App metadata from metadata.json."""

    name: str
    version: str
    entry: str
    icon: Optional[str] = None
    permissions: List[str] = None
    description: str = ""
    author: str = ""

    def __post_init__(self):
        """Initialize defaults."""
        if self.permissions is None:
            self.permissions = []

    @classmethod
    def from_dict(cls, data: Dict) -> "AppMetadata":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "Unknown"),
            version=data.get("version", "1.0"),
            entry=data.get("entry", "main.py"),
            icon=data.get("icon"),
            permissions=data.get("permissions", []),
            description=data.get("description", ""),
            author=data.get("author", ""),
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AppInstance:
    """Running app instance."""

    app_id: str
    app_name: str
    pid: int
    state: AppState
    metadata: AppMetadata
    window_id: Optional[str] = None
    memory_usage: int = 0
    cpu_time: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "pid": self.pid,
            "state": self.state.value,
            "metadata": self.metadata.to_dict(),
            "window_id": self.window_id,
            "memory_usage": self.memory_usage,
            "cpu_time": self.cpu_time,
        }


class AppManager:
    """Manages app installation, loading, and lifecycle."""

    def __init__(self, apps_dir: Path, kernel=None):
        """Initialize app manager.

        Args:
            apps_dir: Directory containing apps
            kernel: Kernel instance for service access
        """
        self.apps_dir = apps_dir
        self.kernel = kernel
        self.installed_apps: Dict[str, AppMetadata] = {}
        self.running_instances: Dict[str, AppInstance] = {}
        self.app_callbacks: Dict[str, List[Callable]] = {}
        self.next_app_id = 1

        # Create apps directory if needed
        self.apps_dir.mkdir(parents=True, exist_ok=True)

        # Scan for installed apps
        self._scan_apps()

        logger.info(f"AppManager initialized with {len(self.installed_apps)} apps")

    def _scan_apps(self) -> None:
        """Scan apps directory for installed apps."""
        self.installed_apps.clear()

        for app_dir in self.apps_dir.iterdir():
            if not app_dir.is_dir():
                continue

            metadata_file = app_dir / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r") as f:
                    data = json.load(f)
                    metadata = AppMetadata.from_dict(data)
                    self.installed_apps[metadata.name] = metadata
                    logger.info(f"Discovered app: {metadata.name} v{metadata.version}")
            except Exception as e:
                logger.error(f"Failed to load app from {app_dir}: {e}")

    def get_installed_apps(self) -> List[AppMetadata]:
        """Get list of installed apps.

        Returns:
            List of app metadata
        """
        return list(self.installed_apps.values())

    def get_app(self, app_name: str) -> Optional[AppMetadata]:
        """Get app metadata by name.

        Args:
            app_name: Name of app

        Returns:
            App metadata or None
        """
        return self.installed_apps.get(app_name)

    def launch_app(
        self, app_name: str, pid: int, window_id: Optional[str] = None
    ) -> Optional[AppInstance]:
        """Launch an app instance.

        Args:
            app_name: Name of app to launch
            pid: Process ID for the app
            window_id: Optional window ID

        Returns:
            App instance or None if failed
        """
        metadata = self.get_app(app_name)
        if not metadata:
            logger.error(f"App not found: {app_name}")
            return None

        # Check permissions
        if not self._check_permissions(metadata):
            logger.error(f"Permission denied for app: {app_name}")
            return None

        # Create instance
        app_id = f"app_{self.next_app_id}"
        self.next_app_id += 1

        instance = AppInstance(
            app_id=app_id,
            app_name=app_name,
            pid=pid,
            state=AppState.RUNNING,
            metadata=metadata,
            window_id=window_id,
        )

        self.running_instances[app_id] = instance
        logger.info(f"Launched app: {app_name} (PID={pid}, ID={app_id})")

        self._emit_event("app_launched", instance)
        return instance

    def close_app(self, app_id: str) -> bool:
        """Close a running app instance.

        Args:
            app_id: App instance ID

        Returns:
            True if successful
        """
        instance = self.running_instances.pop(app_id, None)
        if not instance:
            return False

        logger.info(f"Closed app: {instance.app_name} (ID={app_id})")
        self._emit_event("app_closed", instance)
        return True

    def suspend_app(self, app_id: str) -> bool:
        """Suspend a running app.

        Args:
            app_id: App instance ID

        Returns:
            True if successful
        """
        instance = self.running_instances.get(app_id)
        if not instance:
            return False

        instance.state = AppState.SUSPENDED
        logger.info(f"Suspended app: {instance.app_name} (ID={app_id})")
        self._emit_event("app_suspended", instance)
        return True

    def resume_app(self, app_id: str) -> bool:
        """Resume a suspended app.

        Args:
            app_id: App instance ID

        Returns:
            True if successful
        """
        instance = self.running_instances.get(app_id)
        if not instance:
            return False

        if instance.state != AppState.SUSPENDED:
            return False

        instance.state = AppState.RUNNING
        logger.info(f"Resumed app: {instance.app_name} (ID={app_id})")
        self._emit_event("app_resumed", instance)
        return True

    def get_running_apps(self) -> List[AppInstance]:
        """Get list of running app instances.

        Returns:
            List of app instances
        """
        return list(self.running_instances.values())

    def get_app_instance(self, app_id: str) -> Optional[AppInstance]:
        """Get app instance by ID.

        Args:
            app_id: App instance ID

        Returns:
            App instance or None
        """
        return self.running_instances.get(app_id)

    def update_app_stats(
        self, app_id: str, memory_usage: int = None, cpu_time: int = None
    ) -> bool:
        """Update app statistics.

        Args:
            app_id: App instance ID
            memory_usage: Memory usage in bytes
            cpu_time: CPU time in milliseconds

        Returns:
            True if successful
        """
        instance = self.running_instances.get(app_id)
        if not instance:
            return False

        if memory_usage is not None:
            instance.memory_usage = memory_usage
        if cpu_time is not None:
            instance.cpu_time = cpu_time

        return True

    def _check_permissions(self, metadata: AppMetadata) -> bool:
        """Check if app has required permissions.

        Args:
            metadata: App metadata

        Returns:
            True if permissions are valid
        """
        # For now, allow all permissions
        # In a real system, this would check against a permission policy
        return True

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to app events.

        Args:
            event_name: Event name
            callback: Callback function
        """
        if event_name not in self.app_callbacks:
            self.app_callbacks[event_name] = []
        self.app_callbacks[event_name].append(callback)

    def _emit_event(self, event_name: str, data: Any) -> None:
        """Emit an app event.

        Args:
            event_name: Event name
            data: Event data
        """
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(f"app_{event_name}", data)

        for callback in self.app_callbacks.get(event_name, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in app event callback: {e}")

    def get_app_path(self, app_name: str) -> Optional[Path]:
        """Get the directory path for an app.

        Args:
            app_name: Name of app

        Returns:
            Path to app directory or None
        """
        for app_dir in self.apps_dir.iterdir():
            if app_dir.is_dir() and app_dir.name.lower() == app_name.lower():
                return app_dir

        return None

    def get_app_entry_point(self, app_name: str) -> Optional[Path]:
        """Get the entry point file for an app.

        Args:
            app_name: Name of app

        Returns:
            Path to entry point or None
        """
        metadata = self.get_app(app_name)
        if not metadata:
            return None

        app_dir = self.get_app_path(app_name)
        if not app_dir:
            return None

        entry_path = app_dir / metadata.entry
        if entry_path.exists():
            return entry_path

        return None

    def get_app_stats(self) -> Dict[str, Any]:
        """Get app manager statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "installed_apps": len(self.installed_apps),
            "running_instances": len(self.running_instances),
            "apps": [app.to_dict() for app in self.get_running_apps()],
        }
