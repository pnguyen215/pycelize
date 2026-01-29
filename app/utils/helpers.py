"""
Helper Functions

This module provides general helper functions used throughout the application.
"""

import os
import uuid
from datetime import datetime
from typing import Optional


def generate_output_filename(
    original_filename: str, suffix: str = "", extension: Optional[str] = None
) -> str:
    """
    Generate an output filename based on the original filename.

    Args:
        original_filename: Original file name
        suffix: Suffix to add before extension
        extension: New extension (optional, keeps original if not specified)

    Returns:
        Generated output filename
    """
    base_name = os.path.splitext(original_filename)[0]
    original_ext = os.path.splitext(original_filename)[1]

    new_ext = extension if extension else original_ext
    if not new_ext.startswith("."):
        new_ext = f".{new_ext}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if suffix:
        return f"{base_name}_{suffix}_{timestamp}{new_ext}"
    return f"{base_name}_{timestamp}{new_ext}"


def generate_unique_id() -> str:
    """
    Generate a unique identifier.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def sanitize_string(value: str) -> str:
    """
    Sanitize a string for safe use.

    Args:
        value: String to sanitize

    Returns:
        Sanitized string
    """
    # Remove potentially dangerous characters
    return value.replace("\x00", "").strip()
