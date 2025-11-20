# Sprint 10: Multi-Workspace & Animations - Complete Documentation

## Overview

Sprint 10 adds two powerful systems to PyVirtOS:
1. **Workspace Manager** - Multiple virtual desktops with window management
2. **Animation Engine** - Smooth animations and transitions

## 1. Workspace Manager

### Architecture

The Workspace Manager (`pyvirtos/core/workspace.py`) provides:
- Multiple virtual workspaces (desktops)
- Window management per workspace
- Window positioning and sizing
- Window state management (minimize, maximize, focus)
- Window tiling (horizontal and vertical)

### Key Classes

#### Workspace
Represents a virtual desktop:
```python
@dataclass
class Workspace:
    workspace_id: int
    name: str
    windows: List[Window]
    state: WorkspaceState
    background_color: str
```

#### Window
Represents a window:
```python
@dataclass
class Window:
    window_id: str
    title: str
    x: int
    y: int
    width: int
    height: int
    minimized: bool
    maximized: bool
    focused: bool
```

#### WorkspaceState
Window states:
- `ACTIVE` - Workspace is active
- `INACTIVE` - Workspace is inactive
- `TRANSITIONING` - Workspace is transitioning

### API Usage

```python
from pyvirtos.core.workspace import WorkspaceManager, Window

# Initialize
workspace_manager = WorkspaceManager(kernel, num_workspaces=3)

# Get workspaces
workspaces = workspace_manager.get_workspaces()
current = workspace_manager.get_current_workspace()

# Switch workspace
workspace_manager.switch_workspace(1)

# Window management
window = Window(
    window_id="win_1",
    title="My App",
    x=100, y=100,
    width=800, height=600
)

# Add window to current workspace
workspace_manager.add_window(0, window)

# Move window
workspace_manager.move_window(0, "win_1", 200, 200)

# Resize window
workspace_manager.resize_window(0, "win_1", 1024, 768)

# Focus window
workspace_manager.focus_window(0, "win_1")

# Minimize/Maximize
workspace_manager.minimize_window(0, "win_1")
workspace_manager.maximize_window(0, "win_1")
workspace_manager.restore_window(0, "win_1")

# Tile windows
workspace_manager.tile_windows_horizontal(0)
workspace_manager.tile_windows_vertical(0)
```

### Features

#### Multiple Workspaces
- Create multiple virtual desktops
- Switch between workspaces
- Each workspace has its own windows
- Independent window management

#### Window Management
- Add/remove windows
- Move windows (drag)
- Resize windows
- Focus windows (z-index)
- Minimize/maximize windows
- Restore windows

#### Window Tiling
- Horizontal tiling - stack windows vertically
- Vertical tiling - stack windows horizontally
- Automatic layout

### Events

The workspace manager emits events:
- `workspace_changed` - Workspace switched
- `window_added` - Window added to workspace
- `window_removed` - Window removed
- `window_moved` - Window moved
- `window_resized` - Window resized
- `window_focused` - Window focused
- `window_minimized` - Window minimized
- `window_maximized` - Window maximized
- `window_restored` - Window restored
- `windows_tiled` - Windows tiled

---

## 2. Animation Engine

### Architecture

The Animation Engine (`pyvirtos/core/animation.py`) provides:
- Smooth animations and transitions
- Multiple easing functions
- Preset animations (fade, slide, scale, rotate)
- Animation lifecycle management
- Callback support

### Key Classes

#### Animation
Represents an animation:
```python
@dataclass
class Animation:
    animation_id: str
    target_id: str
    property_name: str
    start_value: float
    end_value: float
    duration_ms: int
    easing: EasingFunction
    on_complete: Optional[Callable]
    active: bool
```

#### EasingFunction
Animation easing functions:
- `LINEAR` - Linear interpolation
- `EASE_IN` - Slow start, fast end
- `EASE_OUT` - Fast start, slow end
- `EASE_IN_OUT` - Slow start and end
- `EASE_QUAD` - Quadratic easing
- `EASE_CUBIC` - Cubic easing

### API Usage

```python
from pyvirtos.core.animation import AnimationEngine, EasingFunction

# Initialize
animation_engine = AnimationEngine(kernel)

# Create custom animation
anim_id = animation_engine.create_animation(
    target_id="obj_1",
    property_name="x",
    start_value=0,
    end_value=100,
    duration_ms=500,
    easing=EasingFunction.EASE_OUT,
    on_complete=lambda id: print(f"Done: {id}")
)

# Preset animations
fade_in = animation_engine.animate_fade_in("obj_1", duration_ms=300)
fade_out = animation_engine.animate_fade_out("obj_1", duration_ms=300)
slide_left = animation_engine.animate_slide_in_left("obj_1", distance=100)
slide_right = animation_engine.animate_slide_in_right("obj_1", distance=100)
scale = animation_engine.animate_scale("obj_1", start_scale=0.8, end_scale=1.0)
rotate = animation_engine.animate_rotate("obj_1", start_angle=0, end_angle=360)

# Update animations (call in main loop)
animation_engine.update()

# Control animations
animation_engine.pause_animation(anim_id)
animation_engine.resume_animation(anim_id)
animation_engine.stop_animation(anim_id)

# Get animation info
animation = animation_engine.get_animation(anim_id)
active_count = animation_engine.get_active_animations()
stats = animation_engine.get_animation_stats()
```

### Features

#### Easing Functions
- **Linear** - Constant speed
- **Ease In** - Accelerating from zero velocity
- **Ease Out** - Decelerating to zero velocity
- **Ease In Out** - Acceleration until halfway, then deceleration
- **Ease Quad** - Quadratic acceleration
- **Ease Cubic** - Cubic acceleration

