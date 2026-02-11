"""
Integration test to verify step_id is stored in database and retrieved correctly
"""

import pytest
import os
import tempfile
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.models import MessageType


class TestStepIdDatabaseStorage:
    """Test step_id is properly stored in database."""
    
    def test_step_id_stored_and_retrieved_from_database(self):
        """Test that step_id is stored in files table and retrieved correctly."""
        
        # Create temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_chat.db")
            workflows_path = os.path.join(tmpdir, "workflows")
            
            # Initialize components
            database = ChatDatabase(db_path)
            storage = ConversationStorage(workflows_path, "time-based")
            repository = ConversationRepository(database, storage)
            
            # Create a conversation
            chat_id = "test-step-id-storage"
            conversation = repository.create_conversation(chat_id)
            
            # Add a workflow step
            step_id = "step-abc-123"
            database.save_workflow_step(
                chat_id=chat_id,
                step_id=step_id,
                operation="excel/extract-columns",
                arguments={"columns": ["name", "email"]},
                status="completed",
                input_file=None,
                output_file="./output/test_file.xlsx",
                progress=100,
                error_message=None,
                started_at="2026-02-11T10:00:00",
                completed_at="2026-02-11T10:01:00"
            )
            
            # Save an output file with step_id
            file_path = "./output/test_file.xlsx"
            database.save_file(chat_id, file_path, "output", step_id)
            
            # Retrieve files from database
            files = database.get_files(chat_id)
            
            # Verify output files structure
            assert "output" in files
            assert len(files["output"]) == 1
            
            output_file = files["output"][0]
            assert isinstance(output_file, dict), "Output file should be a dictionary"
            assert "file_path" in output_file
            assert "step_id" in output_file
            assert output_file["file_path"] == file_path
            assert output_file["step_id"] == step_id
            
            print(f"✓ step_id stored and retrieved correctly: {output_file}")
    
    def test_output_file_without_step_id(self):
        """Test that output files can be stored without step_id (backward compatibility)."""
        
        # Create temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_chat.db")
            workflows_path = os.path.join(tmpdir, "workflows")
            
            # Initialize components
            database = ChatDatabase(db_path)
            storage = ConversationStorage(workflows_path, "time-based")
            repository = ConversationRepository(database, storage)
            
            # Create a conversation
            chat_id = "test-no-step-id"
            conversation = repository.create_conversation(chat_id)
            
            # Save an output file without step_id
            file_path = "./output/orphan_file.xlsx"
            database.save_file(chat_id, file_path, "output", step_id=None)
            
            # Retrieve files from database
            files = database.get_files(chat_id)
            
            # Verify output files structure
            assert "output" in files
            assert len(files["output"]) == 1
            
            output_file = files["output"][0]
            assert isinstance(output_file, dict), "Output file should be a dictionary"
            assert "file_path" in output_file
            assert output_file["file_path"] == file_path
            # step_id should not be present for files without it
            assert "step_id" not in output_file
            
            print(f"✓ File without step_id handled correctly: {output_file}")
    
    def test_multiple_output_files_with_different_steps(self):
        """Test multiple output files with different step_ids."""
        
        # Create temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_chat.db")
            workflows_path = os.path.join(tmpdir, "workflows")
            
            # Initialize components
            database = ChatDatabase(db_path)
            storage = ConversationStorage(workflows_path, "time-based")
            repository = ConversationRepository(database, storage)
            
            # Create a conversation
            chat_id = "test-multiple-steps"
            conversation = repository.create_conversation(chat_id)
            
            # Add multiple workflow steps and files
            step_file_pairs = [
                ("step-001", "./output/file1.xlsx"),
                ("step-002", "./output/file2.xlsx"),
                ("step-003", "./output/file3.xlsx"),
            ]
            
            for step_id, file_path in step_file_pairs:
                # Add workflow step
                database.save_workflow_step(
                    chat_id=chat_id,
                    step_id=step_id,
                    operation="excel/extract-columns",
                    arguments={"columns": ["data"]},
                    status="completed",
                    input_file=None,
                    output_file=file_path,
                    progress=100,
                    error_message=None,
                    started_at="2026-02-11T10:00:00",
                    completed_at="2026-02-11T10:01:00"
                )
                
                # Save output file with step_id
                database.save_file(chat_id, file_path, "output", step_id)
            
            # Retrieve files from database
            files = database.get_files(chat_id)
            
            # Verify all output files have correct step_ids
            assert len(files["output"]) == 3
            
            for i, output_file in enumerate(files["output"]):
                expected_step_id, expected_path = step_file_pairs[i]
                assert output_file["file_path"] == expected_path
                assert output_file["step_id"] == expected_step_id
                print(f"✓ File {i+1}: {output_file['file_path']} → step_id: {output_file['step_id']}")
    
    def test_database_migration_adds_step_id_column(self):
        """Test that database migration adds step_id column to existing databases."""
        
        # Create temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_migration.db")
            
            # Initialize database (migration should run automatically)
            database = ChatDatabase(db_path)
            
            # Verify step_id column exists in files table
            conn = database._get_connection()
            try:
                cursor = conn.execute("PRAGMA table_info(files)")
                columns = [row[1] for row in cursor.fetchall()]
                
                assert "step_id" in columns, "step_id column should exist in files table"
                print(f"✓ Database migration successful. Columns: {columns}")
            finally:
                conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
