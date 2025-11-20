"""Tests for workspace and animation systems."""

import pytest
import time
from pyvirtos.core.workspace import WorkspaceManager, Workspace, Window, WorkspaceState
from pyvirtos.core.animation import AnimationEngine, EasingFunction


class TestWorkspaceManager:
    """Test workspace manager functionality."""

    def test_workspace_manager_initialization(self):
        """Test workspace manager initialization."""
        manager = WorkspaceManager(num_workspaces=3)
        assert manager is not None
        assert len(manager.get_workspaces()) == 3
        assert manager.current_workspace_id == 0

    def test_get_workspaces(self):
        """Test getting all workspaces."""
        manager = WorkspaceManager(num_workspaces=3)
        workspaces = manager.get_workspaces()
        
        assert len(workspaces) == 3
        assert workspaces[0].name == "Workspace 1"
        assert workspaces[1].name == "Workspace 2"
        assert workspaces[2].name == "Workspace 3"

    def test_get_current_workspace(self):
        """Test getting current workspace."""
        manager = WorkspaceManager(num_workspaces=3)
        current = manager.get_current_workspace()
        
        assert current is not None
        assert current.workspace_id == 0
        assert current.state == WorkspaceState.ACTIVE

    def test_switch_workspace(self):
        """Test switching workspaces."""
        manager = WorkspaceManager(num_workspaces=3)
        
        # Switch to workspace 1
        assert manager.switch_workspace(1)
        assert manager.current_workspace_id == 1
        
        current = manager.get_current_workspace()
        assert current.state == WorkspaceState.ACTIVE
        
        # Previous workspace should be inactive
        prev = manager.get_workspace(0)
        assert prev.state == WorkspaceState.INACTIVE

    def test_add_window(self):
        """Test adding window to workspace."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600
        )
        
        assert manager.add_window(0, window)
        windows = manager.get_workspace_windows(0)
        assert len(windows) == 1
        assert windows[0].window_id == "win_1"

    def test_remove_window(self):
        """Test removing window from workspace."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600
        )
        
        manager.add_window(0, window)
        assert len(manager.get_workspace_windows(0)) == 1
        
        assert manager.remove_window(0, "win_1")
        assert len(manager.get_workspace_windows(0)) == 0

    def test_move_window(self):
        """Test moving window."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600
        )
        
        manager.add_window(0, window)
        assert manager.move_window(0, "win_1", 200, 200)
        
        windows = manager.get_workspace_windows(0)
        assert windows[0].x == 200
        assert windows[0].y == 200

    def test_resize_window(self):
        """Test resizing window."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600
        )
        
        manager.add_window(0, window)
        assert manager.resize_window(0, "win_1", 1024, 768)
        
        windows = manager.get_workspace_windows(0)
        assert windows[0].width == 1024
        assert windows[0].height == 768

    def test_focus_window(self):
        """Test focusing window."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window1 = Window(
            window_id="win_1",
            title="Window 1",
            x=100,
            y=100,
            width=800,
            height=600
        )
        window2 = Window(
            window_id="win_2",
            title="Window 2",
            x=200,
            y=200,
            width=800,
            height=600
        )
        
        manager.add_window(0, window1)
        manager.add_window(0, window2)
        
        assert manager.focus_window(0, "win_2")
        
        windows = manager.get_workspace_windows(0)
        assert not windows[0].focused
        assert windows[1].focused

    def test_minimize_window(self):
        """Test minimizing window."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600
        )
        
        manager.add_window(0, window)
        assert manager.minimize_window(0, "win_1")
        
        windows = manager.get_workspace_windows(0)
        assert windows[0].minimized

    def test_maximize_window(self):
        """Test maximizing window."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600
        )
        
        manager.add_window(0, window)
        assert manager.maximize_window(0, "win_1")
        
        windows = manager.get_workspace_windows(0)
        assert windows[0].maximized

    def test_restore_window(self):
        """Test restoring window."""
        manager = WorkspaceManager(num_workspaces=3)
        
        window = Window(
            window_id="win_1",
            title="Test Window",
            x=100,
            y=100,
            width=800,
            height=600,
            minimized=True,
            maximized=True
        )
        
        manager.add_window(0, window)
        assert manager.restore_window(0, "win_1")
        
        windows = manager.get_workspace_windows(0)
        assert not windows[0].minimized
        assert not windows[0].maximized

    def test_tile_windows_horizontal(self):
        """Test tiling windows horizontally."""
        manager = WorkspaceManager(num_workspaces=3)
        
        for i in range(3):
            window = Window(
                window_id=f"win_{i}",
                title=f"Window {i}",
                x=0,
                y=0,
                width=800,
                height=600
            )
            manager.add_window(0, window)
        
        assert manager.tile_windows_horizontal(0)
        
        windows = manager.get_workspace_windows(0)
        assert len(windows) == 3
        assert windows[0].y == 0
        assert windows[1].y == 360
        assert windows[2].y == 720

    def test_tile_windows_vertical(self):
        """Test tiling windows vertically."""
        manager = WorkspaceManager(num_workspaces=3)
        
        for i in range(3):
            window = Window(
                window_id=f"win_{i}",
                title=f"Window {i}",
                x=0,
                y=0,
                width=800,
                height=600
            )
            manager.add_window(0, window)
        
        assert manager.tile_windows_vertical(0)
        
        windows = manager.get_workspace_windows(0)
        assert len(windows) == 3
        assert windows[0].x == 0
        assert windows[1].x == 640
        assert windows[2].x == 1280


class TestAnimationEngine:
    """Test animation engine functionality."""

    def test_animation_engine_initialization(self):
        """Test animation engine initialization."""
        engine = AnimationEngine()
        assert engine is not None
        assert engine.get_active_animations() == 0

    def test_create_animation(self):
        """Test creating animation."""
        engine = AnimationEngine()
        
        anim_id = engine.create_animation(
            target_id="obj_1",
            property_name="x",
            start_value=0,
            end_value=100,
            duration_ms=1000
        )
        
        assert anim_id is not None
        assert engine.get_animation(anim_id) is not None

    def test_animation_update(self):
        """Test animation update."""
        engine = AnimationEngine()
        
        anim_id = engine.create_animation(
            target_id="obj_1",
            property_name="x",
            start_value=0,
            end_value=100,
            duration_ms=100
        )
        
        # Update animation
        engine.update()
        assert engine.get_active_animations() == 1

    def test_stop_animation(self):
        """Test stopping animation."""
        engine = AnimationEngine()
        
        anim_id = engine.create_animation(
            target_id="obj_1",
            property_name="x",
            start_value=0,
            end_value=100,
            duration_ms=1000
        )
        
        assert engine.stop_animation(anim_id)
        assert engine.get_active_animations() == 0

    def test_pause_resume_animation(self):
        """Test pausing and resuming animation."""
        engine = AnimationEngine()
        
        anim_id = engine.create_animation(
            target_id="obj_1",
            property_name="x",
            start_value=0,
            end_value=100,
            duration_ms=1000
        )
        
        # Pause
        assert engine.pause_animation(anim_id)
        assert engine.get_active_animations() == 0
        
        # Resume
        assert engine.resume_animation(anim_id)
        assert engine.get_active_animations() == 1

    def test_fade_in_animation(self):
        """Test fade in animation."""
        engine = AnimationEngine()
        
        anim_id = engine.animate_fade_in("obj_1", duration_ms=300)
        
        assert anim_id is not None
        animation = engine.get_animation(anim_id)
        assert animation.start_value == 0.0
        assert animation.end_value == 1.0

    def test_fade_out_animation(self):
        """Test fade out animation."""
        engine = AnimationEngine()
        
        anim_id = engine.animate_fade_out("obj_1", duration_ms=300)
        
        assert anim_id is not None
        animation = engine.get_animation(anim_id)
        assert animation.start_value == 1.0
        assert animation.end_value == 0.0

    def test_slide_in_animation(self):
        """Test slide in animation."""
        engine = AnimationEngine()
        
        anim_id = engine.animate_slide_in_left("obj_1", distance=100, duration_ms=300)
        
        assert anim_id is not None
        animation = engine.get_animation(anim_id)
        assert animation.start_value == -100
        assert animation.end_value == 0

    def test_scale_animation(self):
        """Test scale animation."""
        engine = AnimationEngine()
        
        anim_id = engine.animate_scale("obj_1", start_scale=0.8, end_scale=1.0, duration_ms=300)
        
        assert anim_id is not None
        animation = engine.get_animation(anim_id)
        assert animation.start_value == 0.8
        assert animation.end_value == 1.0

    def test_rotate_animation(self):
        """Test rotate animation."""
        engine = AnimationEngine()
        
        anim_id = engine.animate_rotate("obj_1", start_angle=0, end_angle=360, duration_ms=500)
        
        assert anim_id is not None
        animation = engine.get_animation(anim_id)
        assert animation.start_value == 0
        assert animation.end_value == 360

    def test_easing_functions(self):
        """Test easing functions."""
        engine = AnimationEngine()
        
        # Test linear
        assert engine._apply_easing(0.5, EasingFunction.LINEAR) == 0.5
        
        # Test ease in
        assert engine._apply_easing(0.5, EasingFunction.EASE_IN) == 0.25
        
        # Test ease out
        result = engine._apply_easing(0.5, EasingFunction.EASE_OUT)
        assert 0.7 < result < 0.8
        
        # Test ease in out
        assert engine._apply_easing(0.25, EasingFunction.EASE_IN_OUT) == 0.125

    def test_animation_completion_callback(self):
        """Test animation completion callback."""
        engine = AnimationEngine()
        
        callback_called = []
        
        def on_complete(anim_id):
            callback_called.append(anim_id)
        
        anim_id = engine.create_animation(
            target_id="obj_1",
            property_name="x",
            start_value=0,
            end_value=100,
            duration_ms=10,
            on_complete=on_complete
        )
        
        # Wait for animation to complete
        time.sleep(0.05)
        engine.update()
        
        assert len(callback_called) > 0

    def test_multiple_animations(self):
        """Test multiple animations."""
        engine = AnimationEngine()
        
        anim1 = engine.create_animation("obj_1", "x", 0, 100, 1000)
        anim2 = engine.create_animation("obj_2", "y", 0, 100, 1000)
        anim3 = engine.create_animation("obj_3", "opacity", 0, 1, 1000)
        
        assert engine.get_active_animations() == 3
        
        engine.stop_animation(anim2)
        assert engine.get_active_animations() == 2

    def test_animation_stats(self):
        """Test animation statistics."""
        engine = AnimationEngine()
        
        engine.create_animation("obj_1", "x", 0, 100, 1000)
        engine.create_animation("obj_2", "y", 0, 100, 1000)
        
        stats = engine.get_animation_stats()
        assert stats["total_animations"] == 2
        assert stats["active_animations"] == 2
