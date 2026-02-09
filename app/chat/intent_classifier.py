"""
Intent Classifier Service

This module provides intent classification for chat bot messages,
mapping user text to appropriate workflow operations.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Enumeration of intent types."""

    EXTRACT_COLUMNS = "extract_columns"
    CONVERT_FORMAT = "convert_format"
    NORMALIZE_DATA = "normalize_data"
    GENERATE_SQL = "generate_sql"
    GENERATE_JSON = "generate_json"
    SEARCH_FILTER = "search_filter"
    BIND_DATA = "bind_data"
    MAP_COLUMNS = "map_columns"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """
    Represents a classified intent with confidence and suggested operations.

    Attributes:
        intent_type: Type of intent detected
        confidence: Confidence score (0.0 - 1.0)
        suggested_operations: List of suggested workflow operations
        extracted_params: Parameters extracted from user message
        explanation: Human-readable explanation of the intent
    """

    intent_type: IntentType
    confidence: float
    suggested_operations: List[Dict[str, Any]]
    extracted_params: Dict[str, Any]
    explanation: str


class IntentClassifier:
    """
    Classifies user messages to determine intent and suggest workflow operations.

    Uses keyword matching, regex patterns, and contextual analysis to map
    user text to appropriate Excel/CSV processing operations.
    """

    # Intent patterns with keywords and regex
    INTENT_PATTERNS = {
        IntentType.EXTRACT_COLUMNS: {
            "keywords": ["extract", "get", "select", "column", "field", "data from"],
            "patterns": [
                r"extract (?:columns?|fields?)",
                r"get (?:the )?(?:columns?|fields?|data)",
                r"select (?:columns?|fields?)",
                r"pull (?:out )?(?:columns?|fields?)",
            ],
            # "operations": ["excel/extract-columns", "excel/extract-columns-to-file"],
            "operations": ["excel/extract-columns-to-file"],
        },
        IntentType.CONVERT_FORMAT: {
            "keywords": ["convert", "transform", "change to", "make it", "export as"],
            "patterns": [
                r"convert (?:to |into )?(?:excel|csv|json)",
                r"(?:transform|change) (?:to |into )?(?:excel|csv|json)",
                r"export (?:as |to )?(?:excel|csv|json)",
            ],
            "operations": ["csv/convert-to-excel", "json/generate"],
        },
        IntentType.NORMALIZE_DATA: {
            "keywords": [
                "normalize",
                "clean",
                "standardize",
                "format",
                "trim",
                "uppercase",
                "lowercase",
            ],
            "patterns": [
                r"(?:normalize|clean|standardize) (?:the )?data",
                r"(?:trim|uppercase|lowercase|format) (?:the )?(?:data|values)",
                r"remove (?:duplicates|spaces)",
            ],
            "operations": ["normalization/apply"],
        },
        IntentType.GENERATE_SQL: {
            "keywords": [
                "sql",
                "insert",
                "database",
                "query",
                "statement",
                "generate sql",
            ],
            "patterns": [
                r"generate (?:sql|insert|queries)",
                r"create (?:sql|insert) (?:statements?|queries)",
                r"(?:sql|database) insert",
            ],
            "operations": ["sql/generate", "sql/generate-to-text"],
        },
        IntentType.GENERATE_JSON: {
            "keywords": ["json", "generate json", "export json", "json format"],
            "patterns": [
                r"generate json",
                r"export (?:as |to )?json",
                r"create json",
                r"convert to json",
            ],
            "operations": ["json/generate", "json/generate-with-template"],
        },
        IntentType.SEARCH_FILTER: {
            "keywords": ["search", "filter", "find", "query", "where", "lookup"],
            "patterns": [
                r"(?:search|filter|find) (?:for |where )",
                r"(?:lookup|query) (?:data|records)",
                r"show (?:me )?(?:only |records where)",
            ],
            "operations": ["excel/search", "csv/search"],
        },
        IntentType.BIND_DATA: {
            "keywords": ["bind", "merge", "join", "combine", "link", "match"],
            "patterns": [
                r"(?:bind|merge|join|combine) (?:with |data)",
                r"(?:link|match) (?:with |data from)",
            ],
            "operations": ["excel/bind-single-key", "excel/bind-multi-key"],
        },
        IntentType.MAP_COLUMNS: {
            "keywords": ["map", "rename", "remap", "column mapping"],
            "patterns": [
                r"(?:map|rename|remap) (?:columns?|fields?)",
                r"change column (?:names?)",
            ],
            "operations": ["excel/map-columns"],
        },
    }

    def __init__(self):
        """Initialize intent classifier."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        for intent_type, config in self.INTENT_PATTERNS.items():
            config["compiled_patterns"] = [
                re.compile(pattern, re.IGNORECASE) for pattern in config["patterns"]
            ]

    def classify(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> Intent:
        """
        Classify user message to determine intent.

        Args:
            message: User message text
            context: Optional context (file type, previous intents, etc.)

        Returns:
            Intent object with classification results
        """
        message_lower = message.lower().strip()

        # Score each intent type
        intent_scores = {}
        for intent_type, config in self.INTENT_PATTERNS.items():
            score = self._score_intent(message_lower, config)
            if score > 0:
                intent_scores[intent_type] = score

        # If no matches, return unknown intent
        if not intent_scores:
            return Intent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                suggested_operations=[],
                extracted_params={},
                explanation="I couldn't understand your request. Could you please rephrase?",
            )

        # Get highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_type, confidence = best_intent

        # Get suggested operations
        suggested_ops = self._generate_suggested_operations(
            intent_type, message_lower, context
        )

        # Extract parameters from message
        extracted_params = self._extract_parameters(intent_type, message_lower)

        # Generate explanation
        explanation = self._generate_explanation(intent_type, suggested_ops)

        return Intent(
            intent_type=intent_type,
            confidence=confidence,
            suggested_operations=suggested_ops,
            extracted_params=extracted_params,
            explanation=explanation,
        )

    def _score_intent(self, message: str, config: Dict[str, Any]) -> float:
        """
        Score an intent based on keyword and pattern matches.

        Args:
            message: Lowercase user message
            config: Intent configuration with keywords and patterns

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0

        # Check keyword matches (0.3 score per keyword)
        keyword_matches = sum(1 for keyword in config["keywords"] if keyword in message)
        if keyword_matches > 0:
            score += min(0.6, keyword_matches * 0.3)

        # Check pattern matches (0.4 score per pattern)
        pattern_matches = sum(
            1 for pattern in config["compiled_patterns"] if pattern.search(message)
        )
        if pattern_matches > 0:
            score += min(0.4, pattern_matches * 0.4)

        return min(1.0, score)

    def _generate_suggested_operations(
        self, intent_type: IntentType, message: str, context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate suggested workflow operations based on intent.

        Args:
            intent_type: Detected intent type
            message: User message
            context: Optional context

        Returns:
            List of suggested operations with arguments
        """
        config = self.INTENT_PATTERNS.get(intent_type, {})
        operations = config.get("operations", [])

        suggested = []
        file_type = context.get("file_type", "xlsx") if context else "xlsx"

        if intent_type == IntentType.EXTRACT_COLUMNS:
            # Extract column names if mentioned
            columns = self._extract_column_names(message)
            suggested.append(
                {
                    "operation": "excel/extract-columns-to-file",
                    "arguments": {
                        "columns": columns if columns else ["column1", "column2"],
                        "remove_duplicates": "unique" in message
                        or "distinct" in message,
                    },
                    "description": "Extract specific columns to a new file",
                }
            )

        elif intent_type == IntentType.CONVERT_FORMAT:
            if "csv" in message and file_type != "csv":
                suggested.append(
                    {
                        "operation": "csv/convert-to-excel",
                        "arguments": {"sheet_name": "Sheet1"},
                        "description": "Convert CSV to Excel format",
                    }
                )
            elif "json" in message:
                suggested.append(
                    {
                        "operation": "json/generate",
                        "arguments": {
                            "pretty_print": True,
                            "null_handling": "include",
                            "array_wrapper": True,
                        },
                        "description": "Convert data to JSON format",
                    }
                )

        elif intent_type == IntentType.NORMALIZE_DATA:
            # Detect normalization types
            normalizations = []
            if "uppercase" in message or "upper" in message:
                normalizations.append({"column": "column_name", "type": "uppercase"})
            if "lowercase" in message or "lower" in message:
                normalizations.append({"column": "column_name", "type": "lowercase"})
            if "trim" in message:
                normalizations.append({"column": "column_name", "type": "trim"})
            if "phone" in message:
                normalizations.append({"column": "phone", "type": "phone_number"})

            if not normalizations:
                normalizations = [{"column": "column_name", "type": "trim"}]

            suggested.append(
                {
                    "operation": "normalization/apply",
                    "arguments": {
                        "normalizations": normalizations,
                        "return_report": True,
                    },
                    "description": "Apply data normalization rules",
                }
            )

        elif intent_type == IntentType.GENERATE_SQL:
            suggested.append(
                {
                    "operation": "sql/generate",
                    "arguments": {
                        "table_name": "data",
                        "database_type": "postgresql",
                        "include_transaction": True,
                    },
                    "description": "Generate SQL INSERT statements",
                }
            )

        elif intent_type == IntentType.GENERATE_JSON:
            suggested.append(
                {
                    "operation": "json/generate",
                    "arguments": {
                        "pretty_print": True,
                        "null_handling": "include",
                        "array_wrapper": True,
                    },
                    "description": "Generate JSON output",
                }
            )

        elif intent_type == IntentType.SEARCH_FILTER:
            suggested.append(
                {
                    "operation": "excel/search",
                    "arguments": {
                        "conditions": [
                            {
                                "column": "column_name",
                                "operator": "equals",
                                "value": "search_value",
                            }
                        ],
                        "logic": "AND",
                        "output_format": "excel",
                    },
                    "description": "Search and filter data",
                }
            )

        elif intent_type == IntentType.BIND_DATA:
            suggested.append(
                {
                    "operation": "excel/bind-single-key",
                    "arguments": {
                        "bind_file": "path_to_bind_file.xlsx",
                        "comparison_column": "id",
                        "bind_columns": ["column1", "column2"],
                    },
                    "description": "Bind data from another file",
                }
            )

        elif intent_type == IntentType.MAP_COLUMNS:
            suggested.append(
                {
                    "operation": "excel/map-columns",
                    "arguments": {"mapping": {"old_name": "new_name"}},
                    "description": "Rename/map columns",
                }
            )

        return suggested

    def _extract_parameters(
        self, intent_type: IntentType, message: str
    ) -> Dict[str, Any]:
        """
        Extract parameters from user message.

        Args:
            intent_type: Detected intent type
            message: User message

        Returns:
            Dictionary of extracted parameters
        """
        params = {}

        # Extract column names
        columns = self._extract_column_names(message)
        if columns:
            params["columns"] = columns

        # Extract boolean flags
        if "unique" in message or "distinct" in message:
            params["remove_duplicates"] = True

        if "uppercase" in message or "upper" in message:
            params["case"] = "upper"
        elif "lowercase" in message or "lower" in message:
            params["case"] = "lower"

        return params

    def _extract_column_names(self, message: str) -> List[str]:
        """
        Extract column names from message.

        Args:
            message: User message

        Returns:
            List of column names
        """
        columns = []

        # Pattern: "columns: col1, col2, col3"
        match = re.search(r"columns?[:\s]+([a-zA-Z0-9_,\s]+)", message, re.IGNORECASE)
        if match:
            column_str = match.group(1)
            columns = [col.strip() for col in column_str.split(",")]

        # Pattern: "extract name, email, phone"
        if not columns:
            match = re.search(
                r"(?:extract|get|select)\s+([a-zA-Z0-9_,\s]+?)(?:\s+from|\s+column|\s*$)",
                message,
                re.IGNORECASE,
            )
            if match:
                column_str = match.group(1)
                # Filter out common words
                potential_cols = [col.strip() for col in column_str.split(",")]
                columns = [
                    col
                    for col in potential_cols
                    if col and len(col) > 1 and col not in ["the", "and", "or", "data"]
                ]

        return columns

    def _generate_explanation(
        self, intent_type: IntentType, suggested_ops: List[Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable explanation of the intent.

        Args:
            intent_type: Detected intent type
            suggested_ops: Suggested operations

        Returns:
            Explanation text
        """
        explanations = {
            IntentType.EXTRACT_COLUMNS: "I can help you extract specific columns from your file.",
            IntentType.CONVERT_FORMAT: "I can convert your file to a different format.",
            IntentType.NORMALIZE_DATA: "I can normalize and clean your data.",
            IntentType.GENERATE_SQL: "I can generate SQL INSERT statements from your data.",
            IntentType.GENERATE_JSON: "I can convert your data to JSON format.",
            IntentType.SEARCH_FILTER: "I can search and filter your data based on conditions.",
            IntentType.BIND_DATA: "I can bind/merge data from another file.",
            IntentType.MAP_COLUMNS: "I can rename or remap your column names.",
        }

        base_explanation = explanations.get(
            intent_type, "I can help you process your file."
        )

        if suggested_ops:
            operation_desc = suggested_ops[0].get("description", "")
            return f"{base_explanation} I suggest: {operation_desc}"

        return base_explanation

    def get_supported_operations(self) -> Dict[str, List[str]]:
        """
        Get all supported operations by intent type.

        Returns:
            Dictionary mapping intent types to operation lists
        """
        return {
            intent_type.value: config["operations"]
            for intent_type, config in self.INTENT_PATTERNS.items()
        }
