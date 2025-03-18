"""
Utility module for handling application resources.
"""

from pathlib import Path
from typing import Optional


def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource file.
    
    Args:
        relative_path: Path relative to the resources directory
        
    Returns:
        Absolute path to the resource file
    """
    base_path = Path(__file__).parent.parent / "resources"
    return base_path / relative_path


def get_icon_path() -> Optional[Path]:
    """
    Get the path to the application icon.
    
    Returns:
        Path to the icon file if it exists, None otherwise
    """
    icon_path = get_resource_path("icon.ico")
    return icon_path if icon_path.exists() else None 