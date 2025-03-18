"""
Main window for the Google Drive Uploader application.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QComboBox,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from src.ui.base import BaseWidget
from src.core.config import Config
from src.core.obs_manager import OBSManager
from src.utils.resources import get_icon_path
import logging
from datetime import datetime
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UploadWorker(QThread):
    """Worker thread for file uploads."""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, file_path: Path, drive_manager, class_name: str, chapter_name: str, current_year: str, subtopic_name: str = "Main"):
        """Initialize the worker."""
        super().__init__()
        self.file_path = file_path
        self.drive_manager = drive_manager
        self.class_name = class_name
        self.chapter_name = chapter_name
        self.current_year = current_year
        self.subtopic_name = subtopic_name
    
    def run(self):
        """Run the upload process."""
        try:
            def progress_callback(progress: int):
                self.progress.emit(progress)
            
            # Upload file with progress tracking
            file_id = self.drive_manager.upload_file(
                str(self.file_path),
                self.class_name,
                self.chapter_name,
                self.current_year,
                self.subtopic_name,
                progress_callback=progress_callback
            )
            
            if file_id:
                self.progress.emit(100)
                self.finished.emit(True, "Upload completed successfully")
            else:
                self.finished.emit(False, "Upload failed - no file ID returned")
        except Exception as e:
            self.finished.emit(False, str(e))


class UIConstants:
    BUTTON_COLORS = {
        "green": {"normal": "#4CAF50", "hover": "#45a049"},
        "blue": {"normal": "#2196F3", "hover": "#1976D2"},
        "red": {"normal": "#f44336", "hover": "#d32f2f"}
    }
    STYLES = {
        "dropdown": """
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #999;
            }
        """
    }


class MainWindow(QMainWindow):
    """Main window of the application."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.config = Config()
        self.selected_file: Optional[Path] = None
        self.obs_manager = OBSManager()
        
        # Initialize Google Drive manager
        try:
            self.drive_manager = self.obs_manager.drive_manager
            self.is_drive_configured = True
        except Exception as e:
            logger.warning(f"Failed to initialize Google Drive manager: {e}")
            self.is_drive_configured = False
        
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self._update_recording_status)
        self.current_recording_path: Optional[Path] = None  # Store current recording path
        self.setup_ui()
        self.setup_icon()
        # Try to connect to OBS but don't block UI if it fails
        QTimer.singleShot(0, self.connect_obs)
    
    def connect_obs(self) -> None:
        """Connect to OBS WebSocket server."""
        try:
            if self.obs_manager.connect():
                # If connected to OBS, assume recording is available
                self.show_info("Connected to OBS. Ready for recording.")
                
                # Enable recording button if class and chapter are selected
                self.record_btn.setEnabled(
                    self.class_dropdown.currentText() != "Select Class" and 
                    self.chapter_dropdown.currentText() != "Select Chapter"
                )
                self.record_btn.setToolTip("Start recording with OBS")
                self.reconnect_btn.setText("Reconnect to OBS")
                self.reconnect_btn.setEnabled(True)
            else:
                self._handle_obs_connection_failure()
        except Exception as e:
            logger.error(f"Error connecting to OBS: {e}", exc_info=True)
            self._handle_obs_connection_failure()
    
    def setup_icon(self) -> None:
        """Setup the application icon."""
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def setup_ui(self) -> None:
        """Setup the UI components."""
        self.setWindowTitle(f"{self.config.app_name} v{self.config.app_version}")
        self.setMinimumSize(800, 500)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align to top
        
        # Create a container widget for content with fixed width
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # Center only horizontally
        content_widget.setFixedWidth(800)
        
        # Add welcome label
        welcome_label = QLabel(f"Welcome to {self.config.app_name}")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; margin: 20px;")
        content_layout.addWidget(welcome_label)
        content_layout.addSpacing(20)  # Add spacing after welcome label
        
        # Add recording controls in a centered horizontal layout
        recording_layout = QHBoxLayout()
        recording_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center horizontally
        
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setStyleSheet(self._get_button_style("red"))
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self.toggle_recording)
        recording_layout.addWidget(self.record_btn)
        
        self.recording_time_label = QLabel("00:00:00")
        self.recording_time_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.recording_time_label.setVisible(False)
        recording_layout.addWidget(self.recording_time_label)
        
        self.reconnect_btn = QPushButton("Connect to OBS")
        self.reconnect_btn.setStyleSheet(self._get_button_style("blue"))
        self.reconnect_btn.clicked.connect(self.reconnect_obs)
        recording_layout.addWidget(self.reconnect_btn)
        
        content_layout.addLayout(recording_layout)
        content_layout.addSpacing(30)  # Add spacing after recording controls
        
        # Add class and chapter selection in a centered layout
        selection_layout = QHBoxLayout()
        selection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center horizontally
        
        # Define the button style with disabled state
        add_button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 4px;
                margin: 0;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """

        # Class dropdown and add button
        class_label = QLabel("Class:")
        class_label.setStyleSheet("font-size: 14px;")
        selection_layout.addWidget(class_label)
        
        self.class_dropdown = QComboBox()
        self.class_dropdown.addItem("Select Class")
        self.class_dropdown.addItems(self.config.get_classes())
        self.class_dropdown.setStyleSheet(UIConstants.STYLES["dropdown"])
        self.class_dropdown.currentTextChanged.connect(self._on_class_changed)
        selection_layout.addWidget(self.class_dropdown)
        
        add_class_btn = QPushButton("+")
        add_class_btn.setFixedSize(30, 30)
        add_class_btn.setStyleSheet(add_button_style)
        add_class_btn.clicked.connect(self._add_new_class)
        selection_layout.addWidget(add_class_btn)
        
        # Add some spacing between dropdowns
        selection_layout.addSpacing(20)
        
        # Chapter dropdown and add button
        chapter_label = QLabel("Chapter:")
        chapter_label.setStyleSheet("font-size: 14px;")
        selection_layout.addWidget(chapter_label)
        
        self.chapter_dropdown = QComboBox()
        self.chapter_dropdown.addItem("Select Chapter")
        self.chapter_dropdown.setStyleSheet(UIConstants.STYLES["dropdown"])
        self.chapter_dropdown.setEnabled(False)
        self.chapter_dropdown.currentTextChanged.connect(self._on_chapter_changed)
        selection_layout.addWidget(self.chapter_dropdown)
        
        # Make add_chapter_btn a class instance variable
        self.add_chapter_btn = QPushButton("+")
        self.add_chapter_btn.setFixedSize(30, 30)
        self.add_chapter_btn.setStyleSheet(add_button_style)
        self.add_chapter_btn.clicked.connect(self._add_new_chapter)
        self.add_chapter_btn.setEnabled(False)
        selection_layout.addWidget(self.add_chapter_btn)
        
        # Add some spacing between dropdowns
        selection_layout.addSpacing(20)
        
        # Subtopic dropdown and add button
        subtopic_label = QLabel("Subtopic:")
        subtopic_label.setStyleSheet("font-size: 14px;")
        selection_layout.addWidget(subtopic_label)
        
        self.subtopic_dropdown = QComboBox()
        self.subtopic_dropdown.addItem("Main")
        self.subtopic_dropdown.setStyleSheet(UIConstants.STYLES["dropdown"])
        self.subtopic_dropdown.setEnabled(False)
        self.subtopic_dropdown.currentTextChanged.connect(self._on_subtopic_changed)
        selection_layout.addWidget(self.subtopic_dropdown)
        
        # Make add_subtopic_btn a class instance variable
        self.add_subtopic_btn = QPushButton("+")
        self.add_subtopic_btn.setFixedSize(30, 30)
        self.add_subtopic_btn.setStyleSheet(add_button_style)
        self.add_subtopic_btn.clicked.connect(self._add_new_subtopic)
        self.add_subtopic_btn.setEnabled(False)
        selection_layout.addWidget(self.add_subtopic_btn)
        
        content_layout.addLayout(selection_layout)
        content_layout.addSpacing(30)  # Add spacing after class/chapter/subtopic selection
        
        # Add file label
        self.file_label = QLabel("No recording available")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.file_label)
        content_layout.addSpacing(20)  # Add spacing after file label
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(400)  # Set fixed width for progress bar
        content_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addSpacing(20)  # Add spacing after progress bar
        
        # Add upload button
        self.upload_btn = QPushButton("Upload Recording")
        self.upload_btn.setStyleSheet(self._get_button_style("blue"))
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self.upload_file)
        self.upload_btn.setFixedWidth(200)  # Set fixed width for upload button
        content_layout.addWidget(self.upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addSpacing(20)  # Add spacing after upload button
        
        # Add status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        # Add the content widget to the main layout
        layout.addWidget(content_widget, alignment=Qt.AlignmentFlag.AlignHCenter)  # Center horizontally only
    
    def _on_class_changed(self, class_name: str) -> None:
        """Handle class selection change."""
        if class_name == "Select Class":
            self.chapter_dropdown.clear()
            self.chapter_dropdown.addItem("Select Chapter")
            self.chapter_dropdown.setEnabled(False)
            self.add_chapter_btn.setEnabled(False)
            self.subtopic_dropdown.clear()
            self.subtopic_dropdown.addItem("Main")
            self.subtopic_dropdown.setEnabled(False)
            self.add_subtopic_btn.setEnabled(False)
            return
        
        # Update chapter dropdown
        self.chapter_dropdown.clear()
        self.chapter_dropdown.addItem("Select Chapter")
        self.chapter_dropdown.addItems(self.config.get_chapters(class_name))
        self.chapter_dropdown.setEnabled(True)
        self.add_chapter_btn.setEnabled(True)
        
        # Reset subtopic dropdown
        self.subtopic_dropdown.clear()
        self.subtopic_dropdown.addItem("Main")
        self.subtopic_dropdown.setEnabled(False)
        self.add_subtopic_btn.setEnabled(False)
        
        # Update recording button state
        self.record_btn.setEnabled(
            self.chapter_dropdown.currentText() != "Select Chapter"
        )
        
        # Reset file selection
        self.selected_file = None
        self.file_label.setText("No recording available")
        self.upload_btn.setEnabled(False)
        
        # Update recording button state only if OBS is connected
        if self.obs_manager.is_connected:
            self.record_btn.setEnabled(
                class_name != "Select Class" and 
                self.chapter_dropdown.currentText() != "Select Chapter"
            )
    
    def _on_chapter_changed(self, chapter_name: str) -> None:
        """Handle chapter selection change."""
        if chapter_name == "Select Chapter":
            self.subtopic_dropdown.clear()
            self.subtopic_dropdown.addItem("Main")
            self.subtopic_dropdown.setEnabled(False)
            self.add_subtopic_btn.setEnabled(False)
            return
        
        # Update subtopic dropdown
        class_name = self.class_dropdown.currentText()
        self.subtopic_dropdown.clear()
        self.subtopic_dropdown.addItems(self.config.get_subtopics(class_name, chapter_name))
        self.subtopic_dropdown.setEnabled(True)
        self.add_subtopic_btn.setEnabled(True)
        
        # Update recording button state
        self.record_btn.setEnabled(True)
    
    def _on_subtopic_changed(self, subtopic_name: str) -> None:
        """Handle subtopic selection change."""
        # Update recording button state
        self.record_btn.setEnabled(
            self.chapter_dropdown.currentText() != "Select Chapter"
        )
    
    def _get_button_style(self, color: str) -> str:
        """Get button style based on color."""
        colors = {
            "green": {
                "normal": "#4CAF50",
                "hover": "#45a049",
            },
            "blue": {
                "normal": "#2196F3",
                "hover": "#1976D2",
            },
            "red": {
                "normal": "#f44336",
                "hover": "#d32f2f",
            },
        }
        return f"""
            QPushButton {{
                background-color: {colors[color]['normal']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {colors[color]['hover']};
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """
    
    def select_file(self) -> None:
        """Handle file selection."""
        if self.class_dropdown.currentText() == "Select Class":
            self.show_error("Please select a class first")
            return
            
        if self.chapter_dropdown.currentText() == "Select Chapter":
            self.show_error("Please select a chapter first")
            return
            
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )
        if file_name:
            file_path = Path(file_name)
            is_valid, error_msg = self.config.validate_file(file_path)
            
            if is_valid:
                self.selected_file = file_path
                self.file_label.setText(f"Selected: {file_path.name}")
                self.upload_btn.setEnabled(True)
                self.status_label.setText("")
            else:
                self.show_error(error_msg)
    
    def upload_file(self) -> None:
        """Upload the selected file to Google Drive."""
        if not self.selected_file:
            self.show_error("No file selected")
            return
        
        # Validate file
        is_valid, error_msg = self.config.validate_file(self.selected_file)
        if not is_valid:
            self.show_error(error_msg)
            return
        
        # Get current year
        current_year = datetime.now().strftime("%Y")
        
        # Get selected class and chapter
        class_name = self.class_dropdown.currentText()
        chapter_name = self.chapter_dropdown.currentText()
        subtopic_name = self.subtopic_dropdown.currentText()
        
        if class_name == "Select Class" or chapter_name == "Select Chapter":
            self.show_error("Please select a class and chapter")
            return
        
        # Show progress bar and disable upload button during upload
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.upload_btn.setEnabled(False)
        
        # Create and start upload worker
        self.upload_worker = UploadWorker(
            self.selected_file,
            self.drive_manager,
            class_name,
            chapter_name,
            current_year,
            subtopic_name
        )
        self.upload_worker.progress.connect(self._update_progress)
        self.upload_worker.finished.connect(self._upload_finished)
        self.upload_worker.start()
    
    def _update_progress(self, value: int) -> None:
        """Update upload progress."""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Uploading... {value}%")
    
    def _upload_finished(self, success: bool, message: str) -> None:
        """Handle upload completion."""
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(False)  # Changed to False since we'll reset state
        
        if success:
            self.show_info("Upload completed successfully")
            self.status_label.setText("Upload completed successfully")
            
            # Reset the application state
            # Reset dropdowns
            self.class_dropdown.setCurrentText("Select Class")
            self.chapter_dropdown.clear()
            self.chapter_dropdown.addItem("Select Chapter")
            self.chapter_dropdown.setEnabled(False)
            self.subtopic_dropdown.clear()
            self.subtopic_dropdown.addItem("Main")
            self.subtopic_dropdown.setEnabled(False)
            
            # Reset buttons
            self.add_chapter_btn.setEnabled(False)
            self.add_subtopic_btn.setEnabled(False)
            
            # Reset file selection
            self.selected_file = None
            self.file_label.setText("No recording available")
            
            # Reset recording button if OBS is connected
            if self.obs_manager.is_connected:
                self.record_btn.setEnabled(False)
        else:
            self.show_error(f"Upload failed: {message}")
            self.status_label.setText("Upload failed")
            self.upload_btn.setEnabled(True)  # Re-enable upload button on failure
    
    def toggle_recording(self) -> None:
        """Toggle recording state."""
        if not self.obs_manager.is_connected:
            self.show_error("OBS is not connected. Please connect to OBS first.")
            return

        if not self.obs_manager.is_recording:
            # Check if class and chapter are selected
            class_name = self.class_dropdown.currentText()
            chapter_name = self.chapter_dropdown.currentText()
            subtopic_name = self.subtopic_dropdown.currentText()
            
            if class_name == "Select Class" or chapter_name == "Select Chapter":
                self.show_info("Please select class and chapter before starting a new recording.")
                return
            
            # Reset application state before starting new recording
            # Reset file selection
            self.selected_file = None
            self.file_label.setText("No recording available")
            self.upload_btn.setEnabled(False)
            
            # Clear any previous status
            self.status_label.setText("")
            
            # Hide progress bar if visible
            self.progress_bar.setVisible(False)
            
            # Create filename with date in DD-MM-YYYY format
            date_format = datetime.now().strftime("%d-%m-%Y")
            
            # Remove any special characters from chapter name that might cause issues in filenames
            safe_chapter_name = "".join(c for c in chapter_name if c.isalnum() or c in (' ', '-', '_'))
            safe_class_name = "".join(c for c in class_name if c.isalnum() or c in (' ', '-', '_'))
            safe_subtopic_name = "".join(c for c in subtopic_name if c.isalnum() or c in (' ', '-', '_'))
            
            # Create filename in the requested format: ${class}_${chapter}_${subtopic}_${DD-MM-YYYY}
            filename = f"{safe_class_name}_{safe_chapter_name}_{safe_subtopic_name}_{date_format}.mp4"
            self.current_recording_path = self.config.data_dir / filename
            
            # Store the desired filename for later use when renaming
            self.desired_filename = filename
            
            logger.info(f"Attempting to start recording. File will be saved to: {self.current_recording_path}")
            logger.info(f"Data directory: {self.config.data_dir}")
            logger.info(f"Base directory: {self.config.base_dir}")
            
            if self.obs_manager.start_recording(self.current_recording_path):
                self.record_btn.setText("Stop Recording")
                self.recording_time_label.setVisible(True)
                self.recording_timer.start(1000)  # Update every second
                self.recording_start_time = datetime.now()
                self.reconnect_btn.setEnabled(False)  # Disable reconnect during recording
                self.show_info(f"Recording started. Will be saved as: {filename}")
            else:
                self.show_error(
                    "Failed to start recording. Please check:\n\n"
                    "1. OBS is running with a scene that has sources\n"
                    "2. OBS recording settings are properly configured in OBS:\n"
                    "   - Go to Settings → Output → Recording tab\n" 
                    "   - Set 'Recording Path' to a folder you have write access to\n"
                    "   - Make sure the Recording Format is set to mp4\n"
                    "3. Try restarting OBS and try again"
                )
        else:
            # Stop recording logic remains the same
            logger.info("Attempting to stop recording...")
            if self.obs_manager.stop_recording():
                self.record_btn.setText("Start Recording")
                self.recording_time_label.setVisible(False)
                self.recording_timer.stop()
                self.reconnect_btn.setEnabled(True)
                
                # Wait a bit longer for the file to be saved
                time.sleep(2)
                
                # Get the actual file path from OBS
                actual_recording_path = self.obs_manager.last_recording_path
                
                # If we have both the actual path and the desired filename, rename the file
                if actual_recording_path and hasattr(self, 'desired_filename'):
                    self.rename_recording_file(actual_recording_path)
                    # Only enable upload if Google Drive is configured
                    if self.is_drive_configured:
                        self.upload_btn.setEnabled(True)
                    else:
                        self.show_warning(
                            "Recording saved successfully, but Google Drive is not configured.\n\n"
                            "To enable uploading:\n"
                            "1. Configure Google Drive credentials in the settings\n"
                            "2. Restart the application"
                        )
                else:
                    # Look for recently created video files
                    self.search_for_recordings()
            else:
                # Even if the stop command failed, try to look for recordings
                logger.warning("Failed to stop recording through API. Checking for recordings anyway.")
                self.record_btn.setText("Start Recording")
                self.recording_time_label.setVisible(False)
                self.recording_timer.stop()
                self.reconnect_btn.setEnabled(True)
                self.search_for_recordings()

    def rename_recording_file(self, actual_path: str) -> None:
        """Rename the recording file to use our desired format.
        
        Args:
            actual_path: The actual path where OBS saved the recording
        """
        try:
            logger.info(f"Renaming recording file from: {actual_path}")
            
            # Convert string path to Path object if it's not already
            if isinstance(actual_path, str):
                actual_path = Path(actual_path)
                
            # Ensure the file exists
            if not actual_path.exists():
                logger.warning(f"Cannot rename file - source does not exist: {actual_path}")
                self.search_for_recordings()
                return
                
            # Get the parent directory to save the renamed file in the same location
            target_dir = actual_path.parent
            
            # Create the target path with our desired filename
            target_path = target_dir / self.desired_filename
            
            logger.info(f"Renaming to: {target_path}")
            
            # If target file already exists, add a numeric suffix
            counter = 1
            while target_path.exists():
                name_parts = self.desired_filename.rsplit('.', 1)
                if len(name_parts) > 1:
                    target_path = target_dir / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    target_path = target_dir / f"{self.desired_filename}_{counter}"
                counter += 1
                
            # Rename the file
            actual_path.rename(target_path)
            
            # Update current_recording_path to the new path
            self.current_recording_path = target_path
            self.selected_file = target_path
            
            # Only enable upload if Google Drive is configured
            if self.is_drive_configured:
                self.upload_btn.setEnabled(True)
            
            logger.info(f"Successfully renamed recording to: {target_path}")
            self.show_info(f"Recording saved as: {target_path.name}")
            self.file_label.setText(f"Recording: {target_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to rename recording file: {e}", exc_info=True)
            # If rename fails, show the original path
            self.show_info(f"Recording saved to: {actual_path}")
            # Try searching for recordings as a fallback
            self.search_for_recordings()

    def search_for_recordings(self) -> None:
        """Search for recent recordings in various locations."""
        # Try to find recent mp4 files in several possible locations
        try:
            # First check the videos directory
            video_files = list(self.config.data_dir.glob("*.mp4"))
            
            # Also check OBS default directory which might be different
            default_obs_paths = [
                Path.home() / "Videos",
                Path("C:/Users") / Path.home().name / "Videos",
                Path.cwd() / "recordings",
                Path("C:/Program Files/obs-studio"),
                Path("C:/Program Files (x86)/obs-studio")
            ]
            
            for path in default_obs_paths:
                if path.exists():
                    video_files.extend(list(path.glob("*.mp4")))
            
            # Sort by modification time to get the most recent
            if video_files:
                video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Consider files modified in the last minute
                recent_files = [f for f in video_files if (datetime.now().timestamp() - f.stat().st_mtime) < 60]
                
                if recent_files:
                    self.show_info(f"Recording saved to: {recent_files[0]}")
                    self.selected_file = recent_files[0]
                    self.file_label.setText(f"Recording: {recent_files[0].name}")
                    self.upload_btn.setEnabled(True)
                    return
                
                # If we found video files but none are recent, mention the most recent one
                self.show_info(f"Recording may have been saved to: {video_files[0]}")
                return
            
            # If we get here, no video files were found
            self.show_warning(
                "Could not find the recording file.\n\n"
                "Please check:\n"
                "1. OBS recording settings in Settings → Output → Recording\n"
                "2. Look in your Videos folder for the recording\n"
                "3. Try recording again with different settings"
            )
        except Exception as e:
            logger.error(f"Error searching for recordings: {e}", exc_info=True)
            self.show_error("Could not locate recording file.")
    
    def _update_recording_status(self) -> None:
        """Update recording time display."""
        if self.obs_manager.is_recording:
            elapsed = datetime.now() - self.recording_start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.recording_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def closeEvent(self, event) -> None:
        """Handle application close event."""
        if self.obs_manager.is_recording:
            self.obs_manager.stop_recording()
        self.obs_manager.disconnect()
        super().closeEvent(event)

    def validate_config(self) -> bool:
        """Validate configuration values."""
        if not self.config.google_client_id or not self.config.google_client_secret:
            logger.warning("Google Drive credentials not configured")
            return False
        return True

    def ensure_directories(self) -> None:
        """Ensure required directories exist with retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.data_dir.mkdir(exist_ok=True)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Failed to create directory: {e}")

    def show_error(self, message: str) -> None:
        """Show error message to user."""
        QMessageBox.critical(self, "Error", message)
        logger.error(message)
    
    def show_info(self, message: str) -> None:
        """Show info message to user."""
        QMessageBox.information(self, "Info", message)
        logger.info(message)

    def _handle_obs_connection_failure(self) -> None:
        """Handle OBS connection failure."""
        self.record_btn.setEnabled(False)
        self.record_btn.setToolTip("OBS not connected. Click 'Connect to OBS' to try again")
        self.reconnect_btn.setText("Connect to OBS")
        self.reconnect_btn.setEnabled(True)
        self.show_error(
            "Failed to connect to OBS. Recording will be disabled.\n\n"
            "To enable recording:\n"
            "1. Start OBS\n"
            "2. Go to Tools -> WebSocket Server Settings\n"
            "3. Enable WebSocket server\n"
            "4. Click 'Connect to OBS' button"
        )

    def reconnect_obs(self) -> None:
        """Attempt to reconnect to OBS."""
        self.reconnect_btn.setEnabled(False)
        self.reconnect_btn.setText("Connecting...")
        # Use QTimer to prevent UI freeze during connection attempt
        QTimer.singleShot(0, self._attempt_reconnect)

    def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to OBS in a non-blocking way."""
        try:
            # Ensure clean disconnect first
            self.obs_manager.disconnect()
            # Try to connect
            self.connect_obs()
        except Exception as e:
            logger.error(f"Error during reconnection: {e}", exc_info=True)
            self._handle_obs_connection_failure()

    def show_warning(self, message: str) -> None:
        """Show warning message to user."""
        QMessageBox.warning(self, "Warning", message)
        logger.warning(message)

    def _add_new_class(self) -> None:
        """Add a new class."""
        class_name, ok = QInputDialog.getText(
            self,
            "Add New Class",
            "Enter class name (e.g., '11th'):",
            text=""
        )
        
        if ok and class_name:
            if self.config.add_class(class_name):
                # Update class dropdown
                current_text = self.class_dropdown.currentText()
                self.class_dropdown.clear()
                self.class_dropdown.addItem("Select Class")
                self.class_dropdown.addItems(self.config.get_classes())
                
                # Try to restore previous selection
                index = self.class_dropdown.findText(current_text)
                if index >= 0:
                    self.class_dropdown.setCurrentIndex(index)
                
                self.show_info(f"Added new class: {class_name}")
            else:
                self.show_error(f"Class '{class_name}' already exists")

    def _add_new_chapter(self) -> None:
        """Add a new chapter to the selected class."""
        class_name = self.class_dropdown.currentText()
        if class_name == "Select Class":
            self.show_error("Please select a class first")
            return
        
        chapter_name, ok = QInputDialog.getText(
            self,
            "Add New Chapter",
            f"Enter chapter name for {class_name}:",
            text=""
        )
        
        if ok and chapter_name:
            if self.config.add_chapter(class_name, chapter_name):
                # Update chapter dropdown
                current_text = self.chapter_dropdown.currentText()
                self.chapter_dropdown.clear()
                self.chapter_dropdown.addItem("Select Chapter")
                self.chapter_dropdown.addItems(self.config.get_chapters(class_name))
                
                # Try to restore previous selection
                index = self.chapter_dropdown.findText(current_text)
                if index >= 0:
                    self.chapter_dropdown.setCurrentIndex(index)
                
                self.show_info(f"Added new chapter: {chapter_name}")
            else:
                self.show_error(f"Chapter '{chapter_name}' already exists in {class_name}")

    def _add_new_subtopic(self) -> None:
        """Add a new subtopic to the current chapter."""
        class_name = self.class_dropdown.currentText()
        chapter_name = self.chapter_dropdown.currentText()
        
        if class_name == "Select Class" or chapter_name == "Select Chapter":
            return
        
        subtopic_name, ok = QInputDialog.getText(
            self,
            "Add New Subtopic",
            "Enter subtopic name:",
            text=""
        )
        
        if ok and subtopic_name:
            if self.config.add_subtopic(class_name, chapter_name, subtopic_name):
                # Update subtopic dropdown
                self.subtopic_dropdown.clear()
                self.subtopic_dropdown.addItems(self.config.get_subtopics(class_name, chapter_name))
                self.subtopic_dropdown.setCurrentText(subtopic_name)
            else:
                self.show_error("Failed to add subtopic. It may already exist.") 