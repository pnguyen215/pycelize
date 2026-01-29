"""
Tests for Normalization Service

This module contains unit tests for the NormalizationService class.
"""

import pytest
import pandas as pd
import tempfile
import os

from app.core.config import Config
from app.services.normalization_service import NormalizationService
from app.models.request import NormalizationConfig
from app.models.enums import NormalizationType


class TestNormalizationService:
    """Test cases for NormalizationService."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config_content = """
app:
  name: "Test"

normalization:
  enabled: true
  backup_original: false
  generate_report: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        config = Config(config_path)
        yield config
        os.unlink(config_path)

    @pytest.fixture
    def service(self, config):
        """Create NormalizationService instance."""
        return NormalizationService(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "name": ["  john doe  ", "JANE SMITH", "Bob Wilson"],
                "email": ["JOHN@TEST.COM", "jane@test.com", "BOB@TEST.COM"],
                "phone": ["1234567890", "(555) 123-4567", "555.987.6543"],
                "value": [100, 200, 300],
            }
        )

    def test_uppercase_normalization(self, service, sample_dataframe):
        """Test uppercase normalization."""
        configs = [
            NormalizationConfig(column_name="name", normalization_type="uppercase")
        ]

        result_df, report = service.normalize(sample_dataframe, configs)

        assert result_df["name"].iloc[0] == "  JOHN DOE  "
        assert report["success"]

    def test_trim_whitespace_normalization(self, service, sample_dataframe):
        """Test trim whitespace normalization."""
        configs = [
            NormalizationConfig(
                column_name="name", normalization_type="trim_whitespace"
            )
        ]

        result_df, report = service.normalize(sample_dataframe, configs)

        assert result_df["name"].iloc[0] == "john doe"

    def test_email_format_normalization(self, service, sample_dataframe):
        """Test email format normalization."""
        configs = [
            NormalizationConfig(column_name="email", normalization_type="email_format")
        ]

        result_df, report = service.normalize(sample_dataframe, configs)

        assert result_df["email"].iloc[0] == "john@test.com"

    def test_multiple_normalizations(self, service, sample_dataframe):
        """Test applying multiple normalizations."""
        configs = [
            NormalizationConfig(
                column_name="name", normalization_type="trim_whitespace"
            ),
            NormalizationConfig(column_name="name", normalization_type="title_case"),
            NormalizationConfig(column_name="email", normalization_type="lowercase"),
        ]

        result_df, report = service.normalize(sample_dataframe, configs)

        assert result_df["name"].iloc[0] == "John Doe"
        assert report["success"]
        assert len(report["columns_processed"]) == 3

    def test_get_available_normalizations(self, service):
        """Test getting available normalization types."""
        types = service.get_available_normalizations()

        assert "uppercase" in types
        assert "lowercase" in types
        assert "trim_whitespace" in types
