"""Process abstraction for PyVirtOS."""

from dataclasses import dataclass, field
from enum import Enum, auto
from time import time
from typing import Any, Callable, Optional


class ProcState(Enum):
    """Process state enumeration."""

    READY = auto()
    RUNNING = auto()
    BLOCKED = auto()
    SLEEPING = auto()
    ZOMBIE = auto()


@dataclass
class Process:
    """Represents a process in the virtual OS.

    Attributes:
        pid: Process ID
        ppid: Parent process ID
        name: Process name
        owner_user: Username of process owner
        state: Current process state
        priority: Process priority (0-10, lower is higher priority)
        cpu_time: Total CPU time used in milliseconds
        memory_used: Memory allocated to process in bytes
        start_time: Unix timestamp when process started
        run_func: Optional callable that simulates process work
        file_handles: List of open file descriptors
        memory_map: Virtual memory mapping
    """

    pid: int
    ppid: int
    name: str
    owner_user: str
    state: ProcState = ProcState.READY
    priority: int = 5
    cpu_time: int = 0
    memory_used: int = 0
    start_time: float = field(default_factory=time)
    run_func: Optional[Callable[[int], None]] = None
    file_handles: list = field(default_factory=list)
    memory_map: dict = field(default_factory=dict)

    def run(self, timeslice_ms: int) -> None:
        """Execute process for a given time slice.

        Args:
            timeslice_ms: Time slice in milliseconds to run
        """
        if self.state == ProcState.ZOMBIE:
            return

        self.state = ProcState.RUNNING
        self.cpu_time += timeslice_ms

        if self.run_func:
            try:
                self.run_func(timeslice_ms)
            except Exception:
                self.state = ProcState.ZOMBIE
                return

        # After running, return to READY state if not blocked
        if self.state == ProcState.RUNNING:
            self.state = ProcState.READY

    def fork(self) -> "Process":
        """Create a child process (fork).

        Returns:
            A new Process instance with incremented PID
        """
        # Note: PID assignment should be handled by kernel
        child = Process(
            pid=self.pid + 1000,  # Placeholder; kernel will assign real PID
            ppid=self.pid,
            name=f"{self.name}_child",
            owner_user=self.owner_user,
            priority=self.priority,
        )
        return child

    def kill(self, signal: str = "SIGTERM") -> None:
        """Terminate the process.

        Args:
            signal: Signal name (e.g., SIGTERM, SIGKILL)
        """
        self.state = ProcState.ZOMBIE

    def sleep(self, duration_ms: int) -> None:
        """Put process to sleep.

        Args:
            duration_ms: Sleep duration in milliseconds
        """
        self.state = ProcState.SLEEPING

    def block(self, reason: str = "I/O") -> None:
        """Block process (e.g., waiting for I/O).

        Args:
            reason: Reason for blocking
        """
        self.state = ProcState.BLOCKED

    def unblock(self) -> None:
        """Unblock process."""
        if self.state == ProcState.BLOCKED:
            self.state = ProcState.READY

    def get_info(self) -> dict:
        """Get process information.

        Returns:
            Dictionary with process details
        """
        return {
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "owner": self.owner_user,
            "state": self.state.name,
            "priority": self.priority,
            "cpu_time": self.cpu_time,
            "memory_used": self.memory_used,
            "start_time": self.start_time,
        }
