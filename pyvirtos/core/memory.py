"""Virtual memory manager for PyVirtOS."""

import mmap
import os
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class VirtualAddressRange:
    """Represents a range of virtual addresses."""

    start: int
    end: int
    size: int

    def contains(self, addr: int) -> bool:
        """Check if address is in range."""
        return self.start <= addr < self.end


@dataclass
class PageTableEntry:
    """Page table entry mapping virtual page to physical frame."""

    vpn: int  # Virtual page number
    pfn: Optional[int]  # Physical frame number (None if swapped)
    present: bool  # Is page in physical memory
    dirty: bool  # Has page been modified
    accessed: bool  # Has page been accessed
    last_access_time: float = 0.0


class MemoryManager:
    """Virtual memory manager with paging and swap support."""

    def __init__(
        self,
        physical_memory_mb: int = 64,
        swap_file_path: Optional[Path] = None,
        page_size_kb: int = 4,
    ):
        """Initialize memory manager.

        Args:
            physical_memory_mb: Physical memory size in MB
            swap_file_path: Path to swap file
            page_size_kb: Page size in KB
        """
        self.page_size = page_size_kb * 1024  # Convert to bytes
        self.physical_memory_size = physical_memory_mb * 1024 * 1024
        self.num_frames = self.physical_memory_size // self.page_size

        # Swap file
        self.swap_file_path = swap_file_path or Path.home() / ".pyvirtos" / "swap.bin"
        self.swap_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize swap file (128MB by default)
        self.swap_size = 128 * 1024 * 1024
        self._init_swap_file()

        # Frame management
        self.free_frames: List[int] = list(range(self.num_frames))
        self.frame_table: Dict[int, Tuple[int, int]] = {}  # pfn -> (pid, vpn)
        self.lru_queue: OrderedDict = OrderedDict()  # Track LRU order

        # Process page tables
        self.page_tables: Dict[int, Dict[int, PageTableEntry]] = {}  # pid -> page_table

        # Process memory allocations
        self.allocations: Dict[int, List[VirtualAddressRange]] = {}  # pid -> ranges

        # Swap usage tracking
        self.swap_usage: Dict[int, int] = {}  # pid -> bytes in swap

        # Statistics
        self.page_faults = 0
        self.swap_ins = 0
        self.swap_outs = 0

    def _init_swap_file(self) -> None:
        """Initialize swap file."""
        if not self.swap_file_path.exists():
            # Create swap file with zeros
            with open(self.swap_file_path, "wb") as f:
                f.write(b"\0" * self.swap_size)

    def allocate(self, pid: int, size: int) -> Optional[VirtualAddressRange]:
        """Allocate virtual memory for a process.

        Args:
            pid: Process ID
            size: Size to allocate in bytes

        Returns:
            VirtualAddressRange or None if allocation fails
        """
        if pid not in self.allocations:
            self.allocations[pid] = []
            self.page_tables[pid] = {}
            self.swap_usage[pid] = 0

        # Find next available virtual address
        if not self.allocations[pid]:
            start_addr = 0x1000  # Start after kernel space
        else:
            last_range = self.allocations[pid][-1]
            start_addr = last_range.end

        # Align to page boundary
        if start_addr % self.page_size != 0:
            start_addr += self.page_size - (start_addr % self.page_size)

        end_addr = start_addr + size

        # Create page table entries
        start_vpn = start_addr // self.page_size
        end_vpn = (end_addr + self.page_size - 1) // self.page_size

        for vpn in range(start_vpn, end_vpn):
            if vpn not in self.page_tables[pid]:
                self.page_tables[pid][vpn] = PageTableEntry(
                    vpn=vpn,
                    pfn=None,
                    present=False,
                    dirty=False,
                    accessed=False,
                )

        vaddr_range = VirtualAddressRange(start=start_addr, end=end_addr, size=size)
        self.allocations[pid].append(vaddr_range)

        return vaddr_range

    def free(self, pid: int, vaddr: int) -> bool:
        """Free virtual memory.

        Args:
            pid: Process ID
            vaddr: Virtual address to free

        Returns:
            True if successful
        """
        if pid not in self.allocations:
            return False

        # Find and remove allocation
        for i, vaddr_range in enumerate(self.allocations[pid]):
            if vaddr_range.contains(vaddr):
                # Free physical frames
                start_vpn = vaddr_range.start // self.page_size
                end_vpn = (vaddr_range.end + self.page_size - 1) // self.page_size

                for vpn in range(start_vpn, end_vpn):
                    pte = self.page_tables[pid].get(vpn)
                    if pte and pte.present and pte.pfn is not None:
                        self.free_frames.append(pte.pfn)
                        del self.frame_table[pte.pfn]
                        if pte.pfn in self.lru_queue:
                            del self.lru_queue[pte.pfn]

                    # Free swap space
                    if pte and not pte.present:
                        self.swap_usage[pid] -= self.page_size

                    if vpn in self.page_tables[pid]:
                        del self.page_tables[pid][vpn]

                self.allocations[pid].pop(i)
                return True

        return False

    def _allocate_frame(self) -> Optional[int]:
        """Allocate a physical frame.

        Returns:
            Frame number or None if no free frames
        """
        if self.free_frames:
            return self.free_frames.pop(0)

        # Evict LRU page
        if self.lru_queue:
            pfn = next(iter(self.lru_queue))
            pid, vpn = self.frame_table[pfn]
            self._swap_out(pid, vpn, pfn)
            return pfn

        return None

    def _swap_out(self, pid: int, vpn: int, pfn: int) -> bool:
        """Swap out a page to disk.

        Args:
            pid: Process ID
            vpn: Virtual page number
            pfn: Physical frame number

        Returns:
            True if successful
        """
        pte = self.page_tables[pid][vpn]

        if not pte.dirty:
            # Clean page, just remove from memory
            self.free_frames.append(pfn)
            del self.frame_table[pfn]
            del self.lru_queue[pfn]
            pte.present = False
            pte.pfn = None
            return True

        # Write to swap file
        swap_offset = (pid * 1000 + vpn) * self.page_size
        if swap_offset + self.page_size > self.swap_size:
            return False

        try:
            with open(self.swap_file_path, "r+b") as f:
                # Read page from memory (simulated)
                page_data = b"\0" * self.page_size
                f.seek(swap_offset)
                f.write(page_data)

            self.free_frames.append(pfn)
            del self.frame_table[pfn]
            del self.lru_queue[pfn]
            pte.present = False
            pte.pfn = None
            pte.dirty = False
            self.swap_usage[pid] += self.page_size
            self.swap_outs += 1
            return True
        except OSError:
            return False

    def _swap_in(self, pid: int, vpn: int) -> bool:
        """Swap in a page from disk.

        Args:
            pid: Process ID
            vpn: Virtual page number

        Returns:
            True if successful
        """
        pfn = self._allocate_frame()
        if pfn is None:
            return False

        # Read from swap file
        swap_offset = (pid * 1000 + vpn) * self.page_size
        try:
            with open(self.swap_file_path, "rb") as f:
                f.seek(swap_offset)
                page_data = f.read(self.page_size)

            pte = self.page_tables[pid][vpn]
            pte.present = True
            pte.pfn = pfn
            pte.dirty = False

            self.frame_table[pfn] = (pid, vpn)
            self.lru_queue[pfn] = True
            self.swap_usage[pid] -= self.page_size
            self.swap_ins += 1
            return True
        except OSError:
            return False

    def read(self, pid: int, vaddr: int, size: int) -> Optional[bytes]:
        """Read from virtual memory.

        Args:
            pid: Process ID
            vaddr: Virtual address
            size: Number of bytes to read

        Returns:
            Data read or None if error
        """
        vpn = vaddr // self.page_size
        offset = vaddr % self.page_size

        if pid not in self.page_tables or vpn not in self.page_tables[pid]:
            return None

        pte = self.page_tables[pid][vpn]

        # Handle page fault
        if not pte.present:
            self.page_faults += 1
            if not self._swap_in(pid, vpn):
                return None

        pte.accessed = True
        pte.last_access_time = self.lru_queue.__len__()

        # Update LRU
        if pte.pfn in self.lru_queue:
            del self.lru_queue[pte.pfn]
        self.lru_queue[pte.pfn] = True

        # Simulate reading data
        return b"\0" * size

    def write(self, pid: int, vaddr: int, data: bytes) -> bool:
        """Write to virtual memory.

        Args:
            pid: Process ID
            vaddr: Virtual address
            data: Data to write

        Returns:
            True if successful
        """
        vpn = vaddr // self.page_size
        offset = vaddr % self.page_size

        if pid not in self.page_tables or vpn not in self.page_tables[pid]:
            return False

        pte = self.page_tables[pid][vpn]

        # Handle page fault
        if not pte.present:
            self.page_faults += 1
            if not self._swap_in(pid, vpn):
                return False

        pte.accessed = True
        pte.dirty = True
        pte.last_access_time = self.lru_queue.__len__()

        # Update LRU
        if pte.pfn in self.lru_queue:
            del self.lru_queue[pte.pfn]
        self.lru_queue[pte.pfn] = True

        return True

    def get_memory_map(self, pid: int) -> Dict:
        """Get memory map for a process.

        Returns:
            Dictionary with memory statistics
        """
        if pid not in self.allocations:
            return {}

        total_allocated = sum(r.size for r in self.allocations[pid])
        total_in_memory = 0
        total_in_swap = 0

        for vpn, pte in self.page_tables[pid].items():
            if pte.present:
                total_in_memory += self.page_size
            else:
                total_in_swap += self.page_size

        return {
            "pid": pid,
            "total_allocated": total_allocated,
            "in_physical_memory": total_in_memory,
            "in_swap": total_in_swap,
            "page_count": len(self.page_tables[pid]),
        }

    def get_system_memory_info(self) -> Dict:
        """Get system-wide memory information.

        Returns:
            Dictionary with memory statistics
        """
        total_in_use = self.num_frames - len(self.free_frames)

        return {
            "physical_memory_mb": self.physical_memory_size // (1024 * 1024),
            "page_size_kb": self.page_size // 1024,
            "total_frames": self.num_frames,
            "free_frames": len(self.free_frames),
            "used_frames": total_in_use,
            "page_faults": self.page_faults,
            "swap_ins": self.swap_ins,
            "swap_outs": self.swap_outs,
            "total_swap_usage": sum(self.swap_usage.values()),
        }

    def cleanup_process(self, pid: int) -> None:
        """Clean up memory for a terminated process.

        Args:
            pid: Process ID
        """
        if pid in self.allocations:
            # Free all allocations
            for vaddr_range in self.allocations[pid]:
                self.free(pid, vaddr_range.start)

            del self.allocations[pid]
            del self.page_tables[pid]
            del self.swap_usage[pid]
