"""Main entry point for PyVirtOS."""

import asyncio
import logging
import sys
from pathlib import Path

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.filesystem import VirtualFilesystem
from pyvirtos.core.users import UserManager
from pyvirtos.core.memory import MemoryManager


def setup_logging():
    """Setup logging configuration."""
    log_dir = Path.home() / ".pyvirtos" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "pyvirtos.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


async def main_cli():
    """CLI mode entry point."""
    setup_logging()
    logger = logging.getLogger("main")

    logger.info("Starting PyVirtOS (CLI mode)...")

    # Create and start kernel
    kernel = Kernel()
    await kernel.start()

    logger.info("Kernel started. System ready.")

    # For now, just run for a few ticks to demonstrate
    try:
        for _ in range(10):
            await kernel.tick()
            await asyncio.sleep(0.05)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        kernel.stop()
        logger.info("PyVirtOS shutdown complete")


def main_gui():
    """GUI mode entry point."""
    setup_logging()
    logger = logging.getLogger("main")

    logger.info("Starting PyVirtOS (GUI mode)...")

    # Create kernel and services
    kernel = Kernel()

    # Initialize filesystem
    vfs_root = Path.home() / ".pyvirtos" / "vfs"
    vfs = VirtualFilesystem(vfs_root)
    kernel.register_service("filesystem", vfs)

    # Initialize user manager
    users_db = Path.home() / ".pyvirtos" / "users.db"
    user_manager = UserManager(users_db)
    kernel.register_service("users", user_manager)

    # Initialize memory manager
    memory_manager = MemoryManager(physical_memory_mb=64)
    kernel.register_service("memory", memory_manager)

    # Initialize app manager
    from pyvirtos.core.app_manager import AppManager
    apps_dir = Path.home() / ".pyvirtos" / "apps"
    app_manager = AppManager(apps_dir, kernel)
    kernel.register_service("app_manager", app_manager)

    # Initialize theme manager
    from pyvirtos.core.theme import ThemeManager
    themes_dir = Path.home() / ".pyvirtos" / "themes"
    theme_manager = ThemeManager(themes_dir, kernel)
    kernel.register_service("theme_manager", theme_manager)

    # Initialize snapshot manager
    from pyvirtos.core.snapshot import SnapshotManager
    snapshots_dir = Path.home() / ".pyvirtos" / "snapshots"
    snapshot_manager = SnapshotManager(snapshots_dir, kernel)
    kernel.register_service("snapshot_manager", snapshot_manager)

    # Initialize workspace manager
    from pyvirtos.core.workspace import WorkspaceManager
    workspace_manager = WorkspaceManager(kernel, num_workspaces=3)
    kernel.register_service("workspace_manager", workspace_manager)

    # Initialize animation engine
    from pyvirtos.core.animation import AnimationEngine
    animation_engine = AnimationEngine(kernel)
    kernel.register_service("animation_engine", animation_engine)

    logger.info("Services initialized")

    # Launch GUI
    try:
        from pyvirtos.ui.desktop_enhanced import run_desktop

        return asyncio.run(run_desktop(kernel))
    except ImportError:
        logger.error("PySide6 not installed. Install with: pip install PySide6")
        return 1


def main():
    """Main entry point."""
    # Check for GUI flag
    if "--cli" in sys.argv:
        asyncio.run(main_cli())
    else:
        sys.exit(main_gui())


if __name__ == "__main__":
    main()
