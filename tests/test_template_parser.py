"""
Tests for Template Parser Utility

This module contains unit tests for the TemplateParser class.
"""

from datetime import datetime

import pytest
import pandas as pd

from app.utils.template_parser import TemplateParser


class TestTemplateParser:
    """Test cases for TemplateParser."""

    def test_parse_placeholder_simple(self):
        """Test parsing simple placeholder."""
        name, type_hint, default = TemplateParser.parse_placeholder("name")
        assert name == "name"
        assert type_hint is None
        assert default is None

    def test_parse_placeholder_with_type(self):
        """Test parsing placeholder with type hint."""
        name, type_hint, default = TemplateParser.parse_placeholder("age:int")
        assert name == "age"
        assert type_hint == "int"
        assert default is None

    def test_parse_placeholder_with_default(self):
        """Test parsing placeholder with default value."""
        name, type_hint, default = TemplateParser.parse_placeholder(
            "email|default@example.com"
        )
        assert name == "email"
        assert type_hint is None
        assert default == "default@example.com"

    def test_parse_placeholder_with_type_and_default(self):
        """Test parsing placeholder with type hint and default value."""
        name, type_hint, default = TemplateParser.parse_placeholder("count:int|0")
        assert name == "count"
        assert type_hint == "int"
        assert default == "0"

    def test_convert_value_int(self):
        """Test converting value to integer."""
        assert TemplateParser.convert_value("42", "int") == 42
        assert TemplateParser.convert_value("42.7", "int") == 42
        assert TemplateParser.convert_value(42, "int") == 42
        assert TemplateParser.convert_value("", "int") is None
        assert TemplateParser.convert_value(None, "int") is None

    def test_convert_value_float(self):
        """Test converting value to float."""
        assert TemplateParser.convert_value("42.5", "float") == 42.5
        assert TemplateParser.convert_value("42", "float") == 42.0
        assert TemplateParser.convert_value(42, "float") == 42.0
        assert TemplateParser.convert_value("", "float") is None
        assert TemplateParser.convert_value(None, "float") is None

    def test_convert_value_bool(self):
        """Test converting value to boolean."""
        assert TemplateParser.convert_value("true", "bool") is True
        assert TemplateParser.convert_value("True", "bool") is True
        assert TemplateParser.convert_value("1", "bool") is True
        assert TemplateParser.convert_value("yes", "bool") is True
        assert TemplateParser.convert_value("false", "bool") is False
        assert TemplateParser.convert_value("False", "bool") is False
        assert TemplateParser.convert_value("0", "bool") is False
        assert TemplateParser.convert_value("no", "bool") is False
        assert TemplateParser.convert_value(1, "bool") is True
        assert TemplateParser.convert_value(0, "bool") is False

    def test_convert_value_datetime(self):
        """Test converting value to datetime string."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = TemplateParser.convert_value(dt, "datetime")
        assert "2024-01-15" in result

        # Test with pandas Timestamp
        pd_ts = pd.Timestamp("2024-01-15 10:30:00")
        result = TemplateParser.convert_value(pd_ts, "datetime")
        assert "2024-01-15" in result

        # Test with string
        result = TemplateParser.convert_value("2024-01-15", "datetime")
        assert result == "2024-01-15"

    def test_convert_value_no_type(self):
        """Test conversion with no type hint."""
        assert TemplateParser.convert_value("hello", None) == "hello"
        assert TemplateParser.convert_value(42, None) == 42

    def test_find_all_placeholders(self):
        """Test finding all placeholders in template."""
        template = "Hello {name}, your age is {age:int} and email is {email|default}"
        placeholders = TemplateParser.find_all_placeholders(template)
        assert len(placeholders) == 3
        assert "name" in placeholders
        assert "age:int" in placeholders
        assert "email|default" in placeholders

    def test_find_all_placeholders_none(self):
        """Test finding placeholders when none exist."""
        template = "Hello world, no placeholders here"
        placeholders = TemplateParser.find_all_placeholders(template)
        assert len(placeholders) == 0

    def test_substitute_value_for_json(self):
        """Test substituting value for JSON (non-SQL)."""
        result = TemplateParser.substitute_value(
            "age: {age}", "age", 25, "int", None, for_sql=False
        )
        assert result == "25"

    def test_substitute_value_for_sql_string(self):
        """Test substituting string value for SQL."""
        result = TemplateParser.substitute_value(
            "name: {name}", "name", "Alice", None, None, for_sql=True
        )
        assert result == "'Alice'"

    def test_substitute_value_for_sql_int(self):
        """Test substituting integer value for SQL."""
        result = TemplateParser.substitute_value(
            "age: {age}", "age", 25, "int", None, for_sql=True
        )
        assert result == "25"

    def test_substitute_value_for_sql_bool(self):
        """Test substituting boolean value for SQL."""
        result = TemplateParser.substitute_value(
            "active: {active}", "active", True, "bool", None, for_sql=True
        )
        assert result == "TRUE"

        result = TemplateParser.substitute_value(
            "active: {active}", "active", False, "bool", None, for_sql=True
        )
        assert result == "FALSE"

    def test_substitute_value_for_sql_null(self):
        """Test substituting NULL value for SQL."""
        result = TemplateParser.substitute_value(
            "email: {email}", "email", None, None, None, for_sql=True
        )
        assert result == "NULL"

    def test_substitute_value_with_default(self):
        """Test substituting value with default when value is None."""
        result = TemplateParser.substitute_value(
            "email: {email}", "email", None, None, "no-email", for_sql=False
        )
        assert result == "no-email"

    def test_substitute_value_sql_escape_quotes(self):
        """Test that SQL values escape single quotes."""
        result = TemplateParser.substitute_value(
            "name: {name}", "name", "O'Brien", None, None, for_sql=True
        )
        assert result == "'O''Brien'"

    def test_substitute_template_basic(self):
        """Test substituting complete template with basic placeholders."""
        template = "Hello {name}, you are {age} years old"
        data = {"name": "Alice", "age": 25}
        result = TemplateParser.substitute_template(template, data, for_sql=False)
        assert result == "Hello Alice, you are 25 years old"

    def test_substitute_template_with_types(self):
        """Test substituting template with type conversions."""
        template = "ID: {id:int}, Score: {score:float}, Active: {active:bool}"
        data = {"id": "42", "score": "95.5", "active": "true"}
        result = TemplateParser.substitute_template(template, data, for_sql=False)
        assert "42" in result
        assert "95.5" in result
        assert "True" in result

    def test_substitute_template_with_defaults(self):
        """Test substituting template with default values."""
        template = "Name: {name}, Email: {email|no-email}"
        data = {"name": "Alice", "email": None}
        result = TemplateParser.substitute_template(template, data, for_sql=False)
        assert result == "Name: Alice, Email: no-email"

    def test_substitute_template_for_sql(self):
        """Test substituting template for SQL."""
        template = "INSERT INTO users (name, age) VALUES ({name}, {age:int})"
        data = {"name": "Alice", "age": "25"}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "INSERT INTO users (name, age) VALUES ('Alice', 25)"

    def test_substitute_template_sql_with_null(self):
        """Test substituting SQL template with NULL values."""
        template = "UPDATE users SET email = {email} WHERE id = {id:int}"
        data = {"email": None, "id": "42"}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "UPDATE users SET email = NULL WHERE id = 42"

    def test_substitute_template_missing_placeholder(self):
        """Test substituting template with missing placeholder."""
        template = "Hello {name}, you are {age} years old"
        data = {"name": "Alice"}  # Missing 'age'
        result = TemplateParser.substitute_template(template, data, for_sql=False)
        # Missing values should be replaced with empty string
        assert "Hello Alice" in result

    def test_substitute_template_none_value_returns_none(self):
        """Test that None value returns None when template is just placeholder."""
        template = "{value}"
        data = {"value": None}
        result = TemplateParser.substitute_template(template, data, for_sql=False)
        assert result is None

    def test_complex_template_with_all_features(self):
        """Test complex template with all features combined."""
        template = (
            "INSERT INTO orders (id, user_id, amount, status, notes) "
            "VALUES ({id:int}, {user_id:int}, {amount:float}, {status|pending}, {notes})"
        )
        data = {
            "id": "123",
            "user_id": "456",
            "amount": "99.99",
            "status": None,
            "notes": "Order notes with 'quotes'",
        }
        result = TemplateParser.substitute_template(template, data, for_sql=True)

        assert "123" in result
        assert "456" in result
        assert "99.99" in result
        assert "'pending'" in result
        assert "Order notes with ''quotes''" in result

    def test_pandas_na_handling(self):
        """Test handling of pandas NA values."""
        result = TemplateParser.substitute_value(
            "value: {value}", "value", pd.NA, None, None, for_sql=True
        )
        assert result == "NULL"

    # ------------------------------------------------------------------
    # SQL wildcard (%, _) extraction tests
    # ------------------------------------------------------------------

    def test_extract_sql_wildcards_both(self):
        """{%name:string%} extracts prefix '%', suffix '%', clean 'name:string'."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards("%name:string%")
        assert clean == "name:string"
        assert prefix == "%"
        assert suffix == "%"

    def test_extract_sql_wildcards_leading_only(self):
        """{%name} extracts prefix '%', suffix '', clean 'name'."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards("%name")
        assert clean == "name"
        assert prefix == "%"
        assert suffix == ""

    def test_extract_sql_wildcards_trailing_only(self):
        """{name%} extracts prefix '', suffix '%', clean 'name'."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards("name%")
        assert clean == "name"
        assert prefix == ""
        assert suffix == "%"

    def test_extract_sql_wildcards_none(self):
        """Plain placeholder has no wildcards."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards("name:string")
        assert clean == "name:string"
        assert prefix == ""
        assert suffix == ""

    def test_extract_sql_wildcards_with_default(self):
        """{%name:string%|default} strips wildcards before the | separator."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards(
            "%name:string%|N/A"
        )
        assert clean == "name:string|N/A"
        assert prefix == "%"
        assert suffix == "%"

    def test_extract_sql_wildcards_underscore(self):
        """{_name_} with single-char wildcard _ is extracted correctly."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards("_name_")
        assert clean == "name"
        assert prefix == "_"
        assert suffix == "_"

    def test_extract_sql_wildcards_mixed(self):
        """{%_name_%} keeps all leading/trailing wildcard characters."""
        clean, prefix, suffix = TemplateParser.extract_sql_wildcards("%_name_%")
        assert clean == "name"
        assert prefix == "%_"
        assert suffix == "_%"

    # ------------------------------------------------------------------
    # SQL wildcard substitution in SQL templates
    # ------------------------------------------------------------------

    def test_substitute_template_sql_ilike_pattern(self):
        """ILIKE pattern {%name:string%} wraps value with % wildcards."""
        template = "WHERE col ILIKE {%name:string%}"
        data = {"name": "foo"}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "WHERE col ILIKE '%foo%'"

    def test_substitute_template_sql_like_leading_wildcard(self):
        """{%name} produces '%value' in SQL."""
        template = "WHERE col LIKE {%name}"
        data = {"name": "bar"}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "WHERE col LIKE '%bar'"

    def test_substitute_template_sql_like_trailing_wildcard(self):
        """{name%} produces 'value%' in SQL."""
        template = "WHERE col LIKE {name%}"
        data = {"name": "baz"}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "WHERE col LIKE 'baz%'"

    def test_substitute_template_sql_wildcard_with_null(self):
        """NULL value with wildcards stays NULL (no wildcard wrapping)."""
        template = "WHERE col ILIKE {%name:string%}"
        data = {"name": None}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "WHERE col ILIKE NULL"

    def test_substitute_template_sql_wildcard_with_default(self):
        """NULL value uses default, then wildcards are applied."""
        template = "WHERE col ILIKE {%name:string%|unknown}"
        data = {"name": None}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "WHERE col ILIKE '%unknown%'"

    def test_substitute_template_sql_wildcard_escapes_quotes(self):
        """Single quotes inside wildcard values are escaped."""
        template = "WHERE col ILIKE {%name:string%}"
        data = {"name": "O'Brien"}
        result = TemplateParser.substitute_template(template, data, for_sql=True)
        assert result == "WHERE col ILIKE '%O''Brien%'"

    def test_substitute_template_sql_wildcard_not_applied_to_json(self):
        """Wildcards are not applied when for_sql=False."""
        template = "prefix {%name:string%} suffix"
        data = {"name": "foo"}
        result = TemplateParser.substitute_template(template, data, for_sql=False)
        # In non-SQL mode the value is substituted without quotes or wildcards
        assert "foo" in result
        assert "'%foo%'" not in result

    # ------------------------------------------------------------------
    # string type hint
    # ------------------------------------------------------------------

    def test_convert_value_string_type(self):
        """'string' type hint converts value to str."""
        assert TemplateParser.convert_value(42, "string") == "42"
        assert TemplateParser.convert_value(3.14, "string") == "3.14"
        assert TemplateParser.convert_value("hello", "string") == "hello"
        assert TemplateParser.convert_value(None, "string") is None

    def test_substitute_value_sql_string_type_hint(self):
        """Explicit :string type produces a SQL-quoted value."""
        result = TemplateParser.substitute_value(
            "{name:string}", "name", "Alice", "string", None, for_sql=True
        )
        assert result == "'Alice'"

    def test_substitute_value_sql_string_type_number(self):
        """Numeric value with :string type is cast and SQL-quoted."""
        result = TemplateParser.substitute_value(
            "{val:string}", "val", 99, "string", None, for_sql=True
        )
        assert result == "'99'"
