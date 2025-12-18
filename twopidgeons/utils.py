import re
import hashlib
import os

# Try to import the C extension for better performance
try:
    from .twopidgeons_c import is_valid_filename_c
except ImportError as e:
    # Fallback if compilation failed or not installed
    print(f"Warning: C extension not loaded. Error: {e}")
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

def is_jpeg_file_fast(filename: str) -> bool:
    """
    Fast check for JPEG magic number using C extension if available.
    Returns True if it looks like a JPEG, False otherwise.
    """
    if is_jpeg_file_c:
        return is_jpeg_file_c(filename)
    
    # Fallback: Read python bytes
    try:
        with open(filename, "rb") as f:
            header = f.read(3)
            return header == b'\xFF\xD8\xFF'
    except Exception:
        return False

def calculate_hash(data: bytes) -> str:
    """Calculates the SHA-256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()
