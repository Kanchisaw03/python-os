"""System logging for PyVirtOS."""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    AUDIT = "AUDIT"


class SystemLogger:
    """System-wide logger for PyVirtOS."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize system logger.

        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = log_dir or Path.home() / ".pyvirtos" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / "syslog.jsonl"
        self.audit_file = self.log_dir / "audit.jsonl"

        # Python logger
        self.logger = logging.getLogger("pyvirtos")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_dir / "pyvirtos.log")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def log(
        self,
        level: LogLevel,
        message: str,
        component: str = "system",
        pid: Optional[int] = None,
        user: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        """Log a message.

        Args:
            level: Log level
            message: Log message
            component: Component name
            pid: Process ID (optional)
            user: Username (optional)
            data: Additional data (optional)
        """
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "level": level.value,
            "component": component,
            "message": message,
        }

        if pid is not None:
            log_entry["pid"] = pid

        if user is not None:
            log_entry["user"] = user

        if data:
            log_entry["data"] = data

        # Write to appropriate file
        if level == LogLevel.AUDIT:
            with open(self.audit_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        else:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        # Also log to Python logger
        log_func = {
            LogLevel.DEBUG: self.logger.debug,
            LogLevel.INFO: self.logger.info,
            LogLevel.WARN: self.logger.warning,
            LogLevel.ERROR: self.logger.error,
            LogLevel.AUDIT: self.logger.info,
        }
        log_func[level](f"[{component}] {message}")

    def debug(self, message: str, component: str = "system", **kwargs) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, component, **kwargs)

    def info(self, message: str, component: str = "system", **kwargs) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, component, **kwargs)

    def warn(self, message: str, component: str = "system", **kwargs) -> None:
        """Log warning message."""
        self.log(LogLevel.WARN, message, component, **kwargs)

    def error(self, message: str, component: str = "system", **kwargs) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, component, **kwargs)

    def audit(self, message: str, component: str = "system", **kwargs) -> None:
        """Log audit message."""
        self.log(LogLevel.AUDIT, message, component, **kwargs)

    def read_logs(
        self,
        level: Optional[LogLevel] = None,
        component: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Read logs from file.

        Args:
            level: Filter by log level
            component: Filter by component
            limit: Maximum number of entries to return

        Returns:
            List of log entries
        """
        entries = []

        if not self.log_file.exists():
            return entries

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    # Apply filters
                    if level and entry.get("level") != level.value:
                        continue
                    if component and entry.get("component") != component:
                        continue

                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        # Return last 'limit' entries
        return entries[-limit:]

    def read_audit_logs(self, limit: int = 100) -> List[dict]:
        """Read audit logs.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        entries = []

        if not self.audit_file.exists():
            return entries

        with open(self.audit_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries[-limit:]

    def clear_logs(self) -> None:
        """Clear all logs."""
        if self.log_file.exists():
            self.log_file.unlink()
        if self.audit_file.exists():
            self.audit_file.unlink()

    def get_log_stats(self) -> dict:
        """Get log statistics.

        Returns:
            Dictionary with log stats
        """
        stats = {
            "total_entries": 0,
            "by_level": {},
            "by_component": {},
        }

        if not self.log_file.exists():
            return stats

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    stats["total_entries"] += 1

                    level = entry.get("level", "UNKNOWN")
                    stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

                    component = entry.get("component", "unknown")
                    stats["by_component"][component] = (
                        stats["by_component"].get(component, 0) + 1
                    )
                except json.JSONDecodeError:
                    continue

        return stats
