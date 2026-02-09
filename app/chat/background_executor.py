"""
Background Workflow Executor

This module provides background task execution for workflows using ThreadPoolExecutor.
It allows workflows to run asynchronously without blocking the API response.
"""

import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class BackgroundWorkflowExecutor:
    """
    Manages background execution of workflows using thread pool.
    
    Provides:
    - Non-blocking workflow execution
    - Job status tracking
    - Thread-safe operation
    - Callback support for completion
    """

    def __init__(self, max_workers: int = 5):
        """
        Initialize background executor.

        Args:
            max_workers: Maximum number of concurrent workflow executions
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="WorkflowExecutor")
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        logger.info(f"BackgroundWorkflowExecutor initialized with {max_workers} workers")

    def submit_workflow(
        self,
        job_id: str,
        workflow_func: Callable,
        *args,
        on_complete: Optional[Callable[[bool, Any, Optional[str]], None]] = None,
        **kwargs
    ) -> str:
        """
        Submit a workflow for background execution.

        Args:
            job_id: Unique job identifier
            workflow_func: Function to execute (should be the workflow execution function)
            *args: Positional arguments for workflow_func
            on_complete: Optional callback when workflow completes (success, result, error)
            **kwargs: Keyword arguments for workflow_func

        Returns:
            Job ID for tracking
        """
        logger.info(f"Submitting workflow job {job_id} for background execution")

        # Register job
        with self.lock:
            self.active_jobs[job_id] = {
                "job_id": job_id,
                "status": "pending",
                "submitted_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error": None,
            }

        # Define wrapper to track execution
        def _execute_with_tracking():
            """Wrapper function to track job execution."""
            try:
                # Mark as running
                with self.lock:
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]["status"] = "running"
                        self.active_jobs[job_id]["started_at"] = datetime.now().isoformat()
                
                logger.info(f"Starting execution of job {job_id}")
                
                # Execute the workflow
                result = workflow_func(*args, **kwargs)
                
                # Mark as completed
                with self.lock:
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]["status"] = "completed"
                        self.active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                        self.active_jobs[job_id]["result"] = result
                
                logger.info(f"Job {job_id} completed successfully")
                
                # Call completion callback if provided
                if on_complete:
                    try:
                        on_complete(True, result, None)
                    except Exception as e:
                        logger.error(f"Error in completion callback for job {job_id}: {e}")
                
                return result

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Job {job_id} failed: {error_msg}")
                
                # Mark as failed
                with self.lock:
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]["status"] = "failed"
                        self.active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                        self.active_jobs[job_id]["error"] = error_msg
                
                # Call completion callback if provided
                if on_complete:
                    try:
                        on_complete(False, None, error_msg)
                    except Exception as cb_error:
                        logger.error(f"Error in completion callback for job {job_id}: {cb_error}")
                
                raise

        # Submit to executor
        future: Future = self.executor.submit(_execute_with_tracking)
        
        # Store future reference
        with self.lock:
            if job_id in self.active_jobs:
                self.active_jobs[job_id]["future"] = future

        logger.info(f"Workflow job {job_id} submitted to thread pool")
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background job.

        Args:
            job_id: Job identifier

        Returns:
            Job status information or None if not found
        """
        with self.lock:
            if job_id not in self.active_jobs:
                return None
            
            # Create a copy without the future object
            job_info = self.active_jobs[job_id].copy()
            job_info.pop("future", None)
            return job_info

    def cancel_job(self, job_id: str) -> bool:
        """
        Attempt to cancel a pending job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was cancelled, False otherwise
        """
        with self.lock:
            if job_id not in self.active_jobs:
                return False
            
            future = self.active_jobs[job_id].get("future")
            if future and future.cancel():
                self.active_jobs[job_id]["status"] = "cancelled"
                self.active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                logger.info(f"Job {job_id} cancelled")
                return True
            
            return False

    def cleanup_completed_jobs(self, max_age_seconds: int = 3600):
        """
        Clean up old completed/failed jobs.

        Args:
            max_age_seconds: Maximum age in seconds for completed jobs to keep
        """
        now = datetime.now()
        with self.lock:
            jobs_to_remove = []
            for job_id, job_info in self.active_jobs.items():
                if job_info["status"] in ["completed", "failed", "cancelled"]:
                    completed_at_str = job_info.get("completed_at")
                    if completed_at_str:
                        completed_at = datetime.fromisoformat(completed_at_str)
                        age = (now - completed_at).total_seconds()
                        if age > max_age_seconds:
                            jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
                logger.info(f"Cleaned up old job {job_id}")
            
            if jobs_to_remove:
                logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

    def get_active_job_count(self) -> int:
        """
        Get the number of currently active (running/pending) jobs.

        Returns:
            Number of active jobs
        """
        with self.lock:
            return sum(1 for job in self.active_jobs.values() 
                      if job["status"] in ["pending", "running"])

    def shutdown(self, wait: bool = True):
        """
        Shutdown the executor.

        Args:
            wait: If True, wait for all jobs to complete
        """
        logger.info("Shutting down BackgroundWorkflowExecutor")
        self.executor.shutdown(wait=wait)

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown(wait=False)
        except:
            pass


# Global instance for the application
_global_executor: Optional[BackgroundWorkflowExecutor] = None


def get_background_executor(max_workers: int = 5) -> BackgroundWorkflowExecutor:
    """
    Get the global background executor instance.

    Args:
        max_workers: Maximum number of workers (only used on first call)

    Returns:
        Background executor instance
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = BackgroundWorkflowExecutor(max_workers=max_workers)
    return _global_executor
