"""
Message Handlers for Chat Bot

This module implements a Chain of Responsibility pattern for processing
different types of chat bot messages (text, file, confirmation, etc.).
"""

import logging
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from app.chat.models import MessageType
from app.chat.intent_classifier import IntentClassifier, IntentType
from app.chat.state_manager import ConversationStateManager, BotState

logger = logging.getLogger(__name__)


class MessageHandler(ABC):
    """
    Abstract base class for message handlers.

    Implements Chain of Responsibility pattern for message processing.
    """

    def __init__(self):
        """Initialize handler."""
        self._next_handler: Optional["MessageHandler"] = None

    def set_next(self, handler: "MessageHandler") -> "MessageHandler":
        """
        Set the next handler in the chain.

        Args:
            handler: Next handler

        Returns:
            The next handler for chaining
        """
        self._next_handler = handler
        return handler

    @abstractmethod
    def can_handle(self, message_type: str, message_data: Dict[str, Any], context: Any) -> bool:
        """
        Check if this handler can handle the message.

        Args:
            message_type: Type of message
            message_data: Message data
            context: Conversation context

        Returns:
            True if can handle
        """
        pass

    @abstractmethod
    def handle(
        self, message_type: str, message_data: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Handle the message.

        Args:
            message_type: Type of message
            message_data: Message data
            context: Conversation context

        Returns:
            Response dictionary
        """
        pass

    def process(
        self, message_type: str, message_data: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Process the message or pass to next handler.

        Args:
            message_type: Type of message
            message_data: Message data
            context: Conversation context

        Returns:
            Response dictionary
        """
        if self.can_handle(message_type, message_data, context):
            return self.handle(message_type, message_data, context)
        elif self._next_handler:
            return self._next_handler.process(message_type, message_data, context)
        else:
            return {
                "success": False,
                "message": "No handler found for this message type",
                "bot_response": "I'm not sure how to handle that message. Could you please try again?",
            }


class TextMessageHandler(MessageHandler):
    """Handler for text messages with intent classification."""

    def __init__(
        self, intent_classifier: IntentClassifier, state_manager: ConversationStateManager
    ):
        """
        Initialize text message handler.

        Args:
            intent_classifier: Intent classifier instance
            state_manager: State manager instance
        """
        super().__init__()
        self.intent_classifier = intent_classifier
        self.state_manager = state_manager

    def can_handle(self, message_type: str, message_data: Dict[str, Any], context: Any) -> bool:
        """Check if can handle text messages."""
        return message_type == "text"

    def handle(
        self, message_type: str, message_data: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Handle text message with intent classification."""
        chat_id = message_data.get("chat_id")
        text = message_data.get("text", "").strip()

        if not text:
            return {
                "success": False,
                "message": "Empty message",
                "bot_response": "Please send me a message describing what you'd like to do.",
            }

        # Get conversation context
        conv_context = self.state_manager.get_or_create_context(chat_id)
        current_state = conv_context.current_state

        # Handle special commands
        if text.lower() in ["cancel", "stop", "quit"]:
            return self._handle_cancel(chat_id, conv_context)

        if text.lower() in ["help", "?"]:
            return self._handle_help()

        # If waiting for confirmation
        if current_state == BotState.AWAITING_CONFIRMATION:
            return self._handle_confirmation_response(chat_id, text, conv_context)

        # If waiting for parameters
        if current_state == BotState.AWAITING_PARAMETERS:
            return self._handle_parameter_response(chat_id, text, conv_context)

        # Classify intent for new requests
        file_type = self._detect_file_type(conv_context)
        intent = self.intent_classifier.classify(text, context={"file_type": file_type})

        # Add intent to history
        self.state_manager.add_intent(
            chat_id,
            {
                "intent_type": intent.intent_type.value,
                "confidence": intent.confidence,
                "message": text,
            },
        )

        # Check if file is needed
        if intent.intent_type == IntentType.UNKNOWN:
            return {
                "success": False,
                "message": "Unknown intent",
                "bot_response": intent.explanation,
                "suggestions": [
                    "extract columns",
                    "convert to JSON",
                    "generate SQL",
                    "normalize data",
                ],
            }

        # Check if we have a file
        latest_file = self.state_manager.get_latest_file(chat_id)
        if not latest_file:
            self.state_manager.transition_state(chat_id, BotState.AWAITING_FILE)
            return {
                "success": True,
                "message": "File required",
                "bot_response": f"{intent.explanation}\n\n📎 Please upload your file to continue.",
                "intent": {"type": intent.intent_type.value, "confidence": intent.confidence},
                "requires_file": True,
            }

        # We have a file, suggest workflow
        self.state_manager.set_pending_workflow(chat_id, intent.suggested_operations)
        self.state_manager.transition_state(chat_id, BotState.AWAITING_CONFIRMATION)

        # Format workflow steps for user
        steps_text = self._format_workflow_steps(intent.suggested_operations)

        return {
            "success": True,
            "message": "Workflow suggested",
            "bot_response": (
                f"{intent.explanation}\n\n"
                f"📋 **Suggested Workflow:**\n{steps_text}\n\n"
                f"Would you like me to proceed with this workflow? (yes/no)\n"
                f"Or you can ask me to modify specific parameters."
            ),
            "intent": {"type": intent.intent_type.value, "confidence": intent.confidence},
            "suggested_workflow": intent.suggested_operations,
            "requires_confirmation": True,
        }

    def _handle_cancel(self, chat_id: str, conv_context: Any) -> Dict[str, Any]:
        """Handle cancellation request."""
        self.state_manager.transition_state(chat_id, BotState.CANCELLED)
        self.state_manager.clear_pending_workflow(chat_id)
        self.state_manager.clear_workflow_params(chat_id)
        self.state_manager.transition_state(chat_id, BotState.IDLE)

        return {
            "success": True,
            "message": "Operation cancelled",
            "bot_response": "✅ Operation cancelled. How else can I help you?",
        }

    def _handle_help(self) -> Dict[str, Any]:
        """Handle help request."""
        help_text = """
🤖 **Chat Bot Help**

I can help you process Excel and CSV files. Here's what I can do:

📊 **Data Operations:**
- Extract specific columns
- Convert between formats (CSV ↔ Excel ↔ JSON)
- Normalize and clean data
- Generate SQL INSERT statements
- Search and filter data
- Bind/merge data from multiple files
- Rename/map column names

💬 **How to use:**
1. Upload your file
2. Tell me what you want to do (e.g., "extract name and email columns")
3. Confirm or modify the suggested workflow
4. I'll process your file and provide download links

📝 **Examples:**
- "extract columns: name, email, phone"
- "convert to JSON"
- "generate SQL for table users"
- "normalize data - uppercase and trim"

Type **cancel** to cancel current operation.
"""
        return {"success": True, "message": "Help information", "bot_response": help_text.strip()}

    def _handle_confirmation_response(
        self, chat_id: str, text: str, conv_context: Any
    ) -> Dict[str, Any]:
        """Handle confirmation response (yes/no)."""
        text_lower = text.lower()

        if text_lower in ["yes", "y", "ok", "proceed", "continue", "go", "confirm"]:
            # User confirmed - ready to execute
            pending_workflow = self.state_manager.get_pending_workflow(chat_id)

            if not pending_workflow:
                return {
                    "success": False,
                    "message": "No pending workflow",
                    "bot_response": "There's no pending workflow to execute. Please describe what you'd like to do.",
                }

            return {
                "success": True,
                "message": "Workflow confirmed",
                "bot_response": "✅ Great! Starting workflow execution...",
                "action": "execute_workflow",
                "workflow_steps": pending_workflow,
            }

        elif text_lower in ["no", "n", "cancel", "stop"]:
            # User declined
            self.state_manager.clear_pending_workflow(chat_id)
            self.state_manager.transition_state(chat_id, BotState.IDLE)

            return {
                "success": True,
                "message": "Workflow declined",
                "bot_response": "No problem! Please tell me what you'd like to do differently.",
            }

        else:
            # User wants to modify - treat as new request
            return {
                "success": True,
                "message": "Modifying workflow",
                "bot_response": "Let me help you modify the workflow. What changes would you like to make?",
                "action": "modify_workflow",
            }

    def _handle_parameter_response(
        self, chat_id: str, text: str, conv_context: Any
    ) -> Dict[str, Any]:
        """Handle parameter input response."""
        # Parse parameter from text (simplified - could be more sophisticated)
        params = {}

        # Try to extract key-value pairs
        if ":" in text or "=" in text:
            parts = text.replace("=", ":").split(",")
            for part in parts:
                if ":" in part:
                    key, value = part.split(":", 1)
                    params[key.strip()] = value.strip()

        if params:
            self.state_manager.set_workflow_params(chat_id, params)
            self.state_manager.transition_state(chat_id, BotState.AWAITING_CONFIRMATION)

            return {
                "success": True,
                "message": "Parameters received",
                "bot_response": f"✅ Parameters updated: {params}\n\nShould I proceed with the workflow? (yes/no)",
                "parameters": params,
            }
        else:
            return {
                "success": False,
                "message": "Invalid parameters",
                "bot_response": "I couldn't parse the parameters. Please provide them in format: key: value, key2: value2",
            }

    def _detect_file_type(self, conv_context: Any) -> str:
        """Detect file type from uploaded files."""
        if conv_context.uploaded_files:
            latest_file = conv_context.uploaded_files[-1]
            ext = os.path.splitext(latest_file)[1].lower()

            if ext in [".xlsx", ".xls"]:
                return "xlsx"
            elif ext == ".csv":
                return "csv"
            elif ext == ".json":
                return "json"

        return "xlsx"  # Default

    def _format_workflow_steps(self, steps: list) -> str:
        """Format workflow steps for display."""
        if not steps:
            return "No steps"

        formatted = []
        for i, step in enumerate(steps, 1):
            operation = step.get("operation", "Unknown")
            description = step.get("description", "")
            formatted.append(f"{i}. {operation}: {description}")

        return "\n".join(formatted)


class FileMessageHandler(MessageHandler):
    """Handler for file upload messages."""

    def __init__(self, state_manager: ConversationStateManager):
        """
        Initialize file message handler.

        Args:
            state_manager: State manager instance
        """
        super().__init__()
        self.state_manager = state_manager

    def can_handle(self, message_type: str, message_data: Dict[str, Any], context: Any) -> bool:
        """Check if can handle file messages."""
        return message_type == "file"

    def handle(
        self, message_type: str, message_data: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Handle file upload message."""
        chat_id = message_data.get("chat_id")
        file_path = message_data.get("file_path")
        filename = message_data.get("filename", "uploaded file")

        if not file_path:
            return {
                "success": False,
                "message": "No file path provided",
                "bot_response": "There was an error with the file upload. Please try again.",
            }

        # Add file to context
        self.state_manager.add_uploaded_file(chat_id, file_path)

        # Get conversation context
        conv_context = self.state_manager.get_or_create_context(chat_id)
        current_state = conv_context.current_state

        # If we were waiting for a file
        if current_state == BotState.AWAITING_FILE:
            # Check if we have a pending workflow
            pending_workflow = self.state_manager.get_pending_workflow(chat_id)

            if pending_workflow:
                # Transition to confirmation
                self.state_manager.transition_state(chat_id, BotState.AWAITING_CONFIRMATION)
                steps_text = self._format_workflow_steps(pending_workflow)

                return {
                    "success": True,
                    "message": "File uploaded, awaiting confirmation",
                    "bot_response": (
                        f"✅ File '{filename}' uploaded successfully!\n\n"
                        f"📋 **Suggested Workflow:**\n{steps_text}\n\n"
                        f"Would you like me to proceed with this workflow? (yes/no)"
                    ),
                    "file_path": file_path,
                    "suggested_workflow": pending_workflow,
                    "requires_confirmation": True,
                }
            else:
                # No pending workflow, ask user what to do
                self.state_manager.transition_state(chat_id, BotState.IDLE)

                return {
                    "success": True,
                    "message": "File uploaded",
                    "bot_response": (
                        f"✅ File '{filename}' uploaded successfully!\n\n"
                        f"What would you like me to do with this file?\n\n"
                        f"Examples:\n"
                        f"- Extract specific columns\n"
                        f"- Convert to JSON\n"
                        f"- Generate SQL statements\n"
                        f"- Normalize data"
                    ),
                    "file_path": file_path,
                }
        else:
            # File uploaded in any other state
            return {
                "success": True,
                "message": "File uploaded",
                "bot_response": (
                    f"✅ File '{filename}' uploaded successfully!\n\n"
                    f"What would you like me to do with this file?"
                ),
                "file_path": file_path,
            }

    def _format_workflow_steps(self, steps: list) -> str:
        """Format workflow steps for display."""
        if not steps:
            return "No steps"

        formatted = []
        for i, step in enumerate(steps, 1):
            operation = step.get("operation", "Unknown")
            description = step.get("description", "")
            formatted.append(f"{i}. {operation}: {description}")

        return "\n".join(formatted)


class ConfirmationHandler(MessageHandler):
    """Handler for workflow confirmation/modification messages."""

    def __init__(self, state_manager: ConversationStateManager):
        """
        Initialize confirmation handler.

        Args:
            state_manager: State manager instance
        """
        super().__init__()
        self.state_manager = state_manager

    def can_handle(self, message_type: str, message_data: Dict[str, Any], context: Any) -> bool:
        """Check if can handle confirmation messages."""
        return message_type == "confirmation"

    def handle(
        self, message_type: str, message_data: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Handle confirmation message."""
        chat_id = message_data.get("chat_id")
        confirmed = message_data.get("confirmed", False)
        modified_workflow = message_data.get("modified_workflow")

        if confirmed:
            # Get pending workflow
            pending_workflow = self.state_manager.get_pending_workflow(chat_id)

            if modified_workflow:
                # Use modified workflow
                pending_workflow = modified_workflow
                self.state_manager.set_pending_workflow(chat_id, pending_workflow)

            if not pending_workflow:
                return {
                    "success": False,
                    "message": "No pending workflow",
                    "bot_response": "There's no pending workflow to execute.",
                }

            return {
                "success": True,
                "message": "Workflow confirmed",
                "bot_response": "✅ Great! Starting workflow execution...",
                "action": "execute_workflow",
                "workflow_steps": pending_workflow,
            }
        else:
            # User declined
            self.state_manager.clear_pending_workflow(chat_id)
            self.state_manager.transition_state(chat_id, BotState.IDLE)

            return {
                "success": True,
                "message": "Workflow declined",
                "bot_response": "No problem! Please tell me what you'd like to do differently.",
            }


class SystemMessageHandler(MessageHandler):
    """Handler for system messages (status updates, errors, etc.)."""

    def __init__(self, state_manager: ConversationStateManager):
        """
        Initialize system message handler.

        Args:
            state_manager: State manager instance
        """
        super().__init__()
        self.state_manager = state_manager

    def can_handle(self, message_type: str, message_data: Dict[str, Any], context: Any) -> bool:
        """Check if can handle system messages."""
        return message_type == "system"

    def handle(
        self, message_type: str, message_data: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Handle system message."""
        chat_id = message_data.get("chat_id")
        system_type = message_data.get("system_type", "info")
        message = message_data.get("message", "")

        # Log system message
        logger.info(f"System message for {chat_id} [{system_type}]: {message}")

        return {
            "success": True,
            "message": "System message processed",
            "bot_response": None,  # System messages don't generate bot responses
        }
