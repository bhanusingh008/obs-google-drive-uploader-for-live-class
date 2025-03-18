"""
Base classes for UI components.
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from src.core.config import Config


class BaseWidget(QWidget):
    """Base class for all custom widgets."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the widget."""
        super().__init__(parent)
        self.config = Config()
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup the UI components. Override in subclasses."""
        raise NotImplementedError
    
    def show_error(self, message: str) -> None:
        """Show an error message."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", message)
    
    def show_info(self, message: str) -> None:
        """Show an information message."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Information", message)
    
    def show_warning(self, message: str) -> None:
        """Show a warning message."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Warning", message)
    
    def set_status(self, message: str, is_error: bool = False) -> None:
        """Set status message. Override in subclasses if needed."""
        pass 