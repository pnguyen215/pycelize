"""
Conversation State Manager

This module manages chat bot conversation states and transitions,
tracking the current state of each conversation and user context.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from app.chat.models import Conversation, ConversationStatus

logger = logging.getLogger(__name__)


class BotState(Enum):
    """Enumeration of bot conversation states."""

    IDLE = "idle"  # Initial state, awaiting user action
    AWAITING_FILE = "awaiting_file"  # Waiting for file upload
    AWAITING_CONFIRMATION = "awaiting_confirmation"  # Waiting for workflow confirmation
    AWAITING_PARAMETERS = "awaiting_parameters"  # Waiting for additional parameters
    PROCESSING = "processing"  # Workflow execution in progress
    COMPLETED = "completed"  # Workflow completed successfully
    FAILED = "failed"  # Workflow failed
    CANCELLED = "cancelled"  # User cancelled the operation


@dataclass
class ConversationContext:
    """
    Context information for a conversation.

    Attributes:
        chat_id: Conversation identifier
        current_state: Current bot state
        previous_state: Previous bot state
        intent_history: List of detected intents
        uploaded_files: List of uploaded file paths
        pending_workflow: Pending workflow steps awaiting confirmation
        workflow_params: Parameters for workflow execution
        user_preferences: User preferences and settings
        last_message_time: Timestamp of last message
        metadata: Additional metadata
    """

    chat_id: str
    current_state: BotState = BotState.IDLE
    previous_state: Optional[BotState] = None
    intent_history: List[Dict[str, Any]] = field(default_factory=list)
    uploaded_files: List[str] = field(default_factory=list)
    pending_workflow: Optional[List[Dict[str, Any]]] = None
    workflow_params: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    last_message_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chat_id": self.chat_id,
            "current_state": self.current_state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "intent_history": self.intent_history,
            "uploaded_files": self.uploaded_files,
            "pending_workflow": self.pending_workflow,
            "workflow_params": self.workflow_params,
            "user_preferences": self.user_preferences,
            "last_message_time": (
                self.last_message_time.isoformat() if self.last_message_time else None
            ),
            "metadata": self.metadata,
        }


class ConversationStateManager:
    """
    Manages conversation states and transitions for chat bot interactions.

    Tracks conversation context, validates state transitions, and maintains
    conversation history and user preferences.
    """

    # Valid state transitions
    STATE_TRANSITIONS = {
        BotState.IDLE: [
            BotState.AWAITING_FILE,
            BotState.AWAITING_CONFIRMATION,
            BotState.AWAITING_PARAMETERS,
        ],
        BotState.AWAITING_FILE: [BotState.AWAITING_CONFIRMATION, BotState.CANCELLED, BotState.IDLE],
        BotState.AWAITING_CONFIRMATION: [
            BotState.PROCESSING,
            BotState.AWAITING_PARAMETERS,
            BotState.CANCELLED,
            BotState.IDLE,
        ],
        BotState.AWAITING_PARAMETERS: [
            BotState.AWAITING_CONFIRMATION,
            BotState.CANCELLED,
            BotState.IDLE,
        ],
        BotState.PROCESSING: [BotState.COMPLETED, BotState.FAILED],
        BotState.COMPLETED: [BotState.IDLE],
        BotState.FAILED: [BotState.IDLE],
        BotState.CANCELLED: [BotState.IDLE],
    }

    def __init__(self):
        """Initialize state manager."""
        self._contexts: Dict[str, ConversationContext] = {}

    def get_or_create_context(self, chat_id: str) -> ConversationContext:
        """
        Get or create conversation context.

        Args:
            chat_id: Conversation identifier

        Returns:
            ConversationContext object
        """
        if chat_id not in self._contexts:
            self._contexts[chat_id] = ConversationContext(chat_id=chat_id)
            logger.info(f"Created new conversation context for chat_id: {chat_id}")

        return self._contexts[chat_id]

    def get_context(self, chat_id: str) -> Optional[ConversationContext]:
        """
        Get conversation context.

        Args:
            chat_id: Conversation identifier

        Returns:
            ConversationContext or None if not found
        """
        return self._contexts.get(chat_id)

    def transition_state(
        self, chat_id: str, new_state: BotState, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Transition conversation to a new state.

        Args:
            chat_id: Conversation identifier
            new_state: Target state
            metadata: Optional metadata about the transition

        Returns:
            True if transition was successful, False otherwise
        """
        context = self.get_or_create_context(chat_id)
        current_state = context.current_state

        # Validate transition
        valid_transitions = self.STATE_TRANSITIONS.get(current_state, [])
        if new_state not in valid_transitions:
            logger.warning(
                f"Invalid state transition for {chat_id}: {current_state.value} -> {new_state.value}"
            )
            return False

        # Perform transition
        context.previous_state = current_state
        context.current_state = new_state
        context.last_message_time = datetime.utcnow()

        if metadata:
            context.metadata.update(metadata)

        logger.info(f"State transition for {chat_id}: {current_state.value} -> {new_state.value}")

        return True

    def set_pending_workflow(self, chat_id: str, workflow_steps: List[Dict[str, Any]]) -> None:
        """
        Set pending workflow steps awaiting confirmation.

        Args:
            chat_id: Conversation identifier
            workflow_steps: List of workflow steps
        """
        context = self.get_or_create_context(chat_id)
        context.pending_workflow = workflow_steps
        logger.info(f"Set pending workflow for {chat_id} with {len(workflow_steps)} steps")

    def get_pending_workflow(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get pending workflow steps.

        Args:
            chat_id: Conversation identifier

        Returns:
            List of workflow steps or None
        """
        context = self.get_context(chat_id)
        return context.pending_workflow if context else None

    def clear_pending_workflow(self, chat_id: str) -> None:
        """
        Clear pending workflow steps.

        Args:
            chat_id: Conversation identifier
        """
        context = self.get_context(chat_id)
        if context:
            context.pending_workflow = None
            logger.info(f"Cleared pending workflow for {chat_id}")

    def add_uploaded_file(self, chat_id: str, file_path: str) -> None:
        """
        Add uploaded file to context.

        Args:
            chat_id: Conversation identifier
            file_path: Path to uploaded file
        """
        context = self.get_or_create_context(chat_id)
        context.uploaded_files.append(file_path)
        logger.info(f"Added uploaded file for {chat_id}: {file_path}")

    def get_latest_file(self, chat_id: str) -> Optional[str]:
        """
        Get latest uploaded file.

        Args:
            chat_id: Conversation identifier

        Returns:
            File path or None
        """
        context = self.get_context(chat_id)
        if context and context.uploaded_files:
            return context.uploaded_files[-1]
        return None

    def add_intent(self, chat_id: str, intent: Dict[str, Any]) -> None:
        """
        Add detected intent to history.

        Args:
            chat_id: Conversation identifier
            intent: Intent information
        """
        context = self.get_or_create_context(chat_id)
        intent_with_time = {**intent, "timestamp": datetime.utcnow().isoformat()}
        context.intent_history.append(intent_with_time)
        logger.info(f"Added intent to history for {chat_id}: {intent.get('intent_type')}")

    def get_recent_intents(self, chat_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent intents from history.

        Args:
            chat_id: Conversation identifier
            limit: Maximum number of intents to return

        Returns:
            List of recent intents
        """
        context = self.get_context(chat_id)
        if context and context.intent_history:
            return context.intent_history[-limit:]
        return []

    def set_workflow_params(self, chat_id: str, params: Dict[str, Any]) -> None:
        """
        Set workflow parameters.

        Args:
            chat_id: Conversation identifier
            params: Workflow parameters
        """
        context = self.get_or_create_context(chat_id)
        context.workflow_params.update(params)
        logger.info(f"Updated workflow params for {chat_id}")

    def get_workflow_params(self, chat_id: str) -> Dict[str, Any]:
        """
        Get workflow parameters.

        Args:
            chat_id: Conversation identifier

        Returns:
            Workflow parameters dictionary
        """
        context = self.get_context(chat_id)
        return context.workflow_params if context else {}

    def clear_workflow_params(self, chat_id: str) -> None:
        """
        Clear workflow parameters.

        Args:
            chat_id: Conversation identifier
        """
        context = self.get_context(chat_id)
        if context:
            context.workflow_params = {}
            logger.info(f"Cleared workflow params for {chat_id}")

    def set_user_preference(self, chat_id: str, key: str, value: Any) -> None:
        """
        Set user preference.

        Args:
            chat_id: Conversation identifier
            key: Preference key
            value: Preference value
        """
        context = self.get_or_create_context(chat_id)
        context.user_preferences[key] = value
        logger.info(f"Set user preference for {chat_id}: {key}")

    def get_user_preference(self, chat_id: str, key: str, default: Any = None) -> Any:
        """
        Get user preference.

        Args:
            chat_id: Conversation identifier
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        context = self.get_context(chat_id)
        if context:
            return context.user_preferences.get(key, default)
        return default

    def reset_context(self, chat_id: str) -> None:
        """
        Reset conversation context to initial state.

        Args:
            chat_id: Conversation identifier
        """
        if chat_id in self._contexts:
            del self._contexts[chat_id]
            logger.info(f"Reset conversation context for {chat_id}")

    def is_processing(self, chat_id: str) -> bool:
        """
        Check if conversation is in processing state.

        Args:
            chat_id: Conversation identifier

        Returns:
            True if processing
        """
        context = self.get_context(chat_id)
        return context and context.current_state == BotState.PROCESSING

    def is_awaiting_input(self, chat_id: str) -> bool:
        """
        Check if conversation is awaiting user input.

        Args:
            chat_id: Conversation identifier

        Returns:
            True if awaiting input
        """
        context = self.get_context(chat_id)
        if not context:
            return False

        awaiting_states = [
            BotState.AWAITING_FILE,
            BotState.AWAITING_CONFIRMATION,
            BotState.AWAITING_PARAMETERS,
        ]
        return context.current_state in awaiting_states

    def get_state_description(self, chat_id: str) -> str:
        """
        Get human-readable description of current state.

        Args:
            chat_id: Conversation identifier

        Returns:
            State description
        """
        context = self.get_context(chat_id)
        if not context:
            return "No conversation found"

        descriptions = {
            BotState.IDLE: "Ready for your request",
            BotState.AWAITING_FILE: "Waiting for file upload",
            BotState.AWAITING_CONFIRMATION: "Waiting for your confirmation",
            BotState.AWAITING_PARAMETERS: "Waiting for additional parameters",
            BotState.PROCESSING: "Processing your request",
            BotState.COMPLETED: "Request completed successfully",
            BotState.FAILED: "Request failed",
            BotState.CANCELLED: "Request cancelled",
        }

        return descriptions.get(context.current_state, "Unknown state")

    def get_all_contexts(self) -> Dict[str, ConversationContext]:
        """
        Get all conversation contexts.

        Returns:
            Dictionary of chat_id to ConversationContext
        """
        return self._contexts.copy()

    def cleanup_old_contexts(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old inactive contexts.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of contexts removed
        """
        now = datetime.utcnow()
        to_remove = []

        for chat_id, context in self._contexts.items():
            if context.last_message_time:
                age = (now - context.last_message_time).total_seconds()
                if age > max_age_seconds and context.current_state in [
                    BotState.COMPLETED,
                    BotState.FAILED,
                    BotState.CANCELLED,
                ]:
                    to_remove.append(chat_id)

        for chat_id in to_remove:
            del self._contexts[chat_id]
            logger.info(f"Cleaned up old context for {chat_id}")

        return len(to_remove)
