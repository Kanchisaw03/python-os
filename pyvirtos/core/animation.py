"""Animation Engine for PyVirtOS.

Handles smooth animations and transitions.
"""

import logging
import time
from typing import Callable, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("pyvirtos.animation")


class EasingFunction(Enum):
    """Easing functions for animations."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_QUAD = "ease_quad"
    EASE_CUBIC = "ease_cubic"


@dataclass
class Animation:
    """Animation definition."""

    animation_id: str
    target_id: str
    property_name: str
    start_value: float
    end_value: float
    duration_ms: int
    easing: EasingFunction = EasingFunction.LINEAR
    start_time: float = None
    on_complete: Optional[Callable] = None
    active: bool = True

    def __post_init__(self):
        """Initialize animation."""
        if self.start_time is None:
            self.start_time = time.time() * 1000


class AnimationEngine:
    """Manages animations and transitions."""

    def __init__(self, kernel=None):
        """Initialize animation engine.

        Args:
            kernel: Kernel instance
        """
        self.kernel = kernel
        self.animations: Dict[str, Animation] = {}
        self.next_animation_id = 1
        self.animation_callbacks: Dict[str, Callable] = {}

        logger.info("AnimationEngine initialized")

    def create_animation(
        self,
        target_id: str,
        property_name: str,
        start_value: float,
        end_value: float,
        duration_ms: int,
        easing: EasingFunction = EasingFunction.LINEAR,
        on_complete: Optional[Callable] = None,
    ) -> str:
        """Create a new animation.

        Args:
            target_id: Target object ID
            property_name: Property to animate
            start_value: Starting value
            end_value: Ending value
            duration_ms: Duration in milliseconds
            easing: Easing function
            on_complete: Callback when animation completes

        Returns:
            Animation ID
        """
        animation_id = f"anim_{self.next_animation_id}"
        self.next_animation_id += 1

        animation = Animation(
            animation_id=animation_id,
            target_id=target_id,
            property_name=property_name,
            start_value=start_value,
            end_value=end_value,
            duration_ms=duration_ms,
            easing=easing,
            on_complete=on_complete,
        )

        self.animations[animation_id] = animation
        logger.info(
            f"Created animation {animation_id}: {target_id}.{property_name} "
            f"{start_value} -> {end_value} ({duration_ms}ms)"
        )

        return animation_id

    def update(self) -> None:
        """Update all active animations."""
        current_time = time.time() * 1000
        completed = []

        for animation_id, animation in self.animations.items():
            if not animation.active:
                continue

            elapsed = current_time - animation.start_time
            progress = min(elapsed / animation.duration_ms, 1.0)

            # Apply easing
            eased_progress = self._apply_easing(progress, animation.easing)

            # Calculate current value
            current_value = (
                animation.start_value
                + (animation.end_value - animation.start_value) * eased_progress
            )

            # Emit animation frame event
            self._emit_animation_frame(
                animation_id, animation.target_id, animation.property_name, current_value
            )

            # Check if animation is complete
            if progress >= 1.0:
                completed.append(animation_id)

        # Clean up completed animations
        for animation_id in completed:
            animation = self.animations[animation_id]
            animation.active = False

            # Call completion callback
            if animation.on_complete:
                try:
                    animation.on_complete(animation_id)
                except Exception as e:
                    logger.error(f"Error in animation callback: {e}")

            logger.info(f"Animation completed: {animation_id}")

    def stop_animation(self, animation_id: str) -> bool:
        """Stop an animation.

        Args:
            animation_id: Animation ID

        Returns:
            True if successful
        """
        animation = self.animations.get(animation_id)
        if not animation:
            return False

        animation.active = False
        logger.info(f"Animation stopped: {animation_id}")
        return True

    def pause_animation(self, animation_id: str) -> bool:
        """Pause an animation.

        Args:
            animation_id: Animation ID

        Returns:
            True if successful
        """
        animation = self.animations.get(animation_id)
        if not animation:
            return False

        animation.active = False
        logger.info(f"Animation paused: {animation_id}")
        return True

    def resume_animation(self, animation_id: str) -> bool:
        """Resume a paused animation.

        Args:
            animation_id: Animation ID

        Returns:
            True if successful
        """
        animation = self.animations.get(animation_id)
        if not animation:
            return False

        animation.active = True
        logger.info(f"Animation resumed: {animation_id}")
        return True

    def get_animation(self, animation_id: str) -> Optional[Animation]:
        """Get animation by ID.

        Args:
            animation_id: Animation ID

        Returns:
            Animation or None
        """
        return self.animations.get(animation_id)

    def get_active_animations(self) -> int:
        """Get count of active animations.

        Returns:
            Number of active animations
        """
        return sum(1 for a in self.animations.values() if a.active)

    # Preset animations

    def animate_fade_in(
        self, target_id: str, duration_ms: int = 300, on_complete: Optional[Callable] = None
    ) -> str:
        """Animate fade in.

        Args:
            target_id: Target object ID
            duration_ms: Duration in milliseconds
            on_complete: Completion callback

        Returns:
            Animation ID
        """
        return self.create_animation(
            target_id,
            "opacity",
            0.0,
            1.0,
            duration_ms,
            EasingFunction.EASE_OUT,
            on_complete,
        )

    def animate_fade_out(
        self, target_id: str, duration_ms: int = 300, on_complete: Optional[Callable] = None
    ) -> str:
        """Animate fade out.

        Args:
            target_id: Target object ID
            duration_ms: Duration in milliseconds
            on_complete: Completion callback

        Returns:
            Animation ID
        """
        return self.create_animation(
            target_id,
            "opacity",
            1.0,
            0.0,
            duration_ms,
            EasingFunction.EASE_IN,
            on_complete,
        )

    def animate_slide_in_left(
        self, target_id: str, distance: float = 100, duration_ms: int = 300,
        on_complete: Optional[Callable] = None
    ) -> str:
        """Animate slide in from left.

        Args:
            target_id: Target object ID
            distance: Distance to slide
            duration_ms: Duration in milliseconds
            on_complete: Completion callback

        Returns:
            Animation ID
        """
        return self.create_animation(
            target_id,
            "x",
            -distance,
            0,
            duration_ms,
            EasingFunction.EASE_OUT,
            on_complete,
        )

    def animate_slide_in_right(
        self, target_id: str, distance: float = 100, duration_ms: int = 300,
        on_complete: Optional[Callable] = None
    ) -> str:
        """Animate slide in from right.

        Args:
            target_id: Target object ID
            distance: Distance to slide
            duration_ms: Duration in milliseconds
            on_complete: Completion callback

        Returns:
            Animation ID
        """
        return self.create_animation(
            target_id,
            "x",
            distance,
            0,
            duration_ms,
            EasingFunction.EASE_OUT,
            on_complete,
        )

    def animate_scale(
        self, target_id: str, start_scale: float = 0.8, end_scale: float = 1.0,
        duration_ms: int = 300, on_complete: Optional[Callable] = None
    ) -> str:
        """Animate scale transformation.

        Args:
            target_id: Target object ID
            start_scale: Starting scale
            end_scale: Ending scale
            duration_ms: Duration in milliseconds
            on_complete: Completion callback

        Returns:
            Animation ID
        """
        return self.create_animation(
            target_id,
            "scale",
            start_scale,
            end_scale,
            duration_ms,
            EasingFunction.EASE_OUT,
            on_complete,
        )

    def animate_rotate(
        self, target_id: str, start_angle: float = 0, end_angle: float = 360,
        duration_ms: int = 500, on_complete: Optional[Callable] = None
    ) -> str:
        """Animate rotation.

        Args:
            target_id: Target object ID
            start_angle: Starting angle
            end_angle: Ending angle
            duration_ms: Duration in milliseconds
            on_complete: Completion callback

        Returns:
            Animation ID
        """
        return self.create_animation(
            target_id,
            "rotation",
            start_angle,
            end_angle,
            duration_ms,
            EasingFunction.LINEAR,
            on_complete,
        )

    # Private helper methods

    def _apply_easing(self, progress: float, easing: EasingFunction) -> float:
        """Apply easing function to progress.

        Args:
            progress: Progress value (0.0 to 1.0)
            easing: Easing function

        Returns:
            Eased progress value
        """
        if easing == EasingFunction.LINEAR:
            return progress
        elif easing == EasingFunction.EASE_IN:
            return progress * progress
        elif easing == EasingFunction.EASE_OUT:
            return 1 - (1 - progress) * (1 - progress)
        elif easing == EasingFunction.EASE_IN_OUT:
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return 1 - 2 * (1 - progress) * (1 - progress)
        elif easing == EasingFunction.EASE_QUAD:
            return progress * progress
        elif easing == EasingFunction.EASE_CUBIC:
            return progress * progress * progress
        else:
            return progress

    def _emit_animation_frame(
        self, animation_id: str, target_id: str, property_name: str, value: float
    ) -> None:
        """Emit animation frame event.

        Args:
            animation_id: Animation ID
            target_id: Target object ID
            property_name: Property name
            value: Current value
        """
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit(
                "animation_frame",
                {
                    "animation_id": animation_id,
                    "target_id": target_id,
                    "property": property_name,
                    "value": value,
                },
            )

        # Call registered callback
        callback_key = f"{target_id}:{property_name}"
        if callback_key in self.animation_callbacks:
            try:
                self.animation_callbacks[callback_key](value)
            except Exception as e:
                logger.error(f"Error in animation callback: {e}")

    def subscribe_animation(self, target_id: str, property_name: str, callback: Callable) -> None:
        """Subscribe to animation updates.

        Args:
            target_id: Target object ID
            property_name: Property name
            callback: Callback function
        """
        callback_key = f"{target_id}:{property_name}"
        self.animation_callbacks[callback_key] = callback

    def get_animation_stats(self) -> Dict[str, Any]:
        """Get animation statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_animations": len(self.animations),
            "active_animations": self.get_active_animations(),
            "animations": [
                {
                    "id": a.animation_id,
                    "target": a.target_id,
                    "property": a.property_name,
                    "active": a.active,
                }
                for a in self.animations.values()
            ],
        }
