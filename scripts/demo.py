"""Demo script showcasing PyVirtOS features."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyvirtos.core.kernel import Kernel
from pyvirtos.core.process import Process
from pyvirtos.core.scheduler import RoundRobinScheduler


def setup_logging():
    """Setup logging for demo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def demo_basic_scheduling():
    """Demonstrate basic process scheduling."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Process Scheduling")
    print("=" * 60)

    kernel = Kernel()
    await kernel.start()

    scheduler = kernel.get_service("scheduler")

    # Create some processes
    processes = [
        Process(pid=1, ppid=0, name="shell", owner_user="root"),
        Process(pid=2, ppid=0, name="editor", owner_user="alice"),
        Process(pid=3, ppid=0, name="compiler", owner_user="bob"),
    ]

    for proc in processes:
        scheduler.add_process(proc)

    print(f"\nCreated {len(processes)} processes")
    print("\nRunning scheduler for 10 ticks...")

    for tick in range(10):
        scheduler.tick()
        print(f"Tick {tick + 1}: {len(scheduler.run_queue)} processes in queue")

    print("\nFinal CPU times:")
    for proc in processes:
        print(f"  {proc.name}: {proc.cpu_time}ms")

    kernel.stop()


async def demo_priority_scheduling():
    """Demonstrate priority-based scheduling."""
    print("\n" + "=" * 60)
    print("DEMO 2: Priority-Based Scheduling")
    print("=" * 60)

    from pyvirtos.core.scheduler import PriorityScheduler

    kernel = Kernel()
    kernel.config["scheduler_type"] = "priority"
    await kernel.start()

    # Replace scheduler with priority scheduler
    priority_scheduler = PriorityScheduler(quantum_ms=100)
    kernel.register_service("scheduler", priority_scheduler)

    # Create processes with different priorities
    processes = [
        Process(pid=1, ppid=0, name="low_priority", owner_user="root", priority=10),
        Process(pid=2, ppid=0, name="high_priority", owner_user="alice", priority=1),
        Process(pid=3, ppid=0, name="medium_priority", owner_user="bob", priority=5),
    ]

    for proc in processes:
        priority_scheduler.add_process(proc)

    print("\nCreated processes with priorities:")
    for proc in processes:
        print(f"  {proc.name}: priority={proc.priority}")

    print("\nRunning scheduler for 6 ticks...")

    for tick in range(6):
        priority_scheduler.tick()
        if priority_scheduler.current_process:
            print(f"Tick {tick + 1}: Running {priority_scheduler.current_process.name}")

    print("\nFinal CPU times:")
    for proc in processes:
        print(f"  {proc.name}: {proc.cpu_time}ms")

    kernel.stop()


async def demo_process_lifecycle():
    """Demonstrate process lifecycle."""
    print("\n" + "=" * 60)
    print("DEMO 3: Process Lifecycle")
    print("=" * 60)

    kernel = Kernel()
    await kernel.start()

    scheduler = kernel.get_service("scheduler")

    # Create a process
    proc = Process(pid=1, ppid=0, name="demo_process", owner_user="root")
    scheduler.add_process(proc)

    print(f"\nCreated process: {proc.name} (PID={proc.pid})")
    print(f"Initial state: {proc.state.name}")

    # Run it
    print("\nRunning process for 5 ticks...")
    for i in range(5):
        scheduler.tick()
        print(f"Tick {i + 1}: state={proc.state.name}, cpu_time={proc.cpu_time}ms")

    # Block it
    print("\nBlocking process...")
    proc.block("I/O wait")
    print(f"State: {proc.state.name}")

    # Unblock it
    print("\nUnblocking process...")
    proc.unblock()
    print(f"State: {proc.state.name}")

    # Kill it
    print("\nKilling process...")
    proc.kill()
    print(f"State: {proc.state.name}")

    # Try to run it (should do nothing)
    scheduler.tick()
    print(f"After tick: {len(scheduler.get_task_list())} processes remaining")

    kernel.stop()


async def demo_many_processes():
    """Demonstrate scheduling many processes."""
    print("\n" + "=" * 60)
    print("DEMO 4: Many Processes (50 concurrent)")
    print("=" * 60)

    kernel = Kernel()
    await kernel.start()

    scheduler = kernel.get_service("scheduler")

    # Create 50 processes
    num_processes = 50
    processes = [
        Process(
            pid=i,
            ppid=0,
            name=f"proc_{i}",
            owner_user="root" if i % 2 == 0 else "user",
        )
        for i in range(1, num_processes + 1)
    ]

    for proc in processes:
        scheduler.add_process(proc)

    print(f"\nCreated {num_processes} processes")

    # Run for 100 ticks
    print("Running scheduler for 100 ticks...")
    for _ in range(100):
        scheduler.tick()

    # Calculate statistics
    total_cpu_time = sum(p.cpu_time for p in processes)
    avg_cpu_time = total_cpu_time / len(processes)
    min_cpu_time = min(p.cpu_time for p in processes)
    max_cpu_time = max(p.cpu_time for p in processes)

    print(f"\nScheduler Statistics:")
    print(f"  Total CPU time distributed: {total_cpu_time}ms")
    print(f"  Average CPU time per process: {avg_cpu_time:.1f}ms")
    print(f"  Min CPU time: {min_cpu_time}ms")
    print(f"  Max CPU time: {max_cpu_time}ms")
    print(f"  Fairness ratio: {max_cpu_time / min_cpu_time:.2f}x")

    kernel.stop()


async def demo_system_info():
    """Demonstrate system information."""
    print("\n" + "=" * 60)
    print("DEMO 5: System Information")
    print("=" * 60)

    kernel = Kernel()
    await kernel.start()

    scheduler = kernel.get_service("scheduler")

    # Create a few processes
    for i in range(5):
        proc = Process(pid=i + 1, ppid=0, name=f"proc_{i}", owner_user="root")
        scheduler.add_process(proc)

    # Run a few ticks
    for _ in range(10):
        await kernel.tick()

    # Get system info
    info = kernel.get_system_info()

    print("\nSystem Information:")
    print(f"  Running: {info['running']}")
    print(f"  Uptime: {info['uptime_ms']:.1f}ms")
    print(f"  Tick count: {info['tick_count']}")
    print(f"  Total processes: {info['total_processes']}")
    print(f"  Memory size: {info['config']['memory_size_mb']}MB")
    print(f"  Scheduler type: {info['config']['scheduler_type']}")

    kernel.stop()


async def main():
    """Run all demos."""
    setup_logging()

    print("\n" + "=" * 60)
    print("PyVirtOS - Demo Script")
    print("=" * 60)

    await demo_basic_scheduling()
    await demo_priority_scheduling()
    await demo_process_lifecycle()
    await demo_many_processes()
    await demo_system_info()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
