"""
Tests for CSV Service

This module contains unit tests for the CSVService class.
"""

import os
import pytest
import pandas as pd
import tempfile

from app.core.config import Config
from app.services.csv_service import CSVService


class TestCSVService:
    """Test cases for CSVService."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config_content = """
app:
  name: "Test"
  version: "v0.0.1"

file:
  upload_folder: "test_uploads"
  output_folder: "test_outputs"
  supported_encodings:
    - "utf-8"
    - "utf-8-sig"
    - "latin1"

excel:
  default_sheet_name: "Sheet1"
  max_column_width: 50
  include_info_sheet: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        config = Config(config_path)
        yield config

        os.unlink(config_path)

    @pytest.fixture
    def service(self, config):
        """Create CSVService instance."""
        return CSVService(config)

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file for testing."""
        csv_path = tmp_path / "test_data.csv"
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
                "age": [25, 30, 35],
            }
        )
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    def test_read_csv(self, service, sample_csv):
        """Test reading a CSV file."""
        df = service.read_csv(sample_csv)

        assert len(df) == 3
        assert "name" in df.columns
        assert "email" in df.columns
        assert "age" in df.columns

    def test_get_file_info(self, service, sample_csv):
        """Test getting CSV file information."""
        info = service.get_file_info(sample_csv)

        assert info["rows"] == 3
        assert info["columns"] == 3
        assert "name" in info["column_names"]

    def test_convert_to_excel(self, service, sample_csv, tmp_path):
        """Test CSV to Excel conversion."""
        output_path = str(tmp_path / "converted.xlsx")

        result_path = service.convert_to_excel(
            csv_path=sample_csv, output_path=output_path, sheet_name="TestSheet"
        )

        assert os.path.exists(result_path)

        # Verify converted file
        df = pd.read_excel(result_path, sheet_name="TestSheet")
        assert len(df) == 3

    def test_write_csv(self, service, tmp_path):
        """Test writing DataFrame to CSV."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        output_path = str(tmp_path / "output.csv")

        result_path = service.write_csv(df, output_path)

        assert os.path.exists(result_path)

        # Read back and verify
        read_df = pd.read_csv(result_path)
        assert len(read_df) == 3
