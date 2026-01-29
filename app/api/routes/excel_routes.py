"""
Excel Processing Routes

This module provides API endpoints for Excel file operations.
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.excel_service import ExcelService
from app.models.request import ColumnExtractionRequest, ColumnMappingRequest
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError

excel_bp = Blueprint("excel", __name__)


def get_excel_service() -> ExcelService:
    """Get ExcelService instance with current app config."""
    config = current_app.config.get("PYCELIZE")
    return ExcelService(config)


@excel_bp.route("/info", methods=["POST"])
def get_excel_info():
    """
    Get information about an Excel file.

    Request:
        POST with multipart/form-data containing 'file'

    Returns:
        JSON with file information (rows, columns, column names, etc.)

    Example:
        curl -X POST -F "file=@data.xlsx" http://localhost:5050/api/v1/excel/info
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
            service = get_excel_service()
            info = service.get_file_info(file_path)

            response = ResponseBuilder.success(
                data=info, message="File information retrieved successfully"
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


@excel_bp.route("/extract-columns", methods=["POST"])
def extract_columns():
    """
    Extract data from specific columns in an Excel file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - columns: JSON array of column names
        - remove_duplicates: Optional boolean (default: false)
        - include_statistics: Optional boolean (default: true)
    
    Returns:
        JSON with extracted column data and statistics
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F 'columns=["name", "email"]' \
             -F "remove_duplicates=true" \
             http://localhost:5050/api/v1/excel/extract-columns
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")

        # Parse request parameters
        import json

        columns_str = request.form.get("columns", "[]")
        columns = json.loads(columns_str)
        remove_duplicates = (
            request.form.get("remove_duplicates", "false").lower() == "true"
        )
        include_statistics = (
            request.form.get("include_statistics", "true").lower() == "true"
        )

        if not columns:
            raise ValidationError("No columns specified for extraction")

        # Save uploaded file
        FileUtils.ensure_directory(upload_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            service = get_excel_service()
            df = service.read_excel(file_path)

            extracted = service.extract_columns(
                data=df,
                columns=columns,
                remove_duplicates=remove_duplicates,
                include_statistics=include_statistics,
            )

            response = ResponseBuilder.success(
                data=extracted, message=f"Successfully extracted {len(columns)} columns"
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


@excel_bp.route("/extract-columns-to-file", methods=["POST"])
def extract_columns_to_file():
    """
    Extract columns from Excel file and save to new Excel file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - columns: JSON array of column names
        - remove_duplicates: Optional boolean (default: false)
    
    Returns:
        JSON with download URL for the extracted file
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F 'columns=["name", "email"]' \
             -F "remove_duplicates=true" \
             http://localhost:5050/api/v1/excel/extract-columns-to-file
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse request parameters
        import json

        columns_str = request.form.get("columns", "[]")
        columns = json.loads(columns_str)
        remove_duplicates = (
            request.form.get("remove_duplicates", "false").lower() == "true"
        )

        if not columns:
            raise ValidationError("No columns specified for extraction")

        # Save uploaded file
        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            service = get_excel_service()
            df = service.read_excel(file_path)

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"extracted_columns_{timestamp}.xlsx"
            output_path = os.path.join(output_folder, output_filename)

            # Extract columns and save to file
            service.extract_columns_to_file(
                data=df,
                columns=columns,
                output_path=output_path,
                remove_duplicates=remove_duplicates,
            )

            # Build download URL
            host = request.host
            download_url = f"http://{host}/api/v1/files/downloads/{output_filename}"

            response = ResponseBuilder.success(
                data={"download_url": download_url},
                message="Extracted Excel file generated successfully",
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


@excel_bp.route("/map-columns", methods=["POST"])
def map_columns():
    """
    Apply column mapping to an Excel file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - mapping: JSON object with column mapping rules
        - output_filename: Optional output filename
    
    Returns:
        Excel file with mapped columns
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F 'mapping={"Customer Name": "name", "Email": {"source": "email", "default": "N/A"}}' \
             http://localhost:5050/api/v1/excel/map-columns
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse mapping
        import json

        mapping_str = request.form.get("mapping", "{}")
        mapping = json.loads(mapping_str)

        if not mapping:
            raise ValidationError("No column mapping provided")

        output_filename = request.form.get("output_filename")

        # Save uploaded file
        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            service = get_excel_service()
            df = service.read_excel(file_path)

            # Apply mapping
            mapped_df = service.apply_column_mapping(df, mapping)

            # Generate output path
            if output_filename:
                output_path = os.path.join(
                    output_folder, secure_filename(output_filename)
                )
            else:
                output_path = os.path.join(
                    output_folder,
                    generate_output_filename(file.filename, "mapped", ".xlsx"),
                )

            # Write result
            service.write_excel(mapped_df, output_path)

            return send_file(
                output_path,
                as_attachment=True,
                download_name=os.path.basename(output_path),
            )

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
