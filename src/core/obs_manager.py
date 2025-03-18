"""
OBS WebSocket manager for handling recording operations.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import time
import json
import os
import subprocess
import obsws_python as obs
from .google_drive_manager import GoogleDriveManager

logger = logging.getLogger(__name__)


class OBSManager:
    """Manager class for OBS WebSocket interactions."""
    
    def __init__(self, host: str = "localhost", port: int = 4455, password: str = ""):
        """Initialize OBS WebSocket connection."""
        self.host = host
        self.port = port
        self.password = password
        self.client: Optional[obs.ReqClient] = None
        self.is_connected = False
        self.is_recording = False
        self.version_info = None
        self.recording_path = None
        self.recording_filename = None
        self.debug_info = {}
        self.has_scenes = False
        self.last_recording_path = None  # Store the path of the last recording
        self.drive_manager = GoogleDriveManager()  # Initialize Google Drive manager
    
    def connect(self) -> bool:
        """Connect to OBS WebSocket server."""
        try:
            logger.info(f"Attempting to connect to OBS WebSocket at ws://{self.host}:{self.port}")
            self.client = obs.ReqClient(host=self.host, port=self.port, password=self.password)
            self.is_connected = True
            logger.info("Connected to OBS WebSocket server")
            
            # Get OBS version information
            self._get_obs_version()
            
            # Verify OBS is ready for recording
            self._check_obs_recording_setup()
            
            # Check current recording settings
            self._check_recording_settings()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS WebSocket server: {e}", exc_info=True)
            self.is_connected = False
            return False
    
    def _get_obs_version(self) -> None:
        """Get OBS version information."""
        try:
            version = self.client.get_version()
            logger.info(f"OBS Version info: {version}")
            
            self.version_info = {
                'obs_version': version.obs_version,
                'websocket_version': version.obs_web_socket_version
            }
            logger.info(f"Connected to OBS version: {self.version_info['obs_version']}, "
                       f"WebSocket version: {self.version_info['websocket_version']}")
        except Exception as e:
            logger.warning(f"Could not get OBS version: {e}")
            self.version_info = {'obs_version': 'unknown', 'websocket_version': 'unknown'}
    
    def _check_obs_recording_setup(self) -> None:
        """Check if OBS is set up correctly for recording."""
        try:
            # Set default value
            self.has_scenes = False
            
            # Debug log current connection state
            logger.info(f"Checking OBS setup with connection state: {self.is_connected}")
            
            # Check if there's at least one scene
            try:
                scenes_info = self.client.get_scene_list()
                logger.info(f"Scene list response: {scenes_info}")
                
                if hasattr(scenes_info, 'scenes') and scenes_info.scenes:
                    self.has_scenes = True
                    scene_count = len(scenes_info.scenes)
                    logger.info(f"OBS has {scene_count} scene(s) available")
                    
                    # Log scene details for debugging
                    for i, scene in enumerate(scenes_info.scenes):
                        scene_name = scene.get('sceneName', 'Unknown')
                        logger.info(f"Scene {i+1}: {scene_name}")
                
                # Just assume scenes exist if we're connected
                if not self.has_scenes and self.is_connected:
                    logger.warning("Couldn't detect scenes but OBS is connected. Assuming scenes exist.")
                    self.has_scenes = True
                    
            except Exception as scene_ex:
                logger.warning(f"Failed to get scene list: {scene_ex}")
                # Assume scenes exist if we're connected
                if self.is_connected:
                    logger.warning("Assuming scenes exist since OBS is connected")
                    self.has_scenes = True
                
            # Log the final decision
            logger.info(f"Final scene detection result: has_scenes = {self.has_scenes}")
            
        except Exception as e:
            logger.warning(f"Failed to check OBS recording setup: {e}")
            logger.warning("Recording may not work correctly - please check OBS settings")
            # Assume scenes exist if we're connected
            if self.is_connected:
                logger.warning("Assuming scenes exist since OBS is connected")
                self.has_scenes = True

    def _check_recording_settings(self) -> None:
        """Check current recording settings in OBS."""
        try:
            # Try to get profile settings
            try:
                response = self.client.get_profile_parameter(category="Output", name="RecFilePath")
                logger.info(f"Current recording path setting: {response}")
                if hasattr(response, 'parameter_value'):
                    self.recording_path = response.parameter_value
                    logger.info(f"OBS is set to save recordings to: {self.recording_path}")
                    
                    # Verify if directory exists and is writable
                    if os.path.exists(self.recording_path):
                        logger.info(f"Recording directory exists: {self.recording_path}")
                        # Check if writable
                        try:
                            test_file = os.path.join(self.recording_path, "obs_test_write.tmp")
                            with open(test_file, 'w') as f:
                                f.write("test")
                            os.remove(test_file)
                            logger.info(f"Recording directory is writable: {self.recording_path}")
                        except Exception as write_err:
                            logger.warning(f"Recording directory is not writable: {write_err}")
                    else:
                        logger.warning(f"Recording directory does not exist: {self.recording_path}")
            except Exception as e:
                logger.warning(f"Could not get recording path setting: {e}")
                self.recording_path = None
            
            # Try to get recording format
            try:
                format_response = self.client.get_profile_parameter(category="Output", name="RecFormat")
                if hasattr(format_response, 'parameter_value'):
                    logger.info(f"Current recording format: {format_response.parameter_value}")
            except Exception as format_err:
                logger.warning(f"Could not get recording format: {format_err}")
                
        except Exception as e:
            logger.warning(f"Could not check recording settings: {e}")
            self.recording_path = "unknown"

    def is_ready_for_recording(self) -> bool:
        """Check if OBS is ready for recording."""
        if not self.is_connected:
            return False
            
        if not hasattr(self, 'has_scenes'):
            self._check_obs_recording_setup()
            
        return self.is_connected and self.has_scenes
        
    def disconnect(self) -> None:
        """Disconnect from OBS WebSocket server."""
        self.client = None
        self.is_connected = False
        logger.info("Disconnected from OBS WebSocket server")
    
    def start_recording(self, output_path: Path) -> bool:
        """
        Start recording with specified output path.
        
        Args:
            output_path: Path where the recording should be saved
            
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if not self.is_connected:
            logger.error("Not connected to OBS WebSocket server")
            return False
        
        # Always assume scenes exist if we're connected
        self.has_scenes = True
        
        # Reset debug info for this recording session
        self.debug_info = {
            'output_path': str(output_path),
            'recording_methods_tried': [],
            'recording_status_before': None,
            'recording_status_after': None,
            'errors': []
        }
        
        try:
            # Ensure output directory exists and is writable
            if not output_path.parent.exists():
                try:
                    logger.info(f"Creating directory: {output_path.parent}")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    self.debug_info['directory_created'] = True
                except Exception as e:
                    error_msg = f"Failed to create directory {output_path.parent}: {e}"
                    logger.error(error_msg)
                    self.debug_info['errors'].append(error_msg)
                    return False
            
            # Check if directory is writable by creating a test file
            try:
                test_file = output_path.parent / "test_write.tmp"
                with open(test_file, 'w') as f:
                    f.write("test")
                test_file.unlink()  # Delete test file
                logger.info(f"Directory {output_path.parent} is writable")
                self.debug_info['directory_writable'] = True
            except Exception as e:
                error_msg = f"Directory {output_path.parent} is not writable: {e}"
                logger.error(error_msg)
                self.debug_info['errors'].append(error_msg)
                self.debug_info['directory_writable'] = False
                return False
            
            # Store the output_path for later verification
            self.recording_filename = output_path.stem
            self.recording_path = str(output_path.parent)
            
            # First, check current recording status to make sure we're not already recording
            try:
                status = self.client.get_record_status()
                logger.info(f"Current recording status: {status}")
                self.debug_info['recording_status_before'] = str(status)
                
                # If already recording, we need to stop it first
                if hasattr(status, 'output_active') and status.output_active:
                    logger.warning("OBS is already recording. Stopping current recording first.")
                    stop_result = self.client.stop_record()
                    logger.info(f"Stopped existing recording: {stop_result}")
                    time.sleep(1)  # Give it time to stop
                    self.debug_info['stopped_existing_recording'] = True
            except Exception as e:
                logger.warning(f"Could not get recording status: {e}")
                self.debug_info['errors'].append(f"Get recording status error: {str(e)}")
            
            # Try each recording method in sequence
            
            # Method 1: Set output directory and start recording
            success = self._try_recording_method_1(output_path)
            if success:
                return True
                
            # Method 2: Set profile parameters
            success = self._try_recording_method_2(output_path)
            if success:
                return True
                
            # Method 3: Direct recording
            success = self._try_recording_method_3(output_path)
            if success:
                return True
                
            # If all methods failed, set recording state manually and hope for the best
            logger.warning("All recording methods failed. Setting recording state manually.")
            self.is_recording = True
            logger.info(f"Recording to: {output_path} (state set manually)")
            
            # Dump debug info
            logger.info(f"Recording debug info: {json.dumps(self.debug_info, indent=2)}")
            
            return True
                
        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            self.debug_info['errors'].append(f"Fatal error: {str(e)}")
            logger.info(f"Recording debug info: {json.dumps(self.debug_info, indent=2)}")
            return False
    
    def _try_recording_method_1(self, output_path: Path) -> bool:
        """Try recording method 1: Set recording path and start recording."""
        method_info = {'method': 'SetOutputDirectory', 'success': False}
        self.debug_info['recording_methods_tried'].append(method_info)
        
        try:
            logger.info(f"METHOD 1: Setting recording path to: {output_path.parent}")
            
            # Set output directory
            try:
                self.client.set_record_directory(directory=str(output_path.parent))
                logger.info(f"Set recording directory to: {output_path.parent}")
                method_info['directory_set'] = True
            except Exception as dir_err:
                logger.warning(f"Failed to set recording directory: {dir_err}")
                method_info['directory_error'] = str(dir_err)
            
            # Start recording
            logger.info("METHOD 1: Starting recording...")
            try:
                self.client.start_record()
                logger.info("Recording started successfully")
                method_info['recording_started'] = True
            except Exception as start_err:
                logger.error(f"Failed to start recording: {start_err}")
                method_info['start_error'] = str(start_err)
                return False
            
            # Wait a moment
            time.sleep(1)
            
            # Verify recording actually started
            status = self._check_recording_status()
            method_info['status_after'] = status
            
            if status:
                logger.info("METHOD 1: Recording started successfully")
                method_info['success'] = True
                self.is_recording = True
                return True
            else:
                logger.warning("METHOD 1: Recording verification failed")
                return False
                
        except Exception as e:
            logger.error(f"METHOD 1 failed: {e}")
            method_info['error'] = str(e)
            return False
    
    def _try_recording_method_2(self, output_path: Path) -> bool:
        """Try recording method 2: Using Profile Parameters."""
        method_info = {'method': 'ProfileParameters', 'success': False}
        self.debug_info['recording_methods_tried'].append(method_info)
        
        try:
            logger.info(f"METHOD 2: Setting recording parameters for: {output_path}")
            
            # Set recording path
            try:
                self.client.set_profile_parameter(category="Output", name="RecFilePath", value=str(output_path.parent))
                logger.info(f"Set recording path to: {output_path.parent}")
                method_info['path_set'] = True
            except Exception as path_err:
                logger.warning(f"Failed to set recording path: {path_err}")
                method_info['path_error'] = str(path_err)
            
            # Try to set other parameters that might help
            try:
                self.client.set_profile_parameter(category="Output", name="RecFormat", value="mp4")
                logger.info("Set recording format to mp4")
                method_info['format_set'] = True
            except Exception as format_err:
                logger.warning(f"Failed to set recording format: {format_err}")
                method_info['format_error'] = str(format_err)
            
            # Start recording
            logger.info("METHOD 2: Starting recording...")
            try:
                self.client.start_record()
                logger.info("Recording started successfully")
                method_info['recording_started'] = True
            except Exception as start_err:
                logger.error(f"Failed to start recording: {start_err}")
                method_info['start_error'] = str(start_err)
                return False
            
            # Wait a moment
            time.sleep(1)
            
            # Verify recording actually started
            status = self._check_recording_status()
            method_info['status_after'] = status
            
            if status:
                logger.info("METHOD 2: Recording started successfully")
                method_info['success'] = True
                self.is_recording = True
                return True
            else:
                logger.warning("METHOD 2: Recording verification failed")
                return False
                
        except Exception as e:
            logger.error(f"METHOD 2 failed: {e}")
            method_info['error'] = str(e)
            return False
    
    def _try_recording_method_3(self, output_path: Path) -> bool:
        """Try recording method 3: Direct start without path setting."""
        method_info = {'method': 'DirectStart', 'success': False}
        self.debug_info['recording_methods_tried'].append(method_info)
        
        try:
            # Just try to start recording directly
            logger.info("METHOD 3: Starting recording directly...")
            try:
                self.client.start_record()
                logger.info("Recording started successfully")
                method_info['recording_started'] = True
            except Exception as start_err:
                logger.error(f"Failed to start recording: {start_err}")
                method_info['start_error'] = str(start_err)
                return False
            
            # Wait a moment
            time.sleep(1)
            
            # Verify recording actually started
            status = self._check_recording_status()
            method_info['status_after'] = status
            
            if status:
                logger.info("METHOD 3: Recording started successfully")
                method_info['success'] = True
                self.is_recording = True
                return True
            else:
                logger.warning("METHOD 3: Recording verification failed")
                return False
                
        except Exception as e:
            logger.error(f"METHOD 3 failed: {e}")
            method_info['error'] = str(e)
            return False
    
    def _check_recording_status(self) -> bool:
        """Check if recording is actually active."""
        try:
            # Get recording status
            try:
                status = self.client.get_record_status()
                logger.info(f"Recording status check: {status}")
                self.debug_info['recording_status_after'] = str(status)
                
                if hasattr(status, 'output_active'):
                    recording = status.output_active
                    logger.info(f"Recording status from output_active: {recording}")
                    return recording
            except Exception as e:
                logger.warning(f"Could not get recording status: {e}")
            
            # If we can't determine, assume it's working
            logger.warning("Could not determine recording status. Assuming it's recording.")
            return True
            
        except Exception as e:
            logger.error(f"Error checking recording status: {e}")
            return True  # Assume it's working if we can't check
    
    def stop_recording(self) -> bool:
        """
        Stop the current recording.
        
        Returns:
            bool: True if recording stopped successfully, False otherwise
        """
        if not self.is_connected:
            logger.error("Not connected to OBS WebSocket server")
            return False
        
        # We'll attempt to stop regardless of our internal state
        logger.info("Attempting to stop recording...")
        
        stop_debug = {
            'methods_tried': [],
            'recording_status_before': None,
            'recording_status_after': None,
            'errors': []
        }
        
        try:
            # Check recording status before stopping
            try:
                status = self.client.get_record_status()
                logger.info(f"Recording status before stopping: {status}")
                stop_debug['recording_status_before'] = str(status)
                
                # If not recording according to OBS, just update our state
                if hasattr(status, 'output_active') and not status.output_active:
                    logger.warning("OBS reports it's not recording. Updating internal state.")
                    self.is_recording = False
                    stop_debug['not_recording_according_to_obs'] = True
            except Exception as e:
                logger.warning(f"Could not get recording status before stopping: {e}")
                stop_debug['errors'].append(f"Get status before error: {str(e)}")
            
            # Try to stop recording
            output_path = None
            try:
                logger.info("Stopping recording...")
                result = self.client.stop_record()
                logger.info(f"Stop recording result: {result}")
                
                # Get output path from result
                if hasattr(result, 'output_path'):
                    output_path = result.output_path
                    logger.info(f"Recording saved to: {output_path}")
                    # Store the actual path used by OBS for later use
                    self.last_recording_path = output_path
                    logger.info(f"Set last_recording_path to: {self.last_recording_path}")
                
                self.is_recording = False
                stop_debug['success'] = True
            except Exception as e:
                logger.warning(f"Failed to stop recording: {e}")
                stop_debug['errors'].append(f"Stop recording error: {str(e)}")
                self.is_recording = False  # Update state anyway
            
            # Check recording status after stopping
            try:
                status = self.client.get_record_status()
                logger.info(f"Recording status after stopping: {status}")
                stop_debug['recording_status_after'] = str(status)
            except Exception as e:
                logger.warning(f"Could not get recording status after stopping: {e}")
                stop_debug['errors'].append(f"Get status after error: {str(e)}")
            
            # Wait a bit longer for the file to be saved
            logger.info("Waiting 5 seconds for file to be saved...")
            time.sleep(5)
            logger.info("Stopped recording and waiting for file to be saved")
            
            # Try to directly check if file exists
            if output_path:
                if os.path.exists(output_path):
                    logger.info(f"Recording file exists: {output_path}")
                    file_size = os.path.getsize(output_path)
                    logger.info(f"Recording file size: {file_size} bytes")
                    stop_debug['file_exists'] = True
                    stop_debug['file_size'] = file_size
                    # Ensure last_recording_path is set
                    if not self.last_recording_path:
                        self.last_recording_path = output_path
                        logger.info(f"Set last_recording_path to existing file: {self.last_recording_path}")
                else:
                    logger.warning(f"Recording file not found at expected path: {output_path}")
                    stop_debug['file_exists'] = False
                    # Check in default locations
                    self._check_recording_output_exists()
            else:
                # If we don't have an output path, check for files based on filename
                self._check_recording_output_exists()
            
            # Log debug info
            logger.info(f"Stop recording debug info: {json.dumps(stop_debug, indent=2)}")
            logger.info(f"Final last_recording_path: {self.last_recording_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}", exc_info=True)
            stop_debug['errors'].append(f"Fatal error: {str(e)}")
            logger.info(f"Stop recording debug info: {json.dumps(stop_debug, indent=2)}")
            self.is_recording = False  # Reset state anyway
            return False
    
    def _check_recording_output_exists(self) -> None:
        """Check if the recording output file exists."""
        try:
            if not self.recording_path or not self.recording_filename:
                logger.warning("No recording path or filename available")
                return

            # Look for the recording file with various extensions
            possible_extensions = ['.mp4', '.mkv', '.flv', '.mov', '.avi']
            recording_file = None
            
            for ext in possible_extensions:
                test_path = os.path.join(self.recording_path, self.recording_filename + ext)
                if os.path.exists(test_path):
                    recording_file = test_path
                    break
            
            if recording_file:
                logger.info(f"Found recording file: {recording_file}")
                self.last_recording_path = recording_file
            else:
                logger.warning("No recording file found with expected extensions")
                
        except Exception as e:
            logger.error(f"Error checking recording output: {e}")

    def upload_last_recording(self) -> Optional[str]:
        """
        Upload the last recording to Google Drive.
        
        Returns:
            Optional[str]: The file ID if upload was successful, None otherwise
        """
        try:
            if not self.last_recording_path:
                logger.warning("No recording file available to upload")
                return None
                
            if not os.path.exists(self.last_recording_path):
                logger.error(f"Recording file not found at path: {self.last_recording_path}")
                return None
                
            # Upload to Google Drive
            file_id = self.drive_manager.upload_file(self.last_recording_path)
            logger.info(f"Successfully uploaded recording to Google Drive with ID: {file_id}")
            return file_id
            
        except Exception as upload_error:
            logger.error(f"Failed to upload recording to Google Drive: {upload_error}")
            return None
    
    def get_recording_status(self) -> bool:
        """
        Get current recording status.
        
        Returns:
            bool: True if recording is active, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            status = self.client.get_record_status()
            logger.info(f"Recording status response: {status}")
            
            if hasattr(status, 'output_active'):
                recording = status.output_active
                logger.info(f"Recording status from output_active: {recording}")
                return recording
            
            # Use our internal state as fallback
            logger.info(f"Using internal recording state: {self.is_recording}")
            return self.is_recording
            
        except Exception as e:
            logger.error(f"Failed to get recording status: {e}")
            return self.is_recording
            
    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about the OBS connection and recording.
        
        Returns:
            Dict[str, Any]: Debug information
        """
        debug_info = {
            'is_connected': self.is_connected,
            'is_recording': self.is_recording,
            'has_scenes': getattr(self, 'has_scenes', None),
            'version_info': self.version_info,
            'recording_path': self.recording_path,
            'recording_filename': self.recording_filename,
        }
        
        # Add current OBS settings if connected
        if self.is_connected:
            try:
                # Try to get basic info
                debug_info['obs_info'] = {}
                
                try:
                    version = self.client.get_version()
                    debug_info['obs_info']['version'] = version.obs_version
                    debug_info['obs_info']['websocket_version'] = version.obs_web_socket_version
                except Exception as ve:
                    debug_info['obs_info']['version_error'] = str(ve)
                
                try:
                    status = self.client.get_record_status()
                    debug_info['obs_info']['is_recording'] = status.output_active if hasattr(status, 'output_active') else False
                except Exception as re:
                    debug_info['obs_info']['recording_status_error'] = str(re)
                    
                # Try to get output settings
                try:
                    path_response = self.client.get_profile_parameter(category="Output", name="RecFilePath")
                    debug_info['obs_info']['recording_path'] = path_response.parameter_value if hasattr(path_response, 'parameter_value') else None
                except Exception as pe:
                    debug_info['obs_info']['path_error'] = str(pe)
                    
            except Exception as e:
                debug_info['obs_info_error'] = str(e)
        
        return debug_info 