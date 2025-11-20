"""Tests for process module."""

import pytest

from pyvirtos.core.process import Process, ProcState


class TestProcess:
    """Test Process class."""

    def test_process_creation(self):
        """Test creating a process."""
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        assert proc.pid == 1
        assert proc.ppid == 0
        assert proc.name == "test"
        assert proc.owner_user == "root"
        assert proc.state == ProcState.READY
        assert proc.cpu_time == 0

    def test_process_run(self):
        """Test running a process."""
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        initial_cpu_time = proc.cpu_time
        proc.run(100)
        assert proc.cpu_time == initial_cpu_time + 100
        assert proc.state == ProcState.READY

    def test_process_kill(self):
        """Test killing a process."""
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        proc.kill()
        assert proc.state == ProcState.ZOMBIE

    def test_process_sleep(self):
        """Test sleeping a process."""
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        proc.sleep(1000)
        assert proc.state == ProcState.SLEEPING

    def test_process_block_unblock(self):
        """Test blocking and unblocking a process."""
        proc = Process(pid=1, ppid=0, name="test", owner_user="root")
        proc.block("I/O")
        assert proc.state == ProcState.BLOCKED
        proc.unblock()
        assert proc.state == ProcState.READY

    def test_process_fork(self):
        """Test forking a process."""
        parent = Process(pid=1, ppid=0, name="parent", owner_user="root")
        child = parent.fork()
        assert child.ppid == parent.pid
        assert child.owner_user == parent.owner_user
        assert child.name == "parent_child"

    def test_process_get_info(self):
        """Test getting process info."""
        proc = Process(pid=1, ppid=0, name="test", owner_user="root", priority=3)
        info = proc.get_info()
        assert info["pid"] == 1
        assert info["ppid"] == 0
        assert info["name"] == "test"
        assert info["owner"] == "root"
        assert info["priority"] == 3
        assert info["state"] == "READY"

    def test_process_with_run_func(self):
        """Test process with custom run function."""
        call_count = 0

        def run_func(timeslice_ms):
            nonlocal call_count
            call_count += 1

        proc = Process(
            pid=1, ppid=0, name="test", owner_user="root", run_func=run_func
        )
        proc.run(100)
        assert call_count == 1

    def test_process_run_func_exception(self):
        """Test process with run function that raises exception."""

        def run_func(timeslice_ms):
            raise RuntimeError("Test error")

        proc = Process(
            pid=1, ppid=0, name="test", owner_user="root", run_func=run_func
        )
        proc.run(100)
        assert proc.state == ProcState.ZOMBIE
