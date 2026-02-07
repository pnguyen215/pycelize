"""
SQLite Database Management for Chat Workflows

This module provides database initialization, schema management,
and connection handling for chat workflow conversations.
"""

import sqlite3
import json
import shutil
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class ChatDatabase:
    """
    Manages SQLite database for chat workflow metadata.

    This class handles conversation indexing, metadata storage,
    and provides optimized queries for conversation management.
    """

    SCHEMA_VERSION = "1.0.0"

    # SQL schema for conversations table
    CREATE_CONVERSATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS conversations (
        chat_id TEXT PRIMARY KEY,
        participant_name TEXT NOT NULL,
        status TEXT NOT NULL,
        partition_key TEXT,
        metadata TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """

    CREATE_MESSAGES_TABLE = """
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        chat_id TEXT NOT NULL,
        message_type TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (chat_id) REFERENCES conversations(chat_id) ON DELETE CASCADE
    )
    """

    CREATE_WORKFLOW_STEPS_TABLE = """
    CREATE TABLE IF NOT EXISTS workflow_steps (
        step_id TEXT PRIMARY KEY,
        chat_id TEXT NOT NULL,
        operation TEXT NOT NULL,
        arguments TEXT NOT NULL,
        input_file TEXT,
        output_file TEXT,
        status TEXT NOT NULL,
        progress INTEGER DEFAULT 0,
        error_message TEXT,
        started_at TEXT,
        completed_at TEXT,
        FOREIGN KEY (chat_id) REFERENCES conversations(chat_id) ON DELETE CASCADE
    )
    """

    CREATE_FILES_TABLE = """
    CREATE TABLE IF NOT EXISTS files (
        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (chat_id) REFERENCES conversations(chat_id) ON DELETE CASCADE
    )
    """

    # Indexes for performance
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_conv_status ON conversations(status)",
        "CREATE INDEX IF NOT EXISTS idx_conv_created ON conversations(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_steps_chat ON workflow_steps(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_files_chat ON files(chat_id)",
    ]

    def __init__(self, db_path: str):
        """
        Initialize database connection and ensure schema exists.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()
        self._init_schema()

    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        conn = self._get_connection()
        try:
            # Create tables
            conn.execute(self.CREATE_CONVERSATIONS_TABLE)
            conn.execute(self.CREATE_MESSAGES_TABLE)
            conn.execute(self.CREATE_WORKFLOW_STEPS_TABLE)
            conn.execute(self.CREATE_FILES_TABLE)

            # Create indexes
            for index_sql in self.CREATE_INDEXES:
                conn.execute(index_sql)

            conn.commit()
        finally:
            conn.close()

    def save_conversation(self, conversation: Dict[str, Any]) -> None:
        """
        Save or update a conversation.

        Args:
            conversation: Conversation dictionary
        """
        conn = self._get_connection()
        try:
            # Use INSERT ... ON CONFLICT DO UPDATE to avoid triggering CASCADE DELETE
            conn.execute(
                """
                INSERT INTO conversations
                (chat_id, participant_name, status, partition_key, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    participant_name = excluded.participant_name,
                    status = excluded.status,
                    partition_key = excluded.partition_key,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at
                """,
                (
                    conversation["chat_id"],
                    conversation["participant_name"],
                    conversation["status"],
                    conversation.get("partition_key"),
                    json.dumps(conversation.get("metadata", {})),
                    conversation["created_at"],
                    conversation["updated_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_conversation(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversation by ID.

        Args:
            chat_id: Conversation identifier

        Returns:
            Conversation dictionary or None if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM conversations WHERE chat_id = ?", (chat_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "chat_id": row["chat_id"],
                    "participant_name": row["participant_name"],
                    "status": row["status"],
                    "partition_key": row["partition_key"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            return None
        finally:
            conn.close()

    def list_conversations(
        self, status: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List conversations with optional filtering.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of conversation dictionaries
        """
        conn = self._get_connection()
        try:
            if status:
                cursor = conn.execute(
                    """
                    SELECT * FROM conversations
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (status, limit, offset),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM conversations
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )

            conversations = []
            for row in cursor.fetchall():
                conversations.append(
                    {
                        "chat_id": row["chat_id"],
                        "participant_name": row["participant_name"],
                        "status": row["status"],
                        "partition_key": row["partition_key"],
                        "metadata": json.loads(row["metadata"])
                        if row["metadata"]
                        else {},
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )
            return conversations
        finally:
            conn.close()

    def delete_conversation(self, chat_id: str) -> bool:
        """
        Delete a conversation and all related data.

        Args:
            chat_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE chat_id = ?", (chat_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def backup(self, snapshot_path: str) -> str:
        """
        Create a backup snapshot of the database.

        Args:
            snapshot_path: Directory for snapshots

        Returns:
            Path to created backup file
        """
        os.makedirs(snapshot_path, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(
            snapshot_path, f"chat_backup_{timestamp}.db"
        )

        # Close any existing connections and copy file
        shutil.copy2(self.db_path, backup_file)
        return backup_file

    def save_file(self, chat_id: str, file_path: str, file_type: str) -> None:
        """
        Save file metadata to database.

        Args:
            chat_id: Conversation identifier
            file_path: Path to the file
            file_type: Type of file (uploaded or output)
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO files (chat_id, file_path, file_type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, file_path, file_type, datetime.utcnow().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_files(self, chat_id: str) -> Dict[str, List[str]]:
        """
        Retrieve all files for a conversation.

        Args:
            chat_id: Conversation identifier

        Returns:
            Dictionary with 'uploaded' and 'output' file lists
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT file_path, file_type FROM files WHERE chat_id = ? ORDER BY created_at",
                (chat_id,),
            )
            
            files = {"uploaded": [], "output": []}
            for row in cursor.fetchall():
                file_type = row["file_type"]
                if file_type == "uploaded":
                    files["uploaded"].append(row["file_path"])
                elif file_type == "output":
                    files["output"].append(row["file_path"])
            
            return files
        finally:
            conn.close()

    def delete_files(self, chat_id: str) -> bool:
        """
        Delete all files for a conversation.

        Args:
            chat_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM files WHERE chat_id = ?", (chat_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def save_message(self, message: Dict[str, Any]) -> None:
        """
        Save a message to database.

        Args:
            message: Message dictionary
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO messages
                (message_id, chat_id, message_type, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message["message_id"],
                    message["chat_id"],
                    message["message_type"],
                    message["content"],
                    json.dumps(message.get("metadata", {})),
                    message["created_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_messages(
        self, chat_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a conversation.

        Args:
            chat_id: Conversation identifier
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of message dictionaries
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM messages
                WHERE chat_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
                """,
                (chat_id, limit, offset),
            )

            messages = []
            for row in cursor.fetchall():
                messages.append(
                    {
                        "message_id": row["message_id"],
                        "chat_id": row["chat_id"],
                        "message_type": row["message_type"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata"])
                        if row["metadata"]
                        else {},
                        "created_at": row["created_at"],
                    }
                )
            return messages
        finally:
            conn.close()

    def save_workflow_step(self, step: Dict[str, Any]) -> None:
        """
        Save or update a workflow step.

        Args:
            step: Workflow step dictionary
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO workflow_steps
                (step_id, chat_id, operation, arguments, input_file, output_file,
                 status, progress, error_message, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(step_id) DO UPDATE SET
                    status = excluded.status,
                    progress = excluded.progress,
                    input_file = excluded.input_file,
                    output_file = excluded.output_file,
                    error_message = excluded.error_message,
                    started_at = excluded.started_at,
                    completed_at = excluded.completed_at
                """,
                (
                    step["step_id"],
                    step["chat_id"],
                    step["operation"],
                    json.dumps(step.get("arguments", {})),
                    step.get("input_file"),
                    step.get("output_file"),
                    step["status"],
                    step.get("progress", 0),
                    step.get("error_message"),
                    step.get("started_at"),
                    step.get("completed_at"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_workflow_steps(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve workflow steps for a conversation.

        Args:
            chat_id: Conversation identifier

        Returns:
            List of workflow step dictionaries
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM workflow_steps
                WHERE chat_id = ?
                ORDER BY started_at ASC
                """,
                (chat_id,),
            )

            steps = []
            for row in cursor.fetchall():
                steps.append(
                    {
                        "step_id": row["step_id"],
                        "chat_id": row["chat_id"],
                        "operation": row["operation"],
                        "arguments": json.loads(row["arguments"])
                        if row["arguments"]
                        else {},
                        "input_file": row["input_file"],
                        "output_file": row["output_file"],
                        "status": row["status"],
                        "progress": row["progress"],
                        "error_message": row["error_message"],
                        "started_at": row["started_at"],
                        "completed_at": row["completed_at"],
                    }
                )
            return steps
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with counts of conversations, messages, steps, files
        """
        conn = self._get_connection()
        try:
            stats = {}
            cursor = conn.execute("SELECT COUNT(*) as count FROM conversations")
            stats["total_conversations"] = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM messages")
            stats["total_messages"] = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM workflow_steps")
            stats["total_steps"] = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM files")
            stats["total_files"] = cursor.fetchone()["count"]

            return stats
        finally:
            conn.close()
