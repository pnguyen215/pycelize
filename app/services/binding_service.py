"""
Binding Service Implementation

This module provides Excel-to-Excel data binding functionality,
allowing values from a source file to be mapped into a target file.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import pandas as pd

from app.core.config import Config
from app.core.exceptions import FileProcessingError, ValidationError
from app.core.logging import get_logger
from app.services.excel_service import ExcelService

logger = get_logger(__name__)


class BindingService:
    """
    Service for Excel-to-Excel data binding operations.

    This service binds values from a source Excel file (containing mapping data)
    into a target Excel file (with columns needing values).

    The binding is performed by matching column names between source and target
    based on a user-provided mapping configuration.

    Example:
        >>> service = BindingService(config)
        >>> result = service.bind_data(
        ...     source_path='source.xlsx',
        ...     target_path='target.xlsx',
        ...     column_mapping={'target_col': 'source_col'}
        ... )
    """

    def __init__(self, config: Config):
        """
        Initialize BindingService with configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.excel_service = ExcelService(config)
        self.output_folder = config.get("file.output_folder", "outputs")

        os.makedirs(self.output_folder, exist_ok=True)

    def bind_data(
        self,
        source_path: str,
        target_path: str,
        column_mapping: Dict[str, str],
        output_path: Optional[str] = None,
        source_sheet: Optional[str] = None,
        target_sheet: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bind data from source file to target file.

        Args:
            source_path: Path to source Excel file
            target_path: Path to target Excel file
            column_mapping: Mapping from target columns to source columns
            output_path: Optional path for output file
            source_sheet: Optional sheet name in source file
            target_sheet: Optional sheet name in target file

        Returns:
            Dictionary containing binding results and statistics

        Raises:
            FileProcessingError: If binding operation fails
        """
        logger.info(f"Starting data binding: {source_path} -> {target_path}")

        try:
            # Read source and target files
            source_df = self.excel_service.read_excel(source_path, source_sheet)
            target_df = self.excel_service.read_excel(target_path, target_sheet)

            # Validate column mapping
            validation = self._validate_mapping(source_df, target_df, column_mapping)

            if not validation["valid"]:
                raise ValidationError(
                    "Column mapping validation failed", details=validation
                )

            # Perform binding
            bound_df, binding_stats = self._perform_binding(
                source_df, target_df, column_mapping
            )

            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(target_path))[0]
                output_path = os.path.join(
                    self.output_folder, f"{base_name}_bound.xlsx"
                )

            # Write result
            result_path = self.excel_service.write_excel(
                data=bound_df, output_path=output_path
            )

            result = {
                "success": True,
                "output_path": result_path,
                "source_rows": len(source_df),
                "target_rows": len(target_df),
                "result_rows": len(bound_df),
                "columns_bound": list(column_mapping.keys()),
                "binding_stats": binding_stats,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Data binding completed: {result_path}")
            return result

        except Exception as e:
            logger.error(f"Error in data binding: {str(e)}")
            raise FileProcessingError(f"Data binding failed: {str(e)}")

    def _validate_mapping(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        column_mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """Validate column mapping against source and target DataFrames."""
        missing_source = []
        missing_target = []
        valid_mappings = []

        for target_col, source_col in column_mapping.items():
            if source_col not in source_df.columns:
                missing_source.append(source_col)
            elif target_col not in target_df.columns:
                missing_target.append(target_col)
            else:
                valid_mappings.append({"target": target_col, "source": source_col})

        return {
            "valid": len(missing_source) == 0 and len(missing_target) == 0,
            "missing_source_columns": missing_source,
            "missing_target_columns": missing_target,
            "valid_mappings": valid_mappings,
        }

    def _perform_binding(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        column_mapping: Dict[str, str],
    ) -> tuple:
        """Perform the actual data binding operation."""
        bound_df = target_df.copy()
        binding_stats = {}

        for target_col, source_col in column_mapping.items():
            if source_col in source_df.columns and target_col in bound_df.columns:
                # Get source values
                source_values = source_df[source_col].tolist()

                # Determine how many values to bind
                target_len = len(bound_df)
                source_len = len(source_values)

                if source_len >= target_len:
                    # Use first target_len values from source
                    bound_df[target_col] = source_values[:target_len]
                else:
                    # Pad with None if source is shorter
                    padded_values = source_values + [None] * (target_len - source_len)
                    bound_df[target_col] = padded_values

                binding_stats[target_col] = {
                    "source_column": source_col,
                    "values_bound": min(source_len, target_len),
                    "null_filled": max(0, target_len - source_len),
                }

                logger.debug(f"Bound column '{target_col}' <- '{source_col}'")

        return bound_df, binding_stats
