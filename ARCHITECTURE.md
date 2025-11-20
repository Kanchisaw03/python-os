# PyVirtOS Architecture

## Overview

PyVirtOS is a modular virtual operating system simulator written in Python. It provides realistic OS simulation with process scheduling, virtual memory management, filesystem operations, user authentication, and an interactive GUI.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GUI Layer                             │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐ │
│  │   Desktop    │   Explorer   │  Terminal    │Task Manager│ │
│  │   (PySide6)  │              │              │            │ │
│  └──────────────┴──────────────┴──────────────┴────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kernel (Service Manager)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Event Bus | Service Registry | Configuration       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
    ┌────────────┐    ┌──────────────┐    ┌──────────────┐
    │ Scheduler  │    │ Filesystem   │    │Memory Manager│
    │            │    │              │    │              │
    │ - RR       │    │ - VFS        │    │ - Paging     │
    │ - Priority │    │ - Perms      │    │ - LRU        │
    │ - Queues   │    │ - SQLite DB  │    │ - Swap       │
    └────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
    ┌────────────┐    ┌──────────────┐    ┌──────────────┐
    │  Process   │    │    Users     │    │    Logs      │
    │            │    │              │    │              │
    │ - States   │    │ - Auth       │    │ - JSON Lines │
    │ - Lifecycle│    │ - Groups     │    │ - Filtering  │
    │ - Signals  │    │ - Bcrypt     │    │ - Audit      │
    └────────────┘    └──────────────┘    └──────────────┘
```

## Core Modules

### 1. Kernel (`core/kernel.py`)

**Responsibilities:**
- Service registration and discovery
- Boot and shutdown sequences
- Event bus for inter-component communication
- Configuration management
- System tick coordination

**Design Pattern:** Service Locator + Event Bus

**Key Classes:**
- `Kernel` - Main kernel class
- `EventBus` - Event distribution system

### 2. Process Model (`core/process.py`)

**Responsibilities:**
- Process abstraction with lifecycle
- State management (READY, RUNNING, BLOCKED, SLEEPING, ZOMBIE)
- CPU time tracking
- Memory allocation tracking
- File handle management

**Design Pattern:** State Machine

**Key Classes:**
- `Process` - Process representation
- `ProcState` - Process state enumeration

### 3. Scheduler (`core/scheduler.py`)

**Responsibilities:**
- CPU scheduling algorithms
- Process queue management
- Fair resource allocation
- Process dispatch

**Design Pattern:** Strategy Pattern (pluggable schedulers)

**Key Classes:**
- `Scheduler` - Abstract base class
- `RoundRobinScheduler` - Fair time-sharing
- `PriorityScheduler` - Priority-based preemption

**Algorithms:**
- Round-Robin: O(n) per tick, fair distribution
- Priority: O(n log n) per tick, preemptive

### 4. Virtual Filesystem (`core/filesystem.py`)

**Responsibilities:**
- Hierarchical directory structure
- File operations (create, read, write, delete)
- Permission enforcement (Unix-style rwx)
- Metadata management
- Access control

**Design Pattern:** Composite Pattern (directory tree)

**Storage:**
- SQLite for metadata
- Host filesystem for file content
- Isolated under `~/.pyvirtos/vfs/`

**Key Classes:**
- `VirtualFilesystem` - Main filesystem class
- `FileMetadata` - File metadata structure
- `FileType` - File type enumeration

### 5. User Management (`core/users.py`)

**Responsibilities:**
- User authentication
- User and group management
- Password hashing and verification
- Permission checking

**Design Pattern:** Repository Pattern

**Storage:**
- SQLite database at `~/.pyvirtos/users.db`
- Bcrypt password hashing with salt

**Key Classes:**
- `UserManager` - User management
- `User` - User representation
- `UserSession` - Authenticated session

### 6. Memory Manager (`core/memory.py`)

**Responsibilities:**
- Virtual memory abstraction
- Page-based memory management
- Physical frame allocation
- Swap file management
- Page replacement (LRU)
- Page fault handling

**Design Pattern:** Virtual Memory Manager

**Key Concepts:**
- Page size: 4KB (configurable)
- Physical memory: 64MB (configurable)
- Swap file: 128MB (configurable)
- Page replacement: LRU (Least Recently Used)

**Key Classes:**
- `MemoryManager` - Memory management
- `VirtualAddressRange` - Virtual address range
- `PageTableEntry` - Page table entry

### 7. System Logging (`core/logs.py`)

**Responsibilities:**
- Structured logging
- Log filtering and retrieval
- Audit trail
- Statistics

**Design Pattern:** Observer Pattern

**Storage:**
- JSON Lines format (`.jsonl`)
- Separate audit log
- Located at `~/.pyvirtos/logs/`

**Key Classes:**
- `SystemLogger` - Logging system
- `LogLevel` - Log level enumeration

## UI Architecture

### Desktop (`ui/desktop.py`)

**Components:**
- `Desktop` - Main window
- `SystemTray` - Status bar with clock and info
- `Dock` - Application launcher

**Features:**
- Window management
- System tray with real-time updates
- App launcher dock
- Event-driven architecture

### File Explorer (`ui/explorer_view.py`)

**Components:**
- Tree view (left panel)
- File list (right panel)
- Toolbar with navigation
- Status bar

**Features:**
- Directory tree navigation
- File listing with icons
- Create folders
- File properties
- Permission-aware display

### Terminal (`ui/terminal_view.py`)

**Components:**
- Output area (read-only text)
- Input field
- Prompt display

**Built-in Commands:**
- `ls` - List directory
- `cd` - Change directory
- `pwd` - Print working directory
- `cat` - Display file
- `touch` - Create file
- `mkdir` - Create directory
- `echo` - Print text
- `clear` - Clear screen
- `exit` - Exit terminal

**Architecture:**
- Command parser
- Command executor
- VFS integration
- Process context

### Task Manager (`ui/task_manager_view.py`)

**Components:**
- Process table
- Control buttons
- System info display

**Features:**
- Real-time process list
- Kill process
- Suspend/resume
- Priority adjustment
- CPU time tracking

## Data Flow

### Process Execution Flow

```
User Input (GUI)
    │
    ▼
