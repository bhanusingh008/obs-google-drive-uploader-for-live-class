import sys
import logging
import os
from pathlib import Path
from datetime import datetime
from src.core.google_drive_manager import GoogleDriveManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_google_drive_upload():
    try:
        # Initialize Google Drive Manager
        drive_manager = GoogleDriveManager()
        
        # Create a test file with current date
        current_date = datetime.now().strftime('%d-%m-%Y')
        test_filename = f"Physics_Thermodynamics_{current_date}.txt"
        test_filepath = Path("test_files") / test_filename
        
        # Create test_files directory if it doesn't exist
        os.makedirs("test_files", exist_ok=True)
        
        # Create a sample file with some content
        with open(test_filepath, "w") as f:
            f.write(f"This is a test file for Google Drive upload. Created at: {datetime.now()}")
        
        logger.info(f"Created local test file: {test_filepath}")
        
        # Upload the file
        logger.info("Attempting to upload file to Google Drive...")
        folder_id = drive_manager.get_or_create_folder("Test Recordings")
        file_id = drive_manager.upload_file(str(test_filepath), folder_id)
        
        if file_id:
            # Get and log the full path
            full_path = drive_manager.get_file_path(file_id)
            logger.info(f"Full Drive path: {full_path}")
            
            # Clean up - delete the local test file
            os.remove(test_filepath)
            logger.info("Cleaned up local test file")
            
        else:
            logger.error("Failed to upload file")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_google_drive_upload() 