# PyVirtOS Quick Start Guide

## Installation

```bash
# Clone the project
cd pyvirtos

# Install dependencies
pip install -r requirements.txt

# Or with Poetry
poetry install
```

## Running PyVirtOS

### GUI Mode (Recommended)

```bash
# Start the GUI
python -m pyvirtos

# Or with demo data
python scripts/demo_gui.py
```

### CLI Mode

```bash
# Run CLI demo
python scripts/demo.py

# Or run kernel only
python -m pyvirtos --cli
```

## Using the Terminal

Once the GUI is open, click the Terminal icon in the dock.

### Available Commands

```bash
# Navigation
ls [path]              # List directory
cd <path>              # Change directory
pwd                    # Print working directory

# File Operations
touch <file>           # Create file
cat <file>             # Display file contents
echo <text>            # Print text
mkdir <dir>            # Create directory

# System
help                   # Show help
clear                  # Clear screen
exit                   # Exit terminal
```

### Examples

```bash
# Create a file
touch /home/alice/test.txt

# Write to file
echo "Hello World" > /home/alice/test.txt

# Read file
cat /home/alice/test.txt

# Create directory
mkdir /home/alice/projects

# List directory
ls /home/alice
```

## Using File Explorer

Click the Explorer icon in the dock to open the file browser.

### Features

- **Tree View** (left) - Navigate directory structure
- **File List** (right) - View files in current directory
- **Path Bar** - Type path directly
- **New Folder** - Create new directory
- **Refresh** - Update file list

## Using Task Manager

Click the Task Manager icon in the dock.

### Features

- **Process List** - View all running processes
- **Kill** - Terminate a process
- **Suspend** - Pause a process
- **Resume** - Continue a suspended process
- **Real-time Updates** - Auto-refresh every 500ms

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest pyvirtos/tests/test_scheduler.py -v

# Run with coverage
pytest --cov=pyvirtos --cov-report=html

# Run specific test
pytest pyvirtos/tests/test_process.py::TestProcess::test_process_creation -v
```

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

All data is stored in `~/.pyvirtos/`:

- `config.json` - Configuration
- `vfs/` - Virtual filesystem
- `users.db` - User database
- `swap.bin` - Swap file
- `logs/` - System logs

## Common Tasks

### Create a User

```bash
# In terminal
# Note: User creation is done programmatically in Python
# For now, use the default root user or modify demo_gui.py
```

### Create Files and Directories

```bash
# In terminal
mkdir /home/mydir
touch /home/mydir/myfile.txt
echo "content" > /home/mydir/myfile.txt
```

### View System Information

Look at the system tray (top of window) for:
- Current time
- System uptime
- Number of processes
- Memory usage

### Monitor Processes

1. Open Task Manager
2. View process list
3. Select a process
4. Click Kill, Suspend, or Resume

## Troubleshooting

### GUI Won't Start

```bash
# Make sure PySide6 is installed
pip install PySide6

# Check Python version (3.11+ required)
python --version
```

### Tests Fail

```bash
# Make sure all dependencies are installed
pip install -r requirements.txt

# Run tests with verbose output
pytest -v --tb=short
```

### Permission Denied Errors

- Make sure `~/.pyvirtos/` directory exists
- Check file permissions in `~/.pyvirtos/`
- Try deleting `~/.pyvirtos/` to reset

## Keyboard Shortcuts

### Terminal
- `Enter` - Execute command
- `Ctrl+C` - Cancel (not implemented)
- `Ctrl+L` - Clear (use `clear` command)

### File Explorer
- `Enter` - Open directory
- `Backspace` - Go up one level

### Task Manager
- `Delete` - Kill selected process
- `Space` - Select/deselect process

## Tips and Tricks

1. **Create Sample Data** - Run `python scripts/demo_gui.py` for pre-populated filesystem

2. **Monitor Processes** - Open Task Manager to see processes created by terminal commands

3. **Check Logs** - View `~/.pyvirtos/logs/syslog.jsonl` for system events

4. **Reset System** - Delete `~/.pyvirtos/` directory to start fresh

5. **Run Tests** - Use `pytest --cov=pyvirtos` to see test coverage

## Next Steps

1. **Explore the GUI** - Try each application window
2. **Run Terminal Commands** - Create files and directories
3. **Monitor Processes** - Watch them in Task Manager
4. **Read Documentation** - Check README.md and API.md
5. **Run Tests** - Verify everything works with `pytest`

## Getting Help

- **README.md** - General information and features
- **API.md** - Complete API documentation
- **ARCHITECTURE.md** - System design and patterns
- **Docstrings** - In-code documentation
- **Tests** - Example usage in test files

## Support

For issues or questions:

1. Check the documentation files
2. Review test files for usage examples
3. Check `~/.pyvirtos/logs/` for error messages
4. Review the source code docstrings

## Performance Tips

1. **Close Unused Windows** - Reduces UI update overhead
2. **Limit Processes** - Too many processes slow down scheduler
3. **Clear Logs** - Large log files slow down logging
4. **Adjust Quantum** - Smaller quantum = more context switches

## Advanced Usage

### Custom Scheduler

Edit `pyvirtos/main.py` to use Priority Scheduler:

```python
kernel.config["scheduler_type"] = "priority"
```

### Custom Memory Size

Edit `pyvirtos/main.py`:

```python
memory_manager = MemoryManager(physical_memory_mb=128)
```

### Custom Processes

Edit `scripts/demo_gui.py` to create custom processes:

```python
proc = Process(
    pid=1,
    ppid=0,
    name="custom_process",
    owner_user="root",
    priority=3
)
scheduler.add_process(proc)
```

## Enjoy PyVirtOS!

Have fun exploring the virtual operating system. Feel free to modify the code and experiment with different configurations!
