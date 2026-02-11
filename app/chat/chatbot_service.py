"""
Chat Bot Service

This module orchestrates the chat bot conversation flow, integrating
intent classification, state management, message handling, and workflow execution.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.chat.intent_classifier import IntentClassifier
from app.chat.state_manager import ConversationStateManager, BotState
from app.chat.message_handlers import (
    TextMessageHandler,
    FileMessageHandler,
    ConfirmationHandler,
    SystemMessageHandler,
)
from app.chat.streaming_executor import StreamingWorkflowExecutor
from app.chat.repository import ConversationRepository
from app.chat.models import Message, MessageType, WorkflowStep, ConversationStatus

logger = logging.getLogger(__name__)


class ChatBotService:
    """
    Chat bot service orchestrating conversational file processing.

    Integrates:
    - Intent classification for understanding user requests
    - State management for tracking conversation flow
    - Message handling for processing different message types
    - Workflow execution for processing files
    - Real-time progress updates via WebSocket
    """

    def __init__(
        self,
        repository: ConversationRepository,
        config: Any,
        streaming_executor: Optional[StreamingWorkflowExecutor] = None,
    ):
        """
        Initialize chat bot service.

        Args:
            repository: Conversation repository
            config: Application configuration
            streaming_executor: Optional streaming executor (created if not provided)
        """
        self.repository = repository
        self.config = config

        # Initialize components
        self.intent_classifier = IntentClassifier()
        self.state_manager = ConversationStateManager()

        # Initialize workflow executor
        if streaming_executor:
            self.executor = streaming_executor
        else:
            self.executor = StreamingWorkflowExecutor(config)

        # Setup message handler chain
        self._setup_message_handlers()

        logger.info("ChatBotService initialized")

    def _setup_message_handlers(self):
        """Setup message handler chain."""
        text_handler = TextMessageHandler(self.intent_classifier, self.state_manager)
        file_handler = FileMessageHandler(self.state_manager)
        confirmation_handler = ConfirmationHandler(self.state_manager)
        system_handler = SystemMessageHandler(self.state_manager)

        # Chain handlers
        text_handler.set_next(file_handler).set_next(confirmation_handler).set_next(system_handler)

        self.message_handler = text_handler

    def start_conversation(self, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new bot conversation.

        Args:
            chat_id: Optional conversation ID (generated if not provided)

        Returns:
            Conversation information
        """
        if not chat_id:
            chat_id = str(uuid.uuid4())

        # Create conversation in repository
        conversation = self.repository.create_conversation(chat_id)

        # Initialize state
        context = self.state_manager.get_or_create_context(chat_id)

        # Add welcome message
        welcome_message = self._create_welcome_message()
        self.repository.add_message(
            chat_id, MessageType.SYSTEM, welcome_message, {"is_welcome": True}
        )

        logger.info(f"Started new bot conversation: {chat_id}")

        return {
            "chat_id": chat_id,
            "participant_name": conversation.participant_name,
            "status": conversation.status.value,
            "bot_message": welcome_message,
            "state": context.current_state.value,
            "created_at": conversation.created_at.isoformat(),
        }

    def send_message(
        self, chat_id: str, message_text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a text message to the bot.

        Args:
            chat_id: Conversation ID
            message_text: Message text
            metadata: Optional metadata

        Returns:
            Bot response
        """
        logger.info(f"Received message for {chat_id}: {message_text[:50]}...")

        # Get conversation
        conversation = self.repository.get_conversation(chat_id)
        if not conversation:
            return {
                "success": False,
                "error": "Conversation not found",
                "bot_response": "I couldn't find this conversation. Please start a new one.",
            }

        # Add user message to conversation
        self.repository.add_message(chat_id, MessageType.USER, message_text, metadata or {})

        # Get conversation context
        context = self.state_manager.get_or_create_context(chat_id)

        # Sync uploaded files from conversation to state manager
        for uploaded_file in conversation.uploaded_files:
            if uploaded_file not in context.uploaded_files:
                context.uploaded_files.append(uploaded_file)
        if conversation.uploaded_files:
            logger.info(f"Synced {len(conversation.uploaded_files)} files to state manager context")

        # Process message through handler chain
        message_data = {"chat_id": chat_id, "text": message_text}

        response = self.message_handler.process("text", message_data, context)

        # Handle workflow execution if requested
        if response.get("action") == "execute_workflow":
            return self._execute_workflow(chat_id, response["workflow_steps"])

        # Add bot response to conversation if present
        if response.get("bot_response"):
            self.repository.add_message(
                chat_id,
                MessageType.SYSTEM,
                response["bot_response"],
                {
                    "intent": response.get("intent"),
                    "suggested_workflow": response.get("suggested_workflow"),
                    "requires_confirmation": response.get("requires_confirmation", False),
                },
            )

        return response

    def upload_file(self, chat_id: str, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Handle file upload for conversation.

        Args:
            chat_id: Conversation ID
            file_path: Path to uploaded file
            filename: Original filename

        Returns:
            Bot response
        """
        logger.info(f"File uploaded for {chat_id}: {filename}")

        # Get conversation
        conversation = self.repository.get_conversation(chat_id)
        if not conversation:
            return {"success": False, "error": "Conversation not found"}

        # Add file to conversation's uploaded_files list
        if file_path not in conversation.uploaded_files:
            conversation.uploaded_files.append(file_path)
            # Save file to database
            self.repository.database.save_file(chat_id, file_path, "uploaded")
            self.repository.update_conversation(conversation)
            logger.info(f"Added file to conversation.uploaded_files and database: {file_path}")

        # Add file message to conversation
        self.repository.add_message(
            chat_id,
            MessageType.FILE_UPLOAD,
            f"File uploaded: {filename}",
            {"file_path": file_path, "filename": filename},
        )

        # Get conversation context and sync uploaded files
        context = self.state_manager.get_or_create_context(chat_id)

        # Sync uploaded files from conversation to state manager
        for uploaded_file in conversation.uploaded_files:
            if uploaded_file not in context.uploaded_files:
                context.uploaded_files.append(uploaded_file)
        logger.info(f"Synced {len(conversation.uploaded_files)} files to state manager context")

        # Process file upload through handler chain
        message_data = {"chat_id": chat_id, "file_path": file_path, "filename": filename}

        response = self.message_handler.process("file", message_data, context)

        # Add bot response to conversation
        if response.get("bot_response"):
            self.repository.add_message(
                chat_id,
                MessageType.SYSTEM,
                response["bot_response"],
                {
                    "file_path": file_path,
                    "suggested_workflow": response.get("suggested_workflow"),
                    "requires_confirmation": response.get("requires_confirmation", False),
                },
            )

        return response

    def confirm_workflow(
        self,
        chat_id: str,
        confirmed: bool,
        modified_workflow: Optional[List[Dict[str, Any]]] = None,
        run_async: bool = False,
    ) -> Dict[str, Any]:
        """
        Confirm or decline workflow execution.

        Args:
            chat_id: Conversation ID
            confirmed: Whether workflow is confirmed
            modified_workflow: Optional modified workflow steps
            run_async: If True, run workflow in background and return immediately

        Returns:
            Bot response (or job submission info if run_async=True)
        """
        logger.info(f"Workflow {'confirmed' if confirmed else 'declined'} for {chat_id}")

        # Get conversation
        conversation = self.repository.get_conversation(chat_id)
        if not conversation:
            return {"success": False, "error": "Conversation not found"}

        # Get conversation context
        context = self.state_manager.get_or_create_context(chat_id)

        # Sync uploaded files from conversation to state manager
        for uploaded_file in conversation.uploaded_files:
            if uploaded_file not in context.uploaded_files:
                context.uploaded_files.append(uploaded_file)
        if conversation.uploaded_files:
            logger.info(f"Synced {len(conversation.uploaded_files)} files to state manager context")

        # Process confirmation through handler chain
        message_data = {
            "chat_id": chat_id,
            "confirmed": confirmed,
            "modified_workflow": modified_workflow,
        }

        response = self.message_handler.process("confirmation", message_data, context)

        # Handle workflow execution if confirmed
        if confirmed and response.get("action") == "execute_workflow":
            if run_async:
                # Execute in background
                return self._execute_workflow_background(chat_id, response["workflow_steps"])
            else:
                # Execute synchronously (original behavior)
                return self._execute_workflow(chat_id, response["workflow_steps"])

        # Add bot response to conversation
        if response.get("bot_response"):
            self.repository.add_message(chat_id, MessageType.SYSTEM, response["bot_response"], {})

        return response

    def get_conversation_history(self, chat_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get conversation history.

        Args:
            chat_id: Conversation ID
            limit: Optional limit on number of messages

        Returns:
            Conversation history
        """
        conversation = self.repository.get_conversation(chat_id)
        if not conversation:
            return {"success": False, "error": "Conversation not found"}

        # Get context
        context = self.state_manager.get_context(chat_id)

        # Get messages
        messages = conversation.messages
        if limit:
            messages = messages[-limit:]

        # Get output files with metadata (includes step_id)
        output_files_with_metadata = getattr(conversation, '_output_files_with_metadata', [])
        # If the attribute doesn't exist (old conversations), fall back to simple list
        if not output_files_with_metadata:
            output_files_with_metadata = [{"file_path": fp} for fp in conversation.output_files]

        return {
            "success": True,
            "chat_id": chat_id,
            "participant_name": conversation.participant_name,
            "status": conversation.status.value,
            "current_state": context.current_state.value if context else "unknown",
            "messages": [msg.to_dict() for msg in messages],
            "uploaded_files": conversation.uploaded_files,
            "output_files": output_files_with_metadata,
            "workflow_steps": [step.to_dict() for step in conversation.workflow_steps],
        }

    def _execute_workflow(
        self, chat_id: str, workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute workflow steps.

        Args:
            chat_id: Conversation ID
            workflow_steps: List of workflow step configurations

        Returns:
            Execution response
        """
        logger.info(f"Executing workflow for {chat_id} with {len(workflow_steps)} steps")

        # Get conversation
        conversation = self.repository.get_conversation(chat_id)
        if not conversation:
            return {"success": False, "error": "Conversation not found"}

        # Transition to processing state
        self.state_manager.transition_state(chat_id, BotState.PROCESSING)
        conversation.status = ConversationStatus.PROCESSING
        self.repository.update_conversation(conversation)

        # Get latest uploaded file
        latest_file = self.state_manager.get_latest_file(chat_id)
        if not latest_file:
            return {"success": False, "error": "No uploaded file found"}

        # Create workflow steps
        steps = []
        for step_data in workflow_steps:
            step = WorkflowStep(
                step_id=str(uuid.uuid4()),
                operation=step_data.get("operation"),
                arguments=step_data.get("arguments", {}),
            )
            steps.append(step)
            # Save workflow step to database
            self.repository.database.save_workflow_step(
                chat_id,
                step.step_id,
                step.operation,
                step.arguments,
                step.status.value,
                step.input_file,
                step.output_file,
                step.progress,
                step.error_message,
                step.started_at.isoformat() if step.started_at else None,
                step.completed_at.isoformat() if step.completed_at else None,
            )

        # Import WebSocket bridge for progress updates
        try:
            from app.chat.websocket_bridge import websocket_bridge

            # Send workflow started notification
            websocket_bridge.send_message(
                chat_id,
                {
                    "type": "workflow_started",
                    "chat_id": chat_id,
                    "total_steps": len(steps),
                    "message": "🚀 Starting workflow execution...",
                },
            )
        except Exception as e:
            logger.warning(f"WebSocket not available: {e}")

        # Create progress callback
        def progress_callback(step, progress, message):
            """Send progress updates to WebSocket clients."""
            try:
                from app.chat.websocket_bridge import websocket_bridge

                ws_message = {
                    "type": "progress",
                    "chat_id": chat_id,
                    "step_id": step.step_id,
                    "operation": step.operation,
                    "progress": progress,
                    "status": (
                        step.status.value if hasattr(step.status, "value") else str(step.status)
                    ),
                    "message": message,
                }
                websocket_bridge.send_message(chat_id, ws_message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket progress update: {e}")

        # Execute workflow
        try:
            results = self.executor.execute_workflow(steps, latest_file, progress_callback)

            # Save updated workflow steps to database (they were updated during execution)
            for step in steps:
                self.repository.database.save_workflow_step(
                    chat_id,
                    step.step_id,
                    step.operation,
                    step.arguments,
                    step.status.value,
                    step.input_file,
                    step.output_file,
                    step.progress,
                    step.error_message,
                    step.started_at.isoformat() if step.started_at else None,
                    step.completed_at.isoformat() if step.completed_at else None,
                )

            # Save output files with their corresponding step_id
            from app.chat.storage import ConversationStorage

            storage = self.repository.storage

            output_files = []
            for i, result in enumerate(results):
                if result.get("output_file_path"):
                    saved_path = storage.save_output_file(
                        chat_id,
                        conversation.partition_key,
                        result["output_file_path"],
                        is_final=(i == len(results) - 1),
                    )
                    # Get the step_id for this result (results and steps are in the same order)
                    step_id = steps[i].step_id if i < len(steps) else None
                    self.repository.database.save_file(chat_id, saved_path, "output", step_id)
                    output_files.append(saved_path)

            # Update conversation
            conversation.status = ConversationStatus.COMPLETED
            self.repository.update_conversation(conversation)

            # Update state
            self.state_manager.transition_state(chat_id, BotState.COMPLETED)
            self.state_manager.clear_pending_workflow(chat_id)

            # Send completion notification
            try:
                from app.chat.websocket_bridge import websocket_bridge

                websocket_bridge.send_message(
                    chat_id,
                    {
                        "type": "workflow_completed",
                        "chat_id": chat_id,
                        "total_steps": len(steps),
                        "output_files_count": len(output_files),
                        "message": "✅ Workflow completed successfully!",
                    },
                )
            except Exception as e:
                logger.warning(f"WebSocket notification failed: {e}")

            # Add completion message
            self.repository.add_message(
                chat_id,
                MessageType.SYSTEM,
                "✅ Workflow completed successfully! Your files are ready for download.",
                {"output_files": output_files, "results": results},
            )

            # Transition back to idle
            self.state_manager.transition_state(chat_id, BotState.IDLE)

            return {
                "success": True,
                "message": "Workflow executed successfully",
                "bot_response": "✅ Workflow completed successfully! Your files are ready for download.",
                "results": results,
                "output_files": output_files,
            }

        except Exception as e:
            # Handle failure
            conversation.status = ConversationStatus.FAILED
            self.repository.update_conversation(conversation)

            self.state_manager.transition_state(chat_id, BotState.FAILED)

            # Send error notification
            try:
                from app.chat.websocket_bridge import websocket_bridge

                websocket_bridge.send_message(
                    chat_id,
                    {
                        "type": "workflow_failed",
                        "chat_id": chat_id,
                        "error": str(e),
                        "message": f"❌ Workflow failed: {str(e)}",
                    },
                )
            except Exception as ws_err:
                logger.warning(f"WebSocket notification failed: {ws_err}")

            # Add error message
            self.repository.add_message(
                chat_id,
                MessageType.ERROR,
                f"❌ Workflow execution failed: {str(e)}",
                {"error": str(e)},
            )

            # Transition back to idle
            self.state_manager.transition_state(chat_id, BotState.IDLE)

            return {
                "success": False,
                "error": str(e),
                "bot_response": f"❌ Sorry, something went wrong: {str(e)}\n\nPlease try again or rephrase your request.",
            }

    def _create_welcome_message(self) -> str:
        """Create welcome message for new conversation."""
        return """👋 **Welcome to Pycelize Chat Bot!**

I'm here to help you process Excel and CSV files. Here's how we can work together:

📋 **What I can do:**
- Extract specific columns
- Convert between formats (CSV ↔ Excel ↔ JSON)
- Normalize and clean data
- Generate SQL INSERT statements
- Search and filter data
- Bind/merge data from multiple files
- Rename/map column names

🚀 **How to get started:**
1. Upload your file
2. Tell me what you want to do
3. I'll suggest a workflow for you to confirm
4. I'll process your file and provide download links

Type **help** for more information or just tell me what you'd like to do!"""

    def _execute_workflow_background(
        self, chat_id: str, workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute workflow steps in background without blocking.

        Args:
            chat_id: Conversation ID
            workflow_steps: List of workflow step configurations

        Returns:
            Job submission response with job_id for tracking
        """
        from app.chat.background_executor import get_background_executor

        logger.info(f"Submitting workflow for {chat_id} for background execution")

        # Get conversation
        conversation = self.repository.get_conversation(chat_id)
        if not conversation:
            return {"success": False, "error": "Conversation not found"}

        # Get latest uploaded file
        latest_file = self.state_manager.get_latest_file(chat_id)
        if not latest_file:
            return {"success": False, "error": "No uploaded file found"}

        # Generate job ID with timestamp to prevent collisions
        import time
        timestamp = int(time.time() * 1000)  # milliseconds
        job_id = f"{chat_id}_workflow_{timestamp}_{uuid.uuid4().hex[:8]}"

        # Get background executor
        executor = get_background_executor()

        # Define completion callback
        def on_workflow_complete(success: bool, result: Any, error: Optional[str]):
            """Callback when workflow completes in background."""
            try:
                if success:
                    logger.info(f"Background workflow for {chat_id} completed successfully")
                else:
                    logger.error(f"Background workflow for {chat_id} failed: {error}")
            except Exception as e:
                logger.error(f"Error in workflow completion callback: {e}")

        # Submit workflow to background executor
        executor.submit_workflow(
            job_id=job_id,
            workflow_func=self._execute_workflow,
            chat_id=chat_id,
            workflow_steps=workflow_steps,
            on_complete=on_workflow_complete,
        )

        logger.info(f"Workflow submitted for background execution with job_id: {job_id}")

        return {
            "success": True,
            "message": "Workflow submitted for background execution",
            "job_id": job_id,
            "status": "submitted",
        }

    def get_workflow_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background workflow job.

        Args:
            job_id: Job identifier

        Returns:
            Job status information or None if not found
        """
        from app.chat.background_executor import get_background_executor

        executor = get_background_executor()
        return executor.get_job_status(job_id)

    def cleanup_old_contexts(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old conversation contexts.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of contexts cleaned up
        """
        return self.state_manager.cleanup_old_contexts(max_age_seconds)
