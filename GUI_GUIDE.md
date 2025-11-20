# PyVirtOS GUI Guide

## What You Should See

When you launch PyVirtOS with `python -m pyvirtos` or `python scripts/demo_gui.py`, you should see:

### Main Desktop Window

```
┌─────────────────────────────────────────────────────────────────┐
│ PyVirtOS - Virtual Operating System                        root  │
├─────────────────────────────────────────────────────────────────┤
│ 20:33:25  PyVirtOS | Uptime: 5s | Processes: 3                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│                                                                   │
│                  Welcome to PyVirtOS                             │
│                                                                   │
│        Click an icon in the dock below to launch an app          │
│                                                                   │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│  📁        ⌨️        ⚙️        🔧                               │
│ Explorer  Terminal  Task Mgr  Settings                          │
└─────────────────────────────────────────────────────────────────┘
```

## How to Use

### 1. **File Explorer** (📁)
Click the folder icon to open the file browser.

**Features:**
- Browse virtual filesystem
- Create new folders
- View file properties
- Navigate directories using the tree view on the left
- See file list on the right

### 2. **Terminal** (⌨️)
Click the terminal icon to open the shell.

**Available Commands:**
```
help              - Show help
ls [path]         - List directory
cd <path>         - Change directory
pwd               - Print working directory
cat <file>        - Display file contents
touch <file>      - Create file
mkdir <dir>       - Create directory
echo <text>       - Print text
clear             - Clear screen
exit              - Exit terminal
```

**Example:**
```
root@pyvirtos:/$ ls /home
alice  bob

root@pyvirtos:/$ cd /home/alice

root@pyvirtos:/home/alice$ ls
readme.txt  projects

root@pyvirtos:/home/alice$ cat readme.txt
Welcome to PyVirtOS!
```

### 3. **Task Manager** (⚙️)
Click the settings icon to view running processes.

**Features:**
- View all processes
- See process details (PID, Name, User, State, CPU Time, Memory)
- Kill processes
- Suspend/resume processes
- Real-time updates

### 4. **System Tray** (Top Bar)
Shows real-time system information:
- **Time**: Current system time
- **System Info**: Uptime, number of processes
- **User Menu**: Click "root" for user options

## Troubleshooting

### Black Screen with Just "root"
This was the initial issue. If you see this:

1. **Check the dock** - Do you see the 4 application icons at the bottom?
   - If YES: Click one to launch an application
   - If NO: The GUI didn't render properly, close and try again

2. **Click an Icon** - Try clicking the Explorer (📁) icon
   - A new window should open with the file browser

3. **Still Black?** - Try these steps:
   ```bash
   # Close any running instances
   # Clear the cache
   rm -rf ~/.pyvirtos/
   
   # Run again
   python -m pyvirtos
   ```

### Applications Won't Launch
If clicking icons doesn't open windows:

1. Check the terminal output for errors
2. Make sure PySide6 is installed: `pip install PySide6`
3. Try running the demo instead: `python scripts/demo_gui.py`

### GUI is Slow
The kernel tick runs every 50ms. If it's slow:

1. Close other applications
2. Reduce the number of processes
3. Adjust the kernel tick interval in `pyvirtos/ui/desktop.py` (line 211)

## Features Demonstrated

### Process Scheduling
- Processes run in the scheduler
- CPU time is tracked and displayed
- Processes can be suspended/resumed

### Virtual Filesystem
- Complete directory structure
- File permissions (rwx)
- User isolation
- Create/read/write/delete operations

### User Management
- Default root user
- Sample users (alice, bob) in demo
- Permission enforcement

### Memory Management
- Virtual memory allocation
- Paging and swap
- Memory tracking per process

### System Logging
- All events logged to `~/.pyvirtos/logs/syslog.jsonl`
- Audit trail for security events
- Real-time system monitoring

## Tips

1. **Start with Terminal** - It's the easiest way to explore the system
2. **Use File Explorer** - Visual way to browse the filesystem
3. **Check Task Manager** - See what processes are running
4. **Read Logs** - Check `~/.pyvirtos/logs/syslog.jsonl` for details

## Example Workflow

1. **Launch Terminal**
   ```
   root@pyvirtos:/$ cd /home/alice
   root@pyvirtos:/home/alice$ ls
   readme.txt  projects
   ```

2. **Create a File**
   ```
   root@pyvirtos:/home/alice$ touch myfile.txt
   root@pyvirtos:/home/alice$ echo "Hello" > myfile.txt
   root@pyvirtos:/home/alice$ cat myfile.txt
   Hello
   ```

3. **View in Explorer**
   - Open File Explorer
   - Navigate to `/home/alice`
   - See the file you just created

4. **Check Task Manager**
   - Open Task Manager
   - See the terminal process running
   - View its CPU time and memory usage

## Keyboard Shortcuts

### Terminal
- `Enter` - Execute command
- `Ctrl+L` - Use `clear` command

### File Explorer
- `Enter` - Open directory
- `Backspace` - Go up one level

### Task Manager
- `Delete` - Kill selected process
- `Space` - Select/deselect

## Performance Notes

- **Kernel Tick**: 50ms interval (adjustable)
- **UI Update**: 100ms interval (adjustable)
- **Max Processes**: Tested with 50+ processes
- **Memory**: Simulated, not real allocation

## Next Steps

1. **Explore the Code** - Check `pyvirtos/ui/` for GUI implementation
2. **Modify Commands** - Add custom terminal commands
3. **Create Themes** - Customize colors and fonts
4. **Build Apps** - Create new applications to launch from dock

## Support

- **README.md** - General information
- **API.md** - API documentation
- **ARCHITECTURE.md** - System design
- **QUICKSTART.md** - Quick reference
- **Docstrings** - In-code documentation

Enjoy exploring PyVirtOS! 🚀
