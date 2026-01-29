"""
SQL Builder Implementation

This module implements the Builder Design Pattern for constructing
SQL statements with support for various database types.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, date
import pandas as pd

from app.models.enums import DatabaseType, SQLAutoIncrementType


class SQLBuilder:
    """
    Builder class for constructing SQL statements.

    Implements the Builder Design Pattern to create SQL INSERT statements
    with support for multiple database types, auto-increment columns,
    and transaction handling.

    Example:
        >>> builder = (
        ...     SQLBuilder()
        ...     .with_table_name('users')
        ...     .with_database_type(DatabaseType.POSTGRESQL)
        ...     .with_columns(['name', 'email'])
        ...     .with_auto_increment('id', SQLAutoIncrementType.POSTGRESQL_SERIAL)
        ...     .with_transaction(True)
        ... )
        >>> statements = builder.build_insert({'name': 'John', 'email': 'john@example.com'})

    Attributes:
        _table_name: Target database table name
        _database_type: Type of database (PostgreSQL, MySQL, SQLite)
        _columns: List of column names
        _auto_increment_config: Auto-increment column configuration
        _include_transaction: Whether to wrap in transaction
        _batch_size: Number of statements per batch
    """

    def __init__(self):
        """Initialize SQLBuilder with default values."""
        self._table_name: str = ""
        self._database_type: DatabaseType = DatabaseType.POSTGRESQL
        self._columns: List[str] = []
        self._column_mapping: Dict[str, str] = {}
        self._auto_increment_enabled: bool = False
        self._auto_increment_column: str = "id"
        self._auto_increment_type: SQLAutoIncrementType = SQLAutoIncrementType.NONE
        self._sequence_name: Optional[str] = None
        self._start_value: int = 1
        self._current_value: int = 1
        self._include_transaction: bool = True
        self._batch_size: int = 1000
        self._template: Optional[str] = None

    def with_table_name(self, table_name: str) -> "SQLBuilder":
        """
        Set the target table name.

        Args:
            table_name: Name of the database table

        Returns:
            Self for method chaining
        """
        self._table_name = table_name
        return self

    def with_database_type(self, db_type: DatabaseType) -> "SQLBuilder":
        """
        Set the database type.

        Args:
            db_type: Target database type

        Returns:
            Self for method chaining
        """
        self._database_type = db_type
        return self

    def with_columns(self, columns: List[str]) -> "SQLBuilder":
        """
        Set the column names.

        Args:
            columns: List of column names

        Returns:
            Self for method chaining
        """
        self._columns = columns
        return self

    def with_column_mapping(self, mapping: Dict[str, str]) -> "SQLBuilder":
        """
        Set column mapping (SQL column -> data column).

        Args:
            mapping: Dictionary mapping SQL columns to data columns

        Returns:
            Self for method chaining
        """
        self._column_mapping = mapping
        self._columns = list(mapping.keys())
        return self

    def with_auto_increment(
        self,
        column_name: str = "id",
        increment_type: SQLAutoIncrementType = SQLAutoIncrementType.POSTGRESQL_SERIAL,
        start_value: int = 1,
        sequence_name: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        Configure auto-increment column.

        Args:
            column_name: Name of the auto-increment column
            increment_type: Type of auto-increment mechanism
            start_value: Starting value for the sequence
            sequence_name: Custom sequence name (for manual sequences)

        Returns:
            Self for method chaining
        """
        self._auto_increment_enabled = True
        self._auto_increment_column = column_name
        self._auto_increment_type = increment_type
        self._start_value = start_value
        self._current_value = start_value
        self._sequence_name = sequence_name or f"seq_{column_name}"
        return self

    def with_transaction(self, include: bool = True) -> "SQLBuilder":
        """
        Set whether to include transaction statements.

        Args:
            include: Whether to wrap statements in transaction

        Returns:
            Self for method chaining
        """
        self._include_transaction = include
        return self

    def with_batch_size(self, size: int) -> "SQLBuilder":
        """
        Set the batch size for batched execution.

        Args:
            size: Number of statements per batch

        Returns:
            Self for method chaining
        """
        self._batch_size = size
        return self

    def with_template(self, template: str) -> "SQLBuilder":
        """
        Set a custom SQL template.

        Args:
            template: Custom SQL template with placeholders

        Returns:
            Self for method chaining
        """
        self._template = template
        return self

    def build_insert(self, row: Dict[str, Any]) -> str:
        """
        Build a single INSERT statement for a row of data.

        Args:
            row: Dictionary of column values

        Returns:
            SQL INSERT statement
        """
        if self._template:
            return self._build_from_template(row)

        columns = []
        values = []

        # Add auto-increment column if configured
        if self._auto_increment_enabled:
            auto_value = self._get_auto_increment_value()
            if auto_value:
                columns.append(self._auto_increment_column)
                values.append(auto_value)
                self._current_value += 1

        # Add mapped columns
        for sql_col, data_col in self._column_mapping.items():
            columns.append(sql_col)
            value = row.get(data_col)
            values.append(self._format_value(value))

        columns_str = ", ".join(columns)
        values_str = ", ".join(values)

        return f"INSERT INTO {self._table_name} ({columns_str}) VALUES ({values_str});"

    def build_all(self, data: pd.DataFrame) -> List[str]:
        """
        Build INSERT statements for all rows in a DataFrame.

        Args:
            data: DataFrame containing the data

        Returns:
            List of SQL INSERT statements
        """
        statements = []

        # Add transaction start if configured
        if self._include_transaction:
            statements.append(self._get_transaction_start())

        # Build insert statements
        for _, row in data.iterrows():
            statements.append(self.build_insert(row.to_dict()))

        # Add transaction end if configured
        if self._include_transaction:
            statements.append(self._get_transaction_end())

        return statements

    def build_with_header(self, data: pd.DataFrame) -> List[str]:
        """
        Build complete SQL script with header comments.

        Args:
            data: DataFrame containing the data

        Returns:
            List of SQL statements with header
        """
        statements = [
            "-- Generated SQL statements",
            f"-- Database: {self._database_type.value}",
            f"-- Table: {self._table_name}",
            f"-- Generated at: {datetime.now().isoformat()}",
            f"-- Total rows: {len(data)}",
            "",
        ]

        statements.extend(self.build_all(data))
        return statements

    def _build_from_template(self, row: Dict[str, Any]) -> str:
        """
        Build SQL statement from custom template.

        Args:
            row: Dictionary of column values

        Returns:
            SQL statement built from template
        """
        sql = self._template

        # Replace auto_id placeholder
        if "{auto_id}" in sql and self._auto_increment_enabled:
            auto_value = self._get_auto_increment_value()
            sql = sql.replace("{auto_id}", auto_value or str(self._current_value))
            self._current_value += 1

        # Replace column placeholders
        for sql_col, data_col in self._column_mapping.items():
            value = row.get(data_col)
            formatted_value = self._format_value(value)
            sql = sql.replace(f"{{{sql_col}}}", formatted_value)

        # Replace special placeholders
        sql = sql.replace("{current_timestamp}", self._get_current_timestamp())
        sql = sql.replace("{current_date}", self._get_current_date())

        return sql

    def _get_auto_increment_value(self) -> Optional[str]:
        """Get the auto-increment value expression."""
        if self._auto_increment_type == SQLAutoIncrementType.NONE:
            return None
        elif self._auto_increment_type == SQLAutoIncrementType.MANUAL_SEQUENCE:
            if self._database_type == DatabaseType.POSTGRESQL:
                return f"nextval('{self._sequence_name}')"
            else:
                return str(self._current_value)
        elif self._auto_increment_type == SQLAutoIncrementType.UUID_GENERATE:
            if self._database_type == DatabaseType.POSTGRESQL:
                return "uuid_generate_v4()"
            else:
                return "UUID()"
        else:
            # For SERIAL/AUTO_INCREMENT, value is auto-generated by DB
            return None

    def _format_value(self, value: Any) -> str:
        """
        Format a value for SQL based on database type.

        Args:
            value: Value to format

        Returns:
            Formatted SQL value string
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "NULL"

        if isinstance(value, str):
            # Escape quotes based on database type
            if self._database_type == DatabaseType.MYSQL:
                escaped = value.replace("'", "\\'").replace('"', '\\"')
            else:
                escaped = value.replace("'", "''")
            return f"'{escaped}'"

        elif isinstance(value, bool):
            if self._database_type == DatabaseType.POSTGRESQL:
                return "TRUE" if value else "FALSE"
            else:
                return "1" if value else "0"

        elif isinstance(value, (int, float)):
            return str(value)

        elif isinstance(value, (datetime, date)):
            formatted = value.strftime("%Y-%m-%d %H:%M:%S")
            if self._database_type == DatabaseType.POSTGRESQL:
                return f"'{formatted}'::timestamp"
            else:
                return f"'{formatted}'"

        else:
            return f"'{str(value)}'"

    def _get_transaction_start(self) -> str:
        """Get transaction start statement."""
        if self._database_type == DatabaseType.POSTGRESQL:
            return "BEGIN;"
        elif self._database_type == DatabaseType.MYSQL:
            return "START TRANSACTION;"
        else:
            return "BEGIN TRANSACTION;"

    def _get_transaction_end(self) -> str:
        """Get transaction end statement."""
        return "COMMIT;"

    def _get_current_timestamp(self) -> str:
        """Get current timestamp function for database type."""
        if self._database_type == DatabaseType.SQLITE:
            return "datetime('now')"
        else:
            return "NOW()"

    def _get_current_date(self) -> str:
        """Get current date function for database type."""
        if self._database_type == DatabaseType.POSTGRESQL:
            return "CURRENT_DATE"
        elif self._database_type == DatabaseType.MYSQL:
            return "CURDATE()"
        else:
            return "date('now')"
