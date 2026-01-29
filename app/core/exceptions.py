"""
Custom Exception Classes

This module defines custom exceptions for the Pycelize application,
providing clear error categorization and handling.
"""

from flask import Flask, jsonify
from typing import Optional, Dict, Any

from app.builders.response_builder import ResponseBuilder


class PycelizeException(Exception):
    """
    Base exception class for all Pycelize-related errors.

    All custom exceptions in the application should inherit from this class
    to ensure consistent error handling and response formatting.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for API responses
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize PycelizeException.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            details: Additional error details dictionary
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format.

        Returns:
            Dictionary representation of the exception
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class FileProcessingError(PycelizeException):
    """
    Exception raised when file processing operations fail.

    This includes errors during file reading, writing, parsing,
    or any other file-related operations.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class ValidationError(PycelizeException):
    """
    Exception raised when validation fails.

    This includes invalid input data, missing required fields,
    or data that doesn't meet expected constraints.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class ConfigurationError(PycelizeException):
    """
    Exception raised when configuration is invalid or missing.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class FileNotFoundError(PycelizeException):
    """
    Exception raised when a requested file is not found.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class UnsupportedFileTypeError(PycelizeException):
    """
    Exception raised when file type is not supported.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=415, details=details)


class NormalizationError(PycelizeException):
    """
    Exception raised when data normalization fails.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class SQLGenerationError(PycelizeException):
    """
    Exception raised when SQL generation fails.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers for the Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(PycelizeException)
    def handle_pycelize_exception(error: PycelizeException):
        """Handle all Pycelize-specific exceptions."""
        response = (
            ResponseBuilder()
            .with_status_code(error.status_code)
            .with_message(error.message)
            .with_data(error.details)
            .build()
        )
        return jsonify(response), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors."""
        response = (
            ResponseBuilder().with_status_code(400).with_message("Bad Request").build()
        )
        return jsonify(response), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        response = (
            ResponseBuilder()
            .with_status_code(404)
            .with_message("Resource not found")
            .build()
        )
        return jsonify(response), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors."""
        response = (
            ResponseBuilder()
            .with_status_code(500)
            .with_message("Internal server error")
            .build()
        )
        return jsonify(response), 500
