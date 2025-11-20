"""Tests for memory manager module."""

import pytest
import tempfile
from pathlib import Path

from pyvirtos.core.memory import MemoryManager, VirtualAddressRange


class TestVirtualAddressRange:
    """Test VirtualAddressRange class."""

    def test_creation(self):
        """Test creating address range."""
        vaddr = VirtualAddressRange(start=0x1000, end=0x2000, size=0x1000)
        assert vaddr.start == 0x1000
        assert vaddr.end == 0x2000
        assert vaddr.size == 0x1000

    def test_contains(self):
        """Test address containment."""
        vaddr = VirtualAddressRange(start=0x1000, end=0x2000, size=0x1000)
        assert vaddr.contains(0x1000)
        assert vaddr.contains(0x1500)
        assert not vaddr.contains(0x2000)
        assert not vaddr.contains(0x500)


class TestMemoryManager:
    """Test MemoryManager class."""

    @pytest.fixture
    def memory_manager(self):
        """Create a temporary memory manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield MemoryManager(
                physical_memory_mb=16,
                swap_file_path=Path(tmpdir) / "swap.bin",
                page_size_kb=4,
            )

    def test_memory_manager_creation(self, memory_manager):
        """Test creating memory manager."""
        assert memory_manager.physical_memory_size > 0
        assert memory_manager.page_size == 4 * 1024
        assert memory_manager.num_frames > 0

    def test_swap_file_created(self, memory_manager):
        """Test that swap file is created."""
        assert memory_manager.swap_file_path.exists()

    def test_allocate_memory(self, memory_manager):
        """Test allocating memory."""
        vaddr = memory_manager.allocate(pid=1, size=4096)
        assert vaddr is not None
        assert vaddr.size == 4096

    def test_allocate_multiple(self, memory_manager):
        """Test allocating multiple regions."""
        vaddr1 = memory_manager.allocate(pid=1, size=4096)
        vaddr2 = memory_manager.allocate(pid=1, size=4096)

        assert vaddr1 is not None
        assert vaddr2 is not None
        assert vaddr1.end <= vaddr2.start

    def test_allocate_different_processes(self, memory_manager):
        """Test allocating for different processes."""
        vaddr1 = memory_manager.allocate(pid=1, size=4096)
        vaddr2 = memory_manager.allocate(pid=2, size=4096)

        assert vaddr1 is not None
        assert vaddr2 is not None

    def test_free_memory(self, memory_manager):
        """Test freeing memory."""
        vaddr = memory_manager.allocate(pid=1, size=4096)
        assert memory_manager.free(pid=1, vaddr=vaddr.start)

    def test_read_write(self, memory_manager):
        """Test reading and writing memory."""
        vaddr = memory_manager.allocate(pid=1, size=4096)
        assert memory_manager.write(pid=1, vaddr=vaddr.start, data=b"test")
        data = memory_manager.read(pid=1, vaddr=vaddr.start, size=4)
        assert data is not None

    def test_page_fault_handling(self, memory_manager):
        """Test page fault handling."""
        initial_faults = memory_manager.page_faults
        vaddr = memory_manager.allocate(pid=1, size=4096)
        memory_manager.read(pid=1, vaddr=vaddr.start, size=4)
        # First read should trigger page fault
        assert memory_manager.page_faults > initial_faults

    def test_get_memory_map(self, memory_manager):
        """Test getting memory map."""
        vaddr = memory_manager.allocate(pid=1, size=8192)
        memory_map = memory_manager.get_memory_map(pid=1)

        assert memory_map["pid"] == 1
        assert memory_map["total_allocated"] == 8192

    def test_get_system_memory_info(self, memory_manager):
        """Test getting system memory info."""
        info = memory_manager.get_system_memory_info()

        assert "physical_memory_mb" in info
        assert "total_frames" in info
        assert "free_frames" in info
        assert "page_faults" in info

    def test_cleanup_process(self, memory_manager):
        """Test cleaning up process memory."""
        vaddr = memory_manager.allocate(pid=1, size=4096)
        memory_manager.cleanup_process(pid=1)

        assert 1 not in memory_manager.allocations

    def test_large_allocation(self, memory_manager):
        """Test allocating large memory region."""
        # Allocate 1MB
        vaddr = memory_manager.allocate(pid=1, size=1024 * 1024)
        assert vaddr is not None
        assert vaddr.size == 1024 * 1024

    def test_multiple_process_isolation(self, memory_manager):
        """Test that processes have isolated memory."""
        vaddr1 = memory_manager.allocate(pid=1, size=4096)
        vaddr2 = memory_manager.allocate(pid=2, size=4096)

        # Write to process 1
        memory_manager.write(pid=1, vaddr=vaddr1.start, data=b"proc1")

        # Write to process 2
        memory_manager.write(pid=2, vaddr=vaddr2.start, data=b"proc2")

        # Verify isolation
        data1 = memory_manager.read(pid=1, vaddr=vaddr1.start, size=5)
        data2 = memory_manager.read(pid=2, vaddr=vaddr2.start, size=5)

        assert data1 is not None
        assert data2 is not None

    def test_invalid_read(self, memory_manager):
        """Test reading from invalid address."""
        data = memory_manager.read(pid=999, vaddr=0x1000, size=4)
        assert data is None

    def test_invalid_write(self, memory_manager):
        """Test writing to invalid address."""
        result = memory_manager.write(pid=999, vaddr=0x1000, data=b"test")
        assert result is False
