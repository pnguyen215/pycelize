"""
Chat Workflows API Routes

This module provides REST API endpoints for chat workflow management.
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.chat.models import ConversationStatus, MessageType, WorkflowStep
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.workflow_executor import WorkflowExecutor
from app.core.exceptions import ValidationError

chat_bp = Blueprint("chat", __name__)


def get_chat_components():
    """Get chat workflow components with configuration."""
    config = current_app.config.get("PYCELIZE")
    chat_config = config.get_section("chat_workflows")

    if not chat_config or not chat_config.get("enabled", False):
        raise ValidationError("Chat workflows feature is not enabled")

    # Initialize components
    db_path = chat_config.get("storage", {}).get("sqlite_path", "./automation/sqlite/chat.db")
    workflows_path = chat_config.get("storage", {}).get("workflows_path", "./automation/workflows")
    partition_strategy = chat_config.get("partition", {}).get("strategy", "time-based")

    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, partition_strategy)
    repository = ConversationRepository(database, storage)
    executor = WorkflowExecutor(config)

    return repository, executor, storage, chat_config


@chat_bp.route("/workflows", methods=["POST"])
def create_conversation():
    """
    Create a new chat workflow conversation.

    Returns:
        JSON response with conversation details
    """
    try:
        repository, _, _, _ = get_chat_components()

        # Generate chat ID
        chat_id = str(uuid.uuid4())

        # Create conversation
        conversation = repository.create_conversation(chat_id)

        # Build response
        response = (
            ResponseBuilder()
            .success()
            .message("Conversation created successfully")
            .data(conversation.to_dict())
            .build()
        )

        return jsonify(response), 201

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to create conversation: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/workflows", methods=["GET"])
def list_conversations():
    """
    List all chat workflow conversations.

    Query parameters:
        status: Optional status filter
        limit: Maximum results (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON response with list of conversations
    """
    try:
        repository, _, _, _ = get_chat_components()

        # Get query parameters
        status = request.args.get("status")
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))

        # List conversations
        conversations = repository.list_conversations(status, limit, offset)

        # Build response
        response = (
            ResponseBuilder()
            .success()
            .message("Conversations retrieved successfully")
            .data({"conversations": conversations, "count": len(conversations)})
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to list conversations: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/workflows/<chat_id>", methods=["GET"])
def get_conversation(chat_id: str):
    """
    Get a specific conversation by ID.

    Args:
        chat_id: Conversation identifier

    Returns:
        JSON response with conversation details
    """
    try:
        repository, _, _, _ = get_chat_components()

        # Get conversation
        conversation = repository.get_conversation(chat_id)

        if not conversation:
            response = ResponseBuilder().error().message("Conversation not found").build()
            return jsonify(response), 404

        # Build response
        response = (
            ResponseBuilder()
            .success()
            .message("Conversation retrieved successfully")
            .data(conversation.to_dict())
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to get conversation: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/workflows/<chat_id>/upload", methods=["POST"])
def upload_file(chat_id: str):
    """
    Upload a file to a conversation.

    Args:
        chat_id: Conversation identifier

    Request:
        Multipart form data with 'file' field

    Returns:
        JSON response with file path
    """
    try:
        repository, _, storage, _ = get_chat_components()

        # Get conversation
        conversation = repository.get_conversation(chat_id)
        if not conversation:
            response = ResponseBuilder().error().message("Conversation not found").build()
            return jsonify(response), 404

        # Check file
        if "file" not in request.files:
            raise ValidationError("No file provided")

        file = request.files["file"]
        if file.filename == "":
            raise ValidationError("Empty filename")

        # Secure filename
        filename = secure_filename(file.filename)

        # Save file
        file_content = file.read()
        file_path = storage.save_uploaded_file(
            chat_id, conversation.partition_key, file_content, filename
        )

        # Add to conversation
        conversation.uploaded_files.append(file_path)
        repository.update_conversation(conversation)

        # Add message
        repository.add_message(
            chat_id,
            MessageType.FILE_UPLOAD,
            f"File uploaded: {filename}",
            {"file_path": file_path},
        )

        # Build response
        response = (
            ResponseBuilder()
            .success()
            .message("File uploaded successfully")
            .data({"file_path": file_path, "filename": filename})
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to upload file: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/workflows/<chat_id>/execute", methods=["POST"])
def execute_workflow(chat_id: str):
    """
    Execute workflow steps for a conversation.

    Args:
        chat_id: Conversation identifier

    Request JSON:
        {
            "steps": [
                {
                    "operation": "excel/extract-columns",
                    "arguments": {"columns": ["col1", "col2"]}
                }
            ]
        }

    Returns:
        JSON response with execution results
    """
    try:
        repository, executor, storage, _ = get_chat_components()

        # Get conversation
        conversation = repository.get_conversation(chat_id)
        if not conversation:
            response = ResponseBuilder().error().message("Conversation not found").build()
            return jsonify(response), 404

        # Get request data
        data = request.get_json()
        if not data or "steps" not in data:
            raise ValidationError("No steps provided")

        # Create workflow steps
        steps = []
        for step_data in data["steps"]:
            step = WorkflowStep(
                step_id=str(uuid.uuid4()),
                operation=step_data.get("operation"),
                arguments=step_data.get("arguments", {}),
            )
            steps.append(step)
            conversation.workflow_steps.append(step)

        # Get initial input file (last uploaded file)
        initial_input = (
            conversation.uploaded_files[-1] if conversation.uploaded_files else None
        )

        if not initial_input:
            raise ValidationError("No uploaded file found for processing")

        # Update status
        conversation.status = ConversationStatus.PROCESSING
        repository.update_conversation(conversation)

        # Execute workflow
        try:
            results = executor.execute_workflow(steps, initial_input)

            # Save output files
            for i, result in enumerate(results):
                if result.get("output_file_path"):
                    saved_path = storage.save_output_file(
                        chat_id,
                        conversation.partition_key,
                        result["output_file_path"],
                        is_final=(i == len(results) - 1),
                    )
                    conversation.output_files.append(saved_path)

            # Update status
            conversation.status = ConversationStatus.COMPLETED
            repository.update_conversation(conversation)

            # Build response
            response = (
                ResponseBuilder()
                .success()
                .message("Workflow executed successfully")
                .data({
                    "results": results,
                    "output_files": conversation.output_files,
                })
                .build()
            )

            return jsonify(response), 200

        except Exception as e:
            # Update status on failure
            conversation.status = ConversationStatus.FAILED
            repository.update_conversation(conversation)

            raise Exception(f"Workflow execution failed: {str(e)}")

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 500


@chat_bp.route("/workflows/<chat_id>", methods=["DELETE"])
def delete_conversation(chat_id: str):
    """
    Delete a conversation.

    Args:
        chat_id: Conversation identifier

    Returns:
        JSON response confirming deletion
    """
    try:
        repository, _, _, _ = get_chat_components()

        # Delete conversation
        deleted = repository.delete_conversation(chat_id)

        if not deleted:
            response = ResponseBuilder().error().message("Conversation not found").build()
            return jsonify(response), 404

        # Build response
        response = (
            ResponseBuilder()
            .success()
            .message("Conversation deleted successfully")
            .data({"chat_id": chat_id})
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to delete conversation: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/workflows/<chat_id>/dump", methods=["POST"])
def dump_conversation(chat_id: str):
    """
    Create a dump of conversation data.

    Args:
        chat_id: Conversation identifier

    Returns:
        JSON response with download link
    """
    try:
        repository, _, _, chat_config = get_chat_components()

        # Get dump path
        dump_path = chat_config.get("storage", {}).get("dumps_path", "./automation/dumps")

        # Create dump
        dump_file = repository.dump_conversation(chat_id, dump_path)

        # Build response with download link
        filename = os.path.basename(dump_file)
        download_url = f"/api/v1/chat/downloads/{filename}"

        response = (
            ResponseBuilder()
            .success()
            .message("Conversation dumped successfully")
            .data({"dump_file": filename, "download_url": download_url})
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to dump conversation: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/workflows/restore", methods=["POST"])
def restore_conversation():
    """
    Restore a conversation from a dump file.

    Request:
        Multipart form data with 'dump_file' field

    Returns:
        JSON response with restored conversation details
    """
    try:
        repository, _, _, chat_config = get_chat_components()

        # Check file
        if "dump_file" not in request.files:
            raise ValidationError("No dump file provided")

        file = request.files["dump_file"]
        if file.filename == "":
            raise ValidationError("Empty filename")

        # Save temporary dump file
        dump_path = chat_config.get("storage", {}).get("dumps_path", "./automation/dumps")
        os.makedirs(dump_path, exist_ok=True)
        
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(dump_path, temp_filename)
        file.save(temp_path)

        # Restore conversation
        conversation = repository.restore_conversation(temp_path)

        # Build response
        response = (
            ResponseBuilder()
            .success()
            .message("Conversation restored successfully")
            .data(conversation.to_dict())
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to restore conversation: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/sqlite/backup", methods=["POST"])
def backup_sqlite():
    """
    Create a backup of the SQLite database.

    Returns:
        JSON response with backup file path
    """
    try:
        _, _, _, chat_config = get_chat_components()

        # Get configuration
        db_path = chat_config.get("storage", {}).get("sqlite_path", "./automation/sqlite/chat.db")
        snapshot_path = chat_config.get("backup", {}).get("snapshot_path", "./automation/sqlite/snapshots")

        # Create backup
        database = ChatDatabase(db_path)
        backup_file = database.backup(snapshot_path)

        # Build response
        filename = os.path.basename(backup_file)
        response = (
            ResponseBuilder()
            .success()
            .message("Database backup created successfully")
            .data({"backup_file": filename, "path": backup_file})
            .build()
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder().error().message(str(e)).build()
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to backup database: {str(e)}").build()
        return jsonify(response), 500


@chat_bp.route("/downloads/<path:filename>", methods=["GET"])
def download_file(filename: str):
    """
    Download a dump file.

    Args:
        filename: Dump filename

    Returns:
        File download
    """
    try:
        config = current_app.config.get("PYCELIZE")
        chat_config = config.get_section("chat_workflows")
        dump_path = chat_config.get("storage", {}).get("dumps_path", "./automation/dumps")

        file_path = os.path.join(dump_path, secure_filename(filename))

        if not os.path.exists(file_path):
            response = ResponseBuilder().error().message("File not found").build()
            return jsonify(response), 404

        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        response = ResponseBuilder().error().message(f"Failed to download file: {str(e)}").build()
        return jsonify(response), 500
