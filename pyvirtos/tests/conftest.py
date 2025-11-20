"""Pytest configuration and fixtures."""

import pytest
import asyncio
import logging
from pathlib import Path
import tempfile


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging handlers after each test."""
    yield
    # Remove all handlers from pyvirtos logger
    logger = logging.getLogger("pyvirtos")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
