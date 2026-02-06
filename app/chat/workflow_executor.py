"""
Workflow Execution Engine

This module implements the workflow execution engine using Chain of Responsibility
pattern for sequential step execution with input/output chaining.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod

from app.chat.models import WorkflowStep, StepStatus


class WorkflowStepHandler(ABC):
    """
    Abstract base class for workflow step handlers.

    Implements Chain of Responsibility pattern for step execution.
    """

    def __init__(self):
        """Initialize handler."""
        self._next_handler: Optional["WorkflowStepHandler"] = None

    def set_next(self, handler: "WorkflowStepHandler") -> "WorkflowStepHandler":
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
    def can_handle(self, operation: str) -> bool:
        """
        Check if this handler can handle the operation.

        Args:
            operation: Operation name

        Returns:
            True if can handle
        """
        pass

    @abstractmethod
    def execute(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute the workflow step.

        Args:
            step: WorkflowStep to execute
            input_file_path: Path to input file
            config: Application configuration
            progress_callback: Optional callback for progress updates

        Returns:
            Execution result with output_file_path and metadata
        """
        pass

    def handle(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Handle the step execution or pass to next handler.

        Args:
            step: WorkflowStep to execute
            input_file_path: Path to input file
            config: Application configuration
            progress_callback: Optional callback for progress updates

        Returns:
            Execution result
        """
        if self.can_handle(step.operation):
            return self.execute(step, input_file_path, config, progress_callback)
        elif self._next_handler:
            return self._next_handler.handle(
                step, input_file_path, config, progress_callback
            )
        else:
            raise ValueError(f"No handler found for operation: {step.operation}")


class ExcelOperationHandler(WorkflowStepHandler):
    """Handler for Excel operations."""

    OPERATIONS = [
        "excel/extract-columns",
        "excel/extract-columns-to-file",
        "excel/map-columns",
        "excel/bind-single-key",
        "excel/bind-multi-key",
        "excel/search",
    ]

    def can_handle(self, operation: str) -> bool:
        """Check if can handle operation."""
        return operation in self.OPERATIONS

    def execute(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute Excel operation."""
        from app.services.excel_service import ExcelService
        from app.services.binding_service import BindingService
        from app.services.search_service import SearchService

        service = ExcelService(config)
        binding_service = BindingService(config)
        search_service = SearchService(config)

        result = {}
        
        try:
            if step.operation == "excel/extract-columns":
                columns = step.arguments.get("columns", [])
                remove_duplicates = step.arguments.get("remove_duplicates", False)
                result_data = service.extract_columns(
                    input_file_path, columns, remove_duplicates
                )
                result = {"data": result_data, "output_file_path": None}

            elif step.operation == "excel/extract-columns-to-file":
                columns = step.arguments.get("columns", [])
                remove_duplicates = step.arguments.get("remove_duplicates", False)
                output_path = service.extract_columns_to_file(
                    input_file_path, columns, remove_duplicates
                )
                result = {"output_file_path": output_path}

            elif step.operation == "excel/map-columns":
                mapping = step.arguments.get("mapping", {})
                output_path = service.map_columns(input_file_path, mapping)
                result = {"output_file_path": output_path}

            elif step.operation == "excel/bind-single-key":
                bind_file = step.arguments.get("bind_file")
                comparison_column = step.arguments.get("comparison_column")
                bind_columns = step.arguments.get("bind_columns", [])
                output_path = binding_service.bind_single_key(
                    input_file_path, bind_file, comparison_column, bind_columns
                )
                result = {"output_file_path": output_path}

            elif step.operation == "excel/bind-multi-key":
                bind_file = step.arguments.get("bind_file")
                comparison_columns = step.arguments.get("comparison_columns", [])
                bind_columns = step.arguments.get("bind_columns", [])
                output_path = binding_service.bind_multi_key(
                    input_file_path, bind_file, comparison_columns, bind_columns
                )
                result = {"output_file_path": output_path}

            elif step.operation == "excel/search":
                conditions = step.arguments.get("conditions", [])
                logic = step.arguments.get("logic", "AND")
                output_format = step.arguments.get("output_format", "excel")
                search_result = search_service.search_excel(
                    input_file_path, conditions, logic, output_format
                )
                result = {
                    "output_file_path": search_result.get("file_path"),
                    "statistics": search_result.get("statistics"),
                }

        except Exception as e:
            raise Exception(f"Excel operation failed: {str(e)}")

        return result


class CSVOperationHandler(WorkflowStepHandler):
    """Handler for CSV operations."""

    OPERATIONS = ["csv/convert-to-excel", "csv/search"]

    def can_handle(self, operation: str) -> bool:
        """Check if can handle operation."""
        return operation in self.OPERATIONS

    def execute(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute CSV operation."""
        from app.services.csv_service import CSVService
        from app.services.search_service import SearchService

        csv_service = CSVService(config)
        search_service = SearchService(config)

        result = {}

        try:
            if step.operation == "csv/convert-to-excel":
                sheet_name = step.arguments.get("sheet_name", "Sheet1")
                output_path = csv_service.convert_to_excel(
                    input_file_path, sheet_name
                )
                result = {"output_file_path": output_path}

            elif step.operation == "csv/search":
                conditions = step.arguments.get("conditions", [])
                logic = step.arguments.get("logic", "AND")
                output_format = step.arguments.get("output_format", "csv")
                search_result = search_service.search_csv(
                    input_file_path, conditions, logic, output_format
                )
                result = {
                    "output_file_path": search_result.get("file_path"),
                    "statistics": search_result.get("statistics"),
                }

        except Exception as e:
            raise Exception(f"CSV operation failed: {str(e)}")

        return result


class NormalizationOperationHandler(WorkflowStepHandler):
    """Handler for normalization operations."""

    OPERATIONS = ["normalization/apply"]

    def can_handle(self, operation: str) -> bool:
        """Check if can handle operation."""
        return operation in self.OPERATIONS

    def execute(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute normalization operation."""
        from app.services.normalization_service import NormalizationService

        service = NormalizationService(config)

        try:
            normalizations = step.arguments.get("normalizations", [])
            return_report = step.arguments.get("return_report", True)

            result_data = service.apply_normalizations(
                input_file_path, normalizations, return_report
            )

            return {
                "output_file_path": result_data.get("file_path"),
                "report": result_data.get("report"),
            }

        except Exception as e:
            raise Exception(f"Normalization operation failed: {str(e)}")


class SQLGenerationHandler(WorkflowStepHandler):
    """Handler for SQL generation operations."""

    OPERATIONS = [
        "sql/generate",
        "sql/generate-to-text",
        "sql/generate-custom-to-text",
    ]

    def can_handle(self, operation: str) -> bool:
        """Check if can handle operation."""
        return operation in self.OPERATIONS

    def execute(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute SQL generation operation."""
        from app.services.sql_generation_service import SQLGenerationService

        service = SQLGenerationService(config)

        try:
            if step.operation == "sql/generate":
                table_name = step.arguments.get("table_name", "data")
                column_mapping = step.arguments.get("column_mapping", {})
                database_type = step.arguments.get("database_type", "postgresql")
                auto_increment = step.arguments.get("auto_increment", {})

                output_path = service.generate_sql(
                    input_file_path,
                    table_name,
                    column_mapping,
                    database_type,
                    auto_increment,
                )
                return {"output_file_path": output_path}

            elif step.operation == "sql/generate-to-text":
                table_name = step.arguments.get("table_name", "data")
                columns = step.arguments.get("columns", [])
                column_mapping = step.arguments.get("column_mapping", {})
                remove_duplicates = step.arguments.get("remove_duplicates", False)

                output_path = service.generate_sql_to_text(
                    input_file_path, table_name, columns, column_mapping, remove_duplicates
                )
                return {"output_file_path": output_path}

            elif step.operation == "sql/generate-custom-to-text":
                columns = step.arguments.get("columns", [])
                template = step.arguments.get("template", "")
                column_mapping = step.arguments.get("column_mapping", {})
                auto_increment = step.arguments.get("auto_increment", {})

                output_path = service.generate_custom_sql_to_text(
                    input_file_path, columns, template, column_mapping, auto_increment
                )
                return {"output_file_path": output_path}

        except Exception as e:
            raise Exception(f"SQL generation operation failed: {str(e)}")


class JSONGenerationHandler(WorkflowStepHandler):
    """Handler for JSON generation operations."""

    OPERATIONS = ["json/generate", "json/generate-with-template"]

    def can_handle(self, operation: str) -> bool:
        """Check if can handle operation."""
        return operation in self.OPERATIONS

    def execute(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        config: Any,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute JSON generation operation."""
        from app.services.json_generation_service import JSONGenerationService

        service = JSONGenerationService(config)

        try:
            if step.operation == "json/generate":
                columns = step.arguments.get("columns", [])
                column_mapping = step.arguments.get("column_mapping", {})
                pretty_print = step.arguments.get("pretty_print", True)
                null_handling = step.arguments.get("null_handling", "include")
                array_wrapper = step.arguments.get("array_wrapper", True)

                output_path = service.generate_json(
                    input_file_path,
                    columns,
                    column_mapping,
                    pretty_print,
                    null_handling,
                    array_wrapper,
                )
                return {"output_file_path": output_path}

            elif step.operation == "json/generate-with-template":
                template = step.arguments.get("template", {})
                column_mapping = step.arguments.get("column_mapping", {})
                aggregation_mode = step.arguments.get("aggregation_mode", "array")

                output_path = service.generate_json_with_template(
                    input_file_path, template, column_mapping, aggregation_mode
                )
                return {"output_file_path": output_path}

        except Exception as e:
            raise Exception(f"JSON generation operation failed: {str(e)}")


class WorkflowExecutor:
    """
    Workflow execution engine.

    Manages sequential execution of workflow steps with input/output chaining.
    """

    def __init__(self, config: Any):
        """
        Initialize workflow executor.

        Args:
            config: Application configuration
        """
        self.config = config
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup handler chain."""
        # Create handlers
        excel_handler = ExcelOperationHandler()
        csv_handler = CSVOperationHandler()
        normalization_handler = NormalizationOperationHandler()
        sql_handler = SQLGenerationHandler()
        json_handler = JSONGenerationHandler()

        # Chain handlers
        excel_handler.set_next(csv_handler).set_next(normalization_handler).set_next(
            sql_handler
        ).set_next(json_handler)

        self.handler_chain = excel_handler

    def execute_step(
        self,
        step: WorkflowStep,
        input_file_path: Optional[str],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: WorkflowStep to execute
            input_file_path: Path to input file
            progress_callback: Optional callback for progress updates

        Returns:
            Execution result
        """
        # Update step status
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()

        try:
            # Report progress start
            if progress_callback:
                progress_callback(step, 0, "Starting step execution")

            # Execute step
            result = self.handler_chain.handle(
                step, input_file_path, self.config, progress_callback
            )

            # Update step with result
            step.output_file = result.get("output_file_path")
            step.status = StepStatus.COMPLETED
            step.progress = 100
            step.completed_at = datetime.utcnow()

            # Report progress complete
            if progress_callback:
                progress_callback(step, 100, "Step completed successfully")

            return result

        except Exception as e:
            # Update step with error
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.completed_at = datetime.utcnow()

            # Report progress error
            if progress_callback:
                progress_callback(step, step.progress, f"Step failed: {str(e)}")

            raise

    def execute_workflow(
        self,
        steps: List[WorkflowStep],
        initial_input_file: Optional[str],
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a complete workflow with sequential steps.

        Args:
            steps: List of workflow steps
            initial_input_file: Initial input file path
            progress_callback: Optional callback for progress updates

        Returns:
            List of execution results for each step
        """
        results = []
        current_input = initial_input_file

        for i, step in enumerate(steps):
            try:
                # Execute step
                result = self.execute_step(step, current_input, progress_callback)

                results.append(result)

                # Chain output to next step input
                if result.get("output_file_path"):
                    current_input = result["output_file_path"]

            except Exception as e:
                # Stop workflow on error
                raise Exception(
                    f"Workflow failed at step {i + 1}/{len(steps)}: {str(e)}"
                )

        return results
