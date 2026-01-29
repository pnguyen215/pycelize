"""
Tests for Factory Classes

This module contains unit tests for factory pattern implementations.
"""

import pytest
import pandas as pd

from app.factories.normalizer_factory import NormalizerFactory
from app.models.enums import NormalizationType
from app.strategies.normalization_strategies import (
    UppercaseStrategy,
    LowercaseStrategy,
    TrimWhitespaceStrategy,
)


class TestNormalizerFactory:
    """Test cases for NormalizerFactory."""

    def test_create_uppercase_strategy(self):
        """Test creating uppercase strategy."""
        strategy = NormalizerFactory.create(NormalizationType.UPPERCASE)

        assert isinstance(strategy, UppercaseStrategy)
        assert strategy.name == "uppercase"

    def test_create_from_string(self):
        """Test creating strategy from string."""
        strategy = NormalizerFactory.create_from_string("lowercase")

        assert isinstance(strategy, LowercaseStrategy)

    def test_create_with_parameters(self):
        """Test creating strategy with parameters."""
        params = {"decimals": 3}
        strategy = NormalizerFactory.create(
            NormalizationType.ROUND_DECIMAL, parameters=params
        )

        assert strategy.parameters["decimals"] == 3

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError):
            NormalizerFactory.create_from_string("invalid_type")

    def test_get_available_types(self):
        """Test getting available normalization types."""
        types = NormalizerFactory.get_available_types()

        assert "uppercase" in types
        assert "lowercase" in types
        assert "trim_whitespace" in types
        assert len(types) > 10  # Should have many types

    def test_strategy_normalize(self):
        """Test that created strategy can normalize data."""
        strategy = NormalizerFactory.create(NormalizationType.UPPERCASE)
        series = pd.Series(["hello", "world"])

        result = strategy.normalize(series)

        assert result.iloc[0] == "HELLO"
        assert result.iloc[1] == "WORLD"
