"""
Tests for Response Builder

This module contains unit tests for the ResponseBuilder class.
"""

import pytest
from app.builders.response_builder import ResponseBuilder


class TestResponseBuilder:
    """Test cases for ResponseBuilder."""

    def test_basic_response(self):
        """Test building a basic response."""
        response = (
            ResponseBuilder()
            .with_data({"id": 1, "name": "Test"})
            .with_message("Success")
            .with_status_code(200)
            .build()
        )

        assert response["status_code"] == 200
        assert response["message"] == "Success"
        assert response["data"]["id"] == 1
        assert "meta" in response
        assert "request_id" in response["meta"]

    def test_response_with_total(self):
        """Test response with total count."""
        response = ResponseBuilder().with_data([1, 2, 3]).with_total(100).build()

        assert response["total"] == 100

    def test_success_convenience_method(self):
        """Test success convenience method."""
        response = ResponseBuilder.success(
            data={"key": "value"}, message="Operation successful", total=5
        )

        assert response["status_code"] == 200
        assert response["message"] == "Operation successful"
        assert response["total"] == 5

    def test_error_convenience_method(self):
        """Test error convenience method."""
        response = ResponseBuilder.error(
            message="Something went wrong",
            status_code=500,
            details={"error_code": "ERR001"},
        )

        assert response["status_code"] == 500
        assert response["message"] == "Something went wrong"

    def test_meta_information(self):
        """Test meta information in response."""
        response = (
            ResponseBuilder().with_api_version("v2.0.0").with_locale("fr_FR").build()
        )

        assert response["meta"]["api_version"] == "v2.0.0"
        assert response["meta"]["locale"] == "fr_FR"
        assert "requested_time" in response["meta"]
