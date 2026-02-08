"""
Conversation Repository

This module provides the repository layer for conversation management,
combining SQLite database and file storage operations.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.chat.models import (
    Conversation,
    Message,
    WorkflowStep,
    ConversationStatus,
    MessageType,
    StepStatus,
)
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.name_generator import NameGenerator

logger = logging.getLogger(__name__)


class ConversationRepository:
    """
    Repository for managing conversations.

    Provides high-level operations combining database and file storage.
    """

    def __init__(self, database: ChatDatabase, storage: ConversationStorage):
        """
        Initialize repository.

        Args:
            database: Database manager instance
            storage: Storage manager instance
        """
        self.database = database
        self.storage = storage

    def create_conversation(self, chat_id: str) -> Conversation:
        """
        Create a new conversation.

        Args:
            chat_id: Unique conversation identifier

        Returns:
            Created Conversation object
        """
        # Generate participant name
        participant_name = NameGenerator.generate()

        # Create conversation object
        created_at = datetime.utcnow()
        conversation = Conversation(
            chat_id=chat_id,
            participant_name=participant_name,
            status=ConversationStatus.CREATED,
            created_at=created_at,
            updated_at=created_at,
        )

        # Create storage directory
        conv_path, partition_key = self.storage.create_conversation_directory(chat_id, created_at)
        conversation.partition_key = partition_key

        # Save to database
        self.database.save_conversation(conversation.to_dict())

        return conversation

    def get_conversation(self, chat_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.

        Args:
            chat_id: Conversation identifier

        Returns:
            Conversation object or None if not found
        """
        # Get from database
        conv_dict = self.database.get_conversation(chat_id)
        if not conv_dict:
            return None

        # Load full conversation data from storage if needed
        conversation = self._dict_to_conversation(conv_dict)
        return conversation

    def update_conversation(self, conversation: Conversation) -> None:
        """
        Update a conversation.

        Args:
            conversation: Conversation object to update
        """
        conversation.updated_at = datetime.utcnow()
        self.database.save_conversation(conversation.to_dict())

    def list_conversations(
        self, status: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List conversations.

        Args:
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of conversation summaries
        """
        return self.database.list_conversations(status, limit, offset)

    def delete_conversation(self, chat_id: str) -> bool:
        """
        Delete a conversation completely.

        Args:
            chat_id: Conversation identifier

        Returns:
            True if deleted successfully
        """
        # Get conversation to find partition key
        conv = self.get_conversation(chat_id)
        if not conv:
            return False

        # Delete from database (cascade deletes related records)
        self.database.delete_conversation(chat_id)

        # Delete files
        if conv.partition_key:
            self.storage.delete_conversation_directory(chat_id, conv.partition_key)

        return True

    def add_message(
        self,
        chat_id: str,
        message_type: MessageType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            chat_id: Conversation identifier
            message_type: Type of message
            content: Message content
            metadata: Optional metadata

        Returns:
            Created Message object
        """
        import uuid

        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            content=content,
            metadata=metadata or {},
        )

        # Save message to database
        self.database.save_message(
            chat_id,
            message.message_id,
            message.message_type.value,
            message.content,
            message.metadata,
            message.created_at.isoformat(),
        )

        return message

    def add_workflow_step(
        self, chat_id: str, operation: str, arguments: Dict[str, Any]
    ) -> WorkflowStep:
        """
        Add a workflow step to a conversation.

        Args:
            chat_id: Conversation identifier
            operation: Operation name
            arguments: Operation arguments

        Returns:
            Created WorkflowStep object
        """
        import uuid

        step = WorkflowStep(step_id=str(uuid.uuid4()), operation=operation, arguments=arguments)

        # Save workflow step to database
        self.database.save_workflow_step(
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

        return step

    def dump_conversation(self, chat_id: str, dump_path: str, compression: str = "gzip") -> str:
        """
        Create a dump of conversation data.

        Args:
            chat_id: Conversation identifier
            dump_path: Path for dumps
            compression: Compression format

        Returns:
            Path to created dump file
        """
        conversation = self.get_conversation(chat_id)
        if not conversation:
            raise ValueError(f"Conversation {chat_id} not found")

        # Create file dump
        dump_file = self.storage.dump_conversation(
            chat_id, conversation.partition_key, dump_path, compression
        )

        # Save conversation metadata to dump directory
        metadata_file = dump_file.replace(".tar.gz", "_metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(conversation.to_dict(), f, indent=2)

        return dump_file

    def restore_conversation(
        self, dump_file_path: str, new_chat_id: Optional[str] = None
    ) -> Conversation:
        """
        Restore a conversation from dump.

        Args:
            dump_file_path: Path to dump file
            new_chat_id: Optional new chat ID

        Returns:
            Restored Conversation object
        """
        # Restore files
        chat_id, partition_key = self.storage.restore_conversation(dump_file_path, new_chat_id)

        # Load metadata
        metadata_file = dump_file_path.replace(".tar.gz", "_metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                conv_dict = json.load(f)
                if new_chat_id:
                    conv_dict["chat_id"] = new_chat_id
                conv_dict["partition_key"] = partition_key

                # Save to database
                self.database.save_conversation(conv_dict)

                return self._dict_to_conversation(conv_dict)
        else:
            raise ValueError("Metadata file not found in dump")

    def _dict_to_conversation(self, conv_dict: Dict[str, Any]) -> Conversation:
        """
        Convert dictionary to Conversation object.

        Args:
            conv_dict: Conversation dictionary

        Returns:
            Conversation object
        """
        # Parse datetimes
        created_at = datetime.fromisoformat(conv_dict["created_at"])
        updated_at = datetime.fromisoformat(conv_dict["updated_at"])

        # Get files from database
        files = self.database.get_files(conv_dict["chat_id"])

        # Get messages from database
        messages_data = self.database.get_messages(conv_dict["chat_id"])
        messages = []
        for msg_data in messages_data:
            messages.append(
                Message(
                    message_id=msg_data["message_id"],
                    message_type=MessageType(msg_data["message_type"]),
                    content=msg_data["content"],
                    metadata=msg_data["metadata"],
                    created_at=datetime.fromisoformat(msg_data["created_at"]),
                )
            )

        # Get workflow steps from database
        steps_data = self.database.get_workflow_steps(conv_dict["chat_id"])
        workflow_steps = []
        for step_data in steps_data:
            workflow_steps.append(
                WorkflowStep(
                    step_id=step_data["step_id"],
                    operation=step_data["operation"],
                    arguments=step_data["arguments"],
                    input_file=step_data["input_file"],
                    output_file=step_data["output_file"],
                    status=StepStatus(step_data["status"]),
                    progress=step_data["progress"],
                    error_message=step_data["error_message"],
                    started_at=(
                        datetime.fromisoformat(step_data["started_at"])
                        if step_data["started_at"]
                        else None
                    ),
                    completed_at=(
                        datetime.fromisoformat(step_data["completed_at"])
                        if step_data["completed_at"]
                        else None
                    ),
                )
            )

        # Create conversation
        conversation = Conversation(
            chat_id=conv_dict["chat_id"],
            participant_name=conv_dict["participant_name"],
            status=ConversationStatus(conv_dict["status"]),
            uploaded_files=files.get("uploaded", []),
            output_files=files.get("output", []),
            messages=messages,
            workflow_steps=workflow_steps,
            metadata=conv_dict.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            partition_key=conv_dict.get("partition_key"),
        )

        return conversation
