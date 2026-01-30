"""
JSON Generation Service Implementation

This module provides JSON generation functionality from Excel data
with support for column mapping and custom template-based generation.
"""

import os
import json
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from copy import deepcopy
import pandas as pd
import numpy as np

from app.core.config import Config
from app.core.exceptions import ValidationError, FileProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class JSONGenerationService:
    """
    Service for JSON generation operations from Excel data.
    
    Provides functionality to:
    - Generate JSON with standard column mapping
    - Generate JSON using custom templates
    - Support nested structures
    - Handle normalization
    
    Attributes:
        config: Application configuration
        excel_service: Excel service for file operations
        output_folder: Folder for generated JSON files
        
    Example:
        >>> service = JSONGenerationService(config)
        >>> result = service.generate_json(df, column_mapping, output_path)
        >>> print(result['total_records'])
        150
    """

    def __init__(self, config: Config):
        """
        Initialize JSONGenerationService with configuration.
        
        Args:
            config: Application configuration instance
        """
        self.config = config
        self.output_folder = config.get("file.output_folder", "outputs")
        
        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_json(
        self,
        data: pd.DataFrame,
        column_mapping: Dict[str, str],
        output_path: str,
        pretty_print: bool = True,
        null_handling: str = "include",
        array_wrapper: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate JSON array from Excel data with standard column mapping.
        
        Args:
            data: Source DataFrame
            column_mapping: Map Excel columns to JSON keys
            output_path: Path for output JSON file
            pretty_print: Whether to format JSON with indentation (default: True)
            null_handling: How to handle null values - "include", "exclude", "default" (default: "include")
            array_wrapper: Whether to wrap objects in array (default: True)
            
        Returns:
            Dictionary containing:
                - output_path: Path to generated JSON file
                - total_records: Number of JSON objects generated
                - file_size: Size of output file in bytes
                - timestamp: Generation timestamp
                
        Raises:
            ValidationError: If validation fails
            FileProcessingError: If file operations fail
            
        Example:
            >>> df = pd.DataFrame({'Name': ['Alice'], 'Email': ['alice@ex.com']})
            >>> mapping = {'Name': 'full_name', 'Email': 'email'}
            >>> result = service.generate_json(df, mapping, 'output.json')
        """
        logger.info(f"Generating JSON from {len(data)} rows with column mapping")
        
        try:
            # Validate DataFrame is not empty
            if data.empty:
                logger.warning("DataFrame is empty, generating empty JSON array")
                json_data = [] if array_wrapper else {}
            else:
                # Validate all mapped columns exist in DataFrame
                missing_columns = [col for col in column_mapping.keys() if col not in data.columns]
                if missing_columns:
                    raise ValidationError(
                        f"Columns not found in data: {', '.join(missing_columns)}"
                    )
                
                # Generate JSON objects for each row
                json_objects = []
                for idx, row in data.iterrows():
                    json_obj = {}
                    for source_col, target_key in column_mapping.items():
                        value = row[source_col]
                        
                        # Convert pandas/numpy types to native Python types
                        if pd.isna(value):
                            value = None
                        elif isinstance(value, (np.integer, np.floating)):
                            value = value.item()
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            value = value.isoformat() if pd.notna(value) else None
                        elif isinstance(value, np.bool_):
                            value = bool(value)
                        
                        json_obj[target_key] = value
                    
                    # Handle null values based on strategy
                    json_obj = self._handle_null_values(json_obj, null_handling)
                    json_objects.append(json_obj)
                
                # Wrap in array or return single object
                if array_wrapper:
                    json_data = json_objects
                else:
                    json_data = json_objects[0] if len(json_objects) == 1 else json_objects
            
            # Write to JSON file with proper formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(json_data, f, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(output_path)
            
            result = {
                "output_path": output_path,
                "total_records": len(json_data) if isinstance(json_data, list) else 1,
                "file_size": file_size,
                "timestamp": datetime.now().isoformat(),
            }
            
            logger.info(
                f"Successfully generated JSON file: {output_path} "
                f"({result['total_records']} records, {file_size} bytes)"
            )
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating JSON: {str(e)}")
            raise FileProcessingError(f"Failed to generate JSON: {str(e)}")

    def generate_json_with_template(
        self,
        data: pd.DataFrame,
        template: Union[str, Dict],
        column_mapping: Dict[str, str],
        output_path: str,
        pretty_print: bool = True,
        aggregation_mode: str = "array",
    ) -> Dict[str, Any]:
        """
        Generate JSON using custom template with placeholder substitution.
        
        Args:
            data: Source DataFrame
            template: JSON template string or dict structure
            column_mapping: Map placeholders to Excel columns
            output_path: Path for output JSON file
            pretty_print: Format JSON with indentation
            aggregation_mode: "array", "single", "nested" (default: "array")
            
        Returns:
            Dictionary containing:
                - output_path: Path to generated JSON file
                - total_records: Number of JSON objects generated
                - file_size: Size of output file in bytes
                - timestamp: Generation timestamp
                
        Raises:
            ValidationError: If validation fails
            FileProcessingError: If file operations fail
            
        Example:
            >>> template = {"user": {"id": "{user_id}", "name": "{name}"}}
            >>> mapping = {"user_id": "UserID", "name": "Name"}
            >>> result = service.generate_json_with_template(df, template, mapping, 'out.json')
        """
        logger.info(f"Generating JSON with template from {len(data)} rows")
        
        try:
            # Parse template (if string, convert to dict)
            if isinstance(template, str):
                try:
                    template_dict = json.loads(template)
                except json.JSONDecodeError as e:
                    raise ValidationError(f"Invalid JSON template: {str(e)}")
            elif isinstance(template, dict):
                template_dict = template
            else:
                raise ValidationError("Template must be a JSON string or dictionary")
            
            # Validate template structure
            if not template_dict:
                raise ValidationError("Template cannot be empty")
            
            # Validate DataFrame is not empty
            if data.empty:
                logger.warning("DataFrame is empty, generating empty JSON array")
                json_data = []
            else:
                # Validate all mapped columns exist in DataFrame
                missing_columns = [col for col in column_mapping.values() if col not in data.columns]
                if missing_columns:
                    raise ValidationError(
                        f"Columns not found in data: {', '.join(missing_columns)}"
                    )
                
                # Generate JSON objects for each row
                json_objects = []
                for idx, row in data.iterrows():
                    # Create row data dictionary
                    row_data = {}
                    for placeholder, column in column_mapping.items():
                        value = row[column]
                        
                        # Convert pandas/numpy types to native Python types
                        if pd.isna(value):
                            value = None
                        elif isinstance(value, (np.integer, np.floating)):
                            value = value.item()
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            value = value.isoformat() if pd.notna(value) else None
                        elif isinstance(value, np.bool_):
                            value = bool(value)
                        else:
                            value = str(value)
                        
                        row_data[placeholder] = value
                    
                    # Deep copy template and substitute placeholders
                    json_obj = self._substitute_placeholders(
                        deepcopy(template_dict), 
                        row_data, 
                        column_mapping
                    )
                    json_objects.append(json_obj)
                
                # Aggregate results based on aggregation_mode
                if aggregation_mode == "array":
                    json_data = json_objects
                elif aggregation_mode == "single":
                    json_data = json_objects[0] if len(json_objects) == 1 else json_objects
                elif aggregation_mode == "nested":
                    json_data = {"items": json_objects, "count": len(json_objects)}
                else:
                    raise ValidationError(
                        f"Invalid aggregation_mode: {aggregation_mode}. "
                        f"Must be 'array', 'single', or 'nested'"
                    )
            
            # Write formatted JSON to file
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(json_data, f, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(output_path)
            
            # Calculate total records
            if aggregation_mode == "nested":
                total_records = json_data.get("count", 0) if isinstance(json_data, dict) else 0
            elif isinstance(json_data, list):
                total_records = len(json_data)
            else:
                total_records = 1
            
            result = {
                "output_path": output_path,
                "total_records": total_records,
                "file_size": file_size,
                "timestamp": datetime.now().isoformat(),
            }
            
            logger.info(
                f"Successfully generated JSON file with template: {output_path} "
                f"({result['total_records']} records, {file_size} bytes)"
            )
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating JSON with template: {str(e)}")
            raise FileProcessingError(f"Failed to generate JSON with template: {str(e)}")

    def _substitute_placeholders(
        self,
        template_obj: Any,
        row_data: Dict[str, Any],
        column_mapping: Dict[str, str],
    ) -> Any:
        """
        Recursively substitute placeholders in template structure.
        
        This method handles different types (dict, list, string, number)
        and replaces placeholders using regex patterns. It preserves
        data types where appropriate.
        
        Args:
            template_obj: Template object/structure
            row_data: Data for current row
            column_mapping: Mapping configuration
            
        Returns:
            Substituted object/structure
            
        Example:
            >>> template = {"id": "{user_id}", "name": "{first} {last}"}
            >>> row_data = {"user_id": 1, "first": "John", "last": "Doe"}
            >>> result = service._substitute_placeholders(template, row_data, {})
            >>> print(result)
            {'id': '1', 'name': 'John Doe'}
        """
        if isinstance(template_obj, dict):
            # Recursively process dictionary values
            result = {}
            for key, value in template_obj.items():
                result[key] = self._substitute_placeholders(value, row_data, column_mapping)
            return result
        
        elif isinstance(template_obj, list):
            # Recursively process list items
            return [
                self._substitute_placeholders(item, row_data, column_mapping)
                for item in template_obj
            ]
        
        elif isinstance(template_obj, str):
            # Replace placeholders in string
            # Support formats: {placeholder}, {placeholder:type}, {placeholder|default}
            result = template_obj
            
            # Find all placeholders in the string
            placeholder_pattern = r'\{([^}]+)\}'
            matches = re.findall(placeholder_pattern, result)
            
            for match in matches:
                # Parse placeholder syntax
                parts = match.split(':')
                placeholder = parts[0].strip()
                type_hint = parts[1].strip() if len(parts) > 1 else None
                
                # Check for default value syntax
                if '|' in placeholder:
                    placeholder, default = placeholder.split('|', 1)
                    placeholder = placeholder.strip()
                    default = default.strip()
                else:
                    default = None
                
                # Get value from row_data
                value = row_data.get(placeholder)
                
                # Handle None/null values
                if value is None:
                    if default is not None:
                        value = default
                    else:
                        value = None
                
                # Apply type conversion if specified
                if value is not None and type_hint:
                    try:
                        if type_hint == 'int':
                            value = int(float(value)) if value != '' else None
                        elif type_hint == 'float':
                            value = float(value) if value != '' else None
                        elif type_hint == 'bool':
                            if isinstance(value, str):
                                value = value.lower() in ('true', '1', 'yes', 'on')
                            else:
                                value = bool(value)
                        elif type_hint == 'datetime':
                            # Keep as string if already ISO format
                            value = str(value)
                    except (ValueError, TypeError):
                        # If conversion fails, keep original value
                        pass
                
                # Replace placeholder with value
                placeholder_full = f'{{{match}}}'
                if value is None:
                    # If the entire string is just the placeholder, return None
                    if result == placeholder_full:
                        return None
                    # Otherwise replace with empty string or "null"
                    result = result.replace(placeholder_full, '')
                else:
                    result = result.replace(placeholder_full, str(value))
            
            return result
        
        else:
            # Return other types as-is (numbers, booleans, None)
            return template_obj

    def _handle_null_values(
        self,
        data_dict: Dict[str, Any],
        strategy: str = "include"
    ) -> Dict[str, Any]:
        """
        Apply null handling strategy to a dictionary.
        
        Args:
            data_dict: Dictionary to process
            strategy: Null handling strategy
                - "include": Keep null values (default)
                - "exclude": Remove null values
                - "default": Replace nulls with type-specific defaults
                
        Returns:
            Processed dictionary
            
        Example:
            >>> data = {"name": "Alice", "age": None, "email": None}
            >>> result = service._handle_null_values(data, "exclude")
            >>> print(result)
            {'name': 'Alice'}
        """
        if strategy == "include":
            # Keep all values including nulls
            return data_dict
        
        elif strategy == "exclude":
            # Remove null values
            return {k: v for k, v in data_dict.items() if v is not None}
        
        elif strategy == "default":
            # Replace nulls with defaults
            result = {}
            for key, value in data_dict.items():
                if value is None:
                    # Use empty string as default
                    result[key] = ""
                else:
                    result[key] = value
            return result
        
        else:
            # Invalid strategy, return as-is
            logger.warning(f"Invalid null_handling strategy: {strategy}, using 'include'")
            return data_dict
