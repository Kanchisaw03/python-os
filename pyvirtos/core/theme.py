"""Theme Engine for PyVirtOS.

Handles theme management and live theme switching.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("pyvirtos.theme")


@dataclass
class ThemeColors:
    """Theme color palette."""

    background: str = "#1a1a1a"
    foreground: str = "#ffffff"
    accent: str = "#3498db"
    accent_dark: str = "#2980b9"
    accent_light: str = "#5dade2"
    success: str = "#27ae60"
    warning: str = "#f39c12"
    error: str = "#e74c3c"
    border: str = "#444444"
    text_primary: str = "#ffffff"
    text_secondary: str = "#bdc3c7"
    surface: str = "#2c3e50"
    surface_light: str = "#34495e"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ThemeColors":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Theme:
    """Complete theme definition."""

    name: str
    version: str = "1.0"
    description: str = ""
    author: str = ""
    colors: ThemeColors = None
    font_family: str = "Arial"
    font_size: int = 10
    border_radius: int = 5
    shadow_enabled: bool = True

    def __post_init__(self):
        """Initialize defaults."""
        if self.colors is None:
            self.colors = ThemeColors()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "colors": self.colors.to_dict(),
            "font_family": self.font_family,
            "font_size": self.font_size,
            "border_radius": self.border_radius,
            "shadow_enabled": self.shadow_enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Theme":
        """Create from dictionary."""
        colors_data = data.get("colors", {})
        return cls(
            name=data.get("name", "Default"),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            colors=ThemeColors.from_dict(colors_data),
            font_family=data.get("font_family", "Arial"),
            font_size=data.get("font_size", 10),
            border_radius=data.get("border_radius", 5),
            shadow_enabled=data.get("shadow_enabled", True),
        )


class ThemeManager:
    """Manages themes and live theme switching."""

    # Built-in themes
    BUILTIN_THEMES = {
        "NeonDark": {
            "name": "NeonDark",
            "description": "Dark theme with neon accents",
            "colors": {
                "background": "#0f0f0f",
                "foreground": "#ffffff",
                "accent": "#ff0084",
                "accent_dark": "#cc0066",
                "accent_light": "#ff3399",
                "success": "#00ff00",
                "warning": "#ffff00",
                "error": "#ff0000",
                "border": "#444444",
                "text_primary": "#ffffff",
                "text_secondary": "#aaaaaa",
                "surface": "#1a1a1a",
                "surface_light": "#2a2a2a",
            },
            "font_family": "Courier New",
            "font_size": 11,
        },
        "Ocean": {
            "name": "Ocean",
            "description": "Cool ocean-inspired theme",
            "colors": {
                "background": "#0a1628",
                "foreground": "#e0f2f1",
                "accent": "#00bcd4",
                "accent_dark": "#0097a7",
                "accent_light": "#4dd0e1",
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#f44336",
                "border": "#1a237e",
                "text_primary": "#e0f2f1",
                "text_secondary": "#80deea",
                "surface": "#0d47a1",
                "surface_light": "#1565c0",
            },
            "font_family": "Arial",
            "font_size": 10,
        },
        "Forest": {
            "name": "Forest",
            "description": "Green forest-inspired theme",
            "colors": {
                "background": "#1b5e20",
                "foreground": "#c8e6c9",
                "accent": "#4caf50",
                "accent_dark": "#388e3c",
                "accent_light": "#81c784",
                "success": "#2e7d32",
                "warning": "#f57f17",
                "error": "#d32f2f",
                "border": "#1b5e20",
                "text_primary": "#c8e6c9",
                "text_secondary": "#a5d6a7",
                "surface": "#2e7d32",
                "surface_light": "#388e3c",
            },
            "font_family": "Arial",
            "font_size": 10,
        },
        "Sunset": {
            "name": "Sunset",
            "description": "Warm sunset-inspired theme",
            "colors": {
                "background": "#1a0033",
                "foreground": "#ffe0b2",
                "accent": "#ff6f00",
                "accent_dark": "#e65100",
                "accent_light": "#ffb74d",
                "success": "#ff6f00",
                "warning": "#fbc02d",
                "error": "#c62828",
                "border": "#4a235a",
                "text_primary": "#ffe0b2",
                "text_secondary": "#ffcc80",
                "surface": "#4a235a",
                "surface_light": "#6a1b9a",
            },
            "font_family": "Arial",
            "font_size": 10,
        },
    }

    def __init__(self, themes_dir: Path, kernel=None):
        """Initialize theme manager.

        Args:
            themes_dir: Directory to store custom themes
            kernel: Kernel instance for service access
        """
        self.themes_dir = themes_dir
        self.kernel = kernel
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        self.theme_callbacks: List[Callable] = []

        # Create themes directory
        self.themes_dir.mkdir(parents=True, exist_ok=True)

        # Load built-in themes
        self._load_builtin_themes()

        # Load custom themes
        self._load_custom_themes()

        # Set default theme
        self.set_theme("NeonDark")

        logger.info(f"ThemeManager initialized with {len(self.themes)} themes")

    def _load_builtin_themes(self) -> None:
        """Load built-in themes."""
        for theme_name, theme_data in self.BUILTIN_THEMES.items():
            theme = Theme.from_dict(theme_data)
            self.themes[theme_name] = theme
            logger.info(f"Loaded built-in theme: {theme_name}")

    def _load_custom_themes(self) -> None:
        """Load custom themes from directory."""
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, "r") as f:
                    data = json.load(f)
                    theme = Theme.from_dict(data)
                    self.themes[theme.name] = theme
                    logger.info(f"Loaded custom theme: {theme.name}")
            except Exception as e:
                logger.error(f"Failed to load theme from {theme_file}: {e}")

    def get_themes(self) -> List[Theme]:
        """Get list of available themes.

        Returns:
            List of themes
        """
        return list(self.themes.values())

    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name.

        Args:
            name: Theme name

        Returns:
            Theme or None
        """
        return self.themes.get(name)

    def set_theme(self, name: str) -> bool:
        """Set current theme.

        Args:
            name: Theme name

        Returns:
            True if successful
        """
        theme = self.get_theme(name)
        if not theme:
            logger.error(f"Theme not found: {name}")
            return False

        self.current_theme = theme
        logger.info(f"Theme changed to: {name}")

        # Emit theme change event
        self._emit_theme_changed()
        return True

    def get_current_theme(self) -> Optional[Theme]:
        """Get current theme.

        Returns:
            Current theme or None
        """
        return self.current_theme

    def create_theme(
        self,
        name: str,
        colors: Dict[str, str],
        description: str = "",
        author: str = "",
    ) -> bool:
        """Create a new custom theme.

        Args:
            name: Theme name
            colors: Color palette dictionary
            description: Theme description
            author: Theme author

        Returns:
            True if successful
        """
        if name in self.themes:
            logger.error(f"Theme already exists: {name}")
            return False

        try:
            theme_colors = ThemeColors.from_dict(colors)
            theme = Theme(
                name=name,
                description=description,
                author=author,
                colors=theme_colors,
            )

            # Save to file
            theme_file = self.themes_dir / f"{name}.json"
            with open(theme_file, "w") as f:
                json.dump(theme.to_dict(), f, indent=2)

            self.themes[name] = theme
            logger.info(f"Created custom theme: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create theme: {e}")
            return False

    def delete_theme(self, name: str) -> bool:
        """Delete a custom theme.

        Args:
            name: Theme name

        Returns:
            True if successful
        """
        if name not in self.themes:
            return False

        # Don't delete built-in themes
        if name in self.BUILTIN_THEMES:
            logger.error(f"Cannot delete built-in theme: {name}")
            return False

        try:
            theme_file = self.themes_dir / f"{name}.json"
            if theme_file.exists():
                theme_file.unlink()

            del self.themes[name]
            logger.info(f"Deleted theme: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete theme: {e}")
            return False

    def subscribe_theme_change(self, callback: Callable) -> None:
        """Subscribe to theme change events.

        Args:
            callback: Callback function
        """
        self.theme_callbacks.append(callback)

    def _emit_theme_changed(self) -> None:
        """Emit theme changed event."""
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.emit("theme_changed", self.current_theme)

        for callback in self.theme_callbacks:
            try:
                callback(self.current_theme)
            except Exception as e:
                logger.error(f"Error in theme change callback: {e}")

    def get_stylesheet(self) -> str:
        """Get Qt stylesheet for current theme.

        Returns:
            Qt stylesheet string
        """
        if not self.current_theme:
            return ""

        colors = self.current_theme.colors
        font = self.current_theme.font_family
        size = self.current_theme.font_size

        stylesheet = f"""
            QMainWindow {{
                background-color: {colors.background};
                color: {colors.text_primary};
            }}
            QWidget {{
                background-color: {colors.background};
                color: {colors.text_primary};
            }}
            QPushButton {{
                background-color: {colors.accent};
                color: {colors.text_primary};
                border: none;
                border-radius: {self.current_theme.border_radius}px;
                padding: 5px;
                font-family: {font};
                font-size: {size}pt;
            }}
            QPushButton:hover {{
                background-color: {colors.accent_light};
            }}
            QPushButton:pressed {{
                background-color: {colors.accent_dark};
            }}
            QLineEdit {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {self.current_theme.border_radius}px;
                padding: 5px;
                font-family: {font};
                font-size: {size}pt;
            }}
            QTextEdit {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {self.current_theme.border_radius}px;
                font-family: {font};
                font-size: {size}pt;
            }}
            QLabel {{
                color: {colors.text_primary};
                font-family: {font};
                font-size: {size}pt;
            }}
            QFrame {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
            }}
            QTableWidget {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                gridline-color: {colors.border};
            }}
            QHeaderView::section {{
                background-color: {colors.surface_light};
                color: {colors.text_primary};
                padding: 5px;
                border: none;
            }}
            QTreeWidget {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
            }}
            QListWidget {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
            }}
        """
        return stylesheet

    def get_theme_stats(self) -> Dict[str, Any]:
        """Get theme manager statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_themes": len(self.themes),
            "current_theme": self.current_theme.name if self.current_theme else None,
            "themes": [t.name for t in self.themes.values()],
        }
