"""
Chat Workflows Data Models

This module defines the data models for chat workflows, conversations,
messages, and workflow steps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class ConversationStatus(Enum):
    """Enumeration of conversation statuses."""

    CREATED = "created"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class StepStatus(Enum):
    """Enumeration of workflow step statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MessageType(Enum):
    """Enumeration of message types."""

    USER = "user"
    SYSTEM = "system"
    FILE_UPLOAD = "file_upload"
    STEP_RESULT = "step_result"
    ERROR = "error"
    PROGRESS = "progress"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow execution.

    Attributes:
        step_id: Unique identifier for the step
        operation: API operation to execute (e.g., 'excel/extract-columns')
        arguments: Arguments for the operation
        input_file: Reference to input file (from previous step or upload)
        output_file: Generated output file path
        status: Current status of the step
        progress: Progress percentage (0-100)
        error_message: Error message if step failed
        started_at: Step start timestamp
        completed_at: Step completion timestamp
    """

    step_id: str
    operation: str
    arguments: Dict[str, Any]
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    progress: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "step_id": self.step_id,
            "operation": self.operation,
            "arguments": self.arguments,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "status": self.status.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


@dataclass
class Message:
    """
    Represents a message in a conversation.

    Attributes:
        message_id: Unique identifier for the message
        message_type: Type of message
        content: Message content
        metadata: Additional metadata
        created_at: Message creation timestamp
    """

    message_id: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Conversation:
    """
    Represents a complete chat conversation with workflow state.

    Attributes:
        chat_id: Unique identifier for the conversation
        participant_name: Auto-generated participant name
        status: Current status of the conversation
        messages: List of messages in the conversation
        workflow_steps: List of workflow steps
        uploaded_files: List of uploaded file paths
        output_files: List of generated output file paths
        metadata: Additional metadata
        created_at: Conversation creation timestamp
        updated_at: Last update timestamp
        partition_key: Partitioning key for storage
    """

    chat_id: str
    participant_name: str
    status: ConversationStatus = ConversationStatus.CREATED
    messages: List[Message] = field(default_factory=list)
    workflow_steps: List[WorkflowStep] = field(default_factory=list)
    uploaded_files: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    partition_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chat_id": self.chat_id,
            "participant_name": self.participant_name,
            "status": self.status.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "workflow_steps": [step.to_dict() for step in self.workflow_steps],
            "uploaded_files": self.uploaded_files,
            "output_files": self.output_files,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "partition_key": self.partition_key,
        }

    def to_summary(self) -> Dict[str, Any]:
        """Convert to summary representation (without full message/step data)."""
        return {
            "chat_id": self.chat_id,
            "participant_name": self.participant_name,
            "status": self.status.value,
            "message_count": len(self.messages),
            "step_count": len(self.workflow_steps),
            "uploaded_file_count": len(self.uploaded_files),
            "output_file_count": len(self.output_files),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
