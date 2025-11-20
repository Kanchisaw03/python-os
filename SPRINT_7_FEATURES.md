# Sprint 7: Advanced Features - Complete Documentation

## Overview

Sprint 7 adds four major advanced features to PyVirtOS:
1. **App System** - Dynamic app loading and management
2. **Snapshot Engine** - Save and restore complete OS state
3. **Advanced Theme Engine** - Live theme switching with 4 built-in themes
4. **Advanced Shell** - Pipes, redirects, and enhanced commands

## 1. App System

### Architecture

The App Manager (`pyvirtos/core/app_manager.py`) provides:
- Dynamic app discovery and loading
- App lifecycle management (launch, suspend, resume, close)
- Permission checking
- Instance tracking and statistics

### App Structure

Each app must have this folder structure:

```
~/.pyvirtos/apps/MyApp/
├── metadata.json
├── main.py
└── icon.png (optional)
```

### metadata.json Format

```json
{
  "name": "Calculator",
  "version": "1.0",
  "entry": "main.py",
  "icon": "icon.png",
  "permissions": ["filesystem", "window"],
  "description": "Simple calculator app",
  "author": "PyVirtOS Team"
}
```

### API Usage

```python
from pyvirtos.core.app_manager import AppManager

# Initialize
app_manager = AppManager(Path.home() / ".pyvirtos" / "apps", kernel)

# List installed apps
apps = app_manager.get_installed_apps()
for app in apps:
    print(f"{app.name} v{app.version}")

# Launch app
instance = app_manager.launch_app("Calculator", pid=42)

# Suspend/Resume
app_manager.suspend_app(instance.app_id)
app_manager.resume_app(instance.app_id)

# Close app
app_manager.close_app(instance.app_id)

# Get running apps
running = app_manager.get_running_apps()
```

### App States

- `INSTALLED` - App is installed but not running
- `RUNNING` - App is currently running
- `SUSPENDED` - App is paused
- `CRASHED` - App has crashed

### Terminal Commands

```bash
app list                    # List installed apps
app launch <name>          # Launch an app
```

---

## 2. Snapshot Engine

### Architecture

The Snapshot Manager (`pyvirtos/core/snapshot.py`) provides:
- Complete OS state serialization
- Snapshot creation and management
- State restoration
- Snapshot listing and deletion

### What Gets Saved

A snapshot captures:
- **Filesystem** - Complete directory structure and files
- **Users** - User accounts and groups
- **Processes** - Running processes and their states
- **Memory** - Memory allocation and usage
- **Apps** - Running app instances
- **Config** - System configuration

### API Usage

```python
from pyvirtos.core.snapshot import SnapshotManager

# Initialize
snapshot_manager = SnapshotManager(
    Path.home() / ".pyvirtos" / "snapshots",
    kernel
)

# Save snapshot
snapshot_manager.save_snapshot(
    "my_snapshot",
    description="Before important update",
    include_apps=True
)

# List snapshots
snapshots = snapshot_manager.list_snapshots()
for snap in snapshots:
    print(f"{snap.name} - {snap.timestamp}")

# Load snapshot
snapshot_manager.load_snapshot("my_snapshot")

# Delete snapshot
snapshot_manager.delete_snapshot("my_snapshot")
```

### Snapshot Storage

Snapshots are stored in:
```
~/.pyvirtos/snapshots/
├── snapshot_name_1/
│   ├── snapshot.json      # Metadata
│   └── state.json         # Full state
├── snapshot_name_2/
│   ├── snapshot.json
│   └── state.json
```

### Terminal Commands

```bash
snapshot save <name>       # Save current state
snapshot load <name>       # Restore from snapshot
snapshot list              # List all snapshots
```

---

## 3. Advanced Theme Engine

### Architecture

The Theme Manager (`pyvirtos/core/theme.py`) provides:
- 4 built-in themes
- Custom theme creation
- Live theme switching
- Qt stylesheet generation
- Theme persistence

