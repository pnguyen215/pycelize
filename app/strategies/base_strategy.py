"""
Base Strategy Interface

This module defines the abstract base class for all normalization strategies,
implementing the Strategy Design Pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd


class NormalizationStrategy(ABC):
    """
    Abstract base class for normalization strategies.

    This class defines the interface that all concrete normalization
    strategies must implement. It follows the Strategy Design Pattern,
    allowing different normalization algorithms to be used interchangeably.

    Subclasses must implement the `normalize` method which takes a
    pandas Series and returns the normalized Series.

    Attributes:
        parameters: Dictionary of strategy-specific parameters

    Example:
        >>> class MyStrategy(NormalizationStrategy):
        ...     def normalize(self, series: pd.Series) -> pd.Series:
        ...         return series.str.upper()
        ...
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_strategy"
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize the normalization strategy.

        Args:
            parameters: Dictionary of strategy-specific parameters
        """
        self.parameters = parameters or {}

    @abstractmethod
    def normalize(self, series: pd.Series) -> pd.Series:
        """
        Apply normalization to a pandas Series.

        This method must be implemented by all concrete strategies.
        It should transform the input Series according to the
        strategy's specific normalization logic.

        Args:
            series: Input pandas Series to normalize

        Returns:
            Normalized pandas Series

        Raises:
            NormalizationError: If normalization fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the strategy name.

        Returns:
            String identifier for the strategy
        """
        pass

    @property
    def description(self) -> str:
        """
        Get a description of what the strategy does.

        Returns:
            Human-readable description of the strategy
        """
        pass
