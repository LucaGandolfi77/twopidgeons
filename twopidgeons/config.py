from pydantic import BaseModel, Field
from typing import Optional
import os

class Config(BaseModel):
    """Global configuration for the TwoPidgeons node."""
    
    # Node Identity
    node_id: str = Field(default_factory=lambda: os.getenv("TP_NODE_ID", "default_node"))
    
    # Network
    host: str = Field(default_factory=lambda: os.getenv("TP_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("TP_PORT", "5000")))
    peers: list[str] = Field(default_factory=list)
    
    # Storage
    storage_dir: str = Field(default_factory=lambda: os.getenv("TP_STORAGE_DIR", "node_storage"))
    storage_backend: str = Field(default_factory=lambda: os.getenv("TP_STORAGE_BACKEND", "sqlite")) # 'sqlite', 'memory'
    db_filename: str = Field(default_factory=lambda: os.getenv("TP_DB_FILENAME", "blockchain.db"))
    
    # Cryptography
    key_size: int = Field(default_factory=lambda: int(os.getenv("TP_KEY_SIZE", "2048")))
    public_exponent: int = 65537
    
    # Blockchain
    difficulty: int = Field(default_factory=lambda: int(os.getenv("TP_DIFFICULTY", "4")))

# Global instance (can be overridden)
settings = Config()
