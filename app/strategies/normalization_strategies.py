"""
Concrete Normalization Strategy Implementations

This module contains all concrete implementations of normalization strategies,
each implementing a specific data transformation algorithm.
"""

import re
from typing import Any, Dict
import pandas as pd
import numpy as np

from app.strategies.base_strategy import NormalizationStrategy


class UppercaseStrategy(NormalizationStrategy):
    """Convert text to uppercase."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Convert all values to uppercase."""
        return series.astype(str).str.upper()

    @property
    def name(self) -> str:
        return "uppercase"

    @property
    def description(self) -> str:
        return "Convert text to uppercase"


class LowercaseStrategy(NormalizationStrategy):
    """Convert text to lowercase."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Convert all values to lowercase."""
        return series.astype(str).str.lower()

    @property
    def name(self) -> str:
        return "lowercase"

    @property
    def description(self) -> str:
        return "Convert text to lowercase"


class TitleCaseStrategy(NormalizationStrategy):
    """Convert text to title case."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Convert all values to title case."""
        return series.astype(str).str.title()

    @property
    def name(self) -> str:
        return "title_case"

    @property
    def description(self) -> str:
        return "Convert text to title case"


class TrimWhitespaceStrategy(NormalizationStrategy):
    """Remove leading and trailing whitespace."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Strip whitespace from values."""
        return series.astype(str).str.strip()

    @property
    def name(self) -> str:
        return "trim_whitespace"

    @property
    def description(self) -> str:
        return "Remove leading and trailing whitespace"


class RemoveSpecialCharsStrategy(NormalizationStrategy):
    """Remove special characters from text."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Remove special characters based on pattern."""
        pattern = self.parameters.get("pattern", r"[^a-zA-Z0-9\s]")
        replacement = self.parameters.get("replacement", "")
        return series.astype(str).str.replace(pattern, replacement, regex=True)

    @property
    def name(self) -> str:
        return "remove_special_chars"

    @property
    def description(self) -> str:
        return "Remove special characters from text"


class PhoneFormatStrategy(NormalizationStrategy):
    """Format phone numbers to a standard format."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Format phone numbers."""
        return series.apply(self._format_phone)

    def _format_phone(self, value: Any) -> str:
        """Format a single phone number value."""
        if pd.isna(value):
            return ""

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", str(value))

        # Format based on length
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return str(value)

    @property
    def name(self) -> str:
        return "phone_format"

    @property
    def description(self) -> str:
        return "Format phone numbers to standard format"


class EmailFormatStrategy(NormalizationStrategy):
    """Format and validate email addresses."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Format email addresses to lowercase and trim."""
        return series.astype(str).str.lower().str.strip()

    @property
    def name(self) -> str:
        return "email_format"

    @property
    def description(self) -> str:
        return "Format email addresses (lowercase, trimmed)"


class NameFormatStrategy(NormalizationStrategy):
    """Format personal names."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Format names to title case and trim."""
        return series.astype(str).str.title().str.strip()

    @property
    def name(self) -> str:
        return "name_format"

    @property
    def description(self) -> str:
        return "Format personal names (title case, trimmed)"


class MinMaxScaleStrategy(NormalizationStrategy):
    """Scale numeric values to 0-1 range."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Apply min-max scaling."""
        numeric_series = pd.to_numeric(series, errors="coerce")
        min_val = numeric_series.min()
        max_val = numeric_series.max()

        if max_val != min_val:
            return (numeric_series - min_val) / (max_val - min_val)
        return numeric_series

    @property
    def name(self) -> str:
        return "min_max_scale"

    @property
    def description(self) -> str:
        return "Scale numeric values to 0-1 range"


class ZScoreStrategy(NormalizationStrategy):
    """Standardize values using z-score normalization."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Apply z-score standardization."""
        numeric_series = pd.to_numeric(series, errors="coerce")
        mean = numeric_series.mean()
        std = numeric_series.std()

        if std != 0:
            return (numeric_series - mean) / std
        return numeric_series - mean

    @property
    def name(self) -> str:
        return "z_score"

    @property
    def description(self) -> str:
        return "Standardize values using z-score"


class RoundDecimalStrategy(NormalizationStrategy):
    """Round numeric values to specified decimal places."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Round values to specified decimals."""
        decimals = self.parameters.get("decimals", 2)
        return pd.to_numeric(series, errors="coerce").round(decimals)

    @property
    def name(self) -> str:
        return "round_decimal"

    @property
    def description(self) -> str:
        return "Round numeric values to specified decimal places"


