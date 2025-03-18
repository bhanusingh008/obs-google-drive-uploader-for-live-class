# OBS Google Drive Uploader

A Python desktop application for uploading files to Google Drive, specifically designed for educational content management.

## Features

- Modern PyQt6-based GUI
- File selection and validation
- Progress tracking for uploads
- Configurable upload settings
- Asynchronous upload processing
- Error handling and user feedback
- Standalone executable with bundled configuration
- Support for large file uploads (up to 500MB)
- Automatic file organization by class, chapter, and subtopic

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- Google Drive API enabled
- Service account credentials

## Setup

### 1. Google Cloud Platform Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create a service account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Click "Create and Continue"
5. Generate service account key:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - Click "Create"
   - Save the downloaded JSON file as `service-account.json`

### 2. Application Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/obs-google-drive-uploader-for-live-class.git
   cd obs-google-drive-uploader-for-live-class
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the application:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Place your `service-account.json` in the project root
   - Update the `.env` file with your settings:
     ```env
     # Recording settings
     RECORDING_PATH=C:\Users\YourUsername\Videos  # Update with your path
     
     # Upload settings
     MAX_UPLOAD_SIZE=500  # Maximum file size in MB
     ALLOWED_FILE_TYPES=*  # Comma-separated list of allowed extensions
     
     # Google Drive settings
     GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here  # The root folder ID where videos will be uploaded
     ```

### 3. Running the Application

#### Development Mode
```bash
python src/main.py
```

#### Building Standalone Executable

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller build.spec
   ```

3. The executable will be created in the `dist` directory as `MathsByPawanSir.exe`

## Security Considerations

1. Never commit your `service-account.json` or `.env` files to version control
2. Keep your service account credentials secure
3. Regularly rotate your service account keys
4. Use environment variables for sensitive information
5. The application stores configuration in the user's AppData directory (Windows) or home directory (Linux/Mac)

## Troubleshooting

### Common Issues

1. **Upload Fails**
   - Check your internet connection
   - Verify service account permissions
   - Ensure file size is within limits
   - Check Google Drive API quotas

2. **Application Won't Start**
   - Verify Python version (3.8+ required)
   - Check if all dependencies are installed
   - Ensure `service-account.json` is present
   - Verify `.env` file configuration

3. **Configuration Not Saving**
   - Check write permissions in AppData directory
   - Verify file paths in `.env`
   - Ensure proper directory structure

### Getting Help

- Check the [Issues](https://github.com/yourusername/obs-google-drive-uploader-for-live-class/issues) page
- Create a new issue with:
  - Error message
  - Steps to reproduce
  - System information
  - Log files (if available)

## Project Structure

```
.
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   └── config.py      # Configuration management
│   ├── ui/                # User interface
│   │   ├── base.py       # Base UI components
│   │   └── main_window.py # Main window implementation
│   ├── utils/             # Utility functions
│   ├── main.py           # Application entry point
│   └── __init__.py       # Package initialization
├── tests/                 # Test files
├── data/                  # Application data directory
├── requirements.txt       # Project dependencies
├── .env.example          # Example environment configuration
├── service-account.json   # Google Drive API credentials
├── build.spec            # PyInstaller configuration
└── README.md             # Project documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- PyQt6 for the GUI framework
- Google Drive API team
- All contributors and users of this project

## OBS Integration & Google Drive Upload

### OBS Setup
1. **OBS Configuration:**
   - Install and configure OBS on your system
   - Set up your scenes and sources for recording
   - Keep OBS running in the background
   - Note: Do NOT start/stop recording directly in OBS
   - Enable websocket servers in OBS

### Recording Workflow
1. **Using the Application:**
   - Launch the MathsByPawanSir application
   - Select your class, chapter, and subtopic
   - Click "Start Recording" in the application (NOT in OBS)
   - The app will control OBS recording in the background
   - Click "Stop Recording" when finished
   - The recorded file will be automatically detected

2. **Uploading:**
   - After stopping the recording, the file will be ready for upload
   - Verify the recording details
   - Click upload to send to Google Drive
   - Monitor the upload progress

### Google Drive Organization
1. **Folder Setup:**
   - Create a folder in Google Drive where you want to store all your videos
   - Get the folder ID from the URL when you open the folder in Google Drive
   - Add this folder ID to your `.env` file as `GOOGLE_DRIVE_FOLDER_ID`

2. **File Structure:**
   - Files are automatically organized in the following structure:
     ```
     Your Specified Google Drive Folder
     └── Class Name
         └── Chapter Name
             └── Subtopic Name
                 └── Your recorded video
     ```

3. **Finding Folder ID:**
   - Open your Google Drive folder in a web browser
   - The URL will look like: `https://drive.google.com/drive/folders/FOLDER_ID`
   - Copy the FOLDER_ID part and paste it in your `.env` file

### Best Practices
1. **Before Starting:**
   - Launch OBS first
   - Verify your scenes and sources in OBS
   - Then launch MathsByPawanSir application
   - Test microphone and screen capture
   - Ensure enough storage space

2. **During Recording:**
   - Use ONLY the application controls, not OBS
   - Monitor recording status in the application
   - Keep both OBS and the application running

3. **After Recording:**
   - Wait for the upload confirmation
   - Verify the upload in Google Drive
   - Keep local recordings until upload is confirmed 


### Video Tutorial
For a detailed walkthrough of the application setup and usage, watch this tutorial:
[Setup and Usage Tutorial](https://www.youtube.com/watch?v=aK-Lq6lPKSM)