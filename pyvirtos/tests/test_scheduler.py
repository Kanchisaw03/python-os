"""Tests for scheduler module."""

import pytest

from pyvirtos.core.process import Process, ProcState
from pyvirtos.core.scheduler import PriorityScheduler, RoundRobinScheduler


class TestRoundRobinScheduler:
    """Test RoundRobinScheduler class."""

    def test_scheduler_creation(self):
        """Test creating a scheduler."""
        scheduler = RoundRobinScheduler(quantum_ms=100)
        assert scheduler.quantum_ms == 100
        assert len(scheduler.get_task_list()) == 0

    def test_add_process(self):
        """Test adding a process to scheduler."""
        scheduler = RoundRobinScheduler()
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        scheduler.add_process(proc)
        assert len(scheduler.get_task_list()) == 1
        assert scheduler.get_process(1) == proc

    def test_remove_process(self):
        """Test removing a process from scheduler."""
        scheduler = RoundRobinScheduler()
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        scheduler.add_process(proc)
        scheduler.remove_process(1)
        assert len(scheduler.get_task_list()) == 0

    def test_tick_single_process(self):
        """Test scheduler tick with single process."""
        scheduler = RoundRobinScheduler(quantum_ms=100)
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        scheduler.add_process(proc)

        initial_cpu_time = proc.cpu_time
        scheduler.tick()
        assert proc.cpu_time == initial_cpu_time + 100

    def test_tick_multiple_processes(self):
        """Test scheduler tick with multiple processes."""
        scheduler = RoundRobinScheduler(quantum_ms=100)
        procs = [
            Process(pid=i, ppid=0, name=f"test{i}", owner_user="root")
            for i in range(3)
        ]
        for proc in procs:
            scheduler.add_process(proc)

        # Tick 3 times - each process should run once
        for _ in range(3):
            scheduler.tick()

        for proc in procs:
            assert proc.cpu_time == 100

    def test_round_robin_fairness(self):
        """Test round-robin fairness."""
        scheduler = RoundRobinScheduler(quantum_ms=50)
        procs = [
            Process(pid=i, ppid=0, name=f"test{i}", owner_user="root")
            for i in range(4)
        ]
        for proc in procs:
            scheduler.add_process(proc)

        # Run 8 ticks (2 full rounds)
        for _ in range(8):
            scheduler.tick()

        # Each process should have run twice
        for proc in procs:
            assert proc.cpu_time == 100

    def test_zombie_process_removal(self):
        """Test that zombie processes are removed."""
        scheduler = RoundRobinScheduler()
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        scheduler.add_process(proc)
        proc.kill()
        scheduler.tick()
        assert len(scheduler.get_task_list()) == 0

    def test_blocked_process_handling(self):
        """Test handling of blocked processes."""
        scheduler = RoundRobinScheduler()
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        scheduler.add_process(proc)
        
        # Block the process before running
        proc.block()
        
        # Add to blocked queue manually to test the logic
        scheduler.blocked_queue.append(proc)
        scheduler.run_queue.remove(proc)
        
        # Tick should keep it in blocked queue
        scheduler.tick()
        
        # Process should still be blocked
        assert proc.state == ProcState.BLOCKED


class TestPriorityScheduler:
    """Test PriorityScheduler class."""

    def test_scheduler_creation(self):
        """Test creating a priority scheduler."""
        scheduler = PriorityScheduler(quantum_ms=100)
        assert scheduler.quantum_ms == 100
        assert len(scheduler.get_task_list()) == 0

    def test_priority_ordering(self):
        """Test that processes are scheduled by priority."""
        scheduler = PriorityScheduler(quantum_ms=100)
        # Add processes in reverse priority order
        procs = [
            Process(pid=1, ppid=0, name="low", owner_user="root", priority=10),
            Process(pid=2, ppid=0, name="high", owner_user="root", priority=1),
            Process(pid=3, ppid=0, name="medium", owner_user="root", priority=5),
        ]
        for proc in procs:
            scheduler.add_process(proc)

        # First tick should run highest priority (pid=2)
        scheduler.tick()
        assert procs[1].cpu_time == 100
        assert procs[0].cpu_time == 0
        assert procs[2].cpu_time == 0

    def test_set_priority(self):
        """Test changing process priority."""
        scheduler = PriorityScheduler()
        proc = Process(pid=1, ppid=0, name="test", owner_user="root", priority=5)
        scheduler.add_process(proc)
        assert scheduler.set_priority(1, 2)
        assert proc.priority == 2

    def test_set_priority_nonexistent(self):
        """Test setting priority for nonexistent process."""
        scheduler = PriorityScheduler()
        assert not scheduler.set_priority(999, 2)

    def test_queue_info(self):
        """Test getting queue information."""
        scheduler = RoundRobinScheduler()
        proc1 = Process(pid=1, ppid=0, name="test1", owner_user="root")
        proc2 = Process(pid=2, ppid=0, name="test2", owner_user="root")
        scheduler.add_process(proc1)
        scheduler.add_process(proc2)

        info = scheduler.get_queue_info()
        assert info["total_processes"] == 2
        assert info["run_queue_size"] == 2
        assert info["quantum_ms"] == 100
