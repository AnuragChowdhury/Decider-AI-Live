"""
Input validation utilities for file uploads and requests.
"""

from pathlib import Path
from typing import Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_file_upload(
    filename: str,
    file_size: int,
    allowed_extensions: list,
    max_bytes: int
) -> Tuple[bool, str]:
    """
    Validate uploaded file.
    
    Args:
        filename: Name of uploaded file
        file_size: Size of file in bytes
        allowed_extensions: List of allowed file extensions (e.g., ['.csv', '.xlsx'])
        max_bytes: Maximum allowed file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        ValidationError: If validation fails
    """
    # Check file size
    if file_size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise ValidationError(
            f"File size ({actual_mb:.2f} MB) exceeds maximum allowed size ({max_mb:.2f} MB)"
        )
    
    if file_size == 0:
        raise ValidationError("File is empty")
    
    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise ValidationError(
            f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )
    
    return True, ""


def validate_validation_mode(mode: str) -> str:
    """
    Validate and normalize validation mode.
    
    Args:
        mode: Validation mode string
        
    Returns:
        Normalized mode ('strict' or 'lenient')
        
    Raises:
        ValidationError: If mode is invalid
    """
    if mode is None:
        return "lenient"
    
    mode = mode.lower().strip()
    if mode not in ["strict", "lenient"]:
        raise ValidationError(
            f"Invalid validation mode '{mode}'. Must be 'strict' or 'lenient'"
        )
    
    return mode


def sanitize_column_name(name: str) -> str:
    """
    Sanitize column name to snake_case.
    
    Args:
        name: Original column name
        
    Returns:
        Sanitized column name
    """
    import re
    
    # Strip whitespace
    name = name.strip()
    
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces and special characters with underscores
    name = re.sub(r'[^\w\s]', '_', name)
    name = re.sub(r'\s+', '_', name)
    
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # Ensure name is not empty
    if not name:
        name = "unnamed_column"
    
    # Ensure name doesn't start with a number
    if name[0].isdigit():
        name = f"col_{name}"
    
    return name
