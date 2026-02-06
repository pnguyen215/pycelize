"""
File Storage Management for Chat Workflows

This module provides file-based storage management for conversation files,
including uploads, outputs, and conversation metadata.
"""

import os
import json
import shutil
import tarfile
import gzip
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class ConversationStorage:
    """
    Manages file-based storage for conversations.

    Each conversation has a dedicated folder containing:
    - Uploaded files
    - Intermediate outputs
    - Final output files
    - Conversation metadata
    """

    def __init__(self, base_path: str, partition_strategy: str = "time-based"):
        """
        Initialize storage manager.

        Args:
            base_path: Base path for workflow storage
            partition_strategy: Partitioning strategy (time-based, hash-based, etc.)
        """
        self.base_path = base_path
        self.partition_strategy = partition_strategy
        os.makedirs(base_path, exist_ok=True)

    def _get_partition_key(self, chat_id: str, created_at: datetime) -> str:
        """
        Generate partition key based on strategy.

        Args:
            chat_id: Conversation ID
            created_at: Creation timestamp

        Returns:
            Partition key string
        """
        if self.partition_strategy == "time-based":
            return created_at.strftime("%Y/%m")
        elif self.partition_strategy == "hash-based":
            # Use first 2 characters of chat_id for partitioning
            return f"{chat_id[:2]}/{chat_id[2:4]}"
        else:
            # Flat structure
            return ""

    def get_conversation_path(
        self, chat_id: str, partition_key: Optional[str] = None
    ) -> str:
        """
        Get full path to conversation directory.

        Args:
            chat_id: Conversation ID
            partition_key: Optional partition key

        Returns:
            Full path to conversation directory
        """
        if partition_key:
            return os.path.join(self.base_path, partition_key, chat_id)
        else:
            return os.path.join(self.base_path, chat_id)

    def create_conversation_directory(
        self, chat_id: str, created_at: datetime
    ) -> tuple[str, str]:
        """
        Create directory structure for a conversation.

        Args:
            chat_id: Conversation ID
            created_at: Creation timestamp

        Returns:
            Tuple of (conversation_path, partition_key)
        """
        partition_key = self._get_partition_key(chat_id, created_at)
        conv_path = self.get_conversation_path(chat_id, partition_key)

        # Create main conversation directory
        os.makedirs(conv_path, exist_ok=True)

        # Create subdirectories
        os.makedirs(os.path.join(conv_path, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(conv_path, "outputs"), exist_ok=True)
        os.makedirs(os.path.join(conv_path, "intermediate"), exist_ok=True)

        # Create metadata file
        metadata_path = os.path.join(conv_path, "metadata.json")
        if not os.path.exists(metadata_path):
            metadata = {
                "chat_id": chat_id,
                "created_at": created_at.isoformat(),
                "partition_key": partition_key,
            }
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        return conv_path, partition_key

    def save_uploaded_file(
        self, chat_id: str, partition_key: str, file_content: bytes, filename: str
    ) -> str:
        """
        Save an uploaded file to conversation directory.

        Args:
            chat_id: Conversation ID
            partition_key: Partition key
            file_content: File content as bytes
            filename: Original filename

        Returns:
            Path to saved file
        """
        conv_path = self.get_conversation_path(chat_id, partition_key)
        upload_dir = os.path.join(conv_path, "uploads")
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path

    def save_output_file(
        self, chat_id: str, partition_key: str, file_path: str, is_final: bool = False
    ) -> str:
        """
        Save or copy an output file to conversation directory.

        Args:
            chat_id: Conversation ID
            partition_key: Partition key
            file_path: Path to file to copy
            is_final: Whether this is a final output or intermediate

        Returns:
            Path to saved file
        """
        conv_path = self.get_conversation_path(chat_id, partition_key)
        target_dir = (
            os.path.join(conv_path, "outputs")
            if is_final
            else os.path.join(conv_path, "intermediate")
        )

        filename = os.path.basename(file_path)
        target_path = os.path.join(target_dir, filename)

        shutil.copy2(file_path, target_path)
        return target_path

    def get_conversation_files(
        self, chat_id: str, partition_key: str
    ) -> Dict[str, List[str]]:
        """
        Get all files associated with a conversation.

        Args:
            chat_id: Conversation ID
            partition_key: Partition key

        Returns:
            Dictionary with lists of file paths by category
        """
        conv_path = self.get_conversation_path(chat_id, partition_key)

        files = {
            "uploads": [],
            "outputs": [],
            "intermediate": [],
        }

        for category in files.keys():
            dir_path = os.path.join(conv_path, category)
            if os.path.exists(dir_path):
                files[category] = [
                    os.path.join(dir_path, f)
                    for f in os.listdir(dir_path)
                    if os.path.isfile(os.path.join(dir_path, f))
                ]

        return files

    def delete_conversation_directory(
        self, chat_id: str, partition_key: str
    ) -> bool:
        """
        Delete entire conversation directory.

        Args:
            chat_id: Conversation ID
            partition_key: Partition key

        Returns:
            True if deleted successfully
        """
        conv_path = self.get_conversation_path(chat_id, partition_key)
        if os.path.exists(conv_path):
            shutil.rmtree(conv_path)
            return True
        return False

    def dump_conversation(
        self,
        chat_id: str,
        partition_key: str,
        dump_path: str,
        compression: str = "gzip",
    ) -> str:
        """
        Create a compressed dump of conversation data.

        Args:
            chat_id: Conversation ID
            partition_key: Partition key
            dump_path: Base path for dumps
            compression: Compression format (gzip, tar, zip)

        Returns:
            Path to created dump file
        """
        conv_path = self.get_conversation_path(chat_id, partition_key)
        os.makedirs(dump_path, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dump_filename = f"{chat_id}_{timestamp}.tar.gz"
        dump_file_path = os.path.join(dump_path, dump_filename)

        # Create tar.gz archive
        with tarfile.open(dump_file_path, "w:gz") as tar:
            tar.add(conv_path, arcname=chat_id)

        return dump_file_path

    def restore_conversation(
        self, dump_file_path: str, target_chat_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Restore a conversation from a dump file.

        Args:
            dump_file_path: Path to dump file
            target_chat_id: Optional new chat ID (defaults to original)

        Returns:
            Tuple of (chat_id, conversation_path)
        """
        # Extract archive to temporary location
        with tarfile.open(dump_file_path, "r:gz") as tar:
            # Get original chat_id from archive
            members = tar.getmembers()
            if not members:
                raise ValueError("Empty archive")

            original_chat_id = members[0].name.split("/")[0]
            chat_id = target_chat_id or original_chat_id

            # Extract to base path
            tar.extractall(path=self.base_path)

            # If new chat_id specified, rename directory
            if target_chat_id and target_chat_id != original_chat_id:
                old_path = os.path.join(self.base_path, original_chat_id)
                new_path = os.path.join(self.base_path, target_chat_id)
                shutil.move(old_path, new_path)
                conv_path = new_path
            else:
                conv_path = os.path.join(self.base_path, original_chat_id)

        # Read partition key from metadata
        metadata_path = os.path.join(conv_path, "metadata.json")
        partition_key = ""
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                partition_key = metadata.get("partition_key", "")

        return chat_id, partition_key
