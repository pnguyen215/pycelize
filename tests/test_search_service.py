"""
Tests for Search Service and Search Endpoints

This module contains unit tests for the search service functionality
and the search API endpoints for Excel and CSV files.
"""

import pytest
import pandas as pd
import tempfile
import os
import json

from app.core.config import Config
from app.services.search_service import SearchService
from app.models.request import SearchCondition, SearchRequest
from app.core.exceptions import ValidationError, FileProcessingError


class TestSearchService:
    """Test cases for SearchService functionality."""

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
        """Create SearchService instance."""
        return SearchService(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "customer_id": ["021201", "021202", "021203", "021204", "021205"],
                "name": ["John Doe", "Jane Smith", "Bob Wilson", "Alice Brown", "Charlie Davis"],
                "email": ["john@test.com", "jane@test.com", "bob@test.com", "alice@test.com", "charlie@test.com"],
                "amount": ["1000", "1500", "800", "2000", "1200"],
                "status": ["active", "inactive", "active", "active", "inactive"],
            }
        )

    def test_apply_search_equals_operator(self, service, sample_dataframe):
        """Test search with equals operator."""
        conditions = [
            SearchCondition(column="customer_id", operator="equals", value="021201")
        ]

        result = service.apply_search(sample_dataframe, conditions, "AND")

        assert len(result) == 1
        assert result.iloc[0]["customer_id"] == "021201"
        assert result.iloc[0]["name"] == "John Doe"

    def test_apply_search_contains_operator(self, service, sample_dataframe):
        """Test search with contains operator."""
        conditions = [
            SearchCondition(column="name", operator="contains", value="smith")
        ]

        result = service.apply_search(sample_dataframe, conditions, "AND")

        assert len(result) == 1
        assert "Smith" in result.iloc[0]["name"]

    def test_apply_search_greater_than_operator(self, service, sample_dataframe):
        """Test search with greater_than operator."""
        conditions = [
            SearchCondition(column="amount", operator="greater_than", value=1000)
        ]

        result = service.apply_search(sample_dataframe, conditions, "AND")

        # Should return rows with amount > 1000
        assert len(result) == 3  # 1500, 2000, 1200
        amounts = result["amount"].astype(float).tolist()
        assert all(amt > 1000 for amt in amounts)

    def test_apply_search_and_logic(self, service, sample_dataframe):
        """Test search with AND logic."""
        conditions = [
            SearchCondition(column="status", operator="equals", value="active"),
            SearchCondition(column="amount", operator="greater_than", value=1000),
        ]

        result = service.apply_search(sample_dataframe, conditions, "AND")

        # Should return rows where status is active AND amount > 1000
        # Alice (2000) is active and > 1000, John (1000) is not > 1000, Bob (800) is not > 1000
        assert len(result) == 1  # Only Alice with 2000
        for _, row in result.iterrows():
            assert row["status"] == "active"
            assert float(row["amount"]) > 1000

    def test_apply_search_or_logic(self, service, sample_dataframe):
        """Test search with OR logic."""
        conditions = [
            SearchCondition(column="customer_id", operator="equals", value="021201"),
            SearchCondition(column="customer_id", operator="equals", value="021202"),
        ]

        result = service.apply_search(sample_dataframe, conditions, "OR")

        # Should return rows where customer_id is 021201 OR 021202
        assert len(result) == 2
        customer_ids = result["customer_id"].tolist()
        assert "021201" in customer_ids
        assert "021202" in customer_ids

    def test_apply_search_starts_with_operator(self, service, sample_dataframe):
        """Test search with starts_with operator."""
        conditions = [
            SearchCondition(column="name", operator="starts_with", value="J")
        ]

        result = service.apply_search(sample_dataframe, conditions, "AND")

        assert len(result) == 2  # John Doe and Jane Smith
        for _, row in result.iterrows():
            assert row["name"].startswith("J")

    def test_apply_search_not_equals_operator(self, service, sample_dataframe):
        """Test search with not_equals operator."""
        conditions = [
            SearchCondition(column="status", operator="not_equals", value="inactive")
        ]

        result = service.apply_search(sample_dataframe, conditions, "AND")

        assert len(result) == 3  # All active rows
        for _, row in result.iterrows():
            assert row["status"] == "active"

    def test_apply_search_empty_conditions(self, service, sample_dataframe):
        """Test search with no conditions raises error."""
        with pytest.raises(ValidationError, match="At least one search condition is required"):
            service.apply_search(sample_dataframe, [], "AND")

    def test_apply_search_invalid_column(self, service, sample_dataframe):
        """Test search with invalid column raises error."""
        conditions = [
            SearchCondition(column="nonexistent_column", operator="equals", value="test")
        ]

        with pytest.raises(ValidationError, match="Column 'nonexistent_column' not found"):
            service.apply_search(sample_dataframe, conditions, "AND")

    def test_apply_search_invalid_logic(self, service, sample_dataframe):
        """Test search with invalid logic raises error."""
        conditions = [
            SearchCondition(column="name", operator="equals", value="test")
        ]

        with pytest.raises(ValidationError, match="Logic must be either 'AND' or 'OR'"):
            service.apply_search(sample_dataframe, conditions, "INVALID")

    def test_get_operator_suggestions_string_type(self, service):
        """Test operator suggestions for string types."""
        operators = service.get_operator_suggestions("object")

        assert "equals" in operators
        assert "contains" in operators
        assert "starts_with" in operators
        assert "not_equals" in operators

    def test_get_operator_suggestions_numeric_type(self, service):
        """Test operator suggestions for numeric types."""
        operators = service.get_operator_suggestions("int64")

        assert "equals" in operators
        assert "greater_than" in operators
        assert "less_than" in operators
        assert "between" in operators

    def test_get_operator_suggestions_float_type(self, service):
        """Test operator suggestions for float types."""
        operators = service.get_operator_suggestions("float64")

        assert "equals" in operators
        assert "greater_than" in operators
        assert "less_than" in operators

    def test_save_search_results_xlsx(self, service, sample_dataframe):
        """Test saving search results to Excel."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name

        try:
            result_path = service.save_search_results(
                sample_dataframe, output_path, "xlsx"
            )

            assert os.path.exists(result_path)
            assert result_path == output_path

            # Verify file can be read
            df = pd.read_excel(result_path)
            assert len(df) == len(sample_dataframe)

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_search_results_csv(self, service, sample_dataframe):
        """Test saving search results to CSV."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            result_path = service.save_search_results(
                sample_dataframe, output_path, "csv"
            )

            assert os.path.exists(result_path)

            # Verify file can be read
            df = pd.read_csv(result_path)
            assert len(df) == len(sample_dataframe)

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_search_results_json(self, service, sample_dataframe):
        """Test saving search results to JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result_path = service.save_search_results(
                sample_dataframe, output_path, "json"
            )

            assert os.path.exists(result_path)

            # Verify file can be read
            with open(result_path, "r") as f:
                data = json.load(f)
            assert len(data) == len(sample_dataframe)

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_search_results_invalid_format(self, service, sample_dataframe):
        """Test saving with invalid format raises error."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises((ValidationError, FileProcessingError)):
                service.save_search_results(
                    sample_dataframe, output_path, "invalid"
                )
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestSearchRequestModel:
    """Test cases for SearchRequest model."""

    def test_search_request_from_dict(self):
        """Test creating SearchRequest from dictionary."""
        data = {
            "conditions": [
                {"column": "name", "operator": "equals", "value": "test"},
                {"column": "amount", "operator": "greater_than", "value": 100},
            ],
            "logic": "AND",
            "output_format": "xlsx",
            "output_filename": "results.xlsx",
        }

        request = SearchRequest.from_dict(data)

        assert len(request.conditions) == 2
        assert request.logic == "AND"
        assert request.output_format == "xlsx"
        assert request.output_filename == "results.xlsx"

    def test_search_request_default_values(self):
        """Test SearchRequest with default values."""
        data = {
            "conditions": [
                {"column": "name", "operator": "equals", "value": "test"}
            ]
        }

        request = SearchRequest.from_dict(data)

        assert request.logic == "AND"
        assert request.output_format == "xlsx"
        assert request.output_filename is None

    def test_search_condition_from_dict(self):
        """Test creating SearchCondition from dictionary."""
        data = {
            "column": "name",
            "operator": "equals",
            "value": "test"
        }

        condition = SearchCondition.from_dict(data)

        assert condition.column == "name"
        assert condition.operator == "equals"
        assert condition.value == "test"
