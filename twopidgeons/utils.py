import re
import hashlib
import os

def is_valid_filename(filename: str) -> bool:
    """
    Verifica se il nome del file rispetta il formato: 5 lettere minuscole + .2pg
    Esempio: abcde.2pg
    """
    pattern = r"^[a-z]{5}\.2pg$"
    return bool(re.match(pattern, filename))

def calculate_hash(data: bytes) -> str:
    """Calcola l'hash SHA-256 dei dati binari."""
    return hashlib.sha256(data).hexdigest()
