"""
Normalization Routes

This module provides API endpoints for data normalization operations.
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.excel_service import ExcelService
from app.services.normalization_service import NormalizationService
from app.models.request import NormalizationConfig
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError, NormalizationError

normalization_bp = Blueprint("normalization", __name__)


def get_services():
    """Get service instances with current app config."""
    config = current_app.config.get("PYCELIZE")
    return ExcelService(config), NormalizationService(config)


@normalization_bp.route("/types", methods=["GET"])
def get_normalization_types():
    """
    Get all available normalization types.

    Returns:
        JSON with list of normalization types and descriptions

    Example:
        curl http://localhost:5050/api/v1/normalization/types
    """
    try:
        config = current_app.config.get("PYCELIZE")
        service = NormalizationService(config)
        types = service.get_available_normalizations()

        response = ResponseBuilder.success(
            data=types,
            message="Normalization types retrieved successfully",
            total=len(types),
        )
        return jsonify(response), 200

    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@normalization_bp.route("/apply", methods=["POST"])
def apply_normalization():
    """
    Apply normalization to an Excel file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - normalizations: JSON array of normalization configs
        - output_filename: Optional output filename
    
    Normalization config format:
        {
            "column_name": "column1",
            "normalization_type": "uppercase",
            "parameters": {},
            "backup_original": false
        }
    
    Returns:
        Normalized Excel file and normalization report
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F 'normalizations=[{"column_name": "name", "normalization_type": "uppercase"}]' \
             http://localhost:5050/api/v1/normalization/apply \
             --output normalized.xlsx
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse normalizations
        import json

        normalizations_str = request.form.get("normalizations", "[]")
        normalizations_data = json.loads(normalizations_str)

        if not normalizations_data:
            raise ValidationError("No normalization configurations provided")

        # Convert to NormalizationConfig objects
        normalization_configs = [
            NormalizationConfig.from_dict(n) for n in normalizations_data
        ]

        output_filename = request.form.get("output_filename")
        return_report = request.form.get("return_report", "false").lower() == "true"

        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            excel_service, norm_service = get_services()

            # Read data
            df = excel_service.read_excel(file_path)

            # Apply normalization
            normalized_df, report = norm_service.normalize(df, normalization_configs)

            # Generate output path
            if output_filename:
                output_path = os.path.join(
                    output_folder, secure_filename(output_filename)
                )
            else:
                output_path = os.path.join(
                    output_folder,
                    generate_output_filename(file.filename, "normalized", ".xlsx"),
                )

            # Write result
            excel_service.write_excel(normalized_df, output_path)

            if return_report:
                response = ResponseBuilder.success(
                    data={
                        "report": report,
                        "output_file": os.path.basename(output_path),
                    },
                    message="Normalization completed successfully",
                )
                return jsonify(response), 200
            else:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=os.path.basename(output_path),
                )

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except NormalizationError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
