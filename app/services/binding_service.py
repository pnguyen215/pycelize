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

    def bind_excel_single_key(
        self,
        source_path: str,
        bind_path: str,
        comparison_column: str,
        bind_columns: List[str],
        output_path: Optional[str] = None,
        source_sheet: Optional[str] = None,
        bind_sheet: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bind columns from bind file to source file using a single comparison column.

        This method performs a left join between the source file (File A) and bind file (File B)
        based on a single comparison column. Values from specified bind columns are appended
        to the source file while preserving all original data.

        Args:
            source_path: Path to source Excel file (File A) - will be extended with new columns
            bind_path: Path to bind Excel file (File B) - contains data to bind
            comparison_column: Column name used to match rows between files
            bind_columns: List of column names from File B to append to File A
            output_path: Optional path for output file (auto-generated if not provided)
            source_sheet: Optional sheet name in source file (uses default if not provided)
            bind_sheet: Optional sheet name in bind file (uses default if not provided)

        Returns:
            Dictionary containing:
                - output_path: Path to the generated Excel file
                - source_rows: Number of rows in source file
                - bind_rows: Number of rows in bind file
                - matched_rows: Number of successfully matched rows
                - unmatched_rows: Number of rows without matches (NaN values)
                - columns_bound: List of bound column names
                - statistics: Detailed binding statistics

        Raises:
            ValidationError: If validation fails (missing columns, duplicate columns, etc.)
            FileProcessingError: If file operations fail

        Example:
            >>> service = BindingService(config)
            >>> result = service.bind_excel_single_key(
            ...     source_path='data.xlsx',
            ...     bind_path='reference.xlsx',
            ...     comparison_column='user_id',
            ...     bind_columns=['email', 'phone']
            ... )
            >>> print(result['matched_rows'])
            150
        """
        logger.info(
            f"Starting single-key binding: {source_path} + {bind_path} "
            f"on column '{comparison_column}'"
        )

        try:
            # Read both Excel files
            source_df = self.excel_service.read_excel(source_path, source_sheet)
            bind_df = self.excel_service.read_excel(bind_path, bind_sheet)

            logger.info(
                f"Loaded source: {len(source_df)} rows, bind: {len(bind_df)} rows"
            )

            # Validate that comparison column exists in both files
            if comparison_column not in source_df.columns:
                raise ValidationError(
                    f"Comparison column '{comparison_column}' not found in source file",
                    details={
                        "available_columns": list(source_df.columns),
                        "requested_column": comparison_column,
                    },
                )

            if comparison_column not in bind_df.columns:
                raise ValidationError(
                    f"Comparison column '{comparison_column}' not found in bind file",
                    details={
                        "available_columns": list(bind_df.columns),
                        "requested_column": comparison_column,
                    },
                )

            # Validate that all bind columns exist in bind file
            missing_bind_cols = [
                col for col in bind_columns if col not in bind_df.columns
            ]
            if missing_bind_cols:
                raise ValidationError(
                    f"Bind columns not found in bind file: {missing_bind_cols}",
                    details={
                        "available_columns": list(bind_df.columns),
                        "missing_columns": missing_bind_cols,
                    },
                )

            # Check for column name conflicts (bind columns already exist in source)
            conflicting_cols = [
                col for col in bind_columns if col not in [comparison_column] and col in source_df.columns
            ]
            if conflicting_cols:
                raise ValidationError(
                    f"Bind columns already exist in source file: {conflicting_cols}. "
                    "This would overwrite existing data.",
                    details={"conflicting_columns": conflicting_cols},
                )

            # Perform the binding using pandas merge (left join)
            # Select only comparison column and bind columns from bind file
            bind_subset = bind_df[[comparison_column] + bind_columns].copy()

            # Remove duplicates in bind file (keep first occurrence)
            bind_subset = bind_subset.drop_duplicates(
                subset=[comparison_column], keep="first"
            )

            # Perform left join
            result_df = pd.merge(
                source_df,
                bind_subset,
                on=comparison_column,
                how="left",
                suffixes=("", "_bind"),
            )

            # Calculate statistics
            source_rows = len(source_df)
            bind_rows = len(bind_df)
            result_rows = len(result_df)

            # Count matched rows (rows where at least one bind column is not NaN)
            matched_rows = 0
            for col in bind_columns:
                matched_rows = result_df[col].notna().sum()
                break  # Use first bind column to count matches

            unmatched_rows = source_rows - matched_rows

            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(source_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{base_name}_bound_single_{timestamp}.xlsx"
                output_path = os.path.join(self.output_folder, output_filename)

            # Write result to Excel
            result_path = self.excel_service.write_excel(
                data=result_df, output_path=output_path
            )

            # Prepare statistics
            statistics = {
                "comparison_column": comparison_column,
                "bind_columns": bind_columns,
                "unique_keys_in_bind": len(bind_subset),
                "duplicate_keys_removed": len(bind_df) - len(bind_subset),
                "match_percentage": (
                    round((matched_rows / source_rows) * 100, 2)
                    if source_rows > 0
                    else 0
                ),
            }

            result = {
                "output_path": result_path,
                "source_rows": source_rows,
                "bind_rows": bind_rows,
                "matched_rows": int(matched_rows),
                "unmatched_rows": int(unmatched_rows),
                "columns_bound": bind_columns,
                "statistics": statistics,
            }

            logger.info(
                f"Single-key binding completed: {matched_rows}/{source_rows} rows matched"
            )
            return result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in single-key binding: {str(e)}")
            raise FileProcessingError(f"Single-key binding failed: {str(e)}")

    def bind_excel_multi_key(
        self,
        source_path: str,
        bind_path: str,
        comparison_columns: List[str],
        bind_columns: List[str],
        output_path: Optional[str] = None,
        source_sheet: Optional[str] = None,
        bind_sheet: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bind columns from bind file to source file using multiple comparison columns.

        This method performs a left join between the source file (File A) and bind file (File B)
        based on multiple comparison columns (composite key). Values from specified bind columns
        are appended to the source file while preserving all original data.

        Args:
            source_path: Path to source Excel file (File A) - will be extended with new columns
            bind_path: Path to bind Excel file (File B) - contains data to bind
            comparison_columns: List of column names used together to match rows (composite key)
            bind_columns: List of column names from File B to append to File A
            output_path: Optional path for output file (auto-generated if not provided)
            source_sheet: Optional sheet name in source file (uses default if not provided)
            bind_sheet: Optional sheet name in bind file (uses default if not provided)

        Returns:
            Dictionary containing:
                - output_path: Path to the generated Excel file
                - source_rows: Number of rows in source file
                - bind_rows: Number of rows in bind file
                - matched_rows: Number of successfully matched rows
                - unmatched_rows: Number of rows without matches (NaN values)
                - columns_bound: List of bound column names
                - statistics: Detailed binding statistics

        Raises:
            ValidationError: If validation fails (missing columns, duplicate columns, etc.)
            FileProcessingError: If file operations fail

        Example:
            >>> service = BindingService(config)
            >>> result = service.bind_excel_multi_key(
            ...     source_path='data.xlsx',
            ...     bind_path='reference.xlsx',
            ...     comparison_columns=['first_name', 'last_name'],
            ...     bind_columns=['email', 'phone']
            ... )
            >>> print(result['matched_rows'])
            142
        """
        logger.info(
            f"Starting multi-key binding: {source_path} + {bind_path} "
            f"on columns {comparison_columns}"
        )

        try:
            # Validate that comparison_columns is not empty
            if not comparison_columns or len(comparison_columns) == 0:
                raise ValidationError(
                    "At least one comparison column must be specified",
                    details={"comparison_columns": comparison_columns},
                )

            # Read both Excel files
            source_df = self.excel_service.read_excel(source_path, source_sheet)
            bind_df = self.excel_service.read_excel(bind_path, bind_sheet)

            logger.info(
                f"Loaded source: {len(source_df)} rows, bind: {len(bind_df)} rows"
            )

            # Validate that all comparison columns exist in both files
            missing_in_source = [
                col for col in comparison_columns if col not in source_df.columns
            ]
            if missing_in_source:
                raise ValidationError(
                    f"Comparison columns not found in source file: {missing_in_source}",
                    details={
                        "available_columns": list(source_df.columns),
                        "missing_columns": missing_in_source,
                    },
                )

            missing_in_bind = [
                col for col in comparison_columns if col not in bind_df.columns
            ]
            if missing_in_bind:
                raise ValidationError(
                    f"Comparison columns not found in bind file: {missing_in_bind}",
                    details={
                        "available_columns": list(bind_df.columns),
                        "missing_columns": missing_in_bind,
                    },
                )

            # Validate that all bind columns exist in bind file
            missing_bind_cols = [
                col for col in bind_columns if col not in bind_df.columns
            ]
            if missing_bind_cols:
                raise ValidationError(
                    f"Bind columns not found in bind file: {missing_bind_cols}",
                    details={
                        "available_columns": list(bind_df.columns),
                        "missing_columns": missing_bind_cols,
                    },
                )

            # Check for column name conflicts (bind columns already exist in source)
            # Exclude comparison columns from conflict check
            conflicting_cols = [
                col
                for col in bind_columns
                if col not in comparison_columns and col in source_df.columns
            ]
            if conflicting_cols:
                raise ValidationError(
                    f"Bind columns already exist in source file: {conflicting_cols}. "
                    "This would overwrite existing data.",
                    details={"conflicting_columns": conflicting_cols},
                )

            # Perform the binding using pandas merge (left join)
            # Select only comparison columns and bind columns from bind file
            bind_subset = bind_df[comparison_columns + bind_columns].copy()

            # Remove duplicates in bind file based on comparison columns (keep first)
            bind_subset = bind_subset.drop_duplicates(
                subset=comparison_columns, keep="first"
            )

            # Perform left join on multiple columns
            result_df = pd.merge(
                source_df,
                bind_subset,
                on=comparison_columns,
                how="left",
                suffixes=("", "_bind"),
            )

            # Calculate statistics
            source_rows = len(source_df)
            bind_rows = len(bind_df)
            result_rows = len(result_df)

            # Count matched rows (rows where at least one bind column is not NaN)
            matched_rows = 0
            for col in bind_columns:
                matched_rows = result_df[col].notna().sum()
                break  # Use first bind column to count matches

            unmatched_rows = source_rows - matched_rows

            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(source_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{base_name}_bound_multi_{timestamp}.xlsx"
                output_path = os.path.join(self.output_folder, output_filename)

            # Write result to Excel
            result_path = self.excel_service.write_excel(
                data=result_df, output_path=output_path
            )

            # Prepare statistics
            statistics = {
                "comparison_columns": comparison_columns,
                "bind_columns": bind_columns,
                "unique_keys_in_bind": len(bind_subset),
                "duplicate_keys_removed": len(bind_df) - len(bind_subset),
                "match_percentage": (
                    round((matched_rows / source_rows) * 100, 2)
                    if source_rows > 0
                    else 0
                ),
            }

            result = {
                "output_path": result_path,
                "source_rows": source_rows,
                "bind_rows": bind_rows,
                "matched_rows": int(matched_rows),
                "unmatched_rows": int(unmatched_rows),
                "columns_bound": bind_columns,
                "statistics": statistics,
            }

            logger.info(
                f"Multi-key binding completed: {matched_rows}/{source_rows} rows matched"
            )
            return result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in multi-key binding: {str(e)}")
            raise FileProcessingError(f"Multi-key binding failed: {str(e)}")
