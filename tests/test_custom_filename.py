"""
Test script for custom filename renaming functionality with OBS recordings.
"""

import sys
import time
import logging
from pathlib import Path
import obsws_python as obs
from datetime import datetime
import os
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rename_recording():
    """Test renaming of OBS recordings."""
    # Configuration
    host = "localhost"
    port = 4455  # Default port for OBS WebSocket v5
    password = ""  # Set your password if required
    
    # Define our desired filename format
    class_name = "Physics"
    chapter_name = "Thermodynamics"
    date_format = datetime.now().strftime("%d-%m-%Y")
    desired_filename = f"{class_name}_{chapter_name}_{date_format}.mp4"
    
    logger.info(f"Test will attempt to rename recording to: {desired_filename}")
    
    try:
        # Connect to OBS
        logger.info(f"Connecting to OBS WebSocket server at {host}:{port}")
        client = obs.ReqClient(host=host, port=port, password=password)
        logger.info("Connected to OBS successfully")
        
        # Get OBS version
        version = client.get_version()
        logger.info(f"OBS Version: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
        
        # Start recording
        logger.info("Starting recording...")
        client.start_record()
        logger.info("Recording started successfully")
        
        # Record for 5 seconds
        logger.info("Recording for 5 seconds...")
        time.sleep(5)
        
        # Stop recording
        logger.info("Stopping recording...")
        result = client.stop_record()
        
        # Get the actual file path
        if hasattr(result, 'output_path'):
            actual_path = result.output_path
            logger.info(f"Recording stopped. File saved to: {actual_path}")
            
            # Wait a bit for the file to be fully written
            time.sleep(2)
            
            # Now rename the file
            logger.info(f"Renaming file from: {actual_path}")
            
            # Convert to Path object
            actual_path = Path(actual_path)
            
            # Ensure the file exists
            if not actual_path.exists():
                logger.error(f"Source file does not exist: {actual_path}")
                return
                
            # Get the parent directory
            target_dir = actual_path.parent
            
            # Create the target path
            target_path = target_dir / desired_filename
            
            # If target already exists, create a copy instead
            if target_path.exists():
                logger.warning(f"Target file already exists: {target_path}")
                counter = 1
                while target_path.exists():
                    name_parts = desired_filename.rsplit('.', 1)
                    if len(name_parts) > 1:
                        target_path = target_dir / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        target_path = target_dir / f"{desired_filename}_{counter}"
                    counter += 1
            
            # Rename (or copy if rename fails)
            try:
                logger.info(f"Renaming to: {target_path}")
                actual_path.rename(target_path)
                logger.info(f"Successfully renamed file to: {target_path}")
                
                # Check if the new file exists and report its size
                if target_path.exists():
                    file_size = target_path.stat().st_size
                    logger.info(f"New file size: {file_size} bytes")
                else:
                    logger.error("Rename seemed to succeed, but target file doesn't exist")
            except Exception as rename_error:
                logger.error(f"Failed to rename file: {rename_error}")
                logger.info("Trying to copy instead...")
                try:
                    shutil.copy2(actual_path, target_path)
                    logger.info(f"Successfully copied file to: {target_path}")
                except Exception as copy_error:
                    logger.error(f"Failed to copy file: {copy_error}")
        else:
            logger.warning("No output_path in result. Cannot rename file.")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    finally:
        logger.info("Test completed")

if __name__ == "__main__":
    test_rename_recording() 