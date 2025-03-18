"""
Setup configuration for the Google Drive Uploader package.
"""

from setuptools import setup, find_packages

setup(
    name="google-drive-uploader",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "PyQt6>=6.6.1",
        "PyQt6-Qt6>=6.6.1",
        "PyQt6-sip>=13.6.0",
        "Pillow>=10.2.0",
    ],
    entry_points={
        "console_scripts": [
            "google-drive-uploader=src.main:main",
        ],
    },
    python_requires=">=3.8",
) 