from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import logging
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleDriveManager:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    SERVICE_ACCOUNT_FILE = 'service-account.json'
    DRIVE_VIEW_URL = "https://drive.google.com/file/d/{}/view"
    SHARED_FOLDER_ID = "1etyTblY2gBnmK5gVG4I-sIqQGwrsyw99"

    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds, cache_discovery=False)

    def _get_service_account_path(self):
        """Get the correct path for the service account file."""
        if getattr(sys, 'frozen', False):
            # If we're running in a PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # If we're running in development
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        return os.path.join(base_path, self.SERVICE_ACCOUNT_FILE)

    def _get_credentials(self):
        try:
            service_account_path = self._get_service_account_path()
            logger.info(f"Loading service account from: {service_account_path}")
            return service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=self.SCOPES
            )
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            raise

    def get_or_create_folder(self, folder_name, parent_id=None):
        """Create a subfolder in the specified parent folder."""
        try:
            # If no parent_id is provided, use the shared folder
            parent_id = parent_id or self.SHARED_FOLDER_ID
            
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                supportsAllDrives=True
            ).execute()
            items = results.get('files', [])

            if items:
                return items[0]['id']
            else:
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                file = self.service.files().create(
                    body=file_metadata,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                return file.get('id')
        except Exception as e:
            logger.error(f"Error with folder operation: {str(e)}")
            raise

    def get_or_create_class_year_folder(self, class_name: str, year: str) -> str:
        """Get or create the class-year folder."""
        folder_name = f"{class_name}_{year}"
        return self.get_or_create_folder(folder_name)

    def get_or_create_chapter_folder(self, chapter_name: str, class_year_folder_id: str) -> str:
        """Get or create the chapter folder inside the class-year folder."""
        return self.get_or_create_folder(chapter_name, class_year_folder_id)

    def count_files_in_folder(self, folder_id: str, file_extension: str = None) -> int:
        """Count the number of files in a folder and all its subfolders, optionally filtered by extension."""
        try:
            total_count = 0
            
            # First count files in the current folder
            query = f"'{folder_id}' in parents and trashed=false"
            if file_extension:
                query += f" and name contains '.{file_extension}'"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                supportsAllDrives=True
            ).execute()
            total_count += len(results.get('files', []))

            # Then get all subfolders and count files in them recursively
            folder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_results = self.service.files().list(
                q=folder_query,
                spaces='drive',
                supportsAllDrives=True
            ).execute()
            
            for subfolder in folder_results.get('files', []):
                total_count += self.count_files_in_folder(subfolder['id'], file_extension)

            return total_count
        except Exception as e:
            logger.error(f"Error counting files in folder: {str(e)}")
            return 0

    def upload_file(self, filepath, class_name: str, chapter_name: str, year: str, subtopic_name: str = "Main", progress_callback=None):
        """Upload a file to Google Drive with progress tracking."""
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            # Get or create the class-year folder
            class_year_folder_id = self.get_or_create_class_year_folder(class_name, year)
            
            # Get or create the chapter folder
            chapter_folder_id = self.get_or_create_chapter_folder(chapter_name, class_year_folder_id)
            
            # Get or create the subtopic folder
            subtopic_folder_id = self.get_or_create_folder(subtopic_name, chapter_folder_id)

            # Get the count of .mp4 files in the chapter folder
            file_count = self.count_files_in_folder(chapter_folder_id, 'mp4')
            class_number = file_count + 1

            # Get the file extension
            _, ext = os.path.splitext(filepath)
            
            # Create the new filename with class number
            new_filename = f"{class_name}_{chapter_name}_{subtopic_name}_{datetime.now().strftime('%d-%m-%Y')}_Class_{class_number}{ext}"

            file_metadata = {
                'name': new_filename,
                'parents': [subtopic_folder_id]
            }

            # Create a MediaFileUpload object with resumable upload enabled
            media = MediaFileUpload(
                filepath,
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )

            # Create the file upload request
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            )

            # Upload the file with progress tracking
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and progress_callback:
                    # status.progress() returns a float between 0 and 1
                    progress = int(status.progress() * 100)
                    progress_callback(progress)

            file_id = response.get('id')
            
            logger.info(f"File uploaded successfully:")
            logger.info(f"- File ID: {file_id}")
            logger.info(f"- File Name: {response.get('name')}")
            logger.info(f"- Web URL: {response.get('webViewLink')}")
            logger.info(f"- Direct URL: {self.DRIVE_VIEW_URL.format(file_id)}")

            return file_id
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise

    def get_file_info(self, file_id):
        """Get file information from Drive."""
        try:
            return self.service.files().get(fileId=file_id).execute()
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return None

    def delete_file(self, file_id):
        """Delete a file from Drive."""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

    def get_file_path(self, file_id):
        """Get the file path in Drive."""
        try:
            file = self.service.files().get(
                fileId=file_id, 
                fields='name, parents'
            ).execute()
            
            path = file.get('name', '')
            
            # Get the full path by traversing up the folder hierarchy
            if 'parents' in file:
                parent_id = file['parents'][0]
                try:
                    parent = self.service.files().get(
                        fileId=parent_id, 
                        fields='name, parents'
                    ).execute()
                    parent_path = parent.get('name', '')
                    
                    # Get the grandparent folder name
                    if 'parents' in parent:
                        grandparent_id = parent['parents'][0]
                        try:
                            grandparent = self.service.files().get(
                                fileId=grandparent_id, 
                                fields='name'
                            ).execute()
                            return f"{grandparent['name']} > {parent_path} > {path}"
                        except:
                            return f"{parent_path} > {path}"
                    
                    return f"{parent_path} > {path}"
                except:
                    return path
            
            return path
        except Exception as e:
            logger.error(f"Error getting file path: {str(e)}")
            return None 