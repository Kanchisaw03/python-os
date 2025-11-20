"""CPU scheduler implementations for PyVirtOS."""

from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, List, Optional

from pyvirtos.core.process import Process, ProcState


class Scheduler(ABC):
    """Abstract base class for CPU schedulers."""

    @abstractmethod
    def add_process(self, process: Process) -> None:
        """Add a process to the scheduler.

        Args:
            process: Process to add
        """
        pass

    @abstractmethod
    def remove_process(self, pid: int) -> None:
        """Remove a process from the scheduler.

        Args:
            pid: Process ID to remove
        """
        pass

    @abstractmethod
    def tick(self) -> None:
        """Execute one scheduler tick (dispatch one process)."""
        pass

    @abstractmethod
    def get_task_list(self) -> List[Process]:
        """Get list of all processes.

        Returns:
            List of Process objects
        """
        pass

    def get_process(self, pid: int) -> Optional[Process]:
        """Get a process by PID.

        Args:
            pid: Process ID

        Returns:
            Process object or None if not found
        """
        for proc in self.get_task_list():
            if proc.pid == pid:
                return proc
        return None


class RoundRobinScheduler(Scheduler):
    """Round-Robin CPU scheduler with fixed time quantum."""

    def __init__(self, quantum_ms: int = 100):
        """Initialize Round-Robin scheduler.

        Args:
            quantum_ms: Time quantum in milliseconds
        """
        self.quantum_ms = quantum_ms
        self.run_queue: deque = deque()
        self.blocked_queue: List[Process] = []
        self.all_processes: Dict[int, Process] = {}
        self.current_process: Optional[Process] = None

    def add_process(self, process: Process) -> None:
        """Add a process to the run queue.

        Args:
            process: Process to add
        """
        self.all_processes[process.pid] = process
        if process.state in (ProcState.READY, ProcState.RUNNING):
            self.run_queue.append(process)

    def remove_process(self, pid: int) -> None:
        """Remove a process from the scheduler.

        Args:
            pid: Process ID to remove
        """
        if pid in self.all_processes:
            proc = self.all_processes[pid]
            if proc in self.run_queue:
                self.run_queue.remove(proc)
            if proc in self.blocked_queue:
                self.blocked_queue.remove(proc)
            del self.all_processes[pid]

    def tick(self) -> None:
        """Execute one scheduler tick."""
        # Check if any blocked processes can be unblocked
        self.blocked_queue = [p for p in self.blocked_queue if p.state == ProcState.BLOCKED]

        if not self.run_queue:
            return

        # Get next process from queue
        process = self.run_queue.popleft()
        self.current_process = process

        # Save state before running
        state_before = process.state

        # Run the process for one quantum
        process.run(self.quantum_ms)

        # If process is not zombie, put it back in queue
        if process.state != ProcState.ZOMBIE:
            # Check if process was blocked during run
            if process.state == ProcState.BLOCKED:
                self.blocked_queue.append(process)
            else:
                self.run_queue.append(process)
        else:
            # Remove zombie process
            if process.pid in self.all_processes:
                del self.all_processes[process.pid]

        self.current_process = None

    def get_task_list(self) -> List[Process]:
        """Get list of all processes.

        Returns:
            List of Process objects
        """
        return list(self.all_processes.values())

    def get_queue_info(self) -> dict:
        """Get scheduler queue information.

        Returns:
            Dictionary with queue stats
        """
        return {
            "run_queue_size": len(self.run_queue),
            "blocked_queue_size": len(self.blocked_queue),
            "total_processes": len(self.all_processes),
            "quantum_ms": self.quantum_ms,
        }


class PriorityScheduler(Scheduler):
    """Priority-based preemptive CPU scheduler."""

    def __init__(self, quantum_ms: int = 100):
        """Initialize Priority scheduler.

        Args:
            quantum_ms: Time quantum in milliseconds
        """
        self.quantum_ms = quantum_ms
        self.run_queue: List[Process] = []
        self.blocked_queue: List[Process] = []
        self.all_processes: Dict[int, Process] = {}
        self.current_process: Optional[Process] = None

    def add_process(self, process: Process) -> None:
        """Add a process to the run queue (sorted by priority).

        Args:
            process: Process to add
        """
        self.all_processes[process.pid] = process
        if process.state in (ProcState.READY, ProcState.RUNNING):
            self.run_queue.append(process)
            self.run_queue.sort(key=lambda p: p.priority)

    def remove_process(self, pid: int) -> None:
        """Remove a process from the scheduler.

        Args:
            pid: Process ID to remove
        """
        if pid in self.all_processes:
            proc = self.all_processes[pid]
            if proc in self.run_queue:
                self.run_queue.remove(proc)
            if proc in self.blocked_queue:
                self.blocked_queue.remove(proc)
            del self.all_processes[pid]

    def tick(self) -> None:
        """Execute one scheduler tick."""
        # Check if any blocked processes can be unblocked
        self.blocked_queue = [p for p in self.blocked_queue if p.state == ProcState.BLOCKED]

        if not self.run_queue:
            return

        # Get highest priority process (lowest priority number)
        process = self.run_queue.pop(0)
        self.current_process = process

        # Run the process for one quantum
        process.run(self.quantum_ms)

        # If process is not zombie, put it back in queue (re-sort by priority)
        if process.state != ProcState.ZOMBIE:
            if process.state == ProcState.BLOCKED:
                self.blocked_queue.append(process)
            else:
                self.run_queue.append(process)
                self.run_queue.sort(key=lambda p: p.priority)
        else:
            # Remove zombie process
            if process.pid in self.all_processes:
                del self.all_processes[process.pid]

        self.current_process = None

    def get_task_list(self) -> List[Process]:
        """Get list of all processes.

        Returns:
            List of Process objects
        """
        return list(self.all_processes.values())

    def get_queue_info(self) -> dict:
        """Get scheduler queue information.

        Returns:
            Dictionary with queue stats
        """
        return {
            "run_queue_size": len(self.run_queue),
            "blocked_queue_size": len(self.blocked_queue),
            "total_processes": len(self.all_processes),
            "quantum_ms": self.quantum_ms,
        }

    def set_priority(self, pid: int, priority: int) -> bool:
        """Change process priority.

        Args:
            pid: Process ID
            priority: New priority (0-10, lower is higher)

        Returns:
            True if successful, False if process not found
        """
        if pid in self.all_processes:
            self.all_processes[pid].priority = priority
            # Re-sort run queue
            self.run_queue.sort(key=lambda p: p.priority)
            return True
        return False
