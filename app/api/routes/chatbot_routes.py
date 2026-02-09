"""
Chat Bot API Routes

This module provides REST API endpoints for the chat bot feature.
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.builders.response_builder import ResponseBuilder
from app.chat.chatbot_service import ChatBotService
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.streaming_executor import StreamingWorkflowExecutor
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint("chatbot", __name__)


def get_chatbot_components():
    """Get chat bot components with configuration."""
    config = current_app.config.get("PYCELIZE")
    chat_config = config.get_section("chat_workflows")

    if not chat_config or not chat_config.get("enabled", False):
        raise ValidationError("Chat workflows feature is not enabled")

    # Initialize components
    # If config options are missing, use defaults for backward compatibility
    # E.g, database path, storage paths, partition strategy
    #   - db_path if not set defaults to ./automation/sqlite/chat.db
    #   - workflows_path if not set defaults to ./automation/workflows
    #   - partition_strategy if not set defaults to time-based partitioning
    db_path = chat_config.get("storage", {}).get(
        "sqlite_path", "./automation/sqlite/chat.db"
    )
    workflows_path = chat_config.get("storage", {}).get(
        "workflows_path", "./automation/workflows"
    )
    partition_strategy = chat_config.get("partition", {}).get("strategy", "time-based")

    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, partition_strategy)
    repository = ConversationRepository(database, storage)
    executor = StreamingWorkflowExecutor(config)

    # Create chat bot service
    chatbot_service = ChatBotService(repository, config, executor)

    return chatbot_service, repository, storage, chat_config


@chatbot_bp.route("/bot/conversations", methods=["POST"])
def create_bot_conversation():
    """
    Start a new chat bot conversation.
    
    Request JSON (optional):
        {
            "chat_id": "optional-custom-id"
        }
    
    Returns:
        JSON response with conversation details and welcome message
        
    Example:
        curl -X POST http://localhost:5050/api/v1/chat/bot/conversations \\
             -H "Content-Type: application/json" \\
             -d '{}'
    """
    try:
        chatbot_service, _, _, _ = get_chatbot_components()

        # Get optional chat_id from request
        data = request.get_json() or {}
        chat_id = data.get("chat_id")

        # Start conversation
        result = chatbot_service.start_conversation(chat_id)

        # Build response
        response = ResponseBuilder.success(
            data=result, message="Bot conversation started successfully"
        )

        return jsonify(response), 201

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        response = ResponseBuilder.error(
            f"Failed to start bot conversation: {str(e)}", 500
        )
        return jsonify(response), 500


@chatbot_bp.route("/bot/conversations/<chat_id>/message", methods=["POST"])
def send_bot_message(chat_id: str):
    """
    Send a message to the chat bot.
    
    Args:
        chat_id: Conversation identifier
    
    Request JSON:
        {
            "message": "extract columns: name, email"
        }
    
    Returns:
        JSON response with bot's response
        
    Example:
        curl -X POST http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/message \\
             -H "Content-Type: application/json" \\
             -d '{"message": "extract columns: name, email"}'
    """
    try:
        chatbot_service, _, _, _ = get_chatbot_components()

        # Get message from request
        data = request.get_json()
        if not data or "message" not in data:
            raise ValidationError("No message provided")

        message = data.get("message", "").strip()
        if not message:
            raise ValidationError("Empty message")

        # Send message to bot
        result = chatbot_service.send_message(chat_id, message)

        # Check if successful
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            response = ResponseBuilder.error(error_msg, 400)
            return jsonify(response), 200  # 200 to indicate bot processed the message

        # Build response
        response = ResponseBuilder.success(
            data={
                "bot_response": result.get("bot_response"),
                "intent": result.get("intent"),
                "suggested_workflow": result.get("suggested_workflow"),
                "requires_confirmation": result.get("requires_confirmation", False),
                "requires_file": result.get("requires_file", False),
                "action": result.get("action"),
                "output_files": result.get("output_files", []),
            },
            message="Message processed successfully",
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        logger.error(f"Failed to send bot message: {str(e)}")
        response = ResponseBuilder.error(f"Failed to send message: {str(e)}", 500)
        return jsonify(response), 500


@chatbot_bp.route("/bot/conversations/<chat_id>/upload", methods=["POST"])
def upload_bot_file(chat_id: str):
    """
    Upload a file to the chat bot conversation.
    
    Args:
        chat_id: Conversation identifier
    
    Request:
        Multipart form data with 'file' field
    
    Returns:
        JSON response with bot's response and file info
        
    Example:
        curl -X POST http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/upload \\
             -F "file=@data.xlsx"
    """
    try:
        chatbot_service, repository, storage, chat_config = get_chatbot_components()

        # Get conversation
        conversation = repository.get_conversation(chat_id)
        if not conversation:
            response = ResponseBuilder.error("Conversation not found", 404)
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

        # Process file upload through bot service (this will save to database)
        result = chatbot_service.upload_file(chat_id, file_path, filename)

        # Build absolute download URL
        download_url = f"{request.scheme}://{request.host}/api/v1/chat/workflows/{chat_id}/files/{filename}"

        # Build response
        response = ResponseBuilder.success(
            data={
                "file_path": file_path,
                "filename": filename,
                "download_url": download_url,
                "bot_response": result.get("bot_response"),
                "suggested_workflow": result.get("suggested_workflow"),
                "requires_confirmation": result.get("requires_confirmation", False),
            },
            message="File uploaded successfully",
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        logger.error(f"Failed to upload bot file: {str(e)}")
        response = ResponseBuilder.error(f"Failed to upload file: {str(e)}", 500)
        return jsonify(response), 500


@chatbot_bp.route("/bot/conversations/<chat_id>/confirm", methods=["POST"])
def confirm_bot_workflow(chat_id: str):
    """
    Confirm or decline a suggested workflow.
    
    This endpoint now runs workflows asynchronously in the background for better performance.
    The API returns immediately with a 202 Accepted status when a workflow is submitted.
    Use the WebSocket connection or the status endpoint to track workflow progress.
    
    Args:
        chat_id: Conversation identifier
    
    Request JSON:
        {
            "confirmed": true,
            "modified_workflow": [...]  # Optional modified workflow steps
        }
    
    Returns:
        JSON response with job submission info (202) or execution results (200 for sync)
        
    Example:
        curl -X POST http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/confirm \\
             -H "Content-Type: application/json" \\
             -d '{"confirmed": true}'
    """
    try:
        chatbot_service, _, _, _ = get_chatbot_components()

        # Get confirmation from request
        data = request.get_json()
        if not data:
            raise ValidationError("No data provided")

        confirmed = data.get("confirmed", False)
        modified_workflow = data.get("modified_workflow")

        # Confirm workflow with async execution (run_async=True)
        result = chatbot_service.confirm_workflow(
            chat_id, confirmed, modified_workflow, run_async=True
        )

        # Check if successful
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            response = ResponseBuilder.error(error_msg, 400)
            return jsonify(response), 400

        # If workflow was submitted for background execution
        if result.get("status") == "submitted":
            job_id = result.get("job_id")

            # Build response for async execution
            response = ResponseBuilder.success(
                data={
                    "job_id": job_id,
                    "status": "submitted",
                    "message": "Workflow submitted for execution. Use WebSocket or check status endpoint for progress.",
                    "bot_response": "🚀 Workflow submitted! I'm processing your request in the background. You'll receive real-time updates via WebSocket.",
                },
                message="Workflow submitted for background execution",
            )

            return jsonify(response), 202  # 202 Accepted

        # Otherwise, return standard response (for declined workflows or immediate responses)
        # Add download URLs to output files if present
        output_files_with_urls = []
        if result.get("output_files"):
            for output_file in result["output_files"]:
                filename = os.path.basename(output_file)
                output_files_with_urls.append(
                    {
                        "file_path": output_file,
                        "download_url": f"{request.scheme}://{request.host}/api/v1/chat/workflows/{chat_id}/files/{filename}",
                    }
                )

        # Build response
        response = ResponseBuilder.success(
            data={
                "bot_response": result.get("bot_response"),
                "output_files": output_files_with_urls,
                "results": result.get("results", []),
            },
            message="Workflow confirmation processed",
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        logger.error(f"Failed to confirm bot workflow: {str(e)}")
        response = ResponseBuilder.error(f"Failed to confirm workflow: {str(e)}", 500)
        return jsonify(response), 500


@chatbot_bp.route("/bot/conversations/<chat_id>/history", methods=["GET"])
def get_bot_conversation_history(chat_id: str):
    """
    Get conversation history with the bot.

    Args:
        chat_id: Conversation identifier

    Query parameters:
        limit: Maximum number of messages to return (optional)

    Returns:
        JSON response with conversation history

    Example:
        curl -X GET http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/history
    """
    try:
        chatbot_service, _, _, _ = get_chatbot_components()

        # Get optional limit
        limit = request.args.get("limit", type=int)

        # Get history
        result = chatbot_service.get_conversation_history(chat_id, limit)

        # Check if successful
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            response = ResponseBuilder.error(error_msg, 404)
            return jsonify(response), 404

        # Add download URLs to files
        uploaded_files_with_urls = []
        for file_path in result.get("uploaded_files", []):
            filename = os.path.basename(file_path)
            uploaded_files_with_urls.append(
                {
                    "file_path": file_path,
                    "download_url": f"{request.scheme}://{request.host}/api/v1/chat/workflows/{chat_id}/files/{filename}",
                }
            )

        output_files_with_urls = []
        for file_path in result.get("output_files", []):
            filename = os.path.basename(file_path)
            output_files_with_urls.append(
                {
                    "file_path": file_path,
                    "download_url": f"{request.scheme}://{request.host}/api/v1/chat/workflows/{chat_id}/files/{filename}",
                }
            )

        # Build response
        response = ResponseBuilder.success(
            data={
                "chat_id": result.get("chat_id"),
                "participant_name": result.get("participant_name"),
                "status": result.get("status"),
                "current_state": result.get("current_state"),
                "messages": result.get("messages", []),
                "uploaded_files": uploaded_files_with_urls,
                "output_files": output_files_with_urls,
                "workflow_steps": result.get("workflow_steps", []),
            },
            message="Conversation history retrieved successfully",
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        logger.error(f"Failed to get bot conversation history: {str(e)}")
        response = ResponseBuilder.error(f"Failed to get history: {str(e)}", 500)
        return jsonify(response), 500


@chatbot_bp.route(
    "/bot/conversations/<chat_id>/workflow/status/<job_id>", methods=["GET"]
)
def get_workflow_job_status(chat_id: str, job_id: str):
    """
    Get the status of a background workflow job.

    Args:
        chat_id: Conversation identifier
        job_id: Job identifier returned when workflow was submitted

    Returns:
        JSON response with job status

    Example:
        curl -X GET http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/workflow/status/{job_id}
    """
    try:
        chatbot_service, _, _, _ = get_chatbot_components()

        # Get job status
        job_status = chatbot_service.get_workflow_job_status(job_id)

        if not job_status:
            response = ResponseBuilder.error("Job not found", 404)
            return jsonify(response), 404

        # Build response
        response = ResponseBuilder.success(
            data=job_status,
            message="Job status retrieved successfully",
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        logger.error(f"Failed to get workflow job status: {str(e)}")
        response = ResponseBuilder.error(f"Failed to get job status: {str(e)}", 500)
        return jsonify(response), 500


@chatbot_bp.route("/bot/conversations/<chat_id>", methods=["DELETE"])
def delete_bot_conversation(chat_id: str):
    """
    Delete a bot conversation.

    Args:
        chat_id: Conversation identifier

    Returns:
        JSON response confirming deletion

    Example:
        curl -X DELETE http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}
    """
    try:
        chatbot_service, repository, _, _ = get_chatbot_components()

        # Delete conversation
        deleted = repository.delete_conversation(chat_id)

        if not deleted:
            response = ResponseBuilder.error("Conversation not found", 404)
            return jsonify(response), 404

        # Reset bot context
        chatbot_service.state_manager.reset_context(chat_id)

        # Build response
        response = ResponseBuilder.success(
            data={"chat_id": chat_id}, message="Bot conversation deleted successfully"
        )

        return jsonify(response), 200

    except ValidationError as e:
        response = ResponseBuilder.error(str(e), 422)
        return jsonify(response), 422
    except Exception as e:
        logger.error(f"Failed to delete bot conversation: {str(e)}")
        response = ResponseBuilder.error(
            f"Failed to delete conversation: {str(e)}", 500
        )
        return jsonify(response), 500


@chatbot_bp.route("/bot/operations", methods=["GET"])
def get_bot_operations():
    """
    Get supported operations and intents.

    Returns:
        JSON response with operation information

    Example:
        curl -X GET http://localhost:5050/api/v1/chat/bot/operations
    """
    try:
        from app.chat.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        operations = classifier.get_supported_operations()

        # Build response
        response = ResponseBuilder.success(
            data={"operations": operations, "total_intents": len(operations)},
            message="Supported operations retrieved successfully",
        )

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Failed to get bot operations: {str(e)}")
        response = ResponseBuilder.error(f"Failed to get operations: {str(e)}", 500)
        return jsonify(response), 500
