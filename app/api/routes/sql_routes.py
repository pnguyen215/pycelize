"""
SQL Generation Routes

This module provides API endpoints for SQL generation operations.
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.services.excel_service import ExcelService
from app.services.sql_generation_service import SQLGenerationService
from app.models.request import SQLGenerationRequest
from app.utils.file_utils import FileUtils
from app.utils.validators import Validators
from app.utils.helpers import generate_output_filename
from app.core.exceptions import ValidationError, FileProcessingError, SQLGenerationError

sql_bp = Blueprint("sql", __name__)


def get_services():
    """Get service instances with current app config."""
    config = current_app.config.get("PYCELIZE")
    return ExcelService(config), SQLGenerationService(config)


@sql_bp.route("/databases", methods=["GET"])
def get_supported_databases():
    """
    Get list of supported database types.

    Returns:
        JSON with list of supported databases

    Example:
        curl http://localhost:5000/api/v1/sql/databases
    """
    try:
        config = current_app.config.get("PYCELIZE")
        service = SQLGenerationService(config)
        databases = service.get_supported_databases()

        response = ResponseBuilder.success(
            data={"databases": databases},
            message="Supported databases retrieved successfully",
        )
        return jsonify(response), 200

    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500


@sql_bp.route("/generate", methods=["POST"])
def generate_sql():
    """
    Generate SQL statements from an Excel file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - table_name: Target table name
        - column_mapping: JSON object mapping SQL columns to data columns
        - database_type: Database type (postgresql, mysql, sqlite)
        - template: Optional custom SQL template
        - auto_increment: Optional auto-increment config
        - batch_size: Optional batch size (default: 1000)
        - include_transaction: Optional boolean (default: true)
        - return_file: Optional boolean to return SQL file (default: false)
    
    Auto-increment config format:
        {
            "enabled": true,
            "column_name": "id",
            "increment_type": "postgresql_serial",
            "start_value": 1,
            "sequence_name": "my_sequence"
        }
    
    Returns:
        JSON with SQL statements or SQL file
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F "table_name=users" \
             -F 'column_mapping={"name": "Name", "email": "Email"}' \
             -F "database_type=postgresql" \
             http://localhost:5000/api/v1/sql/generate
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse request parameters
        import json

        table_name = request.form.get("table_name")
        if not table_name:
            raise ValidationError("table_name is required")

        column_mapping_str = request.form.get("column_mapping", "{}")
        column_mapping = json.loads(column_mapping_str)

        if not column_mapping:
            raise ValidationError("column_mapping is required")

        database_type = request.form.get("database_type", "postgresql")
        template = request.form.get("template")
        batch_size = int(request.form.get("batch_size", 1000))
        include_transaction = (
            request.form.get("include_transaction", "true").lower() == "true"
        )
        return_file = request.form.get("return_file", "false").lower() == "true"

        # Parse auto-increment config
        auto_increment_str = request.form.get("auto_increment", "{}")
        auto_increment_data = json.loads(auto_increment_str)

        # Create request object
        sql_request = SQLGenerationRequest(
            table_name=table_name,
            column_mapping=column_mapping,
            database_type=database_type,
            template=template,
            batch_size=batch_size,
            include_transaction=include_transaction,
        )

        if auto_increment_data:
            from app.models.request import AutoIncrementConfig

            sql_request.auto_increment = AutoIncrementConfig.from_dict(
                auto_increment_data
            )

        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            excel_service, sql_service = get_services()

            # Read data
            df = excel_service.read_excel(file_path)

            # Generate SQL
            result = sql_service.generate_sql(df, sql_request)

            if return_file:
                # Export to file
                output_path = os.path.join(
                    output_folder,
                    generate_output_filename(file.filename, "sql", ".sql"),
                )
                sql_service.export_sql(result["statements"], output_path)

                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=os.path.basename(output_path),
                    mimetype="text/plain",
                )
            else:
                response = ResponseBuilder.success(
                    data=result,
                    message="SQL generated successfully",
                    total=result["total_statements"],
                )
                return jsonify(response), 200

        finally:
            FileUtils.delete_file(file_path)

    except ValidationError as e:
        return jsonify(ResponseBuilder.error(e.message, 422)), 422
    except SQLGenerationError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except FileProcessingError as e:
        return jsonify(ResponseBuilder.error(e.message, 400)), 400
    except Exception as e:
        return jsonify(ResponseBuilder.error(str(e), 500)), 500
