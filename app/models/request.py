"""
API Request Models

This module defines the data structures for API requests,
providing validation and type hints for incoming data.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List


@dataclass
class ColumnExtractionRequest:
    """
    Request model for column extraction operations.

    Attributes:
        columns: List of column names to extract
        remove_duplicates: Whether to remove duplicate values
        include_statistics: Whether to include column statistics
    """

    columns: List[str]
    remove_duplicates: bool = False
    include_statistics: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnExtractionRequest":
        """Create request from dictionary."""
        return cls(
            columns=data.get("columns", []),
            remove_duplicates=data.get("remove_duplicates", False),
            include_statistics=data.get("include_statistics", True),
        )


@dataclass
class NormalizationConfig:
    """
    Configuration for a single column normalization.

    Attributes:
        column_name: Name of the column to normalize
        normalization_type: Type of normalization to apply
        parameters: Additional parameters for normalization
        backup_original: Whether to backup original values
    """

    column_name: str
    normalization_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    backup_original: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizationConfig":
        """Create config from dictionary."""
        return cls(
            column_name=data.get("column_name", ""),
            normalization_type=data.get("normalization_type", ""),
            parameters=data.get("parameters", {}),
            backup_original=data.get("backup_original", False),
        )


@dataclass
class NormalizationRequest:
    """
    Request model for data normalization operations.

    Attributes:
        normalizations: List of normalization configurations
        output_filename: Optional custom output filename
    """

    normalizations: List[NormalizationConfig]
    output_filename: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizationRequest":
        """Create request from dictionary."""
        normalizations = [
            NormalizationConfig.from_dict(n) for n in data.get("normalizations", [])
        ]
        return cls(
            normalizations=normalizations, output_filename=data.get("output_filename")
        )


@dataclass
class ColumnMappingRequest:
    """
    Request model for column mapping operations.

    Attributes:
        mapping: Dictionary mapping target column names to source columns
        output_filename: Optional custom output filename
    """

    mapping: Dict[str, Any]
    output_filename: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnMappingRequest":
        """Create request from dictionary."""
        return cls(
            mapping=data.get("mapping", {}), output_filename=data.get("output_filename")
        )


@dataclass
class AutoIncrementConfig:
    """
    Configuration for auto-increment columns in SQL generation.

    Attributes:
        enabled: Whether auto-increment is enabled
        column_name: Name of the auto-increment column
        increment_type: Type of auto-increment (serial, sequence, etc.)
        start_value: Starting value for the sequence
        sequence_name: Custom sequence name (for manual sequence)
    """

    enabled: bool = False
    column_name: str = "id"
    increment_type: str = "postgresql_serial"
    start_value: int = 1
    sequence_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoIncrementConfig":
        """Create config from dictionary."""
        if not data:
            return cls()
        return cls(
            enabled=data.get("enabled", False),
            column_name=data.get("column_name", "id"),
            increment_type=data.get("increment_type", "postgresql_serial"),
            start_value=data.get("start_value", 1),
            sequence_name=data.get("sequence_name"),
        )


@dataclass
class SQLGenerationRequest:
    """
    Request model for SQL generation operations.

    Attributes:
        table_name: Target database table name
        column_mapping: Mapping of SQL columns to data columns
        database_type: Target database type (postgresql, mysql, sqlite)
        template: Optional custom SQL template
        auto_increment: Auto-increment configuration
        batch_size: Number of statements per batch
        include_transaction: Whether to wrap in transaction
    """

    table_name: str
    column_mapping: Dict[str, str]
    database_type: str = "postgresql"
    template: Optional[str] = None
    auto_increment: Optional[AutoIncrementConfig] = None
    batch_size: int = 1000
    include_transaction: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SQLGenerationRequest":
        """Create request from dictionary."""
        auto_increment = AutoIncrementConfig.from_dict(data.get("auto_increment", {}))
        return cls(
            table_name=data.get("table_name", ""),
            column_mapping=data.get("column_mapping", {}),
            database_type=data.get("database_type", "postgresql"),
            template=data.get("template"),
            auto_increment=auto_increment,
            batch_size=data.get("batch_size", 1000),
            include_transaction=data.get("include_transaction", True),
        )


@dataclass
class BindingRequest:
    """
    Request model for Excel-to-Excel data binding operations.

    Attributes:
        source_column_mapping: Mapping from source columns to target columns
        output_filename: Optional custom output filename
    """

    source_column_mapping: Dict[str, str]
    output_filename: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BindingRequest":
        """Create request from dictionary."""
        return cls(
            source_column_mapping=data.get("source_column_mapping", {}),
            output_filename=data.get("output_filename"),
        )


@dataclass
class SearchCondition:
    """
    Single search condition for filtering data.

    Attributes:
        column: Column name to filter on
        operator: Comparison operator to use
        value: Value to compare against
    """

    column: str
    operator: str
    value: Any

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchCondition":
        """Create condition from dictionary."""
        return cls(
            column=data.get("column", ""),
            operator=data.get("operator", ""),
            value=data.get("value"),
        )


@dataclass
class SearchRequest:
    """
    Request model for search/filter operations.

    Attributes:
        conditions: List of search conditions to apply
        logic: Logical operator between conditions (AND or OR)
        output_format: Output format (xlsx, csv, or json)
        output_filename: Optional custom output filename
    """

    conditions: List[SearchCondition]
    logic: str = "AND"
    output_format: str = "xlsx"
    output_filename: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchRequest":
        """Create request from dictionary."""
        conditions = [SearchCondition.from_dict(c) for c in data.get("conditions", [])]
        return cls(
            conditions=conditions,
            logic=data.get("logic", "AND").upper(),
            output_format=data.get("output_format", "xlsx").lower(),
            output_filename=data.get("output_filename"),
        )
