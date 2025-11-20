"""Workspace Manager for PyVirtOS.

Handles multiple virtual desktops and workspace management.
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("pyvirtos.workspace")


class WorkspaceState(Enum):
    """Workspace states."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRANSITIONING = "transitioning"


@dataclass
class Window:
    """Window representation."""

    window_id: str
    title: str
    x: int
    y: int
    width: int
    height: int
    minimized: bool = False
    maximized: bool = False
    focused: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Window":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Workspace:
    """Virtual workspace/desktop."""

    workspace_id: int
    name: str
    windows: List[Window] = None
    state: WorkspaceState = WorkspaceState.INACTIVE
    background_color: str = "#1a1a1a"

    def __post_init__(self):
        """Initialize defaults."""
        if self.windows is None:
            self.windows = []

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "windows": [w.to_dict() for w in self.windows],
            "state": self.state.value,
            "background_color": self.background_color,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Workspace":
        """Create from dictionary."""
        windows = [Window.from_dict(w) for w in data.get("windows", [])]
        return cls(
            workspace_id=data.get("workspace_id", 0),
            name=data.get("name", ""),
            windows=windows,
            state=WorkspaceState(data.get("state", "inactive")),
            background_color=data.get("background_color", "#1a1a1a"),
        )


class WorkspaceManager:
    """Manages multiple virtual workspaces."""

    def __init__(self, kernel=None, num_workspaces: int = 3):
        """Initialize workspace manager.

        Args:
            kernel: Kernel instance
            num_workspaces: Number of workspaces to create
        """
        self.kernel = kernel
        self.workspaces: Dict[int, Workspace] = {}
        self.current_workspace_id: int = 0
        self.workspace_callbacks: List[Callable] = []

        # Create workspaces
        for i in range(num_workspaces):
            workspace = Workspace(
                workspace_id=i,
                name=f"Workspace {i + 1}",
                state=WorkspaceState.ACTIVE if i == 0 else WorkspaceState.INACTIVE,
            )
            self.workspaces[i] = workspace

        logger.info(f"WorkspaceManager initialized with {num_workspaces} workspaces")

    def get_workspaces(self) -> List[Workspace]:
        """Get all workspaces.

        Returns:
            List of workspaces
        """
        return list(self.workspaces.values())

    def get_workspace(self, workspace_id: int) -> Optional[Workspace]:
        """Get workspace by ID.

        Args:
            workspace_id: Workspace ID

        Returns:
            Workspace or None
        """
        return self.workspaces.get(workspace_id)

    def get_current_workspace(self) -> Optional[Workspace]:
        """Get current active workspace.

        Returns:
            Current workspace or None
        """
        return self.workspaces.get(self.current_workspace_id)

    def switch_workspace(self, workspace_id: int) -> bool:
        """Switch to a different workspace.

        Args:
            workspace_id: Target workspace ID

        Returns:
            True if successful
        """
        if workspace_id not in self.workspaces:
            logger.error(f"Workspace not found: {workspace_id}")
            return False

        # Deactivate current workspace
        current = self.get_current_workspace()
        if current:
            current.state = WorkspaceState.INACTIVE

        # Activate new workspace
        new_workspace = self.workspaces[workspace_id]
        new_workspace.state = WorkspaceState.ACTIVE
        self.current_workspace_id = workspace_id

        logger.info(f"Switched to workspace: {new_workspace.name}")
        self._emit_workspace_changed()
        return True

    def add_window(self, workspace_id: int, window: Window) -> bool:
        """Add window to workspace.

        Args:
            workspace_id: Workspace ID
            window: Window to add

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        workspace.windows.append(window)
        logger.info(f"Added window {window.window_id} to {workspace.name}")
        self._emit_window_added(workspace_id, window)
        return True

    def remove_window(self, workspace_id: int, window_id: str) -> bool:
        """Remove window from workspace.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        workspace.windows = [w for w in workspace.windows if w.window_id != window_id]
        logger.info(f"Removed window {window_id} from {workspace.name}")
        self._emit_window_removed(workspace_id, window_id)
        return True

    def get_workspace_windows(self, workspace_id: int) -> Optional[List[Window]]:
        """Get windows in workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of windows or None
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None
        return workspace.windows

    def move_window(
        self, workspace_id: int, window_id: str, x: int, y: int
    ) -> bool:
        """Move window to new position.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID
            x: New X coordinate
            y: New Y coordinate

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        for window in workspace.windows:
            if window.window_id == window_id:
                window.x = x
                window.y = y
                self._emit_window_moved(workspace_id, window_id, x, y)
                return True

        return False

    def resize_window(
        self, workspace_id: int, window_id: str, width: int, height: int
    ) -> bool:
        """Resize window.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID
            width: New width
            height: New height

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        for window in workspace.windows:
            if window.window_id == window_id:
                window.width = width
                window.height = height
                self._emit_window_resized(workspace_id, window_id, width, height)
                return True

        return False

    def focus_window(self, workspace_id: int, window_id: str) -> bool:
        """Focus a window.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        # Unfocus all windows
        for window in workspace.windows:
            window.focused = False

        # Focus target window
        for window in workspace.windows:
            if window.window_id == window_id:
                window.focused = True
                self._emit_window_focused(workspace_id, window_id)
                return True

        return False

    def minimize_window(self, workspace_id: int, window_id: str) -> bool:
        """Minimize window.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        for window in workspace.windows:
            if window.window_id == window_id:
                window.minimized = True
                self._emit_window_minimized(workspace_id, window_id)
                return True

        return False

    def maximize_window(self, workspace_id: int, window_id: str) -> bool:
        """Maximize window.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        for window in workspace.windows:
            if window.window_id == window_id:
                window.maximized = True
                self._emit_window_maximized(workspace_id, window_id)
                return True

        return False

    def restore_window(self, workspace_id: int, window_id: str) -> bool:
        """Restore minimized/maximized window.

        Args:
            workspace_id: Workspace ID
            window_id: Window ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        for window in workspace.windows:
            if window.window_id == window_id:
                window.minimized = False
                window.maximized = False
                self._emit_window_restored(workspace_id, window_id)
                return True

        return False

    def tile_windows_horizontal(self, workspace_id: int) -> bool:
        """Tile windows horizontally.

        Args:
            workspace_id: Workspace ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace or not workspace.windows:
            return False

        windows = workspace.windows
        screen_height = 1080
        window_height = screen_height // len(windows)

        for i, window in enumerate(windows):
            window.x = 0
            window.y = i * window_height
            window.width = 1920
            window.height = window_height

        logger.info(f"Tiled {len(windows)} windows horizontally")
        self._emit_windows_tiled(workspace_id)
        return True

    def tile_windows_vertical(self, workspace_id: int) -> bool:
        """Tile windows vertically.

        Args:
            workspace_id: Workspace ID

        Returns:
            True if successful
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace or not workspace.windows:
            return False

        windows = workspace.windows
        screen_width = 1920
        window_width = screen_width // len(windows)

        for i, window in enumerate(windows):
            window.x = i * window_width
            window.y = 0
            window.width = window_width
            window.height = 1080

        logger.info(f"Tiled {len(windows)} windows vertically")
        self._emit_windows_tiled(workspace_id)
        return True

    def subscribe_workspace_change(self, callback: Callable) -> None:
        """Subscribe to workspace changes.

        Args:
            callback: Callback function
        """
        self.workspace_callbacks.append(callback)

    def get_workspace_stats(self) -> Dict[str, Any]:
        """Get workspace statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_workspaces": len(self.workspaces),
            "current_workspace": self.current_workspace_id,
            "total_windows": sum(len(w.windows) for w in self.workspaces.values()),
            "workspaces": [ws.to_dict() for ws in self.workspaces.values()],
        }

    # Private helper methods

    def _emit_workspace_changed(self) -> None:
        """Emit workspace changed event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit("workspace_changed", self.current_workspace_id)

        for callback in self.workspace_callbacks:
            try:
                callback("workspace_changed", self.current_workspace_id)
            except Exception as e:
                logger.error(f"Error in workspace callback: {e}")

    def _emit_window_added(self, workspace_id: int, window: Window) -> None:
        """Emit window added event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit("window_added", {"workspace_id": workspace_id, "window": window.to_dict()})

    def _emit_window_removed(self, workspace_id: int, window_id: str) -> None:
        """Emit window removed event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit("window_removed", {"workspace_id": workspace_id, "window_id": window_id})

    def _emit_window_moved(self, workspace_id: int, window_id: str, x: int, y: int) -> None:
        """Emit window moved event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "window_moved",
                {"workspace_id": workspace_id, "window_id": window_id, "x": x, "y": y},
            )

    def _emit_window_resized(
        self, workspace_id: int, window_id: str, width: int, height: int
    ) -> None:
        """Emit window resized event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "window_resized",
                {"workspace_id": workspace_id, "window_id": window_id, "width": width, "height": height},
            )

    def _emit_window_focused(self, workspace_id: int, window_id: str) -> None:
        """Emit window focused event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "window_focused",
                {"workspace_id": workspace_id, "window_id": window_id},
            )

    def _emit_window_minimized(self, workspace_id: int, window_id: str) -> None:
        """Emit window minimized event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "window_minimized",
                {"workspace_id": workspace_id, "window_id": window_id},
            )

    def _emit_window_maximized(self, workspace_id: int, window_id: str) -> None:
        """Emit window maximized event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "window_maximized",
                {"workspace_id": workspace_id, "window_id": window_id},
            )

    def _emit_window_restored(self, workspace_id: int, window_id: str) -> None:
        """Emit window restored event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "window_restored",
                {"workspace_id": workspace_id, "window_id": window_id},
            )

    def _emit_windows_tiled(self, workspace_id: int) -> None:
        """Emit windows tiled event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "windows_tiled",
                {"workspace_id": workspace_id},
            )
