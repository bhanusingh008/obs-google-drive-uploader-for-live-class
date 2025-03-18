"""
Main entry point for the Google Drive Uploader application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.ui.main_window import MainWindow
from src.core.config import Config
from src.utils.resources import get_icon_path


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Set application icon
    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Load configuration
    config = Config()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 