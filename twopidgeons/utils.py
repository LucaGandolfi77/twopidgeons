import re
import hashlib
import os

def is_valid_filename(filename: str) -> bool:
    """
    Checks if the filename respects the format: 5 lowercase letters + .2pg
    Example: abcde.2pg
    """
    pattern = r"^[a-z]{5}\.2pg$"
    return bool(re.match(pattern, filename))

def calculate_hash(data: bytes) -> str:
    """Calculates the SHA-256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()
