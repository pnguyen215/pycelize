"""
Tests for JSON Generation Service

This module contains unit tests for the JSONGenerationService class.
"""

import os
import json
import pytest
import pandas as pd
import tempfile
from datetime import datetime

from app.core.config import Config
from app.services.json_generation_service import JSONGenerationService
from app.core.exceptions import ValidationError, FileProcessingError


class TestJSONGenerationService:
    """Test cases for JSONGenerationService."""

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
    def service(self, config):
        """Create JSONGenerationService instance."""
        return JSONGenerationService(config)

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

    @pytest.fixture
    def output_file(self):
        """Create a temporary output file path."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_generate_json_standard(self, service, sample_dataframe, output_file):
        """Test standard JSON generation with column mapping."""
        column_mapping = {
            "Name": "full_name",
            "Email": "email",
            "Age": "age",
        }

        result = service.generate_json(
            data=sample_dataframe,
            column_mapping=column_mapping,
            output_path=output_file,
            pretty_print=True,
            null_handling="include",
            array_wrapper=True,
        )

        # Verify result structure
        assert result["output_path"] == output_file
        assert result["total_records"] == 3
        assert result["file_size"] > 0
        assert "timestamp" in result

        # Verify JSON file contents
        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert isinstance(json_data, list)
        assert len(json_data) == 3
        assert json_data[0]["full_name"] == "Alice"
        assert json_data[0]["email"] == "alice@test.com"
        assert json_data[0]["age"] == 25

    def test_generate_json_no_array_wrapper(self, service, sample_dataframe, output_file):
        """Test JSON generation without array wrapper."""
        column_mapping = {"Name": "name"}
        
        # Use single row
        df = sample_dataframe.head(1)
        
        result = service.generate_json(
            data=df,
            column_mapping=column_mapping,
            output_path=output_file,
            array_wrapper=False,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Should be a single object, not an array
        assert isinstance(json_data, dict)
        assert json_data["name"] == "Alice"

    def test_generate_json_null_handling_exclude(self, service, output_file):
        """Test JSON generation with null value exclusion."""
        df = pd.DataFrame(
            {
                "Name": ["Alice", "Bob"],
                "Email": ["alice@test.com", None],
                "Age": [25, None],
            }
        )

        column_mapping = {"Name": "name", "Email": "email", "Age": "age"}

        result = service.generate_json(
            data=df,
            column_mapping=column_mapping,
            output_path=output_file,
            null_handling="exclude",
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # First record should have all fields
        assert "email" in json_data[0]
        assert "age" in json_data[0]

        # Second record should not have null fields
        assert "email" not in json_data[1]
        assert "age" not in json_data[1]

    def test_generate_json_null_handling_default(self, service, output_file):
        """Test JSON generation with default null handling."""
        df = pd.DataFrame(
            {
                "Name": ["Alice"],
                "Email": [None],
            }
        )

        column_mapping = {"Name": "name", "Email": "email"}

        result = service.generate_json(
            data=df,
            column_mapping=column_mapping,
            output_path=output_file,
            null_handling="default",
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Null should be replaced with empty string
        assert json_data[0]["email"] == ""

    def test_generate_json_empty_dataframe(self, service, output_file):
        """Test JSON generation with empty DataFrame."""
        df = pd.DataFrame()

        result = service.generate_json(
            data=df,
            column_mapping={},
            output_path=output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert json_data == []
        assert result["total_records"] == 0

    def test_generate_json_missing_column(self, service, sample_dataframe, output_file):
        """Test JSON generation with missing column in mapping."""
        column_mapping = {"NonExistent": "field"}

        with pytest.raises(ValidationError) as exc_info:
            service.generate_json(
                data=sample_dataframe,
                column_mapping=column_mapping,
                output_path=output_file,
            )

        assert "not found in data" in str(exc_info.value)

    def test_generate_json_with_template_basic(self, service, sample_dataframe, output_file):
        """Test template-based JSON generation with basic template."""
        template = {
            "user": {
                "id": "{user_id}",
                "name": "{full_name}",
            },
            "contact": {
                "email": "{email}",
            },
        }

        column_mapping = {
            "user_id": "Age",  # Using Age as ID for testing
            "full_name": "Name",
            "email": "Email",
        }

        result = service.generate_json_with_template(
            data=sample_dataframe,
            template=template,
            column_mapping=column_mapping,
            output_path=output_file,
            aggregation_mode="array",
        )

        assert result["total_records"] == 3

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert isinstance(json_data, list)
        assert len(json_data) == 3
        assert json_data[0]["user"]["name"] == "Alice"
        assert json_data[0]["contact"]["email"] == "alice@test.com"

    def test_generate_json_with_template_string(self, service, sample_dataframe, output_file):
        """Test template-based generation with string template."""
        template_str = '{"name": "{full_name}", "email": "{email}"}'

        column_mapping = {
            "full_name": "Name",
            "email": "Email",
        }

        result = service.generate_json_with_template(
            data=sample_dataframe,
            template=template_str,
            column_mapping=column_mapping,
            output_path=output_file,
        )

        assert result["total_records"] == 3

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert json_data[0]["name"] == "Alice"
        assert json_data[0]["email"] == "alice@test.com"

    def test_generate_json_with_template_nested_mode(self, service, sample_dataframe, output_file):
        """Test template-based generation with nested aggregation mode."""
        template = {"name": "{name}"}
        column_mapping = {"name": "Name"}

        result = service.generate_json_with_template(
            data=sample_dataframe,
            template=template,
            column_mapping=column_mapping,
            output_path=output_file,
            aggregation_mode="nested",
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert isinstance(json_data, dict)
        assert "items" in json_data
        assert "count" in json_data
        assert json_data["count"] == 3
        assert len(json_data["items"]) == 3

    def test_generate_json_with_template_single_mode(self, service, sample_dataframe, output_file):
        """Test template-based generation with single aggregation mode."""
        template = {"name": "{name}"}
        column_mapping = {"name": "Name"}
        
        # Use single row
        df = sample_dataframe.head(1)

        result = service.generate_json_with_template(
            data=df,
            template=template,
            column_mapping=column_mapping,
            output_path=output_file,
            aggregation_mode="single",
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Should be a single object
        assert isinstance(json_data, dict)
        assert json_data["name"] == "Alice"

    def test_generate_json_with_template_type_conversion(self, service, output_file):
        """Test template with type conversion."""
        df = pd.DataFrame(
            {
                "ID": ["1", "2"],
                "Score": ["95.5", "88.0"],
                "Active": ["true", "false"],
            }
        )

        template = {
            "id": "{id:int}",
            "score": "{score:float}",
            "active": "{active:bool}",
        }

        column_mapping = {
            "id": "ID",
            "score": "Score",
            "active": "Active",
        }

        result = service.generate_json_with_template(
            data=df,
            template=template,
            column_mapping=column_mapping,
            output_path=output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Values should still be strings after placeholder substitution
        # (Type conversion happens during substitution but result is string in template)
        assert json_data[0]["id"] == "1"
        assert json_data[0]["score"] == "95.5"

    def test_generate_json_with_template_default_values(self, service, output_file):
        """Test template with default values for null."""
        df = pd.DataFrame(
            {
                "Name": ["Alice", "Bob"],
                "Email": ["alice@test.com", None],
            }
        )

        template = {
            "name": "{name}",
            "email": "{email|no-email}",
        }

        column_mapping = {
            "name": "Name",
            "email": "Email",
        }

        result = service.generate_json_with_template(
            data=df,
            template=template,
            column_mapping=column_mapping,
            output_path=output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert json_data[0]["email"] == "alice@test.com"
        # When value is None, default is used
        assert json_data[1]["email"] == "no-email"

    def test_generate_json_with_template_invalid_json(self, service, sample_dataframe, output_file):
        """Test template-based generation with invalid JSON template."""
        template_str = "invalid json {{"

        column_mapping = {"name": "Name"}

        with pytest.raises(ValidationError) as exc_info:
            service.generate_json_with_template(
                data=sample_dataframe,
                template=template_str,
                column_mapping=column_mapping,
                output_path=output_file,
            )

        assert "Invalid JSON template" in str(exc_info.value)

    def test_generate_json_with_template_missing_column(self, service, sample_dataframe, output_file):
        """Test template-based generation with missing column."""
        template = {"name": "{name}"}
        column_mapping = {"name": "NonExistent"}

        with pytest.raises(ValidationError) as exc_info:
            service.generate_json_with_template(
                data=sample_dataframe,
                template=template,
                column_mapping=column_mapping,
                output_path=output_file,
            )

        assert "not found in data" in str(exc_info.value)

    def test_generate_json_with_template_empty_dataframe(self, service, output_file):
        """Test template-based generation with empty DataFrame."""
        df = pd.DataFrame()
        template = {"name": "{name}"}
        column_mapping = {}

        result = service.generate_json_with_template(
            data=df,
            template=template,
            column_mapping=column_mapping,
            output_path=output_file,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert json_data == []
        assert result["total_records"] == 0

    def test_generate_json_pretty_print_false(self, service, sample_dataframe, output_file):
        """Test JSON generation without pretty print."""
        column_mapping = {"Name": "name"}

        service.generate_json(
            data=sample_dataframe,
            column_mapping=column_mapping,
            output_path=output_file,
            pretty_print=False,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Should be compact (no indentation)
        assert "\n  " not in content

    def test_substitute_placeholders_dict(self, service):
        """Test placeholder substitution in dictionary."""
        template = {
            "user": "{name}",
            "age": "{age}",
        }
        row_data = {"name": "Alice", "age": 25}

        result = service._substitute_placeholders(template, row_data, {})

        assert result["user"] == "Alice"
        assert result["age"] == "25"

    def test_substitute_placeholders_list(self, service):
        """Test placeholder substitution in list."""
        template = ["{name}", "{age}"]
        row_data = {"name": "Alice", "age": 25}

        result = service._substitute_placeholders(template, row_data, {})

        assert result[0] == "Alice"
        assert result[1] == "25"

    def test_substitute_placeholders_nested(self, service):
        """Test placeholder substitution in nested structure."""
        template = {
            "user": {
                "personal": {
                    "name": "{name}",
                },
                "contact": {
                    "email": "{email}",
                },
            },
        }
        row_data = {"name": "Alice", "email": "alice@test.com"}

        result = service._substitute_placeholders(template, row_data, {})

        assert result["user"]["personal"]["name"] == "Alice"
        assert result["user"]["contact"]["email"] == "alice@test.com"

    def test_handle_null_values_include(self, service):
        """Test null handling with include strategy."""
        data = {"name": "Alice", "email": None}

        result = service._handle_null_values(data, "include")

        assert result["name"] == "Alice"
        assert result["email"] is None

    def test_handle_null_values_exclude(self, service):
        """Test null handling with exclude strategy."""
        data = {"name": "Alice", "email": None}

        result = service._handle_null_values(data, "exclude")

        assert result["name"] == "Alice"
        assert "email" not in result

    def test_handle_null_values_default(self, service):
        """Test null handling with default strategy."""
        data = {"name": "Alice", "email": None}

        result = service._handle_null_values(data, "default")

        assert result["name"] == "Alice"
        assert result["email"] == ""