class IntegerConvertStrategy(NormalizationStrategy):
    """Convert values to integers."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Convert values to integers."""
        return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)

    @property
    def name(self) -> str:
        return "integer_convert"

    @property
    def description(self) -> str:
        return "Convert values to integers"


class CurrencyFormatStrategy(NormalizationStrategy):
    """Parse and format currency values."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Remove currency symbols and convert to numeric."""
        cleaned = series.astype(str).str.replace(r"[^\d.-]", "", regex=True)
        return pd.to_numeric(cleaned, errors="coerce")

    @property
    def name(self) -> str:
        return "currency_format"

    @property
    def description(self) -> str:
        return "Parse currency values to numeric format"


class DateFormatStrategy(NormalizationStrategy):
    """Format date values."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Format dates to specified format."""
        date_format = self.parameters.get("format", "%Y-%m-%d")
        return pd.to_datetime(series, errors="coerce").dt.strftime(date_format)

    @property
    def name(self) -> str:
        return "date_format"

    @property
    def description(self) -> str:
        return "Format date values to specified format"


class DateTimeFormatStrategy(NormalizationStrategy):
    """Format datetime values."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Format datetime to specified format."""
        datetime_format = self.parameters.get("format", "%Y-%m-%d %H:%M:%S")
        return pd.to_datetime(series, errors="coerce").dt.strftime(datetime_format)

    @property
    def name(self) -> str:
        return "datetime_format"

    @property
    def description(self) -> str:
        return "Format datetime values to specified format"


class BooleanConvertStrategy(NormalizationStrategy):
    """Convert values to boolean."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Convert values to boolean based on true values list."""
        true_values = self.parameters.get(
            "true_values", ["true", "1", "yes", "y", "on"]
        )
        return series.astype(str).str.lower().isin([v.lower() for v in true_values])

    @property
    def name(self) -> str:
        return "boolean_convert"

    @property
    def description(self) -> str:
        return "Convert values to boolean"


class YesNoConvertStrategy(NormalizationStrategy):
    """Convert boolean-like values to Yes/No strings."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Convert values to Yes/No strings."""
        true_values = self.parameters.get("true_values", ["true", "1", "yes", "y"])
        bool_series = (
            series.astype(str).str.lower().isin([v.lower() for v in true_values])
        )
        return bool_series.map({True: "Yes", False: "No"})

    @property
    def name(self) -> str:
        return "yes_no_convert"

    @property
    def description(self) -> str:
        return "Convert boolean-like values to Yes/No"


class RegexReplaceStrategy(NormalizationStrategy):
    """Replace values using regex pattern."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Replace values matching regex pattern."""
        pattern = self.parameters.get("pattern", "")
        replacement = self.parameters.get("replacement", "")
        return series.astype(str).str.replace(pattern, replacement, regex=True)

    @property
    def name(self) -> str:
        return "regex_replace"

    @property
    def description(self) -> str:
        return "Replace values using regex pattern"


class FillNullValuesStrategy(NormalizationStrategy):
    """Fill null/empty values."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Fill null values with specified value or method."""
        fill_value = self.parameters.get("value", "")
        method = self.parameters.get("method", "value")

        if method == "value":
            return series.fillna(fill_value)
        elif method == "mean" and pd.api.types.is_numeric_dtype(series):
            return series.fillna(series.mean())
        elif method == "median" and pd.api.types.is_numeric_dtype(series):
            return series.fillna(series.median())
        elif method == "mode":
            mode_val = series.mode()
            if not mode_val.empty:
                return series.fillna(mode_val.iloc[0])
            return series.fillna(fill_value)
        else:
            return series.fillna(fill_value)

    @property
    def name(self) -> str:
        return "fill_null_values"

    @property
    def description(self) -> str:
        return "Fill null/empty values with specified value or method"


class OutlierRemovalStrategy(NormalizationStrategy):
    """Remove statistical outliers using IQR method."""

    def normalize(self, series: pd.Series) -> pd.Series:
        """Remove outliers based on IQR method."""
        if not pd.api.types.is_numeric_dtype(series):
            return series

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        multiplier = self.parameters.get("multiplier", 1.5)
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        return series.where((series >= lower_bound) & (series <= upper_bound))

    @property
    def name(self) -> str:
        return "outlier_removal"

    @property
    def description(self) -> str:
        return "Remove statistical outliers using IQR method"
