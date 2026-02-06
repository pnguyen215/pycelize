"""
CSV Processing Routes

This module provides API endpoints for CSV file operations.
"""

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.csv_service import CSVService
from app.services.search_service import SearchService
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError
from app.models.request import SearchRequest

csv_bp = Blueprint("csv", __name__)


def get_csv_service() -> CSVService:
    """Get CSVService instance with current app config."""
    config = current_app.config.get("PYCELIZE")
    return CSVService(config)


def get_search_service() -> SearchService:
    """Get SearchService instance with current app config."""
    config = current_app.config.get("PYCELIZE")
    return SearchService(config)


@csv_bp.route("/info", methods=["POST"])
def get_csv_info():
    """
    Get information about a CSV file.

    Request:
        POST with multipart/form-data containing 'file'

    Returns:
        JSON with file information

    Example:
        curl -X POST -F "file=@data.csv" http://localhost:5050/api/v1/csv/info
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")

        FileUtils.ensure_directory(upload_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            service = get_csv_service()
            info = service.get_file_info(file_path)

            response = ResponseBuilder.success(
                data=info, message="CSV file information retrieved successfully"
            )
            return jsonify(response), 200

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@csv_bp.route("/convert-to-excel", methods=["POST"])
def convert_csv_to_excel():
    """
    Convert a CSV file to Excel format.
    
    Request:
        POST with multipart/form-data:
        - file: CSV file
        - sheet_name: Optional sheet name (default: 'Sheet1')
        - output_filename: Optional output filename
    
    Returns:
        Excel file
    
    Example:
        curl -X POST -F "file=@data.csv" \
             -F "sheet_name=Data" \
             http://localhost:5050/api/v1/csv/convert-to-excel \
             --output result.xlsx
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        sheet_name = request.form.get("sheet_name", "Sheet1")
        output_filename = request.form.get("output_filename")

        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            service = get_csv_service()

            # Generate output path
            if output_filename:
                output_path = os.path.join(
                    output_folder, secure_filename(output_filename)
                )
            else:
                output_path = os.path.join(
                    output_folder,
                    generate_output_filename(file.filename, "converted", ".xlsx"),
                )

            # Convert
            result_path = service.convert_to_excel(
                csv_path=file_path, output_path=output_path, sheet_name=sheet_name
            )

            # Build download URL
            host = request.host
            filename = os.path.basename(output_path)
            download_url = f"http://{host}/api/v1/files/downloads/{filename}"
            response = ResponseBuilder.success(
                data={"download_url": download_url},
                message="Converted to Excel file successfully",
            )
            return jsonify(response), 200

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@csv_bp.route("/search", methods=["POST"])
def search_csv():
    """
    Search and filter CSV file data based on multiple conditions.
    
    This endpoint allows advanced filtering of CSV data with multiple conditions
    across different columns, supporting various operators and logical combinations.
    
    Request:
        POST with multipart/form-data:
        - file: CSV file
        - conditions: JSON array of search conditions
        - logic: Logical operator (AND or OR) - default: AND
        - output_format: Output format (xlsx, csv, or json) - default: csv
        - output_filename: Optional custom output filename
    
    Returns:
        JSON with download URL for the filtered results file
    
    Example:
        curl -X POST -F "file=@data.csv" \
             -F 'conditions=[{"column": "customer_id", "operator": "equals", "value": "021201"}]' \
             -F "logic=AND" \
             -F "output_format=csv" \
             http://localhost:5050/api/v1/csv/search
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse request parameters
        conditions_str = request.form.get("conditions", "[]")
        conditions_data = json.loads(conditions_str)
        logic = request.form.get("logic", "AND").upper()
        output_format = request.form.get("output_format", "csv").lower()
        output_filename = request.form.get("output_filename")

        # Validate parameters
        if not conditions_data:
            raise ValidationError("At least one search condition is required")

        if logic not in ["AND", "OR"]:
            raise ValidationError("Logic must be either 'AND' or 'OR'")

        if output_format not in ["xlsx", "csv", "json"]:
            raise ValidationError("Output format must be xlsx, csv, or json")

        # Save uploaded file
        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            # Read CSV file
            csv_service = get_csv_service()
            df = csv_service.read_csv(file_path)

            # Create search request
            search_request = SearchRequest.from_dict({
                "conditions": conditions_data,
                "logic": logic,
                "output_format": output_format,
                "output_filename": output_filename,
            })

            # Apply search
            search_service = get_search_service()
            filtered_df = search_service.apply_search(
                df, search_request.conditions, search_request.logic
            )

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if output_filename:
                output_name = secure_filename(output_filename)
            else:
                extension = f".{output_format}"
                output_name = f"search_results_{timestamp}{extension}"

            output_path = os.path.join(output_folder, output_name)

            # Save results
            search_service.save_search_results(
                filtered_df, output_path, output_format
            )

            # Build download URL
            host = request.host
            download_url = f"http://{host}/api/v1/files/downloads/{output_name}"

            response = ResponseBuilder.success(
                data={
                    "download_url": download_url,
                    "total_rows": len(df),
                    "filtered_rows": len(filtered_df),
                    "conditions_applied": len(search_request.conditions),
                },
                message=f"Search completed successfully. {len(filtered_df)} rows matched.",
            )
            return jsonify(response), 200

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@csv_bp.route("/search/suggest-operators", methods=["POST"])
def suggest_search_operators_csv():
    """
    Suggest valid search operators for each column in a CSV file.
    
    This endpoint analyzes the CSV file's column data types and suggests
    appropriate search operators for each column.
    
    Request:
        POST with multipart/form-data containing 'file'
    
    Returns:
        JSON with operator suggestions for each column
    
    Example:
        curl -X POST -F "file=@data.csv" \
             http://localhost:5050/api/v1/csv/search/suggest-operators
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")

        # Save uploaded file
        FileUtils.ensure_directory(upload_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            # Get file info (includes data types)
            csv_service = get_csv_service()
            info = csv_service.get_file_info(file_path)

            # Generate operator suggestions
            search_service = get_search_service()
            suggestions = {}

            for column, dtype in info.get("data_types", {}).items():
                operators = search_service.get_operator_suggestions(dtype)
                suggestions[column] = {
                    "type": dtype,
                    "operators": operators,
                }

            response = ResponseBuilder.success(
                data=suggestions,
                message="Operator suggestions generated successfully",
            )
            return jsonify(response), 200

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
