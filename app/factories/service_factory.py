"""
Service Factory Implementation

This module implements the Factory Design Pattern for creating
service instances with proper configuration.
"""

from typing import Optional

from app.core.config import Config
from app.services.excel_service import ExcelService
from app.services.csv_service import CSVService
from app.services.normalization_service import NormalizationService
from app.services.sql_generation_service import SQLGenerationService
from app.services.binding_service import BindingService


class ServiceFactory:
    """
    Factory class for creating service instances.

    This factory provides a centralized way to create service instances
    with proper configuration injection.

    Example:
        >>> factory = ServiceFactory(config)
        >>> excel_service = factory.create_excel_service()
        >>> csv_service = factory.create_csv_service()

    Attributes:
        _config: Application configuration instance
    """

    def __init__(self, config: Config):
        """
        Initialize ServiceFactory with configuration.

        Args:
            config: Application configuration instance
        """
        self._config = config

    def create_excel_service(self) -> ExcelService:
        """
        Create an ExcelService instance.

        Returns:
            Configured ExcelService instance
        """
        return ExcelService(self._config)

    def create_csv_service(self) -> CSVService:
        """
        Create a CSVService instance.

        Returns:
            Configured CSVService instance
        """
        return CSVService(self._config)

    def create_normalization_service(self) -> NormalizationService:
        """
        Create a NormalizationService instance.

        Returns:
            Configured NormalizationService instance
        """
        return NormalizationService(self._config)

    def create_sql_generation_service(self) -> SQLGenerationService:
        """
        Create a SQLGenerationService instance.

        Returns:
            Configured SQLGenerationService instance
        """
        return SQLGenerationService(self._config)

    def create_binding_service(self) -> BindingService:
        """
        Create a BindingService instance.

        Returns:
            Configured BindingService instance
        """
        return BindingService(self._config)
