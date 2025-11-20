"""Tests for kernel module."""

import asyncio
import pytest
from pathlib import Path
import tempfile

from pyvirtos.core.kernel import Kernel, EventBus
from pyvirtos.core.process import Process


class TestEventBus:
    """Test EventBus class."""

    def test_event_subscription(self):
        """Test subscribing to events."""
        bus = EventBus()
        callback_called = False

        def callback(data):
            nonlocal callback_called
            callback_called = True

        bus.subscribe("test_event", callback)
        bus.emit("test_event")
        assert callback_called

    def test_event_data(self):
        """Test event data passing."""
        bus = EventBus()
        received_data = None

        def callback(data):
            nonlocal received_data
            received_data = data

        bus.subscribe("test_event", callback)
        bus.emit("test_event", {"key": "value"})
        assert received_data == {"key": "value"}

    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        bus = EventBus()
        calls = []

        def callback1(data):
            calls.append(1)

        def callback2(data):
            calls.append(2)

        bus.subscribe("test_event", callback1)
        bus.subscribe("test_event", callback2)
        bus.emit("test_event")
        assert calls == [1, 2]


class TestKernel:
    """Test Kernel class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_kernel_creation(self, temp_config_dir):
        """Test creating a kernel."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        assert kernel.running is False
        assert kernel.tick_count == 0

    def test_default_config(self, temp_config_dir):
        """Test default kernel configuration."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        assert kernel.config["memory_size_mb"] == 64
        assert kernel.config["scheduler_type"] == "round_robin"
        assert kernel.config["quantum_ms"] == 100

    @pytest.mark.asyncio
    async def test_kernel_start(self, temp_config_dir):
        """Test starting the kernel."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        await kernel.start()
        assert kernel.running is True
        kernel.stop()

    @pytest.mark.asyncio
    async def test_kernel_stop(self, temp_config_dir):
        """Test stopping the kernel."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        await kernel.start()
        kernel.stop()
        assert kernel.running is False

    def test_register_service(self, temp_config_dir):
        """Test registering a service."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        service = {"name": "test_service"}
        kernel.register_service("test", service)
        assert kernel.get_service("test") == service

    def test_get_service(self, temp_config_dir):
        """Test getting a service."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        service = {"name": "test_service"}
        kernel.register_service("test", service)
        retrieved = kernel.get_service("test")
        assert retrieved == service

    def test_get_nonexistent_service(self, temp_config_dir):
        """Test getting a nonexistent service."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        assert kernel.get_service("nonexistent") is None

    def test_subscribe_event(self, temp_config_dir):
        """Test subscribing to kernel events."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        event_received = False

        def callback(data):
            nonlocal event_received
            event_received = True

        kernel.subscribe_event("TEST_EVENT", callback)
        kernel.event_bus.emit("TEST_EVENT")
        assert event_received

    @pytest.mark.asyncio
    async def test_kernel_tick(self, temp_config_dir):
        """Test kernel tick."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        await kernel.start()
        initial_tick = kernel.tick_count
        await kernel.tick()
        assert kernel.tick_count == initial_tick + 1
        kernel.stop()

    @pytest.mark.asyncio
    async def test_kernel_scheduler_initialization(self, temp_config_dir):
        """Test that scheduler is initialized on boot."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        await kernel.start()
        scheduler = kernel.get_service("scheduler")
        assert scheduler is not None
        kernel.stop()

    def test_get_system_info(self, temp_config_dir):
        """Test getting system information."""
        config_path = temp_config_dir / "config.json"
        kernel = Kernel(config_path)
        info = kernel.get_system_info()
        assert "uptime_ms" in info
        assert "tick_count" in info
        assert "running" in info
        assert "total_processes" in info

    def test_config_save_load(self, temp_config_dir):
        """Test saving and loading configuration."""
        config_path = temp_config_dir / "config.json"
        kernel1 = Kernel(config_path)
        kernel1.config["custom_key"] = "custom_value"
        kernel1._save_config()

        kernel2 = Kernel(config_path)
        assert kernel2.config.get("custom_key") == "custom_value"
