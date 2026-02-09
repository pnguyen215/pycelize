"""
Tests for Enhanced Template Syntax in SQL and JSON Generation

This module tests the enhanced template syntax features in both
SQL and JSON generation services.
"""

import os
import json
import tempfile

import pytest
import pandas as pd

from app.core.config import Config
from app.services.sql_generation_service import SQLGenerationService
from app.services.json_generation_service import JSONGenerationService
from app.models.request import AutoIncrementConfig


class TestEnhancedTemplateSyntax:
    """Test cases for enhanced template syntax."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config_content = """
app:
  name: "Test"

file:
  output_folder: "test_outputs"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        config = Config(config_path)
        yield config

        os.unlink(config_path)

    @pytest.fixture
    def sql_service(self, config):
        """Create SQLGenerationService instance."""
        return SQLGenerationService(config)

    @pytest.fixture
    def json_service(self, config):
        """Create JSONGenerationService instance."""
        return JSONGenerationService(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame with various data types."""
        return pd.DataFrame(
            {
                "ID": ["1", "2", "3"],
                "Name": ["Alice", "Bob", "Charlie"],
                "Age": ["25", "30", "35"],
                "Score": ["95.5", "88.0", "92.3"],
                "Active": ["true", "false", "true"],
                "Email": ["alice@test.com", None, "charlie@test.com"],
                "CreatedAt": ["2024-01-15", "2024-02-20", "2024-03-10"],
            }
        )

    @pytest.fixture
    def output_file(self):
        """Create a temporary output file path."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_sql_template_with_int_conversion(self, sql_service, sample_dataframe):
        """Test SQL template with integer type conversion."""
        template = "INSERT INTO users (id, name) VALUES ({id:int}, {name});"
        column_mapping = {"id": "ID", "name": "Name"}

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # ID should be unquoted integer
        assert "VALUES (1, 'Alice')" in statements[0]
        assert "VALUES (2, 'Bob')" in statements[1]

    def test_sql_template_with_float_conversion(self, sql_service, sample_dataframe):
        """Test SQL template with float type conversion."""
        template = "UPDATE scores SET score = {score:float} WHERE id = {id:int};"
        column_mapping = {"id": "ID", "score": "Score"}

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # Score should be unquoted float
        assert "score = 95.5" in statements[0]
        assert "score = 88.0" in statements[1]

    def test_sql_template_with_bool_conversion(self, sql_service, sample_dataframe):
        """Test SQL template with boolean type conversion."""
        template = "UPDATE users SET active = {active:bool} WHERE id = {id:int};"
        column_mapping = {"id": "ID", "active": "Active"}

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # Boolean should be TRUE/FALSE
        assert "active = TRUE" in statements[0]
        assert "active = FALSE" in statements[1]

    def test_sql_template_with_datetime_conversion(self, sql_service, sample_dataframe):
        """Test SQL template with datetime type conversion."""
        template = "INSERT INTO logs (id, created_at) VALUES ({id:int}, {created:datetime});"
        column_mapping = {"id": "ID", "created": "CreatedAt"}

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # Datetime should be quoted string
        assert "'2024-01-15'" in statements[0]
        assert "'2024-02-20'" in statements[1]

    def test_sql_template_with_default_value(self, sql_service, sample_dataframe):
        """Test SQL template with default value for NULL."""
        template = "INSERT INTO users (id, email) VALUES ({id:int}, {email|no-email@example.com});"
        column_mapping = {"id": "ID", "email": "Email"}

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # First row has email
        assert "'alice@test.com'" in statements[0]
        # Second row should use default
        assert "'no-email@example.com'" in statements[1]
        # Third row has email
        assert "'charlie@test.com'" in statements[2]

    def test_sql_template_with_null_handling(self, sql_service, sample_dataframe):
        """Test SQL template with NULL value handling."""
        template = "INSERT INTO users (id, email) VALUES ({id:int}, {email});"
        column_mapping = {"id": "ID", "email": "Email"}

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # Second row email is None, should be NULL
        assert "VALUES (2, NULL)" in statements[1]

    def test_sql_template_mixed_types(self, sql_service, sample_dataframe):
        """Test SQL template with multiple type conversions."""
        template = (
            "INSERT INTO users (id, name, age, score, active) "
            "VALUES ({id:int}, {name}, {age:int}, {score:float}, {active:bool});"
        )
        column_mapping = {
            "id": "ID",
            "name": "Name",
            "age": "Age",
            "score": "Score",
            "active": "Active",
        }

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # First row should have all types properly converted
        assert "VALUES (1, 'Alice', 25, 95.5, TRUE)" in statements[0]

    def test_json_template_with_int_conversion(
        self, json_service, sample_dataframe, output_file
    ):
        """Test JSON template with integer type conversion producing native JSON int."""
        template = {"id": "{id:int}", "name": "{name}"}
        column_mapping = {"id": "ID", "name": "Name"}

        result = json_service.generate_json_with_template(
            sample_dataframe,
            template,
            column_mapping,
            output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # ID should be native int in JSON (not string)
        assert json_data[0]["id"] == 1
        assert isinstance(json_data[0]["id"], int)
        assert json_data[1]["id"] == 2
        assert isinstance(json_data[1]["id"], int)

    def test_json_template_with_float_conversion(
        self, json_service, sample_dataframe, output_file
    ):
        """Test JSON template with float type conversion producing native JSON float."""
        template = {"id": "{id:int}", "score": "{score:float}"}
        column_mapping = {"id": "ID", "score": "Score"}

        result = json_service.generate_json_with_template(
            sample_dataframe,
            template,
            column_mapping,
            output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Score should be native float in JSON (not string)
        assert json_data[0]["score"] == 95.5
        assert isinstance(json_data[0]["score"], float)
        assert json_data[1]["score"] == 88.0
        assert isinstance(json_data[1]["score"], float)

    def test_json_template_with_bool_conversion(
        self, json_service, sample_dataframe, output_file
    ):
        """Test JSON template with boolean type conversion producing native JSON bool."""
        template = {"id": "{id:int}", "active": "{active:bool}"}
        column_mapping = {"id": "ID", "active": "Active"}

        result = json_service.generate_json_with_template(
            sample_dataframe,
            template,
            column_mapping,
            output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Boolean should be native bool in JSON (not string)
        assert json_data[0]["active"] is True
        assert isinstance(json_data[0]["active"], bool)
        assert json_data[1]["active"] is False
        assert isinstance(json_data[1]["active"], bool)

    def test_json_template_with_datetime_conversion(
        self, json_service, sample_dataframe, output_file
    ):
        """Test JSON template with datetime type conversion."""
        template = {"id": "{id:int}", "created_at": "{created:datetime}"}
        column_mapping = {"id": "ID", "created": "CreatedAt"}

        result = json_service.generate_json_with_template(
            sample_dataframe,
            template,
            column_mapping,
            output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Datetime should be string
        assert json_data[0]["created_at"] == "2024-01-15"
        assert json_data[1]["created_at"] == "2024-02-20"

    def test_json_template_with_default_value(
        self, json_service, sample_dataframe, output_file
    ):
        """Test JSON template with default value for NULL."""
        template = {"id": "{id:int}", "email": "{email|no-email}"}
        column_mapping = {"id": "ID", "email": "Email"}

        result = json_service.generate_json_with_template(
            sample_dataframe,
            template,
            column_mapping,
            output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # First row has email
        assert json_data[0]["email"] == "alice@test.com"
        # Second row should use default
        assert json_data[1]["email"] == "no-email"
        # Third row has email
        assert json_data[2]["email"] == "charlie@test.com"

    def test_json_template_mixed_types(
        self, json_service, sample_dataframe, output_file
    ):
        """Test JSON template with multiple type conversions producing native JSON types."""
        template = {
            "user": {
                "id": "{id:int}",
                "name": "{name}",
                "age": "{age:int}",
            },
            "stats": {
                "score": "{score:float}",
                "active": "{active:bool}",
            },
        }
        column_mapping = {
            "id": "ID",
            "name": "Name",
            "age": "Age",
            "score": "Score",
            "active": "Active",
        }

        result = json_service.generate_json_with_template(
            sample_dataframe,
            template,
            column_mapping,
            output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # First record should have all types properly converted to native JSON types
        assert json_data[0]["user"]["id"] == 1
        assert isinstance(json_data[0]["user"]["id"], int)
        
        assert json_data[0]["user"]["name"] == "Alice"
        assert isinstance(json_data[0]["user"]["name"], str)
        
        assert json_data[0]["user"]["age"] == 25
        assert isinstance(json_data[0]["user"]["age"], int)
        
        assert json_data[0]["stats"]["score"] == 95.5
        assert isinstance(json_data[0]["stats"]["score"], float)
        
        assert json_data[0]["stats"]["active"] is True
        assert isinstance(json_data[0]["stats"]["active"], bool)

    def test_sql_template_with_special_chars_and_type(self, sql_service):
        """Test SQL template with special characters and type conversion."""
        df = pd.DataFrame(
            {
                "ID": ["1", "2"],
                "Name": ["O'Brien", "D'Angelo"],
                "Score": ["95.5", "88.0"],
            }
        )

        template = "INSERT INTO users (id, name, score) VALUES ({id:int}, {name}, {score:float});"
        column_mapping = {"id": "ID", "name": "Name", "score": "Score"}

        statements = sql_service.generate_custom_sql(df, template, column_mapping)

        # Special characters should be escaped
        assert "VALUES (1, 'O''Brien', 95.5)" in statements[0]
        assert "VALUES (2, 'D''Angelo', 88.0)" in statements[1]

    def test_complex_update_statement_with_types(self, sql_service, sample_dataframe):
        """Test complex UPDATE statement with multiple type conversions."""
        template = (
            "UPDATE users SET age = {age:int}, score = {score:float}, "
            "active = {active:bool}, email = {email|unknown@example.com} "
            "WHERE id = {id:int};"
        )
        column_mapping = {
            "id": "ID",
            "age": "Age",
            "score": "Score",
            "active": "Active",
            "email": "Email",
        }

        statements = sql_service.generate_custom_sql(
            sample_dataframe, template, column_mapping
        )

        assert len(statements) == 3
        # First row
        assert "age = 25" in statements[0]
        assert "score = 95.5" in statements[0]
        assert "active = TRUE" in statements[0]
        assert "email = 'alice@test.com'" in statements[0]
        # Second row with NULL email should use default
        assert "email = 'unknown@example.com'" in statements[1]
