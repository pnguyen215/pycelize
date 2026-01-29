"""
Validation Utility Functions

This module provides validation functions for request data and files.
"""

from typing import Any, Dict, List, Optional
from app.core.exceptions import ValidationError


class Validators:
    """
    Utility class for data validation.

    Provides static methods for validating various types of input data.
    """

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """
        Validate that required fields are present in data.

        Args:
            data: Dictionary to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If any required field is missing
        """
        missing = [f for f in required_fields if f not in data or data[f] is None]

        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing)}",
                details={"missing_fields": missing},
            )

    @staticmethod
    def validate_file_uploaded(file) -> None:
        """
        Validate that a file was uploaded.

        Args:
            file: File object from request

        Raises:
            ValidationError: If no file was uploaded
        """
        if file is None or file.filename == "":
            raise ValidationError("No file uploaded")

    @staticmethod
    def validate_columns_exist(
        columns: List[str], available_columns: List[str]
    ) -> Dict[str, List[str]]:
        """
        Validate that requested columns exist.

        Args:
            columns: List of requested column names
            available_columns: List of available column names

        Returns:
            Dictionary with 'valid' and 'invalid' column lists
        """
        valid = [c for c in columns if c in available_columns]
        invalid = [c for c in columns if c not in available_columns]

        return {"valid": valid, "invalid": invalid, "all_valid": len(invalid) == 0}

    @staticmethod
    def validate_normalization_type(type_string: str) -> bool:
        """
        Validate that a normalization type is valid.

        Args:
            type_string: Normalization type string

        Returns:
            True if valid
        """
        from app.models.enums import NormalizationType

        try:
            NormalizationType.from_string(type_string)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_database_type(type_string: str) -> bool:
        """
        Validate that a database type is valid.

        Args:
            type_string: Database type string

        Returns:
            True if valid
        """
        from app.models.enums import DatabaseType

        try:
            DatabaseType.from_string(type_string)
            return True
        except ValueError:
            return False
