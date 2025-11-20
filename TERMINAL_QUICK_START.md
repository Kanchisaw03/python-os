# PyVirtOS Terminal - Quick Start Guide

## 🎯 Terminal Now Fully Functional!

The terminal now has:
- ✅ **Input field** - Type commands directly
- ✅ **Send button** - Click to execute
- ✅ **Press Enter** - Also executes commands
- ✅ **Auto-focus** - Input field is ready to type

---

## 🚀 How to Use

1. **Launch PyVirtOS**
   ```bash
   python -m pyvirtos
   ```

2. **Click Terminal icon** (⌨️) in the dock

3. **Type a command** in the input field at the bottom

4. **Press Enter** or click **Send** button

5. **See output** in the terminal window

---

## 📝 Try These Commands

### Basic File Operations
```bash
help                    # Show all commands
ls                      # List files
pwd                     # Print working directory
cd /home                # Change directory
touch myfile.txt        # Create file
echo "hello" > file.txt # Write to file
cat file.txt            # Read file
mkdir mydir             # Create directory
```

### Advanced Shell Features
```bash
# Pipes - connect commands
ls /home | grep alice

# Redirects - save to files
ps > processes.txt
ps --json > data.json

# Complex pipes
ls /home | grep alice | wc
```

### Themes (4 Beautiful Themes)
```bash
theme list              # Show available themes
theme set Ocean         # Switch to Ocean theme
theme set Forest        # Switch to Forest theme
theme set NeonDark      # Switch to NeonDark theme
theme set Sunset        # Switch to Sunset theme
```

### Snapshots (Save/Restore State)
```bash
snapshot save state1    # Save current state
snapshot list           # Show all snapshots
snapshot load state1    # Restore to state1
```

### Process Management
```bash
ps                      # List all processes
ps --json               # Get JSON output
kill 1                  # Kill process with ID 1
```

### Apps
```bash
app list                # List installed apps
app launch Calculator   # Launch Calculator app
```

### System Info
```bash
whoami                  # Current user
sysinfo                 # System information
```

---

## 🎨 Terminal Features

- **Green text on black** - Classic terminal look
- **Prompt shows path** - `root@pyvirtos:/home$`
- **Auto-scroll** - Output scrolls to show latest
- **Input field** - Clear, focused input area
- **Send button** - Visual feedback for execution

---

## 💡 Tips

1. **Type `help`** to see all available commands
2. **Use Tab** to autocomplete (if supported)
3. **Use Up/Down arrows** to navigate command history (if supported)
4. **Click in input field** if it loses focus
5. **Press Enter** to execute command

---

## 🔧 Advanced Examples

### Example 1: Create Project Structure
```bash
mkdir /home/myproject
mkdir /home/myproject/src
mkdir /home/myproject/tests
touch /home/myproject/README.txt
echo "# My Project" > /home/myproject/README.txt
```

### Example 2: Backup Before Changes
```bash
snapshot save before_changes
mkdir /home/data
touch /home/data/file.txt
snapshot save after_changes
snapshot list
```

### Example 3: Process Monitoring
```bash
ps
ps --json > processes.json
ps | grep python
```

### Example 4: Theme Switching
```bash
theme set Ocean
# UI updates immediately!
theme set Forest
theme set NeonDark
```

---

## ✨ All Advanced Features Working

✅ Pipes (`|`)
✅ Redirects (`>`, `>>`)
✅ Themes (4 built-in)
✅ Snapshots (save/restore)
✅ Apps (dynamic loading)
✅ Processes (with JSON)
✅ File operations
✅ System info

---

## 🎉 Everything is Ready!

**The terminal is now fully functional with all advanced features!**

Start typing commands and explore PyVirtOS! 🚀
