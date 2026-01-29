"""
File Management Routes

This module provides API endpoints for file binding and management.
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.binding_service import BindingService
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError

file_bp = Blueprint("files", __name__)


def get_binding_service() -> BindingService:
    """Get BindingService instance with current app config."""
    config = current_app.config.get("PYCELIZE")
    return BindingService(config)


@file_bp.route("/bind", methods=["POST"])
def bind_excel_files():
    """
    Bind data from source Excel file to target Excel file.
    
    Request:
        POST with multipart/form-data:
        - source_file: Source Excel file with data
        - target_file: Target Excel file to populate
        - column_mapping: JSON object mapping target columns to source columns
        - output_filename: Optional output filename
    
    Returns:
        Excel file with bound data
    
    Example:
        curl -X POST \
             -F "source_file=@source.xlsx" \
             -F "target_file=@target.xlsx" \
             -F 'column_mapping={"Target_Name": "Source_Name", "Target_Email": "Source_Email"}' \
             http://localhost:5050/api/v1/files/bind \
             --output result.xlsx
    """
    try:
        # Validate files
        source_file = request.files.get("source_file")
        target_file = request.files.get("target_file")

        Validators.validate_file_uploaded(source_file)
        Validators.validate_file_uploaded(target_file)

        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse column mapping
        import json

        column_mapping_str = request.form.get("column_mapping", "{}")
        column_mapping = json.loads(column_mapping_str)

        if not column_mapping:
            raise ValidationError("column_mapping is required")

        output_filename = request.form.get("output_filename")

        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)

        # Save uploaded files
        source_path = FileUtils.secure_save_path(source_file.filename, upload_folder)
        target_path = FileUtils.secure_save_path(target_file.filename, upload_folder)
        source_file.save(source_path)
        target_file.save(target_path)

        try:
            service = get_binding_service()

            # Generate output path
            if output_filename:
                output_path = os.path.join(
                    output_folder, secure_filename(output_filename)
                )
            else:
                output_path = os.path.join(
                    output_folder,
                    generate_output_filename(target_file.filename, "bound", ".xlsx"),
                )

            # Perform binding
            result = service.bind_data(
                source_path=source_path,
                target_path=target_path,
                column_mapping=column_mapping,
                output_path=output_path,
            )

            return send_file(
                result["output_path"],
                as_attachment=True,
                download_name=os.path.basename(result["output_path"]),
            )

        finally:
            FileUtils.delete_file(source_path)
            FileUtils.delete_file(target_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@file_bp.route("/bind/preview", methods=["POST"])
def preview_binding():
    """
    Preview binding operation without saving result.

    Returns:
        JSON with binding preview and statistics
    """
    try:
        source_file = request.files.get("source_file")
        target_file = request.files.get("target_file")

        Validators.validate_file_uploaded(source_file)
        Validators.validate_file_uploaded(target_file)

        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")

        import json

        column_mapping_str = request.form.get("column_mapping", "{}")
        column_mapping = json.loads(column_mapping_str)

        FileUtils.ensure_directory(upload_folder)

        source_path = FileUtils.secure_save_path(source_file.filename, upload_folder)
        target_path = FileUtils.secure_save_path(target_file.filename, upload_folder)
        source_file.save(source_path)
        target_file.save(target_path)

        try:
            from app.services.excel_service import ExcelService

            excel_service = ExcelService(config)

            source_df = excel_service.read_excel(source_path)
            target_df = excel_service.read_excel(target_path)

            # Validate mapping
            validation = {
                "source_columns": list(source_df.columns),
                "target_columns": list(target_df.columns),
                "source_rows": len(source_df),
                "target_rows": len(target_df),
                "mapping_valid": True,
                "issues": [],
            }

            for target_col, source_col in column_mapping.items():
                if source_col not in source_df.columns:
                    validation["issues"].append(
                        f"Source column '{source_col}' not found"
                    )
                    validation["mapping_valid"] = False
                if target_col not in target_df.columns:
                    validation["issues"].append(
                        f"Target column '{target_col}' not found"
                    )
                    validation["mapping_valid"] = False

            response = ResponseBuilder.success(
                data=validation, message="Binding preview generated"
            )
            return jsonify(response), 200

        finally:
            FileUtils.delete_file(source_path)
            FileUtils.delete_file(target_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