### Built-in Themes

#### NeonDark
- **Style**: Dark with neon accents
- **Primary Color**: #ff0084 (Neon Pink)
- **Background**: #0f0f0f (Almost Black)
- **Best For**: Developers, night use

#### Ocean
- **Style**: Cool ocean-inspired
- **Primary Color**: #00bcd4 (Cyan)
- **Background**: #0a1628 (Deep Blue)
- **Best For**: Professional, calm environment

#### Forest
- **Style**: Green forest-inspired
- **Primary Color**: #4caf50 (Green)
- **Background**: #1b5e20 (Dark Green)
- **Best For**: Nature lovers, relaxing

#### Sunset
- **Style**: Warm sunset-inspired
- **Primary Color**: #ff6f00 (Orange)
- **Background**: #1a0033 (Deep Purple)
- **Best For**: Evening use, warm feel

### API Usage

```python
from pyvirtos.core.theme import ThemeManager

# Initialize
theme_manager = ThemeManager(
    Path.home() / ".pyvirtos" / "themes",
    kernel
)

# Get available themes
themes = theme_manager.get_themes()
for theme in themes:
    print(f"{theme.name}: {theme.description}")

# Set theme
theme_manager.set_theme("Ocean")

# Get current theme
current = theme_manager.get_current_theme()
print(f"Current: {current.name}")

# Create custom theme
colors = {
    "background": "#000000",
    "foreground": "#ffffff",
    "accent": "#ff0000",
    "success": "#00ff00",
    "error": "#ff0000",
}
theme_manager.create_theme("MyTheme", colors, "My custom theme")

# Get Qt stylesheet
stylesheet = theme_manager.get_stylesheet()
app.setStyleSheet(stylesheet)

# Subscribe to theme changes
def on_theme_changed(theme):
    print(f"Theme changed to: {theme.name}")

theme_manager.subscribe_theme_change(on_theme_changed)
```

### Theme Colors

Each theme defines:
- `background` - Main background color
- `foreground` - Main text color
- `accent` - Primary accent color
- `accent_dark` - Darker accent variant
- `accent_light` - Lighter accent variant
- `success` - Success indicator color
- `warning` - Warning indicator color
- `error` - Error indicator color
- `border` - Border color
- `text_primary` - Primary text color
- `text_secondary` - Secondary text color
- `surface` - Surface/panel color
- `surface_light` - Lighter surface color

### Terminal Commands

```bash
theme list                 # List available themes
theme set <name>          # Switch to theme
```

---

## 4. Advanced Shell

### Architecture

The Shell system (`pyvirtos/core/shell.py`) provides:
- **ShellParser** - Parses commands with pipes and redirects
- **ShellExecutor** - Executes parsed commands

### Features

#### Pipes
Connect command output to input:
```bash
ls /home | grep alice
ps | grep python
```

#### Output Redirection
Write output to files:
```bash
echo "hello" > file.txt          # Overwrite
echo "world" >> file.txt         # Append
```

#### Flags
Commands support flags:
```bash
ls --json /home                  # JSON output
ps --json                        # Process list as JSON
```

### Supported Commands

#### File Operations
- `ls [path]` - List directory
- `cd <path>` - Change directory
- `pwd` - Print working directory
- `cat <file>` - Display file
- `touch <file>` - Create file
- `mkdir <dir>` - Create directory
- `echo <text>` - Print text

#### Process Management
- `ps [--json]` - List processes
- `kill <pid>` - Terminate process

#### System Info
- `whoami` - Current user
- `sysinfo` - System information
- `uptime` - System uptime

#### Theme Management
- `theme list` - List themes
- `theme set <name>` - Change theme

#### Snapshot Management
- `snapshot save <name>` - Save state
- `snapshot load <name>` - Restore state
- `snapshot list` - List snapshots

