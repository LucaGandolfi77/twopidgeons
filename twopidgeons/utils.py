import re
import hashlib
import os

# Try to import the C extension for better performance
try:
    from .twopidgeons_c import is_valid_filename_c
except ImportError:
    # Fallback if compilation failed or not installed
    is_valid_filename_c = None

def is_valid_filename(filename: str) -> bool:
    """
    Checks if the filename respects the format: 5 lowercase letters + .2pg
    Example: abcde.2pg
    """
    # Use C extension if available (much faster than regex)
    if is_valid_filename_c:
        return is_valid_filename_c(filename)

    # Fallback to Python Regex
    pattern = r"^[a-z]{5}\.2pg$"
    return bool(re.match(pattern, filename))

def calculate_hash(data: bytes) -> str:
    """Calculates the SHA-256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()
