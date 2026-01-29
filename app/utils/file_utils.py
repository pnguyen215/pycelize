"""
File Utility Functions

This module provides utility functions for file operations.
"""

import os
from pathlib import Path
from typing import List, Optional
from werkzeug.utils import secure_filename

from app.models.enums import FileType


class FileUtils:
    """
    Utility class for file operations.

    Provides static methods for common file operations such as
    path validation, extension checking, and file type detection.
    """

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get the file extension from a filename.

        Args:
            filename: Name of the file

        Returns:
            Lowercase file extension including the dot
        """
        return Path(filename).suffix.lower()

    @staticmethod
    def get_file_type(filename: str) -> FileType:
        """
        Determine the FileType from a filename.

        Args:
            filename: Name of the file

        Returns:
            FileType enum value
        """
        ext = FileUtils.get_file_extension(filename)
        return FileType.from_extension(ext)

    @staticmethod
    def is_allowed_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """
        Check if file has an allowed extension.

        Args:
            filename: Name of the file
            allowed_extensions: List of allowed extensions (with dots)

        Returns:
            True if extension is allowed
        """
        ext = FileUtils.get_file_extension(filename)
        return ext in [e.lower() for e in allowed_extensions]

    @staticmethod
    def secure_save_path(filename: str, upload_folder: str) -> str:
        """
        Generate a secure file path for saving.

        Args:
            filename: Original filename
            upload_folder: Target folder for upload

        Returns:
            Full secure path for the file
        """
        secure_name = secure_filename(filename)
        return os.path.join(upload_folder, secure_name)

    @staticmethod
    def ensure_directory(path: str) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure
        """
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes
        """
        return os.path.getsize(file_path)

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path: Path to the file

        Returns:
            True if file exists
        """
        return os.path.isfile(file_path)

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file if it exists.

        Args:
            file_path: Path to the file

        Returns:
            True if file was deleted
        """
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