#### App Management
- `app list` - List installed apps
- `app launch <name>` - Launch app

#### Utilities
- `help` - Show help
- `clear` - Clear screen
- `exit` - Exit terminal

### API Usage

```python
from pyvirtos.core.shell import ShellParser, ShellExecutor

# Parse command
parser = ShellParser()
parser.parse("ls /home | grep alice")

# Check for pipes
if parser.has_pipes():
    print("Command has pipes")

# Check for redirects
if parser.has_redirect():
    print(f"Output redirected to: {parser.redirect_output}")

# Execute command
executor = ShellExecutor(vfs, users, scheduler, app_manager)
output, success = executor.execute("ls /home")
print(output)

# Execute with pipes
output, success = executor.execute("ps | grep python")

# Execute with redirect
output, success = executor.execute("echo hello > output.txt")
```

### Advanced Examples

```bash
# List files in home directory
ls /home

# Find all Python processes
ps | grep python

# Save system info to file
sysinfo > system_info.txt

# Create and populate a file
touch myfile.txt
echo "Hello World" > myfile.txt

# Change theme and save snapshot
theme set Ocean
snapshot save after_theme_change

# Launch app and check running processes
app launch Calculator
ps --json
```

---

## Integration with GUI

### Desktop Integration

The new services are automatically registered with the kernel:

```python
# In main.py
app_manager = AppManager(apps_dir, kernel)
kernel.register_service("app_manager", app_manager)

theme_manager = ThemeManager(themes_dir, kernel)
kernel.register_service("theme_manager", theme_manager)

snapshot_manager = SnapshotManager(snapshots_dir, kernel)
kernel.register_service("snapshot_manager", snapshot_manager)
```

### Terminal Integration

The terminal uses the new shell system:

```python
from pyvirtos.core.shell import ShellExecutor

executor = ShellExecutor(vfs, users, scheduler, app_manager)
output, success = executor.execute(command_line)
```

---

## Testing

### Test Coverage

21 new tests covering:
- App Manager (3 tests)
- Theme Manager (5 tests)
- Snapshot Manager (3 tests)
- Shell Parser (5 tests)
- Shell Executor (5 tests)

### Running Tests

```bash
# Run advanced features tests
pytest pyvirtos/tests/test_advanced_features.py -v

# Run all tests
pytest pyvirtos/tests/ -v
```

---

## File Structure

```
pyvirtos/
├── core/
│   ├── app_manager.py         # App system
│   ├── theme.py               # Theme engine
│   ├── snapshot.py            # Snapshot engine
│   ├── shell.py               # Advanced shell
│   └── ...
├── tests/
│   ├── test_advanced_features.py  # New tests
│   └── ...
└── ...
```

---

## Configuration

### App Directory
```
~/.pyvirtos/apps/
```

### Theme Directory
```
~/.pyvirtos/themes/
```

### Snapshot Directory
```
~/.pyvirtos/snapshots/
```

---

## Performance Notes

- **App Loading**: O(n) where n = number of apps
- **Theme Switching**: O(1) - instant
- **Snapshot Save**: O(m) where m = system state size
- **Shell Parsing**: O(k) where k = command length

---

## Future Enhancements

1. **App Permissions** - Enforce app permissions
2. **App Store** - Download and install apps
3. **Theme Editor** - Visual theme creation
4. **Snapshot Diff** - Compare snapshots
5. **Shell Scripting** - .pv script files
6. **App Marketplace** - Community apps

---

## Summary

Sprint 7 adds powerful advanced features to PyVirtOS:
- ✅ Dynamic app system with lifecycle management
- ✅ Complete OS state snapshots
- ✅ Live theme switching with 4 themes
- ✅ Advanced shell with pipes and redirects
- ✅ 21 comprehensive tests
- ✅ Full integration with existing systems

**Total Tests**: 110 (89 existing + 21 new)
**Code Added**: ~1,500 lines
**Documentation**: Complete
