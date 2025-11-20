"""GUI demo script for PyVirtOS."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.filesystem import VirtualFilesystem
from pyvirtos.core.users import UserManager
from pyvirtos.core.memory import MemoryManager
from pyvirtos.core.process import Process


async def setup_demo_environment():
    """Setup demo environment with sample data."""
    print("Setting up demo environment...")

    # Create kernel
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

    # Create sample users
    print("Creating sample users...")
    user_manager.create_user("alice", "alicepass")
    user_manager.create_user("bob", "bobpass")

    # Create filesystem structure
    print("Creating filesystem structure...")
    vfs.mkdir("/home", 0, 0)
    vfs.mkdir("/home/alice", 0, 0)
    vfs.mkdir("/home/bob", 0, 0)
    vfs.mkdir("/tmp", 0, 0)
    vfs.mkdir("/var", 0, 0)
    vfs.mkdir("/var/log", 0, 0)

    # Change ownership
    alice = user_manager.get_user("alice")
    bob = user_manager.get_user("bob")
    vfs.chown("/home/alice", alice.uid, alice.gid, 0)
    vfs.chown("/home/bob", bob.uid, bob.gid, 0)

    # Create sample files
    print("Creating sample files...")
    vfs.touch("/home/alice/readme.txt", alice.uid, alice.gid)
    vfs.write("/home/alice/readme.txt", b"Welcome to PyVirtOS!\n\nThis is Alice's home directory.", alice.uid, alice.gid)

    vfs.touch("/home/bob/notes.txt", bob.uid, bob.gid)
    vfs.write("/home/bob/notes.txt", b"Bob's notes:\n- PyVirtOS is cool\n- Virtual OS simulation", bob.uid, bob.gid)

    vfs.touch("/var/log/system.log", 0, 0)
    vfs.write("/var/log/system.log", b"[INFO] System started\n[INFO] Services initialized\n", 0, 0)

    # Create some sample processes
    print("Creating sample processes...")
    scheduler = kernel.get_service("scheduler")
    if scheduler:
        for i in range(5):
            proc = Process(
                pid=i + 1,
                ppid=0,
                name=f"demo_proc_{i}",
                owner_user="root",
                priority=5
            )
            scheduler.add_process(proc)

    print("Demo environment ready!")
    return kernel


async def main():
    """Main entry point."""
    print("PyVirtOS GUI Demo")
    print("=" * 50)

    # Setup demo environment
    kernel = await setup_demo_environment()

    # Launch GUI
    try:
        from pyvirtos.ui.desktop import run_desktop

        print("\nLaunching GUI...")
        print("Close the window to exit.")
        await run_desktop(kernel)
    except ImportError as e:
        print(f"Error: {e}")
        print("Make sure PySide6 is installed: pip install PySide6")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
