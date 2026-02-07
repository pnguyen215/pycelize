"""
Message Service for Conversational Chat

This module provides intelligent message processing and workflow operation suggestions.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.chat.models import MessageType
from app.chat.repository import ConversationRepository

logger = logging.getLogger(__name__)


class MessageService:
    """
    Service for processing messages and suggesting workflow operations.
    
    Acts as the intelligent assistant in the conversational chat system.
    """

    # Available workflow operations with their descriptions and arguments
    AVAILABLE_OPERATIONS = [
        {
            "name": "excel/extract-columns",
            "display_name": "Extract Columns to File",
            "description": "Extract specific columns from Excel file to a new file",
            "category": "excel",
            "arguments": [
                {
                    "name": "columns",
                    "type": "list",
                    "required": True,
                    "description": "List of column names to extract",
                    "example": ["customer_id", "name", "email"]
                }
            ]
        },
        {
            "name": "excel/normalize-columns",
            "display_name": "Normalize Column Data",
            "description": "Normalize and clean data in Excel columns",
            "category": "excel",
            "arguments": [
                {
                    "name": "columns",
                    "type": "list",
                    "required": True,
                    "description": "List of column names to normalize"
                },
                {
                    "name": "normalization_type",
                    "type": "string",
                    "required": False,
                    "description": "Type of normalization (lowercase, uppercase, trim, etc.)",
                    "default": "trim"
                }
            ]
        },
        {
            "name": "excel/convert-to-json",
            "display_name": "Convert to JSON",
            "description": "Convert Excel data to JSON format",
            "category": "conversion",
            "arguments": [
                {
                    "name": "orient",
                    "type": "string",
                    "required": False,
                    "description": "JSON orientation (records, split, index, columns, values)",
                    "default": "records"
                }
            ]
        },
        {
            "name": "excel/convert-to-csv",
            "display_name": "Convert to CSV",
            "description": "Convert Excel file to CSV format",
            "category": "conversion",
            "arguments": [
                {
                    "name": "delimiter",
                    "type": "string",
                    "required": False,
                    "description": "CSV delimiter character",
                    "default": ","
                }
            ]
        },
        {
            "name": "csv/convert-to-excel",
            "display_name": "Convert CSV to Excel",
            "description": "Convert CSV file to Excel format",
            "category": "conversion",
            "arguments": []
        },
        {
            "name": "excel/generate-sql",
            "display_name": "Generate SQL Insert Statements",
            "description": "Generate SQL INSERT statements from Excel data",
            "category": "sql",
            "arguments": [
                {
                    "name": "table_name",
                    "type": "string",
                    "required": True,
                    "description": "Target database table name"
                },
                {
                    "name": "database_type",
                    "type": "string",
                    "required": False,
                    "description": "Database type (postgresql, mysql, sqlite)",
                    "default": "postgresql"
                }
            ]
        },
        {
            "name": "excel/search-data",
            "display_name": "Search Data",
            "description": "Search for specific data in Excel file",
            "category": "analysis",
            "arguments": [
                {
                    "name": "search_term",
                    "type": "string",
                    "required": True,
                    "description": "Term to search for"
                },
                {
                    "name": "columns",
                    "type": "list",
                    "required": False,
                    "description": "Specific columns to search in (searches all if not specified)"
                }
            ]
        }
    ]

    def __init__(self, repository: ConversationRepository):
        """
        Initialize message service.

        Args:
            repository: Conversation repository instance
        """
        self.repository = repository

    def process_user_message(
        self, chat_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate system response.

        Args:
            chat_id: Conversation identifier
            content: User message content
            metadata: Optional metadata

        Returns:
            Dictionary with system response and suggested operations
        """
        # Save user message
        user_message = self.repository.add_message(
            chat_id=chat_id,
            message_type=MessageType.USER,
            content=content,
            metadata=metadata or {}
        )

        # Analyze intent and suggest operations
        suggested_ops = self._suggest_operations(content)

        # Generate system response
        if suggested_ops:
            response_content = self._generate_operation_suggestions(suggested_ops)
        else:
            response_content = (
                "I can help you process your data with various operations. "
                "Available categories: Excel processing, CSV conversion, "
                "SQL generation, and data analysis. "
                "Please upload a file or tell me what you'd like to do."
            )

        # Save system response
        system_message = self.repository.add_message(
            chat_id=chat_id,
            message_type=MessageType.SYSTEM,
            content=response_content,
            metadata={
                "suggested_operations": suggested_ops,
                "response_type": "operation_suggestions"
            }
        )

        return {
            "user_message": user_message.to_dict(),
            "system_message": system_message.to_dict(),
            "suggested_operations": suggested_ops
        }

    def _suggest_operations(self, content: str) -> List[Dict[str, Any]]:
        """
        Analyze user message and suggest relevant operations.

        Args:
            content: User message content

        Returns:
            List of suggested operations
        """
        content_lower = content.lower()
        suggestions = []

        # Simple keyword-based suggestion logic
        keywords_map = {
            "extract": ["excel/extract-columns"],
            "column": ["excel/extract-columns", "excel/normalize-columns"],
            "normalize": ["excel/normalize-columns"],
            "clean": ["excel/normalize-columns"],
            "json": ["excel/convert-to-json"],
            "csv": ["excel/convert-to-csv", "csv/convert-to-excel"],
            "sql": ["excel/generate-sql"],
            "search": ["excel/search-data"],
            "find": ["excel/search-data"],
            "convert": ["excel/convert-to-json", "excel/convert-to-csv", "csv/convert-to-excel"],
        }

        # Find matching operations
        suggested_names = set()
        for keyword, ops in keywords_map.items():
            if keyword in content_lower:
                suggested_names.update(ops)

        # Get full operation details
        for op in self.AVAILABLE_OPERATIONS:
            if op["name"] in suggested_names:
                suggestions.append(op)

        # If no specific matches, return common operations
        if not suggestions:
            suggestions = [
                op for op in self.AVAILABLE_OPERATIONS
                if op["name"] in [
                    "excel/extract-columns",
                    "excel/convert-to-json",
                    "excel/convert-to-csv"
                ]
            ]

        return suggestions

    def _generate_operation_suggestions(self, operations: List[Dict[str, Any]]) -> str:
        """
        Generate a formatted string with operation suggestions.

        Args:
            operations: List of operation dictionaries

        Returns:
            Formatted suggestion text
        """
        lines = ["I can help you with the following operations:"]
        lines.append("")

        for i, op in enumerate(operations, 1):
            lines.append(f"{i}. **{op['display_name']}**")
            lines.append(f"   {op['description']}")
            
            if op['arguments']:
                args_text = ", ".join([arg['name'] for arg in op['arguments'] if arg['required']])
                if args_text:
                    lines.append(f"   Required: {args_text}")
            
            lines.append("")

        lines.append("Please select an operation or ask me a specific question about your data.")
        return "\n".join(lines)

    def handle_file_upload(
        self, chat_id: str, filename: str, file_path: str
    ) -> Dict[str, Any]:
        """
        Handle file upload and suggest appropriate operations.

        Args:
            chat_id: Conversation identifier
            filename: Uploaded filename
            file_path: File path

        Returns:
            System response with operation suggestions
        """
        # Determine file type
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Save file upload message (already done in upload endpoint)
        # Generate appropriate suggestions based on file type
        if file_extension in ['xlsx', 'xls']:
            suggested_ops = [
                op for op in self.AVAILABLE_OPERATIONS
                if op['category'] in ['excel', 'conversion', 'sql']
            ]
            message = (
                f"Excel file **{filename}** uploaded successfully! "
                f"I can help you process this file with various operations:"
            )
        elif file_extension == 'csv':
            suggested_ops = [
                op for op in self.AVAILABLE_OPERATIONS
                if op['name'] in ['csv/convert-to-excel', 'excel/search-data']
            ]
            message = (
                f"CSV file **{filename}** uploaded successfully! "
                f"I can help you convert or analyze this file:"
            )
        else:
            suggested_ops = self.AVAILABLE_OPERATIONS
            message = (
                f"File **{filename}** uploaded successfully! "
                f"Here are available operations:"
            )

        response_content = message + "\n\n" + self._generate_operation_suggestions(suggested_ops)

        # Save system response
        system_message = self.repository.add_message(
            chat_id=chat_id,
            message_type=MessageType.SYSTEM,
            content=response_content,
            metadata={
                "suggested_operations": suggested_ops,
                "response_type": "file_upload_response",
                "filename": filename
            }
        )

        return {
            "system_message": system_message.to_dict(),
            "suggested_operations": suggested_ops
        }

    @staticmethod
    def get_available_operations() -> List[Dict[str, Any]]:
        """
        Get list of all available workflow operations.

        Returns:
            List of operation definitions
        """
        return MessageService.AVAILABLE_OPERATIONS

    @staticmethod
    def get_operation_by_name(operation_name: str) -> Optional[Dict[str, Any]]:
        """
        Get operation details by name.

        Args:
            operation_name: Operation name

        Returns:
            Operation dictionary or None if not found
        """
        for op in MessageService.AVAILABLE_OPERATIONS:
            if op["name"] == operation_name:
                return op
        return None
