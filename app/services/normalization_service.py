"""
Normalization Service Implementation

This module provides data normalization functionality using
the Strategy pattern for extensible normalization operations.
"""

from typing import Any, Dict, List, Tuple
from datetime import datetime
import pandas as pd

from app.core.config import Config
from app.core.exceptions import NormalizationError
from app.core.logging import get_logger
from app.models.enums import NormalizationType
from app.models.request import NormalizationConfig
from app.factories.normalizer_factory import NormalizerFactory

logger = get_logger(__name__)


class NormalizationService:
    """
    Service for data normalization operations.

    This service applies various normalization strategies to DataFrame columns
    using the Factory and Strategy patterns for extensibility.

    Attributes:
        config: Application configuration
        backup_original: Whether to backup original values
        generate_report: Whether to generate normalization report

    Example:
        >>> service = NormalizationService(config)
        >>> configs = [NormalizationConfig('name', 'uppercase')]
        >>> normalized_df, report = service.normalize(df, configs)
    """

    def __init__(self, config: Config):
        """
        Initialize NormalizationService with configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.backup_original = config.get("normalization.backup_original", False)
        self.generate_report = config.get("normalization.generate_report", True)

    def normalize(
        self, data: pd.DataFrame, normalization_configs: List[NormalizationConfig]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply normalization to DataFrame columns.

        Args:
            data: DataFrame to normalize
            normalization_configs: List of normalization configurations

        Returns:
            Tuple of (normalized DataFrame, normalization report)

        Raises:
            NormalizationError: If normalization fails
        """
        logger.info(f"Starting normalization for {len(normalization_configs)} columns")

        normalized_data = data.copy()
        report = self._init_report(len(data), normalization_configs)

        for config in normalization_configs:
            try:
                column_name = config.column_name

                # Check if column exists
                if column_name not in normalized_data.columns:
                    self._add_warning(report, f"Column '{column_name}' not found")
                    continue

                # Backup original if requested
                if config.backup_original or self.backup_original:
                    backup_name = f"{column_name}_original"
                    normalized_data[backup_name] = data[column_name].copy()

                # Get before statistics
                before_stats = self._get_column_stats(normalized_data[column_name])

                # Create and apply strategy
                strategy = NormalizerFactory.create_from_string(
                    config.normalization_type, config.parameters
                )

                normalized_data[column_name] = strategy.normalize(
                    normalized_data[column_name]
                )

                # Get after statistics
                after_stats = self._get_column_stats(normalized_data[column_name])

                # Record result
                self._record_result(
                    report,
                    column_name,
                    config.normalization_type,
                    before_stats,
                    after_stats,
                    config.parameters,
                )

                logger.debug(
                    f"Normalized column '{column_name}' using {config.normalization_type}"
                )

            except Exception as e:
                error_msg = f"Error normalizing '{config.column_name}': {str(e)}"
                logger.error(error_msg)
                self._add_error(report, error_msg)

        report["completed_at"] = datetime.now().isoformat()
        report["success"] = len(report["errors"]) == 0

        logger.info(
            f"Normalization completed. "
            f"Processed: {len(report['columns_processed'])}, "
            f"Errors: {len(report['errors'])}"
        )

        return normalized_data, report

    def get_available_normalizations(self) -> Dict[str, str]:
        """
        Get all available normalization types with descriptions.

        Returns:
            Dictionary mapping type names to descriptions
        """
        return NormalizerFactory.get_available_types()

    def _init_report(
        self, total_rows: int, configs: List[NormalizationConfig]
    ) -> Dict[str, Any]:
        """Initialize normalization report."""
        return {
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "success": False,
            "total_rows": total_rows,
            "requested_normalizations": [
                {
                    "column": c.column_name,
                    "type": c.normalization_type,
                    "parameters": c.parameters,
                }
                for c in configs
            ],
            "columns_processed": [],
            "errors": [],
            "warnings": [],
        }

    def _get_column_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for a column."""
        return {
            "total_values": len(series),
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique()),
            "data_type": str(series.dtype),
        }

    def _record_result(
        self,
        report: Dict[str, Any],
        column_name: str,
        normalization_type: str,
        before_stats: Dict[str, Any],
        after_stats: Dict[str, Any],
        parameters: Dict[str, Any],
    ) -> None:
        """Record normalization result in report."""
        report["columns_processed"].append(
            {
                "column_name": column_name,
                "normalization_type": normalization_type,
                "parameters": parameters,
                "before_stats": before_stats,
                "after_stats": after_stats,
                "success": True,
            }
        )

    def _add_error(self, report: Dict[str, Any], message: str) -> None:
        """Add error to report."""
        report["errors"].append(
            {"message": message, "timestamp": datetime.now().isoformat()}
        )

    def _add_warning(self, report: Dict[str, Any], message: str) -> None:
        """Add warning to report."""
        report["warnings"].append(
            {"message": message, "timestamp": datetime.now().isoformat()}
        )
