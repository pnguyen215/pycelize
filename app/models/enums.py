"""
Enumeration Definitions

This module contains all enumeration types used in the Pycelize application,
providing type-safe constants for various operations.
"""

from enum import Enum, auto


class NormalizationType(Enum):
    """
    Enumeration of available normalization types.

    These types define the various data normalization operations
    that can be applied to Excel/CSV columns.

    String Normalizations:
        UPPERCASE: Convert text to uppercase
        LOWERCASE: Convert text to lowercase
        TITLE_CASE: Convert text to title case
        TRIM_WHITESPACE: Remove leading/trailing whitespace
        REMOVE_SPECIAL_CHARS: Remove special characters
        PHONE_FORMAT: Format as phone number
        EMAIL_FORMAT: Format and validate email
        NAME_FORMAT: Format personal names

    Numeric Normalizations:
        MIN_MAX_SCALE: Scale values to 0-1 range
        Z_SCORE: Standardize using z-score
        ROUND_DECIMAL: Round to specified decimals
        INTEGER_CONVERT: Convert to integer
        CURRENCY_FORMAT: Format as currency value

    Date/Time Normalizations:
        DATE_FORMAT: Format date values
        DATETIME_FORMAT: Format datetime values
        DATE_EXTRACT_YEAR: Extract year from date
        DATE_EXTRACT_MONTH: Extract month from date
        DATE_EXTRACT_DAY: Extract day from date

    Boolean Normalizations:
        BOOLEAN_CONVERT: Convert to boolean
        YES_NO_CONVERT: Convert to Yes/No strings

    Custom Normalizations:
        REGEX_REPLACE: Replace using regex pattern
        CUSTOM_FUNCTION: Apply custom function
        CATEGORICAL_MAPPING: Map categorical values

    Data Quality:
        REMOVE_DUPLICATES: Remove duplicate rows
        FILL_NULL_VALUES: Fill null/empty values
        OUTLIER_REMOVAL: Remove statistical outliers
    """

    # String normalizations
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TITLE_CASE = "title_case"
    TRIM_WHITESPACE = "trim_whitespace"
    REMOVE_SPECIAL_CHARS = "remove_special_chars"
    PHONE_FORMAT = "phone_format"
    EMAIL_FORMAT = "email_format"
    NAME_FORMAT = "name_format"

    # Numeric normalizations
    MIN_MAX_SCALE = "min_max_scale"
    Z_SCORE = "z_score"
    ROUND_DECIMAL = "round_decimal"
    INTEGER_CONVERT = "integer_convert"
    CURRENCY_FORMAT = "currency_format"

    # Date/Time normalizations
    DATE_FORMAT = "date_format"
    DATETIME_FORMAT = "datetime_format"
    DATE_EXTRACT_YEAR = "date_extract_year"
    DATE_EXTRACT_MONTH = "date_extract_month"
    DATE_EXTRACT_DAY = "date_extract_day"

    # Boolean normalizations
    BOOLEAN_CONVERT = "boolean_convert"
    YES_NO_CONVERT = "yes_no_convert"

    # Custom normalizations
    REGEX_REPLACE = "regex_replace"
    CUSTOM_FUNCTION = "custom_function"
    CATEGORICAL_MAPPING = "categorical_mapping"

    # Data quality
    REMOVE_DUPLICATES = "remove_duplicates"
    FILL_NULL_VALUES = "fill_null_values"
    OUTLIER_REMOVAL = "outlier_removal"

    @classmethod
    def from_string(cls, value: str) -> "NormalizationType":
        """
        Create NormalizationType from string value.

        Args:
            value: String representation of normalization type

        Returns:
            Corresponding NormalizationType enum value

        Raises:
            ValueError: If string doesn't match any type
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_types = [t.value for t in cls]
            raise ValueError(
                f"Invalid normalization type: '{value}'. "
                f"Valid types are: {valid_types}"
            )

    @classmethod
    def list_all(cls) -> list:
        """
        List all available normalization types.

        Returns:
            List of all normalization type string values
        """
        return [t.value for t in cls]


class DatabaseType(Enum):
    """
    Enumeration of supported database types for SQL generation.

    Attributes:
        POSTGRESQL: PostgreSQL database
        MYSQL: MySQL database
        SQLITE: SQLite database
    """

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"

    @classmethod
    def from_string(cls, value: str) -> "DatabaseType":
        """Create DatabaseType from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            valid_types = [t.value for t in cls]
            raise ValueError(
                f"Invalid database type: '{value}'. " f"Valid types are: {valid_types}"
            )


class FileType(Enum):
    """
    Enumeration of supported file types.

    Attributes:
        CSV: Comma-separated values file
        EXCEL: Excel spreadsheet (.xlsx, .xls)
        UNKNOWN: Unknown or unsupported file type
    """

    CSV = "csv"
    EXCEL = "excel"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, extension: str) -> "FileType":
        """
        Determine FileType from file extension.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            Corresponding FileType
        """
        ext = extension.lower().lstrip(".")
        if ext == "csv":
            return cls.CSV
        elif ext in ["xlsx", "xls"]:
            return cls.EXCEL
        return cls.UNKNOWN


class ExportFormat(Enum):
    """
    Enumeration of export formats.

    Attributes:
        JSON: JSON format
        EXCEL: Excel format
        CSV: CSV format
        SQL: SQL statements
    """

    JSON = "json"
    EXCEL = "excel"
    CSV = "csv"
    SQL = "sql"


class SQLAutoIncrementType(Enum):
    """
    Enumeration of auto-increment types for SQL generation.

    Attributes:
        NONE: No auto-increment
        POSTGRESQL_SERIAL: PostgreSQL SERIAL type
        MYSQL_AUTO_INCREMENT: MySQL AUTO_INCREMENT
        SQLITE_AUTOINCREMENT: SQLite AUTOINCREMENT
        MANUAL_SEQUENCE: Manual sequence management
        UUID_GENERATE: UUID generation
    """

    NONE = "none"
    POSTGRESQL_SERIAL = "postgresql_serial"
    MYSQL_AUTO_INCREMENT = "mysql_auto_increment"
    SQLITE_AUTOINCREMENT = "sqlite_autoincrement"
    MANUAL_SEQUENCE = "manual_sequence"
    UUID_GENERATE = "uuid_generate"
