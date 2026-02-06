"""
Search Service Implementation

This module provides data search and filtering functionality for
Excel and CSV files with support for multiple conditions and operators.
"""

import os
from typing import List
import pandas as pd

from app.core.config import Config
from app.core.exceptions import ValidationError, FileProcessingError
from app.core.logging import get_logger
from app.models.request import SearchCondition

logger = get_logger(__name__)


class SearchService:
    """
    Service for searching and filtering data in Excel and CSV files.

    This service provides comprehensive data filtering including:
    - Multiple search conditions across different columns
    - Support for various operators (equals, contains, greater_than, etc.)
    - Logical combinations (AND/OR)
    - Different data types (string, number, date, boolean)
    - Export to multiple formats (Excel, CSV, JSON)

    Attributes:
        config: Application configuration

    Example:
        >>> service = SearchService(config)
        >>> filtered_df = service.apply_search(df, conditions, "AND")
    """

    def __init__(self, config: Config):
        """
        Initialize SearchService with configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.output_folder = config.get("file.output_folder", "outputs")

        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def apply_search(
        self,
        data: pd.DataFrame,
        conditions: List[SearchCondition],
        logic: str = "AND",
    ) -> pd.DataFrame:
        """
        Apply search conditions to a DataFrame.

        Args:
            data: DataFrame to filter
            conditions: List of search conditions
            logic: Logical operator ("AND" or "OR")

        Returns:
            Filtered DataFrame

        Raises:
            ValidationError: If conditions are invalid
        """
        if not conditions:
            raise ValidationError("At least one search condition is required")

        if logic not in ["AND", "OR"]:
            raise ValidationError("Logic must be either 'AND' or 'OR'")

        logger.info(f"Applying {len(conditions)} search conditions with {logic} logic")

        # Build masks for each condition
        masks = []
        for condition in conditions:
            mask = self._apply_condition(data, condition)
            masks.append(mask)

        # Combine masks with logic
        if logic == "AND":
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask &= mask
        else:  # OR
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask |= mask

        result = data[combined_mask].copy()
        logger.info(f"Filtered {len(data)} rows to {len(result)} rows")

        return result

    def _apply_condition(
        self, data: pd.DataFrame, condition: SearchCondition
    ) -> pd.Series:
        """
        Apply a single search condition to a DataFrame.

        Args:
            data: DataFrame to filter
            condition: Search condition to apply

        Returns:
            Boolean mask series

        Raises:
            ValidationError: If column doesn't exist or operator is invalid
        """
        if condition.column not in data.columns:
            raise ValidationError(f"Column '{condition.column}' not found in data")

        column_data = data[condition.column]
        operator = condition.operator.lower()
        value = condition.value

        logger.debug(f"Applying condition: {condition.column} {operator} {value}")

        # String operators
        if operator == "equals":
            return column_data.astype(str) == str(value)
        elif operator == "not_equals":
            return column_data.astype(str) != str(value)
        elif operator == "contains":
            return column_data.astype(str).str.contains(
                str(value), case=False, na=False
            )
        elif operator == "not_contains":
            return ~column_data.astype(str).str.contains(
                str(value), case=False, na=False
            )
        elif operator == "starts_with":
            return column_data.astype(str).str.startswith(str(value), na=False)
        elif operator == "ends_with":
            return column_data.astype(str).str.endswith(str(value), na=False)
        elif operator == "is_empty":
            return (column_data.astype(str) == "") | (column_data.isna())
        elif operator == "is_not_empty":
            return (column_data.astype(str) != "") & (~column_data.isna())

        # Numeric operators
        elif operator == "greater_than":
            numeric_col = pd.to_numeric(column_data, errors="coerce")
            compare_val = pd.to_numeric(value, errors="coerce")
            return numeric_col > compare_val
        elif operator == "greater_than_or_equal":
            numeric_col = pd.to_numeric(column_data, errors="coerce")
            compare_val = pd.to_numeric(value, errors="coerce")
            return numeric_col >= compare_val
        elif operator == "less_than":
            numeric_col = pd.to_numeric(column_data, errors="coerce")
            compare_val = pd.to_numeric(value, errors="coerce")
            return numeric_col < compare_val
        elif operator == "less_than_or_equal":
            numeric_col = pd.to_numeric(column_data, errors="coerce")
            compare_val = pd.to_numeric(value, errors="coerce")
            return numeric_col <= compare_val
        elif operator == "between":
            # Value should be a list/tuple with [min, max]
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValidationError(
                    "For 'between' operator, value must be a list with [min, max]"
                )
            numeric_col = pd.to_numeric(column_data, errors="coerce")
            min_val = pd.to_numeric(value[0], errors="coerce")
            max_val = pd.to_numeric(value[1], errors="coerce")
            return (numeric_col >= min_val) & (numeric_col <= max_val)

        # Date operators
        elif operator == "before":
            try:
                date_col = pd.to_datetime(column_data, errors="coerce")
                compare_date = pd.to_datetime(value, errors="coerce")
                return date_col < compare_date
            except Exception:
                raise ValidationError("Invalid date format for 'before' operator")
        elif operator == "after":
            try:
                date_col = pd.to_datetime(column_data, errors="coerce")
                compare_date = pd.to_datetime(value, errors="coerce")
                return date_col > compare_date
            except Exception:
                raise ValidationError("Invalid date format for 'after' operator")

        else:
            raise ValidationError(f"Unsupported operator: {operator}")

    @staticmethod
    def get_operator_suggestions(column_type: str) -> List[str]:
        """
        Get suggested operators based on column data type.

        Args:
            column_type: Data type of the column

        Returns:
            List of operator names
        """
        # Normalize type string
        column_type = str(column_type).lower()

        # Detect type and return operators
        if any(t in column_type for t in ["int", "float", "number", "numeric"]):
            return [
                "equals",
                "not_equals",
                "greater_than",
                "greater_than_or_equal",
                "less_than",
                "less_than_or_equal",
                "between",
            ]
        elif any(t in column_type for t in ["date", "time", "datetime"]):
            return ["equals", "before", "after", "between"]
        elif any(t in column_type for t in ["bool", "boolean"]):
            return ["equals", "not_equals"]
        else:  # Default to string operators
            return [
                "equals",
                "not_equals",
                "contains",
                "not_contains",
                "starts_with",
                "ends_with",
                "is_empty",
                "is_not_empty",
            ]

    def save_search_results(
        self,
        data: pd.DataFrame,
        output_path: str,
        output_format: str = "xlsx",
    ) -> str:
        """
        Save search results to file.

        Args:
            data: Filtered DataFrame
            output_path: Path to save the file
            output_format: Format to save (xlsx, csv, or json)

        Returns:
            Path to saved file

        Raises:
            ValidationError: If output format is invalid
            FileProcessingError: If file cannot be saved
        """
        try:
            logger.info(f"Saving {len(data)} rows to {output_path} as {output_format}")

            if output_format == "xlsx":
                data.to_excel(output_path, index=False, engine="openpyxl")
            elif output_format == "csv":
                data.to_csv(output_path, index=False, encoding="utf-8")
            elif output_format == "json":
                data.to_json(output_path, orient="records", indent=2)
            else:
                raise ValidationError(
                    f"Unsupported output format: {output_format}. "
                    "Supported formats: xlsx, csv, json"
                )

            logger.info(f"Successfully saved file to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error saving search results: {str(e)}")
            raise FileProcessingError(f"Failed to save search results: {str(e)}")
