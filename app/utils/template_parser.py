"""
Template Parser Utility

This module provides a unified template parser that handles enhanced placeholder syntax
for both SQL and JSON generation services.

Supported placeholder syntax:
- {column_name}: Basic substitution
- {column_name:int}: Convert to integer
- {column_name:float}: Convert to float
- {column_name:bool}: Convert to boolean
- {column_name:datetime}: Keep as datetime string
- {column_name|default}: Use default if value is null
"""

import re
from typing import Any, Optional, Tuple
from datetime import datetime

import pandas as pd


class TemplateParser:
    """
    Parser for template placeholders with type conversion and default values.

    This class provides methods to parse and substitute placeholders in templates
    with support for type conversion and default values.

    Example:
        >>> parser = TemplateParser()
        >>> result = parser.parse_placeholder("{name:int|0}")
        >>> print(result)
        ('name', 'int', '0')
    """

    # Regex pattern to match placeholders: {placeholder:type|default}
    PLACEHOLDER_PATTERN = r"\{([^}]+)\}"

    @staticmethod
    def parse_placeholder(
        placeholder_text: str,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Parse a placeholder text to extract name, type, and default value.

        Supports the following syntax:
        - {column}: Basic substitution
        - {column:type}: With type conversion
        - {column|default}: With default value
        - {column:type|default}: With both type and default

        Args:
            placeholder_text: The placeholder text (without braces)
                             e.g., "name", "age:int", "email|default@example.com", "count:int|0"

        Returns:
            Tuple of (placeholder_name, type_hint, default_value)

        Example:
            >>> TemplateParser.parse_placeholder("age:int|0")
            ('age', 'int', '0')
            >>> TemplateParser.parse_placeholder("name")
            ('name', None, None)
            >>> TemplateParser.parse_placeholder("email|no-email")
            ('email', None, 'no-email')
        """
        # First, check for default value syntax (splits by |)
        default_value = None
        if "|" in placeholder_text:
            placeholder_text, default_value = placeholder_text.split("|", 1)
            placeholder_text = placeholder_text.strip()
            default_value = default_value.strip()

        # Then, split by colon to separate type hint
        parts = placeholder_text.split(":", 1)
        name_part = parts[0].strip()
        type_hint = parts[1].strip() if len(parts) > 1 else None

        return name_part, type_hint, default_value

    @staticmethod
    def convert_value(value: Any, type_hint: Optional[str]) -> Any:
        """
        Convert a value to the specified type.

        Args:
            value: The value to convert
            type_hint: The target type ('int', 'float', 'bool', 'datetime')

        Returns:
            Converted value, or original value if conversion fails or no type hint

        Example:
            >>> TemplateParser.convert_value("42", "int")
            42
            >>> TemplateParser.convert_value("true", "bool")
            True
        """
        if value is None or type_hint is None:
            return value

        try:
            if type_hint == "int":
                if value == "" or pd.isna(value):
                    return None
                return int(float(value))

            elif type_hint == "float":
                if value == "" or pd.isna(value):
                    return None
                return float(value)

            elif type_hint == "bool":
                if pd.isna(value):
                    return None
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)

            elif type_hint == "datetime":
                # Keep as string representation
                if pd.isna(value):
                    return None
                if isinstance(value, (pd.Timestamp, datetime)):
                    return value.isoformat()
                return str(value)

            elif type_hint in ("string", "str", "text"):
                if pd.isna(value):
                    return None
                return str(value)

            else:
                # Unknown type hint, return original value
                return value

        except (ValueError, TypeError, AttributeError):
            # If conversion fails, return original value
            return value

    @staticmethod
    def extract_sql_wildcards(placeholder_text: str) -> Tuple[str, str, str]:
        """
        Extract SQL wildcard characters (%, _) from the boundaries of a placeholder.

        Handles patterns like {%name:string%} where % are SQL LIKE/ILIKE wildcards.
        Supports % (any characters) and _ (single character) SQL wildcards.

        Args:
            placeholder_text: The placeholder text (without outer braces)

        Returns:
            Tuple of (clean_placeholder_text, sql_prefix, sql_suffix)

        Example:
            >>> TemplateParser.extract_sql_wildcards("%name:string%")
            ('name:string', '%', '%')
            >>> TemplateParser.extract_sql_wildcards("%name%")
            ('name', '%', '%')
            >>> TemplateParser.extract_sql_wildcards("name:int")
            ('name:int', '', '')
            >>> TemplateParser.extract_sql_wildcards("%name:string%|default")
            ('name:string|default', '%', '%')
        """
        SQL_WILDCARDS = set("%_")

        text = placeholder_text
        sql_prefix = ""
        sql_suffix = ""

        # Extract leading SQL wildcards
        i = 0
        while i < len(text) and text[i] in SQL_WILDCARDS:
            sql_prefix += text[i]
            i += 1
        text = text[i:]

        # Split off default value part (after '|') before stripping trailing wildcards
        if "|" in text:
            base_part, default_part = text.split("|", 1)
        else:
            base_part = text
            default_part = None

        # Extract trailing SQL wildcards from the base_part (name or name:type)
        j = len(base_part)
        while j > 0 and base_part[j - 1] in SQL_WILDCARDS:
            j -= 1
        sql_suffix = base_part[j:]
        base_part = base_part[:j]

        # Reconstruct clean placeholder text
        if default_part is not None:
            clean_text = f"{base_part}|{default_part}"
        else:
            clean_text = base_part

        return clean_text, sql_prefix, sql_suffix

    @staticmethod
    def substitute_value(
        template: str,
        placeholder_name: str,
        value: Any,
        type_hint: Optional[str] = None,
        default_value: Optional[str] = None,
        for_sql: bool = False,
    ) -> str:
        """
        Substitute a placeholder in template with its value.

        Args:
            template: The template string containing placeholders
            placeholder_name: The name of the placeholder to replace
            value: The value to substitute
            type_hint: Optional type conversion hint
            default_value: Optional default value if value is None
            for_sql: Whether this is for SQL generation (adds quotes for strings)

        Returns:
            Template string with placeholder substituted

        Example:
            >>> TemplateParser.substitute_value("age: {age}", "age", 25, "int")
            'age: 25'
        """
        # Handle None/null/empty values
        # Treat empty string as None if default is specified
        if (
            value is None
            or pd.isna(value)
            or (isinstance(value, str) and value == "" and default_value is not None)
        ):
            if default_value is not None:
                value = default_value
            else:
                if for_sql:
                    return "NULL"
                return None

        # Apply type conversion if specified
        converted_value = TemplateParser.convert_value(value, type_hint)

        if for_sql:
            # Format value for SQL
            if converted_value is None or pd.isna(converted_value):
                return "NULL"
            elif type_hint in ("int", "float"):
                return str(converted_value)
            elif type_hint == "bool":
                # SQL boolean representation
                return "TRUE" if converted_value else "FALSE"
            elif isinstance(converted_value, str):
                # Escape single quotes for SQL
                escaped_value = str(converted_value).replace("'", "''")
                return f"'{escaped_value}'"
            elif isinstance(converted_value, (int, float)):
                return str(converted_value)
            else:
                # Default: treat as string
                escaped_value = str(converted_value).replace("'", "''")
                return f"'{escaped_value}'"
        else:
            # For JSON, just convert to string
            if converted_value is None:
                return None
            return str(converted_value)

    @staticmethod
    def find_all_placeholders(template: str) -> list:
        """
        Find all placeholder matches in a template string.

        Args:
            template: The template string

        Returns:
            List of placeholder texts (without braces)

        Example:
            >>> TemplateParser.find_all_placeholders("Hello {name}, you are {age:int}")
            ['name', 'age:int']
        """
        return re.findall(TemplateParser.PLACEHOLDER_PATTERN, template)

    @staticmethod
    def substitute_template(template: str, data: dict, for_sql: bool = False) -> str:
        """
        Substitute all placeholders in a template with values from data dictionary.

        Args:
            template: The template string with placeholders
            data: Dictionary mapping placeholder names to values
            for_sql: Whether this is for SQL generation

        Returns:
            Template string with all placeholders substituted

        Example:
            >>> data = {"name": "Alice", "age": 25}
            >>> TemplateParser.substitute_template("Name: {name}, Age: {age:int}", data)
            'Name: Alice, Age: 25'
        """
        result = template
        placeholders = TemplateParser.find_all_placeholders(template)

        for placeholder_text in placeholders:
            # Extract SQL wildcards (%, _) from placeholder boundaries before parsing
            clean_text, sql_prefix, sql_suffix = TemplateParser.extract_sql_wildcards(
                placeholder_text
            )

            # Parse the placeholder
            name, type_hint, default_value = TemplateParser.parse_placeholder(
                clean_text
            )

            # Get value from data
            value = data.get(name)

            # Substitute the value
            substituted = TemplateParser.substitute_value(
                result, name, value, type_hint, default_value, for_sql
            )

            # Apply SQL wildcards to quoted string values (e.g. for LIKE/ILIKE patterns)
            if (
                for_sql
                and (sql_prefix or sql_suffix)
                and substituted not in (None, "NULL")
                and isinstance(substituted, str)
                and substituted.startswith("'")
                and substituted.endswith("'")
            ):
                inner = substituted[1:-1]
                substituted = f"'{sql_prefix}{inner}{sql_suffix}'"

            # Replace in template
            placeholder_full = f"{{{placeholder_text}}}"
            if substituted is None:
                # If entire template is just this placeholder, return None
                if result == placeholder_full:
                    return None
                # Otherwise remove the placeholder
                result = result.replace(placeholder_full, "")
            else:
                result = result.replace(placeholder_full, substituted)

        return result
