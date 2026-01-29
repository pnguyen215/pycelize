"""
API Response Models

This module defines the data structures for API responses,
ensuring consistent response formatting across all endpoints.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from datetime import datetime


@dataclass
class MetaInfo:
    """
    Metadata information for API responses.

    Attributes:
        api_version: Version of the API
        locale: Locale setting for the response
        request_id: Unique identifier for the request
        requested_time: Timestamp of the request
    """

    api_version: str
    locale: str
    request_id: str
    requested_time: str

    def to_dict(self) -> Dict[str, str]:
        """Convert MetaInfo to dictionary."""
        return {
            "api_version": self.api_version,
            "locale": self.locale,
            "request_id": self.request_id,
            "requested_time": self.requested_time,
        }


@dataclass
class ApiResponse:
    """
    Standard API response structure.

    All API endpoints should return responses following this structure
    to ensure consistency across the application.

    Attributes:
        data: Response payload data
        message: Human-readable message
        meta: Response metadata
        status_code: HTTP status code
        total: Total count for paginated responses
    """

    data: Optional[Any] = None
    message: str = ""
    meta: Optional[MetaInfo] = None
    status_code: int = 200
    total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ApiResponse to dictionary format.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "data": self.data,
            "message": self.message,
            "meta": self.meta.to_dict() if self.meta else None,
            "status_code": self.status_code,
            "total": self.total,
        }
