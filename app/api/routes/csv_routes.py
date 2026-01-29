"""
CSV Processing Routes

This module provides API endpoints for CSV file operations.
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.csv_service import CSVService
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError

csv_bp = Blueprint("csv", __name__)


def get_csv_service() -> CSVService:
    """Get CSVService instance with current app config."""
    config = current_app.config.get("PYCELIZE")
    return CSVService(config)


@csv_bp.route("/info", methods=["POST"])
def get_csv_info():
    """
    Get information about a CSV file.

    Request:
        POST with multipart/form-data containing 'file'

    Returns:
        JSON with file information

    Example:
        curl -X POST -F "file=@data.csv" http://localhost:5000/api/v1/csv/info
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
             http://localhost:5000/api/v1/csv/convert-to-excel \
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

            return send_file(
                result_path,
                as_attachment=True,
                download_name=os.path.basename(result_path),
            )

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
