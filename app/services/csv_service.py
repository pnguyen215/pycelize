"""
CSV Service Implementation

This module provides CSV file processing functionality including
reading, writing, and conversion to Excel format.
"""

import os
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.config import Config
from app.core.exceptions import FileProcessingError
from app.core.logging import get_logger
from app.services.excel_service import ExcelService

logger = get_logger(__name__)


class CSVService:
    """
    Service for CSV file processing operations.

    This service provides CSV file handling including:
    - Reading CSV files with encoding detection
    - Converting CSV to Excel format
    - Writing DataFrames to CSV

    Attributes:
        config: Application configuration
        supported_encodings: List of encodings to try when reading
        excel_service: Excel service for conversion operations

    Example:
        >>> service = CSVService(config)
        >>> df = service.read_csv('data.csv')
        >>> excel_path = service.convert_to_excel('data.csv')
    """

    def __init__(self, config: Config):
        """
        Initialize CSVService with configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.supported_encodings = config.get(
            "file.supported_encodings", ["utf-8", "utf-8-sig", "latin1", "cp1252"]
        )
        self.output_folder = config.get("file.output_folder", "outputs")
        self.excel_service = ExcelService(config)

        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def read_csv(self, file_path: str, encoding: Optional[str] = None) -> pd.DataFrame:
        """
        Read a CSV file with automatic encoding detection.

        Args:
            file_path: Path to the CSV file
            encoding: Optional specific encoding to use

        Returns:
            DataFrame containing the CSV data

        Raises:
            FileProcessingError: If file cannot be read
        """
        logger.info(f"Reading CSV file: {file_path}")

        encodings_to_try = [encoding] if encoding else self.supported_encodings

        for enc in encodings_to_try:
            try:
                logger.debug(f"Trying encoding: {enc}")
                df = pd.read_csv(file_path, encoding=enc, dtype=str, keep_default_na=False)
                logger.info(f"Successfully read CSV with encoding: {enc}")
                logger.info(f"Read {len(df)} rows, {len(df.columns)} columns")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading CSV: {str(e)}")
                raise FileProcessingError(f"Failed to read CSV file: {str(e)}")

        raise FileProcessingError(
            f"Unable to read CSV file with supported encodings: {encodings_to_try}"
        )

    def write_csv(
        self,
        data: pd.DataFrame,
        output_path: str,
        encoding: str = "utf-8",
        index: bool = False,
    ) -> str:
        """
        Write a DataFrame to a CSV file.

        Args:
            data: DataFrame to write
            output_path: Path for the output file
            encoding: File encoding
            index: Whether to include row index

        Returns:
            Path to the created file

        Raises:
            FileProcessingError: If file cannot be written
        """
        try:
            logger.info(f"Writing CSV file: {output_path}")
            data.to_csv(output_path, encoding=encoding, index=index)
            logger.info(f"Successfully wrote CSV file: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error writing CSV file: {str(e)}")
            raise FileProcessingError(f"Failed to write CSV file: {str(e)}")

    def convert_to_excel(
        self,
        csv_path: str,
        output_path: Optional[str] = None,
        sheet_name: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> str:
        """
        Convert a CSV file to Excel format.

        Args:
            csv_path: Path to the CSV file
            output_path: Optional path for the output Excel file
            sheet_name: Name for the data sheet
            encoding: Optional encoding for reading CSV

        Returns:
            Path to the created Excel file

        Raises:
            FileProcessingError: If conversion fails
        """
        logger.info(f"Converting CSV to Excel: {csv_path}")

        # Read CSV
        df = self.read_csv(csv_path, encoding)

        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(csv_path))[0]
            output_path = os.path.join(self.output_folder, f"{base_name}.xlsx")

        # Write to Excel
        result_path = self.excel_service.write_excel(
            data=df, output_path=output_path, sheet_name=sheet_name
        )

        logger.info(f"Successfully converted CSV to Excel: {result_path}")
        return result_path

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            Dictionary containing file information
        """
        try:
            df = self.read_csv(file_path)

            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
        except Exception as e:
            raise FileProcessingError(f"Failed to get file info: {str(e)}")
