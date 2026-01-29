"""
Strategies module initialization.

This module contains strategy pattern implementations for various
data processing operations, particularly normalization.
"""

from app.strategies.base_strategy import NormalizationStrategy
from app.strategies.normalization_strategies import (
    UppercaseStrategy,
    LowercaseStrategy,
    TitleCaseStrategy,
    TrimWhitespaceStrategy,
    RemoveSpecialCharsStrategy,
    PhoneFormatStrategy,
    EmailFormatStrategy,
    NameFormatStrategy,
    MinMaxScaleStrategy,
    ZScoreStrategy,
    RoundDecimalStrategy,
    IntegerConvertStrategy,
    CurrencyFormatStrategy,
    DateFormatStrategy,
    DateTimeFormatStrategy,
    BooleanConvertStrategy,
    YesNoConvertStrategy,
    RegexReplaceStrategy,
    FillNullValuesStrategy,
    OutlierRemovalStrategy,
)

__all__ = [
    "NormalizationStrategy",
    "UppercaseStrategy",
    "LowercaseStrategy",
    "TitleCaseStrategy",
    "TrimWhitespaceStrategy",
    "RemoveSpecialCharsStrategy",
    "PhoneFormatStrategy",
    "EmailFormatStrategy",
    "NameFormatStrategy",
    "MinMaxScaleStrategy",
    "ZScoreStrategy",
    "RoundDecimalStrategy",
    "IntegerConvertStrategy",
    "CurrencyFormatStrategy",
    "DateFormatStrategy",
    "DateTimeFormatStrategy",
    "BooleanConvertStrategy",
    "YesNoConvertStrategy",
    "RegexReplaceStrategy",
    "FillNullValuesStrategy",
    "OutlierRemovalStrategy",
]
