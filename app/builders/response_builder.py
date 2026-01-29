"""
Response Builder Implementation

This module implements the Builder Design Pattern for constructing
API responses with consistent structure and metadata.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Dict

from flask import current_app


class ResponseBuilder:
    """
    Builder class for constructing standardized API responses.

    Implements the Builder Design Pattern to create API responses
    with consistent structure, including metadata, status codes,
    and proper formatting.

    The builder provides a fluent interface for step-by-step
    construction of response objects.

    Example:
        >>> response = (
        ...     ResponseBuilder()
        ...     .with_data({'user': 'john'})
        ...     .with_message('User retrieved successfully')
        ...     .with_status_code(200)
        ...     .build()
        ... )
        >>> print(response['status_code'])
        200

    Attributes:
        _data: Response payload data
        _message: Human-readable message
        _status_code: HTTP status code
        _total: Total count for collections
        _api_version: API version string
        _locale: Locale setting
        _request_id: Unique request identifier
    """

    def __init__(self):
        """Initialize ResponseBuilder with default values."""
        self._data: Optional[Any] = None
        self._message: str = ""
        self._status_code: int = 200
        self._total: int = 0
        self._api_version: str = "v0.0.1"
        self._locale: str = "en_US"
        self._request_id: str = self._generate_request_id()
        self._requested_time: str = self._get_current_time()

    def with_data(self, data: Any) -> "ResponseBuilder":
        """
        Set the response data payload.

        Args:
            data: The data to include in the response

        Returns:
            Self for method chaining
        """
        self._data = data
        return self

    def with_message(self, message: str) -> "ResponseBuilder":
        """
        Set the response message.

        Args:
            message: Human-readable message describing the response

        Returns:
            Self for method chaining
        """
        self._message = message
        return self

    def with_status_code(self, status_code: int) -> "ResponseBuilder":
        """
        Set the HTTP status code.

        Args:
            status_code: HTTP status code (e.g., 200, 404, 500)

        Returns:
            Self for method chaining
        """
        self._status_code = status_code
        return self

    def with_total(self, total: int) -> "ResponseBuilder":
        """
        Set the total count for paginated responses.

        Args:
            total: Total number of items in the full result set

        Returns:
            Self for method chaining
        """
        self._total = total
        return self

    def with_api_version(self, version: str) -> "ResponseBuilder":
        """
        Set the API version in metadata.

        Args:
            version: API version string (e.g., 'v1.0.0')

        Returns:
            Self for method chaining
        """
        self._api_version = version
        return self

    def with_locale(self, locale: str) -> "ResponseBuilder":
        """
        Set the locale in metadata.

        Args:
            locale: Locale string (e.g., 'en_US')

        Returns:
            Self for method chaining
        """
        self._locale = locale
        return self

    def with_config(self) -> "ResponseBuilder":
        """
        Apply configuration from Flask app context.

        Reads API version and locale from application configuration.

        Returns:
            Self for method chaining
        """
        try:
            config = current_app.config.get("PYCELIZE")
            if config:
                self._api_version = config.get("app.version", "v0.0.1")
                self._locale = config.get("api.locale", "en_US")
        except RuntimeError:
            # Outside application context, use defaults
            pass
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build and return the final response dictionary.

        Constructs the complete response structure with all
        configured values and metadata.

        Returns:
            Complete response dictionary ready for JSON serialization
        """
        # Apply config if in app context
        self.with_config()

        return {
            "data": self._data,
            "message": self._message,
            "meta": {
                "api_version": self._api_version,
                "locale": self._locale,
                "request_id": self._request_id,
                "requested_time": self._requested_time,
            },
            "status_code": self._status_code,
            "total": self._total,
        }

    def build_error(self, error_type: str = "Error") -> Dict[str, Any]:
        """
        Build an error response.

        Convenience method for building error responses with
        proper error type indication.

        Args:
            error_type: Type/category of the error

        Returns:
            Error response dictionary
        """
        self.with_config()

        return {
            "data": {"error_type": error_type, "details": self._data},
            "message": self._message,
            "meta": {
                "api_version": self._api_version,
                "locale": self._locale,
                "request_id": self._request_id,
                "requested_time": self._requested_time,
            },
            "status_code": self._status_code,
            "total": 0,
        }

    @staticmethod
    def _generate_request_id() -> str:
        """
        Generate a unique request identifier.

        Returns:
            32-character hexadecimal request ID
        """
        return uuid.uuid4().hex

    @staticmethod
    def _get_current_time() -> str:
        """
        Get the current timestamp in ISO format with timezone.

        Returns:
            ISO formatted timestamp string
        """
        return datetime.now(timezone.utc).astimezone().isoformat()

    @classmethod
    def success(
        cls, data: Any = None, message: str = "Success", total: int = 0
    ) -> Dict[str, Any]:
        """
        Convenience method for creating success responses.

        Args:
            data: Response data payload
            message: Success message
            total: Total count for collections

        Returns:
            Success response dictionary
        """
        return (
            cls()
            .with_data(data)
            .with_message(message)
            .with_status_code(200)
            .with_total(total)
            .build()
        )

    @classmethod
    def error(
        cls, message: str = "Error", status_code: int = 500, details: Any = None
    ) -> Dict[str, Any]:
        """
        Convenience method for creating error responses.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details

        Returns:
            Error response dictionary
        """
        return (
            cls()
            .with_data(details)
            .with_message(message)
            .with_status_code(status_code)
            .build_error()
        )
