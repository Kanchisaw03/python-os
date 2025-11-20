"""Integration tests for PyVirtOS."""

import asyncio
import pytest
import tempfile
from pathlib import Path

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.process import Process
from pyvirtos.core.filesystem import VirtualFilesystem
from pyvirtos.core.users import UserManager
from pyvirtos.core.memory import MemoryManager
from pyvirtos.core.logs import SystemLogger


class TestIntegration:
    """Integration tests combining multiple modules."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_boot_sequence(self, temp_dir):
        """Test complete boot sequence."""
        config_path = temp_dir / "config.json"
        kernel = Kernel(config_path)

        await kernel.start()
        assert kernel.running is True

        scheduler = kernel.get_service("scheduler")
        assert scheduler is not None

        kernel.stop()
        assert kernel.running is False

    @pytest.mark.asyncio
    async def test_process_creation_and_scheduling(self, temp_dir):
        """Test creating and scheduling processes."""
        config_path = temp_dir / "config.json"
        kernel = Kernel(config_path)
        await kernel.start()

        scheduler = kernel.get_service("scheduler")

        # Create processes
        processes = [
            Process(pid=i, ppid=0, name=f"proc_{i}", owner_user="root")
            for i in range(1, 4)
        ]

        for proc in processes:
            scheduler.add_process(proc)

        # Run scheduler
        for _ in range(10):
            await kernel.tick()

        # Verify processes ran
        for proc in processes:
            assert proc.cpu_time > 0

        kernel.stop()

    @pytest.mark.asyncio
    async def test_filesystem_with_users(self, temp_dir):
        """Test filesystem with user permissions."""
        vfs = VirtualFilesystem(temp_dir / "vfs")
        user_manager = UserManager(temp_dir / "users.db")

        # Create users
        assert user_manager.create_user("alice", "alicepass")
        assert user_manager.create_user("bob", "bobpass")

        alice = user_manager.get_user("alice")
        bob = user_manager.get_user("bob")

        # Create directories as root
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.mkdir("/home/alice", 0, 0)
        assert vfs.mkdir("/home/bob", 0, 0)
        # Change ownership
        assert vfs.chown("/home/alice", alice.uid, alice.gid, 0)
        assert vfs.chown("/home/bob", bob.uid, bob.gid, 0)

        # Create files with restricted permissions
        assert vfs.touch("/home/alice/secret.txt", alice.uid, alice.gid, 0o600)
        assert vfs.write("/home/alice/secret.txt", b"alice's secret", alice.uid, alice.gid)

        # Alice can read her own file
        data = vfs.read("/home/alice/secret.txt", alice.uid, alice.gid)
        assert data == b"alice's secret"

        # Bob cannot read Alice's file (permission denied)
        data = vfs.read("/home/alice/secret.txt", bob.uid, bob.gid)
        assert data is None

    @pytest.mark.asyncio
    async def test_memory_allocation_and_processes(self, temp_dir):
        """Test memory allocation for processes."""
        memory_manager = MemoryManager(
            physical_memory_mb=16,
            swap_file_path=temp_dir / "swap.bin",
        )

        # Allocate memory for multiple processes
        vaddr1 = memory_manager.allocate(pid=1, size=8192)
        vaddr2 = memory_manager.allocate(pid=2, size=8192)

        assert vaddr1 is not None
        assert vaddr2 is not None

        # Write to memory
        assert memory_manager.write(pid=1, vaddr=vaddr1.start, data=b"proc1_data")
        assert memory_manager.write(pid=2, vaddr=vaddr2.start, data=b"proc2_data")

        # Read from memory
        data1 = memory_manager.read(pid=1, vaddr=vaddr1.start, size=10)
        data2 = memory_manager.read(pid=2, vaddr=vaddr2.start, size=10)

        assert data1 is not None
        assert data2 is not None

    @pytest.mark.asyncio
    async def test_system_logging(self, temp_dir):
        """Test system logging."""
        logger = SystemLogger(temp_dir / "logs")

        from pyvirtos.core.logs import LogLevel

        logger.info("System started", component="kernel")
        logger.debug("Debug message", component="scheduler")
        logger.error("Error occurred", component="memory")
        logger.audit("User login", component="auth", user="alice")

        # Read logs
        logs = logger.read_logs()
        assert len(logs) > 0

        # Check audit logs
        audit_logs = logger.read_audit_logs()
        assert len(audit_logs) > 0

        # Get stats
        stats = logger.get_log_stats()
        assert stats["total_entries"] > 0

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_dir):
        """Test complete workflow: boot, create users, allocate memory, run processes."""
        # Setup
        config_path = temp_dir / "config.json"
        kernel = Kernel(config_path)
        vfs = VirtualFilesystem(temp_dir / "vfs")
        user_manager = UserManager(temp_dir / "users.db")
        memory_manager = MemoryManager(
            physical_memory_mb=16,
            swap_file_path=temp_dir / "swap.bin",
        )
        logger = SystemLogger(temp_dir / "logs")

        # Boot kernel
        await kernel.start()
        logger.info("Kernel booted", component="kernel")

        # Create users
        assert user_manager.create_user("alice", "alicepass")
        alice = user_manager.get_user("alice")
        logger.audit("User created", component="auth", user="alice")

        # Create filesystem structure
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.mkdir("/home/alice", 0, 0)
        assert vfs.chown("/home/alice", alice.uid, alice.gid, 0)
        logger.info("Filesystem initialized", component="filesystem")

        # Allocate memory for processes
        vaddr = memory_manager.allocate(pid=1, size=8192)
        assert vaddr is not None
        logger.info("Memory allocated", component="memory", pid=1)

        # Create and schedule processes
        scheduler = kernel.get_service("scheduler")
        processes = [
            Process(pid=i, ppid=0, name=f"proc_{i}", owner_user="alice")
            for i in range(1, 4)
        ]

        for proc in processes:
            scheduler.add_process(proc)
            logger.info(f"Process created: {proc.name}", component="scheduler", pid=proc.pid)

        # Run simulation
        for _ in range(20):
            await kernel.tick()

        # Verify results
        system_info = kernel.get_system_info()
        assert system_info["total_processes"] == 3

        memory_info = memory_manager.get_system_memory_info()
        assert memory_info["page_faults"] >= 0

        log_stats = logger.get_log_stats()
        assert log_stats["total_entries"] > 0

        # Shutdown
        kernel.stop()
        logger.info("System shutdown", component="kernel")

        assert not kernel.running

    @pytest.mark.asyncio
    async def test_process_lifecycle_with_memory(self, temp_dir):
        """Test process lifecycle with memory management."""
        kernel = Kernel(temp_dir / "config.json")
        memory_manager = MemoryManager(
            physical_memory_mb=16,
            swap_file_path=temp_dir / "swap.bin",
        )

        await kernel.start()
        scheduler = kernel.get_service("scheduler")

        # Create process
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        scheduler.add_process(proc)

        # Allocate memory
        vaddr = memory_manager.allocate(pid=proc.pid, size=4096)
        assert vaddr is not None

        # Run process
        for _ in range(5):
            await kernel.tick()

        # Process should have run
        assert proc.cpu_time > 0

        # Kill process
        proc.kill()
        await kernel.tick()

        # Clean up memory
        memory_manager.cleanup_process(proc.pid)
        assert proc.pid not in memory_manager.allocations

        kernel.stop()

    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self, temp_dir):
        """Test user isolation in filesystem."""
        vfs = VirtualFilesystem(temp_dir / "vfs")
        user_manager = UserManager(temp_dir / "users.db")

        # Create users
        user_manager.create_user("alice", "alicepass")
        user_manager.create_user("bob", "bobpass")

        alice = user_manager.get_user("alice")
        bob = user_manager.get_user("bob")

        # Create home directories as root
        vfs.mkdir("/home", 0, 0)
        vfs.mkdir("/home/alice", 0, 0, 0o700)
        vfs.mkdir("/home/bob", 0, 0, 0o700)
        # Change ownership
        vfs.chown("/home/alice", alice.uid, alice.gid, 0)
        vfs.chown("/home/bob", bob.uid, bob.gid, 0)

        # Create private files
        vfs.touch("/home/alice/private.txt", alice.uid, alice.gid, 0o600)
        vfs.touch("/home/bob/private.txt", bob.uid, bob.gid, 0o600)

        vfs.write("/home/alice/private.txt", b"alice_data", alice.uid, alice.gid)
        vfs.write("/home/bob/private.txt", b"bob_data", bob.uid, bob.gid)

        # Test isolation
        # Alice can read her file
        assert vfs.read("/home/alice/private.txt", alice.uid, alice.gid) == b"alice_data"

        # Alice cannot read Bob's file
        assert vfs.read("/home/bob/private.txt", alice.uid, alice.gid) is None

        # Bob can read his file
        assert vfs.read("/home/bob/private.txt", bob.uid, bob.gid) == b"bob_data"

        # Bob cannot read Alice's file
        assert vfs.read("/home/alice/private.txt", bob.uid, bob.gid) is None

        # Root can read both
        assert vfs.read("/home/alice/private.txt", 0, 0) == b"alice_data"
        assert vfs.read("/home/bob/private.txt", 0, 0) == b"bob_data"
