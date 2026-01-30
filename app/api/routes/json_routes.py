"""
JSON Generation Routes

This module provides API endpoints for JSON generation operations.
"""

import os
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.excel_service import ExcelService
from app.services.json_generation_service import JSONGenerationService
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError

json_bp = Blueprint("json", __name__)


def get_services():
    """Get service instances with current app config."""
    config = current_app.config.get("PYCELIZE")
    return ExcelService(config), JSONGenerationService(config)


@json_bp.route("/generate", methods=["POST"])
def generate_json():
    """
    Generate JSON from Excel file with column mapping.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file (required)
        - columns: JSON array of column names to extract (optional)
        - column_mapping: JSON object mapping Excel columns to JSON keys (optional)
        - pretty_print: Boolean (default: true)
        - null_handling: String - "include", "exclude", "default" (default: "include")
        - array_wrapper: Boolean (default: true)
        - output_filename: Optional string
    
    Returns:
        JSON with download URL for the generated JSON file
    
    Example:
        curl -X POST -F "file=@data.xlsx" \\
             -F 'column_mapping={"Name": "full_name", "Email": "email"}' \\
             -F "pretty_print=true" \\
             http://localhost:5050/api/v1/json/generate
    """
    try:
        # Validate file upload
        Validators.validate_file_uploaded(request.files.get("file"))
        
        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")
        
        # Parse request parameters
        columns_str = request.form.get("columns", "[]")
        columns = json.loads(columns_str) if columns_str else []
        
        column_mapping_str = request.form.get("column_mapping", "{}")
        column_mapping = json.loads(column_mapping_str) if column_mapping_str else {}
        
        pretty_print = request.form.get("pretty_print", "true").lower() == "true"
        null_handling = request.form.get("null_handling", "include")
        array_wrapper = request.form.get("array_wrapper", "true").lower() == "true"
        output_filename = request.form.get("output_filename")
        
        # Validate null_handling
        if null_handling not in ["include", "exclude", "default"]:
            raise ValidationError(
                f"Invalid null_handling: {null_handling}. "
                f"Must be 'include', 'exclude', or 'default'"
            )
        
        # Ensure directories exist
        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        
        # Save uploaded file
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)
        
        try:
            excel_service, json_service = get_services()
            
            # Read Excel file
            df = excel_service.read_excel(file_path)
            
            # Extract specified columns if provided
            if columns:
                missing_columns = [col for col in columns if col not in df.columns]
                if missing_columns:
                    raise ValidationError(
                        f"Columns not found: {', '.join(missing_columns)}"
                    )
                df = df[columns]
            
            # Use all columns if no mapping provided
            if not column_mapping:
                column_mapping = {col: col for col in df.columns}
            
            # Generate output filename
            if output_filename:
                output_file = output_filename
                if not output_file.endswith('.json'):
                    output_file += '.json'
            else:
                output_file = generate_output_filename(file.filename, "generated", ".json")
            
            output_path = os.path.join(output_folder, output_file)
            
            # Generate JSON
            result = json_service.generate_json(
                data=df,
                column_mapping=column_mapping,
                output_path=output_path,
                pretty_print=pretty_print,
                null_handling=null_handling,
                array_wrapper=array_wrapper,
            )
            
            # Build download URL
            download_url = f"{request.scheme}://{request.host}/api/v1/files/downloads/{output_file}"
            
            response_data = {
                "download_url": download_url,
                "total_records": result["total_records"],
                "file_size": result["file_size"],
            }
            
            response = ResponseBuilder.success(
                data=response_data,
                message="JSON file generated successfully",
            )
            return jsonify(response), 200
            
        finally:
            # Clean up uploaded file
            FileUtils.delete_file(file_path)
    
    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@json_bp.route("/generate-with-template", methods=["POST"])
def generate_json_with_template():
    """
    Generate JSON using custom template with placeholder substitution.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file (required)
        - template: JSON string or object template (required)
        - column_mapping: JSON object mapping placeholders to Excel columns (required)
        - pretty_print: Boolean (default: true)
        - aggregation_mode: String - "array", "single", "nested" (default: "array")
        - output_filename: Optional string
    
    Template placeholders:
        - {column_name}: Basic substitution
        - {column_name:type}: With type conversion (int, float, bool, datetime)
        - {column_name|default}: With default if null
    
    Returns:
        JSON with download URL for the generated JSON file
    
    Example:
        curl -X POST -F "file=@users.xlsx" \\
             -F 'template={"user":{"id":"{user_id}","name":"{first_name} {last_name}"}}' \\
             -F 'column_mapping={"user_id":"UserID","first_name":"FirstName","last_name":"LastName"}' \\
             -F "aggregation_mode=array" \\
             http://localhost:5050/api/v1/json/generate-with-template
    """
    try:
        # Validate file upload
        Validators.validate_file_uploaded(request.files.get("file"))
        
        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")
        
        # Parse required parameters
        template_str = request.form.get("template")
        if not template_str:
            raise ValidationError("template is required")
        
        column_mapping_str = request.form.get("column_mapping")
        if not column_mapping_str:
            raise ValidationError("column_mapping is required")
        
        # Parse JSON parameters
        try:
            # Template can be a JSON string or already parsed
            template = json.loads(template_str) if isinstance(template_str, str) else template_str
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid template JSON: {str(e)}")
        
        try:
            column_mapping = json.loads(column_mapping_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid column_mapping JSON: {str(e)}")
        
        if not column_mapping:
            raise ValidationError("column_mapping cannot be empty")
        
        # Parse optional parameters
        pretty_print = request.form.get("pretty_print", "true").lower() == "true"
        aggregation_mode = request.form.get("aggregation_mode", "array")
        output_filename = request.form.get("output_filename")
        
        # Validate aggregation_mode
        if aggregation_mode not in ["array", "single", "nested"]:
            raise ValidationError(
                f"Invalid aggregation_mode: {aggregation_mode}. "
                f"Must be 'array', 'single', or 'nested'"
            )
        
        # Ensure directories exist
        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        
        # Save uploaded file
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)
        
        try:
            excel_service, json_service = get_services()
            
            # Read Excel file
            df = excel_service.read_excel(file_path)
            
            # Generate output filename
            if output_filename:
                output_file = output_filename
                if not output_file.endswith('.json'):
                    output_file += '.json'
            else:
                output_file = generate_output_filename(
                    file.filename, "generated_template", ".json"
                )
            
            output_path = os.path.join(output_folder, output_file)
            
            # Generate JSON with template
            result = json_service.generate_json_with_template(
                data=df,
                template=template,
                column_mapping=column_mapping,
                output_path=output_path,
                pretty_print=pretty_print,
                aggregation_mode=aggregation_mode,
            )
            
            # Build download URL
            download_url = f"{request.scheme}://{request.host}/api/v1/files/downloads/{output_file}"
            
            response_data = {
                "download_url": download_url,
                "total_records": result["total_records"],
                "file_size": result["file_size"],
            }
            
            response = ResponseBuilder.success(
                data=response_data,
                message="JSON file generated successfully with template",
            )
            return jsonify(response), 200
            
        finally:
            # Clean up uploaded file
            FileUtils.delete_file(file_path)
    
    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