#### Preset Animations
- **Fade In/Out** - Opacity animation
- **Slide In** - Position animation from edge
- **Scale** - Size transformation
- **Rotate** - Rotation transformation

#### Animation Control
- Pause/resume animations
- Stop animations
- Get animation status
- Subscribe to animation frames

### Events

The animation engine emits events:
- `animation_frame` - Animation frame update

---

## Integration

### Kernel Integration

Both services are registered with the kernel:

```python
# In main.py
workspace_manager = WorkspaceManager(kernel, num_workspaces=3)
kernel.register_service("workspace_manager", workspace_manager)

animation_engine = AnimationEngine(kernel)
kernel.register_service("animation_engine", animation_engine)
```

### Event Bus Integration

Services emit events through the kernel's event bus:
- Workspace events for workspace changes
- Animation events for animation updates

### GUI Integration

The desktop can use these services:

```python
# Get workspace manager
workspace_manager = kernel.get_service("workspace_manager")

# Get animation engine
animation_engine = kernel.get_service("animation_engine")

# Switch workspace on keyboard shortcut
workspace_manager.switch_workspace(1)

# Animate window opening
animation_engine.animate_fade_in("window_1")
```

---

## Usage Examples

### Workspace Switching

```python
# Switch to workspace 2
workspace_manager.switch_workspace(1)

# Get current workspace
current = workspace_manager.get_current_workspace()
print(f"Current: {current.name}")

# List all workspaces
for ws in workspace_manager.get_workspaces():
    print(f"{ws.workspace_id}: {ws.name}")
```

### Window Management

```python
# Create window
window = Window(
    window_id="calc",
    title="Calculator",
    x=100, y=100,
    width=400, height=300
)

# Add to workspace
workspace_manager.add_window(0, window)

# Move window
workspace_manager.move_window(0, "calc", 200, 200)

# Focus window
workspace_manager.focus_window(0, "calc")

# Minimize
workspace_manager.minimize_window(0, "calc")

# Restore
workspace_manager.restore_window(0, "calc")
```

### Window Tiling

```python
# Tile windows horizontally
workspace_manager.tile_windows_horizontal(0)

# Tile windows vertically
workspace_manager.tile_windows_vertical(0)
```

### Animations

```python
# Fade in animation
anim_id = animation_engine.animate_fade_in("window_1", duration_ms=300)

# Slide in from left
anim_id = animation_engine.animate_slide_in_left("window_1", distance=100)

# Scale animation
anim_id = animation_engine.animate_scale("window_1", start_scale=0.8, end_scale=1.0)

# Custom animation
anim_id = animation_engine.create_animation(
    target_id="obj_1",
    property_name="x",
    start_value=0,
    end_value=500,
    duration_ms=1000,
    easing=EasingFunction.EASE_OUT
)

# Update in main loop
animation_engine.update()
```

---

## Testing

### Test Coverage

28 new tests covering:
- Workspace Manager (14 tests)
  - Initialization
  - Workspace switching
  - Window management
  - Window positioning
  - Window state (minimize, maximize, focus)
  - Window tiling
  
- Animation Engine (14 tests)
  - Animation creation
  - Animation control (pause, resume, stop)
  - Preset animations
  - Easing functions
  - Animation callbacks
  - Multiple animations

### Running Tests

```bash
# Run workspace and animation tests
pytest pyvirtos/tests/test_workspace_animation.py -v

# Run all tests
pytest pyvirtos/tests/ -v
```

**Results**: ✅ **28/28 PASSING**

---

## File Structure

```
pyvirtos/
├── core/
│   ├── workspace.py           # NEW - Workspace manager
│   ├── animation.py           # NEW - Animation engine
│   ├── kernel.py              # UPDATED - Service registration
│   └── ...
├── tests/
│   ├── test_workspace_animation.py  # NEW - 28 tests
│   └── ...
├── SPRINT_10_FEATURES.md      # NEW - Feature documentation
└── ...
```

---

## Configuration

### Workspace Configuration

Number of workspaces can be configured:

```python
workspace_manager = WorkspaceManager(kernel, num_workspaces=4)
```

### Animation Configuration

Animation duration and easing can be customized:

```python
animation_engine.create_animation(
    target_id="obj_1",
    property_name="x",
    start_value=0,
    end_value=100,
    duration_ms=500,  # Customize duration
    easing=EasingFunction.EASE_OUT  # Customize easing
)
```

---

## Performance Notes

- **Workspace Switching**: O(1) - instant
- **Window Operations**: O(n) where n = windows in workspace
- **Animation Update**: O(m) where m = active animations
- **Tiling**: O(n) where n = windows to tile

---

## Future Enhancements

1. **Workspace Animations** - Animate workspace transitions
2. **Window Snap** - Snap windows to edges
3. **Virtual Desktops** - More than 3 workspaces
4. **Window Groups** - Group related windows
5. **Workspace Layouts** - Save/restore layouts
6. **Advanced Animations** - Bezier curves, keyframes

---

## Summary

Sprint 10 adds powerful workspace and animation capabilities:
- ✅ Multiple virtual desktops
- ✅ Complete window management
- ✅ Window tiling (horizontal/vertical)
- ✅ Smooth animations with easing
- ✅ Preset animations (fade, slide, scale, rotate)
- ✅ 28 comprehensive tests
- ✅ Full kernel integration

**Total Tests**: 138 (110 existing + 28 new)
**Code Added**: ~1,200 lines
**Documentation**: Complete
