"""
Streaming Workflow Executor

This module extends the existing WorkflowExecutor with async/await support
and real-time streaming progress updates via WebSocket.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from app.chat.workflow_executor import WorkflowExecutor, WorkflowStep
from app.chat.models import StepStatus

logger = logging.getLogger(__name__)


class StreamingWorkflowExecutor(WorkflowExecutor):
    """
    Streaming workflow executor with async/await support.

    Extends WorkflowExecutor to provide:
    - Asynchronous step execution
    - Non-blocking background task execution
    - Real-time progress streaming via WebSocket
    - Better error handling and recovery
    """

    def __init__(self, config: Any, max_workers: int = 3):
        """
        Initialize streaming workflow executor.

        Args:
            config: Application configuration
            max_workers: Maximum number of worker threads for parallel execution
        """
        super().__init__(config)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def execute_workflow_async(
        self,
        steps: List[WorkflowStep],
        initial_input_file: Optional[str],
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute workflow asynchronously with real-time progress updates.

        Args:
            steps: List of workflow steps
            initial_input_file: Initial input file path
            progress_callback: Optional callback for progress updates

        Returns:
            List of execution results for each step
        """
        logger.info(f"Starting async workflow execution with {len(steps)} steps")

        results = []
        current_input = initial_input_file

        for i, step in enumerate(steps):
            try:
                logger.info(f"Executing step {i + 1}/{len(steps)}: {step.operation}")

                # Execute step in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    partial(self.execute_step, step, current_input, progress_callback),
                )

                results.append(result)

                # Chain output to next step input
                if result.get("output_file_path"):
                    current_input = result["output_file_path"]
                    logger.info(f"Step {i + 1} completed, output: {current_input}")

                # Small delay to allow progress updates to propagate
                await asyncio.sleep(0.1)

            except Exception as e:
                error_msg = f"Workflow failed at step {i + 1}/{len(steps)}: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)

        logger.info(f"Async workflow execution completed successfully")
        return results

    def execute_workflow_background(
        self,
        steps: List[WorkflowStep],
        initial_input_file: Optional[str],
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None,
    ) -> asyncio.Task:
        """
        Execute workflow in background without blocking.

        Args:
            steps: List of workflow steps
            initial_input_file: Initial input file path
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback when workflow completes

        Returns:
            asyncio.Task for the background execution
        """

        async def _execute():
            """Internal async execution wrapper."""
            try:
                results = await self.execute_workflow_async(
                    steps, initial_input_file, progress_callback
                )

                if completion_callback:
                    completion_callback(True, results, None)

                return results

            except Exception as e:
                logger.error(f"Background workflow execution failed: {e}")

                if completion_callback:
                    completion_callback(False, None, str(e))

                raise

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Schedule task
        task = loop.create_task(_execute())
        logger.info("Workflow scheduled for background execution")

        return task

    async def execute_step_async(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step asynchronously.

        Args:
            step: WorkflowStep to execute
            input_file_path: Path to input file
            progress_callback: Optional callback for progress updates

        Returns:
            Execution result
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, partial(self.execute_step, step, input_file_path, progress_callback)
        )
        return result

    def shutdown(self):
        """Shutdown the executor and cleanup resources."""
        logger.info("Shutting down streaming workflow executor")
        self.executor.shutdown(wait=True)

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except:
            pass
