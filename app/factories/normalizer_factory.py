"""
Normalizer Factory Implementation

This module implements the Factory Design Pattern for creating
normalization strategy instances based on type.
"""

from typing import Dict, Any, Optional, Type

from app.models.enums import NormalizationType
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


class NormalizerFactory:
    """
    Factory class for creating normalization strategy instances.

    This class implements the Factory Design Pattern, providing a
    centralized way to create normalization strategies based on
    the NormalizationType enum.

    Example:
        >>> factory = NormalizerFactory()
        >>> strategy = factory.create(NormalizationType.UPPERCASE)
        >>> normalized = strategy.normalize(data_series)

    Attributes:
        _strategies: Registry mapping normalization types to strategy classes
    """

    # Registry of normalization types to strategy classes
    _strategies: Dict[NormalizationType, Type[NormalizationStrategy]] = {
        NormalizationType.UPPERCASE: UppercaseStrategy,
        NormalizationType.LOWERCASE: LowercaseStrategy,
        NormalizationType.TITLE_CASE: TitleCaseStrategy,
        NormalizationType.TRIM_WHITESPACE: TrimWhitespaceStrategy,
        NormalizationType.REMOVE_SPECIAL_CHARS: RemoveSpecialCharsStrategy,
        NormalizationType.PHONE_FORMAT: PhoneFormatStrategy,
        NormalizationType.EMAIL_FORMAT: EmailFormatStrategy,
        NormalizationType.NAME_FORMAT: NameFormatStrategy,
        NormalizationType.MIN_MAX_SCALE: MinMaxScaleStrategy,
        NormalizationType.Z_SCORE: ZScoreStrategy,
        NormalizationType.ROUND_DECIMAL: RoundDecimalStrategy,
        NormalizationType.INTEGER_CONVERT: IntegerConvertStrategy,
        NormalizationType.CURRENCY_FORMAT: CurrencyFormatStrategy,
        NormalizationType.DATE_FORMAT: DateFormatStrategy,
        NormalizationType.DATETIME_FORMAT: DateTimeFormatStrategy,
        NormalizationType.BOOLEAN_CONVERT: BooleanConvertStrategy,
        NormalizationType.YES_NO_CONVERT: YesNoConvertStrategy,
        NormalizationType.REGEX_REPLACE: RegexReplaceStrategy,
        NormalizationType.FILL_NULL_VALUES: FillNullValuesStrategy,
        NormalizationType.OUTLIER_REMOVAL: OutlierRemovalStrategy,
    }

    @classmethod
    def create(
        cls,
        normalization_type: NormalizationType,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> NormalizationStrategy:
        """
        Create a normalization strategy instance.

        Args:
            normalization_type: Type of normalization strategy to create
            parameters: Optional parameters for the strategy

        Returns:
            Instance of the requested normalization strategy

        Raises:
            ValueError: If normalization type is not supported
        """
        strategy_class = cls._strategies.get(normalization_type)

        if strategy_class is None:
            raise ValueError(
                f"Unsupported normalization type: {normalization_type.value}. "
                f"Supported types: {list(cls._strategies.keys())}"
            )

        return strategy_class(parameters or {})

    @classmethod
    def create_from_string(
        cls, type_string: str, parameters: Optional[Dict[str, Any]] = None
    ) -> NormalizationStrategy:
        """
        Create a normalization strategy from string type name.

        Args:
            type_string: String name of the normalization type
            parameters: Optional parameters for the strategy

        Returns:
            Instance of the requested normalization strategy

        Raises:
            ValueError: If type string is not valid
        """
        normalization_type = NormalizationType.from_string(type_string)
        return cls.create(normalization_type, parameters)

    @classmethod
    def get_available_types(cls) -> Dict[str, str]:
        """
        Get all available normalization types with descriptions.

        Returns:
            Dictionary mapping type names to descriptions
        """
        result = {}
        for norm_type, strategy_class in cls._strategies.items():
            # Create temporary instance to get description
            strategy = strategy_class({})
            result[norm_type.value] = strategy.description
        return result

    @classmethod
    def register_strategy(
        cls,
        normalization_type: NormalizationType,
        strategy_class: Type[NormalizationStrategy],
    ) -> None:
        """
        Register a new normalization strategy.

        Allows extending the factory with custom strategies at runtime.

        Args:
            normalization_type: Type enum value for the strategy
            strategy_class: Strategy class to register
        """
        cls._strategies[normalization_type] = strategy_class
