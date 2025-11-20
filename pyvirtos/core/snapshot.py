"""Snapshot Service for PyVirtOS.

Handles saving and restoring complete OS state.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger("pyvirtos.snapshot")


@dataclass
class SnapshotInfo:
    """Snapshot metadata."""

    name: str
    timestamp: str
    description: str = ""
    os_version: str = "1.0"
    size_mb: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SnapshotInfo":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            timestamp=data.get("timestamp", ""),
            description=data.get("description", ""),
            os_version=data.get("os_version", "1.0"),
            size_mb=data.get("size_mb", 0.0),
        )


class SnapshotManager:
    """Manages OS state snapshots."""

    def __init__(self, snapshots_dir: Path, kernel=None):
        """Initialize snapshot manager.

        Args:
            snapshots_dir: Directory to store snapshots
            kernel: Kernel instance for service access
        """
        self.snapshots_dir = snapshots_dir
        self.kernel = kernel
        self.snapshots: Dict[str, SnapshotInfo] = {}

        # Create snapshots directory
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Scan for existing snapshots
        self._scan_snapshots()

        logger.info(f"SnapshotManager initialized with {len(self.snapshots)} snapshots")

    def _scan_snapshots(self) -> None:
        """Scan snapshots directory for existing snapshots."""
        self.snapshots.clear()

        for snapshot_dir in self.snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            info_file = snapshot_dir / "snapshot.json"
            if not info_file.exists():
                continue

            try:
                with open(info_file, "r") as f:
                    data = json.load(f)
                    info = SnapshotInfo.from_dict(data)
                    self.snapshots[info.name] = info
                    logger.info(f"Found snapshot: {info.name} ({info.timestamp})")
            except Exception as e:
                logger.error(f"Failed to load snapshot from {snapshot_dir}: {e}")

    def save_snapshot(
        self, name: str, description: str = "", include_apps: bool = True
    ) -> bool:
        """Save complete OS state to snapshot.

        Args:
            name: Snapshot name
            description: Optional description
            include_apps: Whether to include running apps

        Returns:
            True if successful
        """
        if not self.kernel:
            logger.error("Kernel not available for snapshot")
            return False

        try:
            snapshot_dir = self.snapshots_dir / name
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # Collect all system state
            state = {
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "os_version": "1.0",
            }

            # Save filesystem state
            vfs = self.kernel.get_service("filesystem")
            if vfs:
                state["filesystem"] = self._snapshot_filesystem(vfs)
                logger.info("Saved filesystem state")

            # Save user state
            users = self.kernel.get_service("users")
            if users:
                state["users"] = self._snapshot_users(users)
                logger.info("Saved user state")

            # Save process state
            scheduler = self.kernel.get_service("scheduler")
            if scheduler:
                state["processes"] = self._snapshot_processes(scheduler)
                logger.info("Saved process state")

            # Save memory state
            memory = self.kernel.get_service("memory")
            if memory:
                state["memory"] = self._snapshot_memory(memory)
                logger.info("Saved memory state")

            # Save app state
            app_manager = self.kernel.get_service("app_manager")
            if app_manager and include_apps:
                state["apps"] = self._snapshot_apps(app_manager)
                logger.info("Saved app state")

            # Save config
            state["config"] = self.kernel.config.copy()
            logger.info("Saved config state")

            # Write snapshot metadata
            info = SnapshotInfo(
                name=name,
                timestamp=state["timestamp"],
                description=description,
                os_version="1.0",
            )

            info_file = snapshot_dir / "snapshot.json"
            with open(info_file, "w") as f:
                json.dump(
                    {
                        "name": info.name,
                        "timestamp": info.timestamp,
                        "description": info.description,
                        "os_version": info.os_version,
                    },
                    f,
                    indent=2,
                )

            # Write full state
            state_file = snapshot_dir / "state.json"
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2, default=str)

            # Update snapshots list
            self.snapshots[name] = info

            logger.info(f"Snapshot saved: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False

    def load_snapshot(self, name: str) -> bool:
        """Load OS state from snapshot.

        Args:
            name: Snapshot name

        Returns:
            True if successful
        """
        if not self.kernel:
            logger.error("Kernel not available for snapshot")
            return False

        if name not in self.snapshots:
            logger.error(f"Snapshot not found: {name}")
            return False

        try:
            snapshot_dir = self.snapshots_dir / name
            state_file = snapshot_dir / "state.json"

            if not state_file.exists():
                logger.error(f"State file not found for snapshot: {name}")
                return False

            with open(state_file, "r") as f:
                state = json.load(f)

            # Restore filesystem state
            vfs = self.kernel.get_service("filesystem")
            if vfs and "filesystem" in state:
                self._restore_filesystem(vfs, state["filesystem"])
                logger.info("Restored filesystem state")

            # Restore user state
            users = self.kernel.get_service("users")
            if users and "users" in state:
                self._restore_users(users, state["users"])
                logger.info("Restored user state")

            # Restore process state
            scheduler = self.kernel.get_service("scheduler")
            if scheduler and "processes" in state:
                self._restore_processes(scheduler, state["processes"])
                logger.info("Restored process state")

            # Restore memory state
            memory = self.kernel.get_service("memory")
            if memory and "memory" in state:
                self._restore_memory(memory, state["memory"])
                logger.info("Restored memory state")

            # Restore app state
            app_manager = self.kernel.get_service("app_manager")
            if app_manager and "apps" in state:
                self._restore_apps(app_manager, state["apps"])
                logger.info("Restored app state")

            # Restore config
            if "config" in state:
                self.kernel.config.update(state["config"])
                logger.info("Restored config state")

            logger.info(f"Snapshot loaded: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return False

    def delete_snapshot(self, name: str) -> bool:
        """Delete a snapshot.

        Args:
            name: Snapshot name

        Returns:
            True if successful
        """
        if name not in self.snapshots:
            return False

        try:
            snapshot_dir = self.snapshots_dir / name
            shutil.rmtree(snapshot_dir)
            del self.snapshots[name]
            logger.info(f"Snapshot deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return False

    def list_snapshots(self) -> List[SnapshotInfo]:
        """List all snapshots.

        Returns:
            List of snapshot info
        """
        return list(self.snapshots.values())

    def get_snapshot(self, name: str) -> Optional[SnapshotInfo]:
        """Get snapshot info by name.

        Args:
            name: Snapshot name

        Returns:
            Snapshot info or None
        """
        return self.snapshots.get(name)

    # Private helper methods

    def _snapshot_filesystem(self, vfs) -> Dict:
        """Snapshot filesystem state."""
        try:
            # Get all files and directories
            result = {
                "root": self._snapshot_directory(vfs, "/"),
            }
            return result
        except Exception as e:
            logger.error(f"Error snapshotting filesystem: {e}")
            return {}

    def _snapshot_directory(self, vfs, path: str) -> Dict:
        """Recursively snapshot a directory."""
        try:
            items = vfs.listdir(path, 0, 0) or []
            result = {"path": path, "items": []}

            for item in items:
                item_path = f"{path}/{item}" if path != "/" else f"/{item}"
                stat = vfs.stat(item_path, 0, 0)

                if stat and stat.get("type") == "directory":
                    result["items"].append(
                        self._snapshot_directory(vfs, item_path)
                    )
                else:
                    result["items"].append({"path": item_path, "type": "file"})

            return result
        except Exception as e:
            logger.error(f"Error snapshotting directory {path}: {e}")
            return {"path": path, "items": []}

    def _snapshot_users(self, users) -> Dict:
        """Snapshot user state."""
        try:
            user_list = users.list_users()
            return {
                "users": [
                    {
                        "uid": u.uid,
                        "username": u.username,
                        "gid": u.gid,
                        "groups": u.groups,
                        "home_directory": u.home_directory,
                    }
                    for u in user_list
                ]
            }
        except Exception as e:
            logger.error(f"Error snapshotting users: {e}")
            return {"users": []}

    def _snapshot_processes(self, scheduler) -> Dict:
        """Snapshot process state."""
        try:
            processes = scheduler.get_task_list()
            return {
                "processes": [
                    {
                        "pid": p.pid,
                        "ppid": p.ppid,
                        "name": p.name,
                        "owner_user": p.owner_user,
                        "state": p.state.value,
                        "priority": p.priority,
                        "cpu_time": p.cpu_time,
                        "memory_used": p.memory_used,
                    }
                    for p in processes
                ]
            }
        except Exception as e:
            logger.error(f"Error snapshotting processes: {e}")
            return {"processes": []}

    def _snapshot_memory(self, memory) -> Dict:
        """Snapshot memory state."""
        try:
            info = memory.get_system_memory_info()
            return {
                "physical_memory_mb": info.get("physical_memory_mb", 0),
                "used_memory_mb": info.get("used_memory_mb", 0),
                "swap_enabled": info.get("swap_enabled", False),
            }
        except Exception as e:
            logger.error(f"Error snapshotting memory: {e}")
            return {}

    def _snapshot_apps(self, app_manager) -> Dict:
        """Snapshot app state."""
        try:
            running_apps = app_manager.get_running_apps()
            return {
                "apps": [app.to_dict() for app in running_apps]
            }
        except Exception as e:
            logger.error(f"Error snapshotting apps: {e}")
            return {"apps": []}

    def _restore_filesystem(self, vfs, state: Dict) -> None:
        """Restore filesystem state."""
        # This is a simplified restore - in production, would need more logic
        logger.info("Filesystem restore not fully implemented")

    def _restore_users(self, users, state: Dict) -> None:
        """Restore user state."""
        logger.info("User restore not fully implemented")

    def _restore_processes(self, scheduler, state: Dict) -> None:
        """Restore process state."""
        logger.info("Process restore not fully implemented")

    def _restore_memory(self, memory, state: Dict) -> None:
        """Restore memory state."""
        logger.info("Memory restore not fully implemented")

    def _restore_apps(self, app_manager, state: Dict) -> None:
        """Restore app state."""
        logger.info("App restore not fully implemented")
