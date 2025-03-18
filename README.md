# Google Drive Uploader

A Python desktop application for uploading files to Google Drive.

## Features

- Modern PyQt6-based GUI
- File selection and validation
- Progress tracking for uploads
- Configurable upload settings
- Asynchronous upload processing
- Error handling and user feedback
- Standalone executable with bundled configuration

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the application:
   - Copy `.env.example` to `.env`
   - Update the Google Drive API credentials in `.env`
   - Place your `service-account.json` in the project root
   - Adjust upload settings as needed

## Running the Application

### Development Mode
To run the desktop application in development mode:
```bash
python src/main.py
```

### Building Standalone Executable
To create a standalone executable with bundled configuration:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller build.spec
   ```

3. The executable will be created in the `dist` directory as `MathsByPawanSir.exe`

### Bundled Configuration
The standalone executable includes:
- `.env` file with your environment variables
- `service-account.json` with your Google Drive API credentials

These files are automatically bundled into the executable and extracted to a temporary directory when the application runs. You don't need to distribute these files separately.

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

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`

## Configuration

The application can be configured through environment variables in the `.env` file:

- `GOOGLE_CLIENT_ID`: Google Drive API client ID
- `GOOGLE_CLIENT_SECRET`: Google Drive API client secret
- `GOOGLE_REDIRECT_URI`: OAuth redirect URI
- `MAX_UPLOAD_SIZE`: Maximum file size in MB
- `ALLOWED_FILE_TYPES`: Comma-separated list of allowed file extensions

## License

MIT License 