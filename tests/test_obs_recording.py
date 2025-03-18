"""
Test script for OBS recording functionality.
This script connects to OBS, starts a recording for 10 seconds, and saves it in the default directory.
"""

import sys
import time
import logging
from pathlib import Path
import obsws_python as obs

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_obs_recording():
    """Test OBS recording functionality - Direct implementation using obsws_python."""
    # Configuration
    host = "localhost"
    port = 4455  # Default port for OBS WebSocket v5
    password = ""  # Set your password if required
    
    try:
        # Connect to OBS
        logger.info(f"Connecting to OBS WebSocket server at {host}:{port}")
        client = obs.ReqClient(host=host, port=port, password=password)
        logger.info("Connected to OBS successfully")
        
        # Get OBS version
        version = client.get_version()
        logger.info(f"OBS Version: {version.obs_version}, WebSocket: {version.obs_web_socket_version}")
        
        # Get current scene information
        scenes_info = client.get_scene_list()
        logger.info(f"Current scene: {scenes_info.current_program_scene_name}")
        
        # Print available scenes - properly accessing the dictionary structure
        scene_list = scenes_info.scenes
        scene_names = []
        for scene in scene_list:
            # Use dictionary access since these are dictionaries, not objects
            if isinstance(scene, dict) and 'sceneName' in scene:
                scene_names.append(scene['sceneName'])
        
        logger.info(f"Available scenes: {scene_names}")
        
        # Start recording
        logger.info("Starting recording...")
        try:
            client.start_record()
            logger.info("Recording started successfully")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return
        
        # Wait for 10 seconds
        logger.info("Recording for 10 seconds...")
        time.sleep(10)
        
        # Stop recording
        logger.info("Stopping recording...")
        try:
            recording_output = client.stop_record()
            # Check if recording_output has output_path attribute or is a dict
            if hasattr(recording_output, 'output_path'):
                output_path = recording_output.output_path
            elif isinstance(recording_output, dict) and 'outputPath' in recording_output:
                output_path = recording_output['outputPath']
            else:
                logger.warning(f"Unexpected recording output format: {recording_output}")
                output_path = None
            
            if output_path:
                logger.info(f"Recording stopped. File saved to: {output_path}")
            else:
                logger.warning("Recording stopped but output path unknown")
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            output_path = None
        
        # Check if recording was actually saved
        if output_path:
            path_obj = Path(output_path)
            if path_obj.exists():
                logger.info(f"Recording file exists: {output_path}")
                logger.info(f"File size: {path_obj.stat().st_size} bytes")
            else:
                logger.warning(f"Recording file not found at: {output_path}")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    finally:
        logger.info("Test completed")

if __name__ == "__main__":
    test_obs_recording() 