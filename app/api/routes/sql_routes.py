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
        curl http://localhost:5050/api/v1/sql/databases
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
             http://localhost:5050/api/v1/sql/generate
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


@sql_bp.route("/generate-to-text", methods=["POST"])
def generate_sql_to_text():
    """
    Generate SQL statements from Excel file and save to text file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - columns: JSON array of column names to extract
        - table_name: Target table name
        - column_mapping: JSON object mapping SQL columns to data columns
        - database_type: Database type (postgresql, mysql, sqlite)
        - auto_increment: Optional auto-increment config
        - remove_duplicates: Optional boolean (default: false)
    
    Returns:
        JSON with download URL for the SQL text file
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F 'columns=["name", "email"]' \
             -F "table_name=users" \
             -F 'column_mapping={"name": "name", "email": "email"}' \
             -F "database_type=postgresql" \
             -F 'auto_increment={"enabled": true, "column_name": "id"}' \
             http://localhost:5050/api/v1/sql/generate-to-text
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse request parameters
        import json
        from datetime import datetime

        columns_str = request.form.get("columns", "[]")
        columns = json.loads(columns_str)
        
        table_name = request.form.get("table_name")
        if not table_name:
            raise ValidationError("table_name is required")

        column_mapping_str = request.form.get("column_mapping", "{}")
        column_mapping = json.loads(column_mapping_str)

        if not column_mapping:
            raise ValidationError("column_mapping is required")

        database_type = request.form.get("database_type", "postgresql")
        remove_duplicates = (
            request.form.get("remove_duplicates", "false").lower() == "true"
        )

        # Parse auto-increment config
        auto_increment_str = request.form.get("auto_increment", "{}")
        auto_increment_data = json.loads(auto_increment_str)

        # Create request object
        sql_request = SQLGenerationRequest(
            table_name=table_name,
            column_mapping=column_mapping,
            database_type=database_type,
            batch_size=1000,
            include_transaction=True,
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

            # Extract columns if specified
            if columns:
                missing_columns = [col for col in columns if col not in df.columns]
                if missing_columns:
                    raise ValidationError(
                        f"Columns not found: {', '.join(missing_columns)}"
                    )
                df = df[columns]

            # Remove duplicates if requested
            if remove_duplicates:
                df = df.drop_duplicates()

            # Generate SQL
            result = sql_service.generate_sql(df, sql_request)

            # Save to text file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"sql_statements_{timestamp}.txt"
            output_path = os.path.join(output_folder, output_filename)
            sql_service.export_sql(result["statements"], output_path)

            # Build download URL
            host = request.host
            download_url = f"http://{host}/api/v1/files/downloads/{output_filename}"

            response = ResponseBuilder.success(
                data={"download_url": download_url},
                message="SQL text file generated successfully",
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


@sql_bp.route("/generate-custom-to-text", methods=["POST"])
def generate_custom_sql_to_text():
    """
    Generate SQL statements using custom template and save to text file.
    
    Request:
        POST with multipart/form-data:
        - file: Excel file
        - columns: JSON array of column names to extract
        - template: Custom SQL template with placeholders
        - column_mapping: JSON object mapping placeholders to data columns
        - auto_increment: Optional auto-increment config
        - remove_duplicates: Optional boolean (default: false)
    
    Template placeholders:
        - {column_name}: Will be replaced with value from mapped column
        - {auto_id}: Auto-incremented ID if auto_increment is enabled
        - {current_timestamp}: Current timestamp
    
    Returns:
        JSON with download URL for the SQL text file
    
    Example:
        curl -X POST -F "file=@data.xlsx" \
             -F 'columns=["Name", "Email"]' \
             -F 'template=INSERT INTO users (id, name, email, created_at) VALUES ({auto_id}, '\''{name}'\'', '\''{email}'\'', {current_timestamp});' \
             -F 'column_mapping={"name": "Name", "email": "Email"}' \
             -F 'auto_increment={"enabled": true, "column_name": "id", "start_value": 1}' \
             http://localhost:5050/api/v1/sql/generate-custom-to-text
    """
    try:
        Validators.validate_file_uploaded(request.files.get("file"))

        file = request.files["file"]
        config = current_app.config.get("PYCELIZE")
        upload_folder = config.get("file.upload_folder", "uploads")
        output_folder = config.get("file.output_folder", "outputs")

        # Parse request parameters
        import json
        from datetime import datetime

        columns_str = request.form.get("columns", "[]")
        columns = json.loads(columns_str)
        
        template = request.form.get("template")
        if not template:
            raise ValidationError("template is required")

        column_mapping_str = request.form.get("column_mapping", "{}")
        column_mapping = json.loads(column_mapping_str)

        if not column_mapping:
            raise ValidationError("column_mapping is required")

        remove_duplicates = (
            request.form.get("remove_duplicates", "false").lower() == "true"
        )

        # Parse auto-increment config
        auto_increment_str = request.form.get("auto_increment", "{}")
        auto_increment_data = json.loads(auto_increment_str)

        FileUtils.ensure_directory(upload_folder)
        FileUtils.ensure_directory(output_folder)
        file_path = FileUtils.secure_save_path(file.filename, upload_folder)
        file.save(file_path)

        try:
            excel_service, sql_service = get_services()

            # Read data
            df = excel_service.read_excel(file_path)

            # Extract columns if specified
            if columns:
                missing_columns = [col for col in columns if col not in df.columns]
                if missing_columns:
                    raise ValidationError(
                        f"Columns not found: {', '.join(missing_columns)}"
                    )
                df = df[columns]

            # Remove duplicates if requested
            if remove_duplicates:
                df = df.drop_duplicates()

            # Generate custom SQL
            from app.models.request import AutoIncrementConfig
            
            auto_config = AutoIncrementConfig.from_dict(auto_increment_data)
            statements = sql_service.generate_custom_sql(
                df, template, column_mapping, auto_config
            )

            # Save to text file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"custom_sql_{timestamp}.txt"
            output_path = os.path.join(output_folder, output_filename)
            sql_service.export_sql(statements, output_path)

            # Build download URL
            host = request.host
            download_url = f"http://{host}/api/v1/files/downloads/{output_filename}"

            response = ResponseBuilder.success(
                data={"download_url": download_url},
                message="Custom SQL text file generated successfully",
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
