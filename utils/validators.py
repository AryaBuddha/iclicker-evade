"""Validation utility functions for iClicker Evade.

This module provides validation functions for user input,
configuration values, and data integrity checks.
"""

import re
from typing import Optional


def validate_email_address(email: str) -> bool:
    """Validate an email address format.

    Uses a regex pattern to check if the provided string
    matches a valid email address format.

    Args:
        email: Email address string to validate

    Returns:
        True if email format is valid, False otherwise

    Example:
        >>> validate_email_address("user@example.com")
        True
        >>> validate_email_address("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_polling_interval(interval: int) -> bool:
    """Validate a polling interval value.

    Checks if the polling interval is within reasonable bounds
    for iClicker monitoring (1-300 seconds).

    Args:
        interval: Polling interval in seconds

    Returns:
        True if interval is valid, False otherwise
    """
    return isinstance(interval, int) and 1 <= interval <= 300


def validate_class_name(class_name: Optional[str]) -> bool:
    """Validate a class name string.

    Checks if the class name is a reasonable length and
    contains valid characters.

    Args:
        class_name: Class name to validate (can be None)

    Returns:
        True if class name is valid or None, False otherwise
    """
    if class_name is None:
        return True

    if not isinstance(class_name, str):
        return False

    # Class name should be 1-100 characters
    if not (1 <= len(class_name.strip()) <= 100):
        return False

    # Should contain mostly alphanumeric and common punctuation
    pattern = r'^[a-zA-Z0-9\s\-_.,()]+$'
    return bool(re.match(pattern, class_name.strip()))


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.

    Removes or replaces characters that are not allowed in filenames
    on most operating systems.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for use on most filesystems
    """
    if not filename:
        return "unnamed_file"

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Ensure filename is not empty after sanitization
    if not sanitized:
        return "unnamed_file"

    # Limit length to 255 characters (common filesystem limit)
    return sanitized[:255]