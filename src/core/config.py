"""
Configuration management for the application.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Config:
    """Application configuration manager."""
    
    # Default class and chapter configuration
    DEFAULT_CHAPTERS = {}
    
    def __init__(self):
        """Initialize configuration."""
        # Load environment variables
        load_dotenv()
        
        # Application settings
        self.app_name = "MathsByPawanSir"
        self.app_version = "1.0.0"
        
        # Paths
        self.base_dir = Path(__file__).parent.parent.parent
        
        # Use AppData directory for Windows
        if os.name == 'nt':  # Windows
            self.app_data_dir = Path(os.getenv('APPDATA')) / self.app_name
        else:  # Linux/Mac
            self.app_data_dir = Path.home() / f'.{self.app_name.lower()}'
            
        self.data_dir = Path(os.getenv("RECORDING_PATH", str(self.app_data_dir / "data")))
        self.config_file = self.app_data_dir / "chapters.json"
        self.ensure_directories()
        
        # Google Drive settings
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        # Upload settings
        self.max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE", "100")) * 1024 * 1024  # Convert MB to bytes
        self.allowed_file_types = os.getenv("ALLOWED_FILE_TYPES", "*").split(",")
        
        # Load or create chapters configuration
        self.chapters = self._load_chapters()
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.data_dir.mkdir(exist_ok=True)
        self.config_file.parent.mkdir(exist_ok=True)
    
    def _load_chapters(self) -> dict:
        """Load chapters from JSON file or create new if not exists."""
        if self.config_file.exists():
            try:
                with self.config_file.open("r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading chapters: {e}")
        
        # Return empty dict if file doesn't exist or there's an error
        return {}
    
    def _save_chapters(self, chapters: Dict[str, Dict[str, List[str]]]) -> None:
        """Save chapters to config file."""
        try:
            logger.info(f"Saving chapters configuration to: {self.config_file}")
            with self.config_file.open('w', encoding='utf-8') as f:
                json.dump(chapters, f, indent=4, ensure_ascii=False)
            logger.info("Successfully saved chapters configuration")
        except Exception as e:
            logger.error(f"Error saving chapters: {e}")
    
    def add_class(self, class_name: str) -> bool:
        """Add a new class."""
        if class_name in self.chapters:
            return False
        self.chapters[class_name] = {}  # Initialize with empty dict for chapters
        self._save_chapters(self.chapters)
        return True
    
    def add_chapter(self, class_name: str, chapter_name: str) -> bool:
        """Add a new chapter to a class."""
        if class_name not in self.chapters:
            return False
        if chapter_name in self.chapters[class_name]:
            return False
        self.chapters[class_name][chapter_name] = ["Main"]  # Initialize with "Main" subtopic
        self._save_chapters(self.chapters)
        return True
    
    def add_subtopic(self, class_name: str, chapter_name: str, subtopic_name: str) -> bool:
        """Add a new subtopic to a chapter."""
        if class_name not in self.chapters or chapter_name not in self.chapters[class_name]:
            return False
        if subtopic_name in self.chapters[class_name][chapter_name]:
            return False
        self.chapters[class_name][chapter_name].append(subtopic_name)
        self._save_chapters(self.chapters)
        return True
    
    @property
    def is_google_configured(self) -> bool:
        """Check if Google Drive credentials are configured."""
        return bool(self.google_client_id and self.google_client_secret)
    
    def get_upload_path(self, filename: str) -> Path:
        """Get the path for temporary file storage."""
        return self.data_dir / filename
    
    def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate a file for upload.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, "File does not exist"
        
        if file_path.stat().st_size > self.max_upload_size:
            return False, f"File size exceeds maximum allowed size of {self.max_upload_size // (1024 * 1024)}MB"
        
        if self.allowed_file_types != ["*"]:
            file_ext = file_path.suffix.lower()
            if not any(file_ext.endswith(ext.strip()) for ext in self.allowed_file_types):
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_file_types)}"
        
        return True, None
    
    def get_classes(self) -> List[str]:
        """
        Get list of available classes.
        
        Returns:
            List of class names
        """
        return list(self.chapters.keys())
    
    def get_chapters(self, class_name: str) -> List[str]:
        """
        Get list of chapters for a given class.
        
        Args:
            class_name: Name of the class
            
        Returns:
            List of chapter names
        """
        return list(self.chapters.get(class_name, {}).keys())
    
    def get_subtopics(self, class_name: str, chapter_name: str) -> List[str]:
        """
        Get list of subtopics for a given chapter.
        
        Args:
            class_name: Name of the class
            chapter_name: Name of the chapter
            
        Returns:
            List of subtopic names
        """
        return self.chapters.get(class_name, {}).get(chapter_name, ["Main"]) 