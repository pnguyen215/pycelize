"""
Tests for New Excel and SQL Endpoints

This module contains unit tests for the new extract-columns-to-file,
generate-to-text, and generate-custom-to-text endpoints.
"""

import pytest
import pandas as pd
import tempfile
import os
import json

from app.core.config import Config
from app.services.excel_service import ExcelService
from app.services.sql_generation_service import SQLGenerationService
from app.models.request import AutoIncrementConfig


class TestExcelExtractToFile:
    """Test cases for extract_columns_to_file functionality."""

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

excel:
  default_sheet_name: "Sheet1"
  max_column_width: 50
  include_info_sheet: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        config = Config(config_path)
        yield config
        os.unlink(config_path)

    @pytest.fixture
    def service(self, config):
        """Create ExcelService instance."""
        return ExcelService(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "Name": ["John Doe", "Jane Smith", "Bob Wilson", "John Doe"],
                "Email": ["john@test.com", "jane@test.com", "bob@test.com", "john@test.com"],
                "Phone": ["555-1234", "555-5678", "555-9012", "555-1234"],
                "Age": [30, 25, 35, 30],
            }
        )

    def test_extract_columns_to_file(self, service, sample_dataframe):
        """Test extracting columns to file."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name

        try:
            result_path = service.extract_columns_to_file(
                data=sample_dataframe,
                columns=["Name", "Email"],
                output_path=output_path,
                remove_duplicates=False,
            )

            assert os.path.exists(result_path)
            assert result_path == output_path

            # Read the file and verify contents
            df = pd.read_excel(result_path, engine='openpyxl')
            assert len(df.columns) == 2
            assert "Name" in df.columns
            assert "Email" in df.columns
            assert len(df) == 4  # No duplicates removed

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_extract_columns_with_duplicates_removed(self, service, sample_dataframe):
        """Test extracting columns with duplicate removal."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name

        try:
            result_path = service.extract_columns_to_file(
                data=sample_dataframe,
                columns=["Name", "Email"],
                output_path=output_path,
                remove_duplicates=True,
            )

            assert os.path.exists(result_path)

            # Read the file and verify duplicate removal
            df = pd.read_excel(result_path, engine='openpyxl')
            assert len(df) == 3  # One duplicate removed

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_extract_nonexistent_column(self, service, sample_dataframe):
        """Test extracting non-existent column raises error."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(Exception):  # Should raise ValidationError
                service.extract_columns_to_file(
                    data=sample_dataframe,
                    columns=["Name", "NonExistentColumn"],
                    output_path=output_path,
                    remove_duplicates=False,
                )
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestSQLGenerationCustom:
    """Test cases for custom SQL generation."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config_content = """
app:
  name: "Test"

file:
  output_folder: "test_outputs"

sql:
  supported_databases:
    - "postgresql"
    - "mysql"
    - "sqlite"
  default_database: "postgresql"
  default_batch_size: 1000
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        config = Config(config_path)
        yield config
        os.unlink(config_path)

    @pytest.fixture
    def service(self, config):
        """Create SQLGenerationService instance."""
        return SQLGenerationService(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "Name": ["John Doe", "Jane Smith"],
                "Email": ["john@test.com", "jane@test.com"],
            }
        )

    def test_generate_custom_sql(self, service, sample_dataframe):
        """Test custom SQL generation with template."""
        template = "INSERT INTO users (id, name, email) VALUES ({auto_id}, {name}, {email});"
        column_mapping = {"name": "Name", "email": "Email"}
        auto_config = AutoIncrementConfig(
            enabled=True,
            column_name="id",
            start_value=100,
        )

        statements = service.generate_custom_sql(
            data=sample_dataframe,
            template=template,
            column_mapping=column_mapping,
            auto_increment=auto_config,
        )

        assert len(statements) == 2
        assert "100" in statements[0]
        assert "101" in statements[1]
        assert "John Doe" in statements[0]
        assert "Jane Smith" in statements[1]

    def test_generate_custom_sql_with_timestamp(self, service, sample_dataframe):
        """Test custom SQL generation with timestamp placeholder."""
        template = "INSERT INTO users (name, created_at) VALUES ({name}, {current_timestamp});"
        column_mapping = {"name": "Name"}

        statements = service.generate_custom_sql(
            data=sample_dataframe,
            template=template,
            column_mapping=column_mapping,
            auto_increment=None,
        )

        assert len(statements) == 2
        assert "CURRENT_TIMESTAMP" in statements[0]
        assert "CURRENT_TIMESTAMP" in statements[1]

    def test_generate_custom_sql_missing_column(self, service, sample_dataframe):
        """Test custom SQL generation with missing column."""
        template = "INSERT INTO users (name, phone) VALUES ({name}, {phone});"
        column_mapping = {"name": "Name", "phone": "Phone"}  # Phone doesn't exist

        with pytest.raises(Exception):  # Should raise SQLGenerationError
            service.generate_custom_sql(
                data=sample_dataframe,
                template=template,
                column_mapping=column_mapping,
                auto_increment=None,
            )

    def test_generate_custom_sql_with_quotes(self, service):
        """Test custom SQL generation handles quotes properly."""
        df = pd.DataFrame(
            {
                "Name": ["O'Brien", "Jane's Name"],
            }
        )

        template = "INSERT INTO users (name) VALUES ({name});"
        column_mapping = {"name": "Name"}

        statements = service.generate_custom_sql(
            data=df,
            template=template,
            column_mapping=column_mapping,
            auto_increment=None,
        )

        # Single quotes should be escaped
        assert "O''Brien" in statements[0]
        assert "Jane''s Name" in statements[1]

    def test_generate_custom_sql_with_null_values(self, service):
        """Test custom SQL generation handles NULL values."""
        df = pd.DataFrame(
            {
                "Name": ["John Doe", None],
                "Email": ["john@test.com", "jane@test.com"],
            }
        )

        template = "INSERT INTO users (name, email) VALUES ({name}, {email});"
        column_mapping = {"name": "Name", "email": "Email"}

        statements = service.generate_custom_sql(
            data=df,
            template=template,
            column_mapping=column_mapping,
            auto_increment=None,
        )

        assert "NULL" in statements[1]  # Second row has NULL name
