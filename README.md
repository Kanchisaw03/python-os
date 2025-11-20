# PyVirtOS - A Mini Operating System Simulator

A fully functional, modular virtual operating system simulator written in Python with an interactive GUI. PyVirtOS simulates core OS concepts including process scheduling, virtual memory management, filesystem operations, user permissions, and system logging.

## Features

- **Process Management**: Process lifecycle, forking, and state management
- **CPU Scheduling**: Round-Robin and Priority-based scheduling algorithms
- **Virtual Memory**: Page-based memory management with LRU eviction and swap support
- **Virtual Filesystem**: Complete filesystem abstraction with permissions and access control
- **User Management**: User authentication, groups, and permission enforcement
- **Interactive GUI**: Desktop environment with file explorer, terminal, and task manager
- **System Logging**: Comprehensive audit and system logging
- **Theme System**: Customizable light/dark themes
- **App Launcher**: Plugin architecture for third-party applications

## Project Structure

```
pyvirtos/
├── core/                    # Core OS modules
│   ├── kernel.py           # Boot and service management
│   ├── process.py          # Process abstraction
│   ├── scheduler.py        # CPU scheduling algorithms
│   ├── memory.py           # Virtual memory manager
│   ├── filesystem.py       # Virtual filesystem
│   ├── users.py            # User and permission management
│   ├── logs.py             # System logging
│   └── apps/               # Built-in applications
├── ui/                      # GUI components
│   ├── desktop.py          # Desktop window manager
│   ├── explorer_view.py    # File explorer
│   ├── task_manager_view.py # Process manager
│   ├── terminal_view.py    # Interactive shell
│   └── theme_manager.py    # Theme system
├── apps/                    # Third-party apps
├── tests/                   # Unit and integration tests
├── scripts/                 # Build and demo scripts
└── config/                  # Configuration files
```

## Requirements

- Python 3.11+
- PySide6 (for GUI) or Textual (for TUI)
- See `pyproject.toml` for full dependencies

## Installation

### Using Poetry (Recommended)

```bash
poetry install
```

### Using pip

```bash
pip install -e .
```

## Quick Start

### Run the Kernel (CLI mode)

```bash
python -m pyvirtos --cli
```

### Run with GUI

```bash
python -m pyvirtos
```

Or run the demo with sample data:

```bash
python scripts/demo_gui.py
```

### Run Tests

```bash
pytest
pytest --cov=pyvirtos tests/
```

### Run Demo Script (CLI)

```bash
python scripts/demo.py
```

## Architecture Overview

### Kernel
The kernel is the core of PyVirtOS, managing:
- Service registration and lookup
- Event bus for inter-component communication
- Boot and shutdown sequences
- System configuration

### Process Model
Processes have:
- Process ID (PID) and Parent PID (PPID)
- State (READY, RUNNING, BLOCKED, SLEEPING, ZOMBIE)
- Priority and CPU time tracking
- Memory allocation
- File handles

### Scheduler
Two scheduling algorithms are implemented:
- **Round-Robin**: Fair time-sharing with fixed quantum
- **Priority**: Preemptive scheduling based on process priority

### Virtual Memory
- Page-based memory management (4KB pages)
- LRU page replacement policy
- Swap file support for overcommitted memory
- Per-process page tables

### Virtual Filesystem
- Hierarchical directory structure
- File permissions (rwx for user/group/other)
- User and group ownership
- Standard operations: create, read, write, delete, chmod, chown

### Users & Permissions
- User authentication with bcrypt hashing
- Group membership
- Permission enforcement at filesystem and process level
- Root user with special privileges

### GUI Components
- **Desktop**: Main window with system tray, dock, and desktop area
- **File Explorer**: Browse virtual filesystem with tree view and file listing
- **Terminal**: Interactive shell with commands (ls, cd, cat, touch, mkdir, echo, etc.)
- **Task Manager**: View and manage running processes (kill, suspend, resume)
- **System Tray**: Clock, system info, and user menu

## Features

### Implemented ✓
- Process management and scheduling (Round-Robin, Priority)
- Virtual filesystem with permissions
- User authentication and management
- Virtual memory with paging and swap
- System logging
- Desktop GUI with multiple windows
- File explorer
- Terminal emulator
- Task manager
- 89 unit tests

### In Progress
- Theme system (light/dark modes)
- App launcher and plugin system
- Advanced shell commands

### Future
- Inter-process communication (pipes, message queues)
- Virtual device drivers
- Checkpoint/restore snapshots
- Network simulation
- Multi-session support

## Development

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run pre-commit hooks:
```bash
pre-commit run --all-files
```

### Testing

Unit tests are located in `pyvirtos/tests/`. Run them with:

```bash
pytest
pytest -v  # Verbose output
pytest --cov=pyvirtos  # With coverage report
```

Coverage target: 70%+ for core modules

## Configuration

Configuration is stored in `~/.pyvirtos/config.json`:

```json
{
  "memory_size_mb": 64,
  "scheduler_type": "round_robin",
  "quantum_ms": 100,
  "theme": "light",
  "swap_enabled": true,
  "swap_size_mb": 128
}
```

## Data Storage

PyVirtOS stores data in `~/.pyvirtos/`:
- `config.json` - System configuration
- `vfs/` - Virtual filesystem storage
- `vfs_meta.sqlite` - Filesystem metadata
- `users.db` - User database
- `swap.bin` - Swap file
- `logs/` - System logs (JSONL format)

## Demo Script

A demo script is provided to showcase PyVirtOS features:

```bash
python scripts/demo.py
```

This will:
1. Boot the kernel
2. Create sample users
3. Create test files
4. Spawn multiple processes
5. Show scheduler fairness
6. Display system statistics

## Roadmap

### Sprint 1 ✓ (In Progress)
- [x] Kernel and service registry
- [x] Process model
- [x] Round-Robin and Priority schedulers
- [x] Unit tests for core modules

### Sprint 2 (Next)
- [ ] Virtual filesystem
- [ ] User management and authentication
- [ ] Permission enforcement
- [ ] Shell commands

### Sprint 3
- [ ] Virtual memory manager
- [ ] Paging and swap
- [ ] Memory visualization

### Sprint 4
- [ ] Desktop GUI
- [ ] File explorer
- [ ] Terminal emulator
- [ ] Window manager

### Sprint 5
- [ ] Task manager
- [ ] System logging viewer
- [ ] Theme system
- [ ] App launcher

### Sprint 6
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Packaging and distribution
- [ ] Demo video

## Security Considerations

- No direct host shell execution - all commands simulated
- Filesystem access limited to `~/.pyvirtos/` sandbox
- Password storage using bcrypt with salt
- Permission enforcement at filesystem and process level
- User isolation and privilege separation

## Performance Targets

- Support 200+ concurrent simulated processes
- Virtual memory up to 512MB with reasonable host memory usage
- Responsive UI during heavy simulation
- Async/await for non-blocking operations

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Author

PyVirtOS Contributors

## Acknowledgments

Inspired by classic OS education projects and modern system design patterns.
