"""
Tests for SQL Generation Service

This module contains unit tests for the SQLGenerationService class.
"""

import os
import pytest
import pandas as pd
import tempfile

from app.core.config import Config
from app.services.sql_generation_service import SQLGenerationService
from app.models.request import SQLGenerationRequest, AutoIncrementConfig
from app.models.enums import DatabaseType, SQLAutoIncrementType


class TestSQLGenerationService:
    """Test cases for SQLGenerationService."""

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
  default_batch_size: 1000
  include_transaction: true
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
                "Name": ["Alice", "Bob", "Charlie"],
                "Email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
                "Age": [25, 30, 35],
            }
        )

    def test_generate_sql_postgresql(self, service, sample_dataframe):
        """Test SQL generation for PostgreSQL."""
        request = SQLGenerationRequest(
            table_name="users",
            column_mapping={"name": "Name", "email": "Email", "age": "Age"},
            database_type="postgresql",
            include_transaction=True,
        )

        result = service.generate_sql(sample_dataframe, request)

        assert result["success"]
        assert result["total_rows"] == 3
        assert len(result["statements"]) > 0

        # Check that at least one statement contains INSERT INTO users
        insert_found = any("INSERT INTO users" in stmt for stmt in result["statements"])
        assert insert_found, "No INSERT INTO users statement found"

    def test_generate_sql_with_auto_increment(self, service, sample_dataframe):
        """Test SQL generation with auto-increment."""
        auto_config = AutoIncrementConfig(
            enabled=True,
            column_name="id",
            increment_type="manual_sequence",
            start_value=100,
            sequence_name="users_id_seq",
        )

        request = SQLGenerationRequest(
            table_name="users",
            column_mapping={"name": "Name", "email": "Email"},
            database_type="postgresql",
            auto_increment=auto_config,
            include_transaction=False,
        )

        result = service.generate_sql(sample_dataframe, request)

        assert result["success"]
        # Check that sequence is used
        statements_text = "\n".join(result["statements"])
        assert "nextval" in statements_text or "100" in statements_text

    def test_generate_sql_mysql(self, service, sample_dataframe):
        """Test SQL generation for MySQL."""
        request = SQLGenerationRequest(
            table_name="customers",
            column_mapping={"customer_name": "Name", "customer_email": "Email"},
            database_type="mysql",
            include_transaction=True,
        )

        result = service.generate_sql(sample_dataframe, request)

        assert result["success"]
        assert result["database_type"] == "mysql"

    def test_get_supported_databases(self, service):
        """Test getting supported database list."""
        databases = service.get_supported_databases()

        assert "postgresql" in databases
        assert "mysql" in databases
        assert "sqlite" in databases

    def test_export_sql(self, service, sample_dataframe, tmp_path):
        """Test exporting SQL to file."""
        request = SQLGenerationRequest(
            table_name="test_table",
            column_mapping={"col1": "Name"},
            database_type="postgresql",
        )

        result = service.generate_sql(sample_dataframe, request)
        output_path = str(tmp_path / "test.sql")

        service.export_sql(result["statements"], output_path)

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            content = f.read()
            assert "INSERT INTO test_table" in content