Command Parser (Terminal)
    │
    ▼
Process Creation
    │
    ▼
Scheduler Queue
    │
    ▼
Scheduler Tick
    │
    ├─ Get next process
    ├─ Set state to RUNNING
    ├─ Execute process.run(quantum)
    ├─ Update CPU time
    └─ Return to queue or block
    │
    ▼
Memory Manager (if needed)
    │
    ├─ Check page table
    ├─ Handle page faults
    └─ Update LRU
    │
    ▼
Filesystem (if needed)
    │
    ├─ Check permissions
    ├─ Read/write files
    └─ Update metadata
    │
    ▼
Process State Update
    │
    ▼
GUI Update (Task Manager, etc.)
```

### Filesystem Access Flow

```
User Request (Explorer/Terminal)
    │
    ▼
Permission Check
    │
    ├─ Get user UID/GID
    ├─ Get file permissions
    └─ Verify access
    │
    ▼
File Operation
    │
    ├─ Create/Read/Write/Delete
    ├─ Update metadata
    └─ Update timestamps
    │
    ▼
Logging
    │
    ▼
GUI Update (Explorer, etc.)
```

## Design Patterns Used

1. **Service Locator** - Kernel service registry
2. **Event Bus** - Inter-component communication
3. **Strategy Pattern** - Pluggable schedulers
4. **State Machine** - Process states
5. **Composite Pattern** - Filesystem tree
6. **Repository Pattern** - User management
7. **Observer Pattern** - Logging system
8. **MVC Pattern** - GUI components

## Concurrency Model

- **Async/Await** - Used for kernel ticks and GUI updates
- **Non-blocking** - UI remains responsive during simulation
- **Timer-based** - Kernel ticks via QTimer (50ms interval)
- **UI Updates** - Via signals/slots (PySide6)

## Security Considerations

1. **Sandboxing** - VFS isolated to `~/.pyvirtos/`
2. **Permission Enforcement** - Unix-style rwx checks
3. **Password Security** - Bcrypt with salt
4. **User Isolation** - Per-user file access control
5. **No Host Access** - Commands simulated, not executed

## Performance Characteristics

- **Process Creation** - O(1)
- **Scheduler Tick** - O(n) for RR, O(n log n) for Priority
- **Memory Allocation** - O(1) average
- **Filesystem Operations** - O(log n) for tree traversal
- **User Lookup** - O(1) with SQLite indexing

## Extensibility Points

1. **Custom Schedulers** - Implement `Scheduler` interface
2. **Custom Apps** - Register with kernel
3. **Custom Commands** - Add to terminal
4. **Custom Themes** - Theme configuration files
5. **Custom Logging** - Extend `SystemLogger`

## Configuration

All configuration stored in `~/.pyvirtos/config.json`:

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

## Testing Strategy

- **Unit Tests** - Individual module testing (89 tests)
- **Integration Tests** - Multi-module workflows
- **GUI Tests** - Manual testing (automated via pytest-qt)
- **Coverage Target** - 70%+ for core modules

## Future Enhancements

1. **IPC** - Pipes, message queues, sockets
2. **Virtual Devices** - Network, sound, display
3. **Snapshots** - Checkpoint/restore
4. **Networking** - Virtual network simulation
5. **Multi-session** - Multiple concurrent users
6. **Plugins** - Dynamic app loading
7. **Performance** - Optimization and profiling
