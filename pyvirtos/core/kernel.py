"""Kernel - Core OS service manager and boot sequence."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pyvirtos.core.scheduler import RoundRobinScheduler, Scheduler


class EventBus:
    """Simple event bus for kernel events."""

    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to an event.

        Args:
            event_name: Name of event
            callback: Callback function
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def emit(self, event_name: str, data: Any = None) -> None:
        """Emit an event.

        Args:
            event_name: Name of event
            data: Event data
        """
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logging.error(f"Error in event handler for {event_name}: {e}")


class Kernel:
    """PyVirtOS Kernel - manages boot, services, and system lifecycle."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize kernel.

        Args:
            config_path: Path to config file (optional)
        """
        self.services: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}
        self.running = False
        self.event_bus = EventBus()
        self.logger = logging.getLogger("kernel")
        self.config_path = config_path or Path.home() / ".pyvirtos" / "config.json"
        self.tick_count = 0
        self.boot_time = 0.0

        # Load config
        self._load_config()

    def _load_config(self) -> None:
        """Load kernel configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self.config = json.load(f)
                self.logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
                self.config = self._default_config()
        else:
            self.config = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Get default kernel configuration.

        Returns:
            Default config dictionary
        """
        return {
            "memory_size_mb": 64,
            "scheduler_type": "round_robin",
            "quantum_ms": 100,
            "theme": "light",
            "swap_enabled": True,
            "swap_size_mb": 128,
        }

    def _save_config(self) -> None:
        """Save kernel configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def register_service(self, name: str, obj: Any) -> None:
        """Register a service with the kernel.

        Args:
            name: Service name
            obj: Service object
        """
        self.services[name] = obj
        self.logger.debug(f"Registered service: {name}")
        self.event_bus.emit("SERVICE_REGISTERED", {"name": name, "service": obj})

    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service.

        Args:
            name: Service name

        Returns:
            Service object or None if not found
        """
        return self.services.get(name)

    def subscribe_event(self, event_name: str, callback: Callable) -> None:
        """Subscribe to a kernel event.

        Args:
            event_name: Event name
            callback: Callback function
        """
        self.event_bus.subscribe(event_name, callback)

    async def start(self) -> None:
        """Boot the kernel and start services.

        This initializes all registered services and starts the main event loop.
        """
        self.logger.info("=== PyVirtOS Kernel Starting ===")
        self.running = True
        self.boot_time = asyncio.get_event_loop().time()

        # Initialize scheduler if not already registered
        if "scheduler" not in self.services:
            scheduler_type = self.config.get("scheduler_type", "round_robin")
            quantum_ms = self.config.get("quantum_ms", 100)

            if scheduler_type == "priority":
                from pyvirtos.core.scheduler import PriorityScheduler

                scheduler = PriorityScheduler(quantum_ms)
            else:
                scheduler = RoundRobinScheduler(quantum_ms)

            self.register_service("scheduler", scheduler)
            self.logger.info(f"Initialized {scheduler_type} scheduler")

        self.event_bus.emit("KERNEL_BOOT")
        self.logger.info("Kernel boot complete")

    def stop(self) -> None:
        """Shutdown the kernel gracefully."""
        self.logger.info("=== PyVirtOS Kernel Shutting Down ===")
        self.running = False
        self.event_bus.emit("KERNEL_SHUTDOWN")
        self._save_config()
        self.logger.info("Kernel shutdown complete")

    async def tick(self) -> None:
        """Execute one kernel tick (advance simulation).

        This should be called regularly by the main event loop.
        """
        if not self.running:
            return

        self.tick_count += 1

        # Tick the scheduler
        scheduler = self.get_service("scheduler")
        if scheduler:
            scheduler.tick()

        # Tick other services as needed
        self.event_bus.emit("KERNEL_TICK", {"tick": self.tick_count})

    def get_uptime_ms(self) -> float:
        """Get kernel uptime in milliseconds.

        Returns:
            Uptime in milliseconds
        """
        if not self.running:
            return 0.0
        return (asyncio.get_event_loop().time() - self.boot_time) * 1000

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information.

        Returns:
            Dictionary with system info
        """
        scheduler = self.get_service("scheduler")
        task_list = scheduler.get_task_list() if scheduler else []

        return {
            "uptime_ms": self.get_uptime_ms(),
            "tick_count": self.tick_count,
            "running": self.running,
            "total_processes": len(task_list),
            "config": self.config,
        }
