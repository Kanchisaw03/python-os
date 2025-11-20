# PyVirtOS Terminal - Complete Usage Guide

## ✅ Terminal is Now Fully Functional!

The terminal input field is now ready to accept commands with:
- ✅ **Input field** - Type commands here
- ✅ **Send button** - Click to execute
- ✅ **Enter key** - Press to execute
- ✅ **Auto-focus** - Ready to type immediately

---

## 🎯 Getting Started

1. **Launch PyVirtOS**
   ```bash
   python -m pyvirtos
   ```

2. **Click Terminal icon** (⌨️) in the dock

3. **Type a command** in the input field at the bottom

4. **Press Enter** or click **Send** button

5. **See output** in the terminal window above

---

## 📋 Available Commands

### File Operations
```bash
ls                      # List current directory
ls /path                # List specific directory
cd /path                # Change directory
pwd                     # Print working directory
cat file.txt            # Display file contents
touch file.txt          # Create empty file
mkdir dirname           # Create directory
echo "text" > file.txt  # Write to file
echo "text" >> file.txt # Append to file
```

### Process Management
```bash
ps                      # List all processes
ps --json               # Get JSON output
kill <pid>              # Kill process by ID
```

### System Information
```bash
whoami                  # Current user
sysinfo                 # System information
```

### Advanced Features

#### Themes (4 Beautiful Themes)
```bash
theme list              # Show available themes
theme set Ocean         # Switch to Ocean theme
theme set Forest        # Switch to Forest theme
theme set NeonDark      # Switch to NeonDark theme
theme set Sunset        # Switch to Sunset theme
```

**Themes Available:**
- **NeonDark** - Dark background with neon pink accents
- **Ocean** - Cool cyan/blue theme
- **Forest** - Green forest theme
- **Sunset** - Warm orange/red theme

#### Snapshots (Save/Restore OS State)
```bash
snapshot save name      # Save current OS state
snapshot list           # Show all saved snapshots
snapshot load name      # Restore to saved state
```

#### Apps (Dynamic App System)
```bash
app list                # List installed apps
app launch AppName      # Launch an app
```

#### Shell Features

**Pipes** - Connect command outputs:
```bash
ls /home | grep alice
ps | grep python
ls /home | grep alice | wc
```

**Redirects** - Save output to files:
```bash
echo "hello" > file.txt         # Overwrite file
echo "world" >> file.txt        # Append to file
ps > processes.txt              # Save process list
ps --json > data.json           # Save JSON output
```

**Flags** - Get different output formats:
```bash
ps --json                       # JSON format
ls --json /path                 # JSON format
```

---

## 🎯 Quick Examples

### Example 1: Create Project Structure
```bash
mkdir /home/myproject
mkdir /home/myproject/src
mkdir /home/myproject/tests
touch /home/myproject/README.txt
echo "# My Project" > /home/myproject/README.txt
ls /home/myproject
```

### Example 2: Use Pipes
```bash
ls /home | grep alice
ps | grep python
ls /home | grep alice | wc
```

### Example 3: Save and Restore State
```bash
snapshot save initial_state
mkdir /home/test
touch /home/test/file.txt
snapshot save with_test_dir
snapshot list
snapshot load initial_state
```

### Example 4: Switch Themes
```bash
theme set Ocean
# UI updates immediately!
theme set Forest
theme set NeonDark
theme set Sunset
```

### Example 5: Process Management
```bash
ps
ps --json
ps | grep python
ps > processes.txt
```

### Example 6: File Operations with Redirects
```bash
echo "Line 1" > data.txt
echo "Line 2" >> data.txt
echo "Line 3" >> data.txt
cat data.txt
```

---

## 💡 Tips & Tricks

1. **Type `help`** - Shows all available commands
2. **Use pipes** - Connect commands with `|`
3. **Use redirects** - Save output with `>` or `>>`
4. **Use flags** - Add `--json` for JSON output
5. **Click input field** - If focus is lost
6. **Press Enter** - To execute commands
7. **Use Send button** - Visual way to execute

---

## 🔧 Troubleshooting

### Input field not responding
- Click in the input field to focus it
- Try clicking the Send button instead of pressing Enter

### Command not found
- Type `help` to see available commands
- Check spelling of command

### No output shown
- Some commands may not produce output
- Check if command executed successfully

### Error messages
- Read the error message carefully
- Check command syntax
- Verify file/directory paths exist

---

## 📊 Terminal Features

- **Green text on black** - Classic terminal appearance
- **Prompt shows path** - `root@pyvirtos:/home$`
- **Auto-scroll** - Automatically shows latest output
- **Input field** - Clear, focused input area
- **Send button** - Visual feedback for execution
- **Command echo** - Shows command before output

---

## ✨ Advanced Features Summary

✅ **Pipes** - `command1 | command2`
✅ **Redirects** - `command > file` and `command >> file`
✅ **Flags** - `command --json`
✅ **Themes** - 4 built-in themes + live switching
✅ **Snapshots** - Save/restore complete OS state
✅ **Apps** - Dynamic app loading and management
✅ **Processes** - Process management with JSON output
✅ **File Operations** - Complete filesystem access
✅ **System Info** - User and system information

---

## 🎉 You're Ready!

The terminal is fully functional with all advanced features integrated!

**Start typing commands and explore PyVirtOS!** 🚀

---

## 📚 Additional Resources

- Type `help` in terminal for command list
- Check ADVANCED_FEATURES_NOW_ACTIVE.md for feature overview
- See SPRINT_10_FEATURES.md for technical details
- Review API.md for complete API reference
