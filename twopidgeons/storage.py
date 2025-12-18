from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import sqlite3
import json

class StorageBackend(ABC):
    """Abstract base class for blockchain storage backends."""

    @abstractmethod
    def initialize(self):
        """Initialize the storage (create tables, etc.)."""
        pass

    @abstractmethod
    def save_block(self, block_data: Dict[str, Any], transactions: List[Dict[str, Any]]):
        """Save a block and its transactions."""
        pass

    @abstractmethod
    def load_chain(self) -> List[Dict[str, Any]]:
        """Load the entire chain from storage."""
        pass

    @abstractmethod
    def clear_chain(self):
        """Delete all blocks and transactions (used for chain replacement)."""
        pass

    @abstractmethod
    def find_transaction_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Find a transaction by image hash."""
        pass


class SQLiteBackend(StorageBackend):
    """Storage backend using SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.initialize()

    def initialize(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                idx INTEGER PRIMARY KEY,
                timestamp REAL,
                previous_hash TEXT,
                hash TEXT,
                nonce INTEGER,
                merkle_root TEXT
            )
        """)
        
        # Check if merkle_root column exists (migration for existing DBs)
        cursor.execute("PRAGMA table_info(blocks)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'merkle_root' not in columns:
            cursor.execute("ALTER TABLE blocks ADD COLUMN merkle_root TEXT")
            
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_idx INTEGER,
                image_hash TEXT,
                source_hash TEXT,
                data TEXT,
                FOREIGN KEY(block_idx) REFERENCES blocks(idx)
            )
        """)
        self.conn.commit()

    def save_block(self, block_data: Dict[str, Any], transactions: List[Dict[str, Any]]):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO blocks (idx, timestamp, previous_hash, hash, nonce, merkle_root) VALUES (?, ?, ?, ?, ?, ?)",
                       (block_data['index'], block_data['timestamp'], block_data['previous_hash'], 
                        block_data['hash'], block_data['nonce'], block_data['merkle_root']))
        
        for tx in transactions:
            tx_json = json.dumps(tx)
            img_hash = tx.get('image_hash')
            src_hash = tx.get('source_hash')
            cursor.execute("INSERT INTO transactions (block_idx, image_hash, source_hash, data) VALUES (?, ?, ?, ?)",
                           (block_data['index'], img_hash, src_hash, tx_json))
        self.conn.commit()

    def load_chain(self) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT idx, timestamp, previous_hash, hash, nonce, merkle_root FROM blocks ORDER BY idx ASC")
            rows = cursor.fetchall()
            chain_data = []
            for row in rows:
                idx, timestamp, previous_hash, block_hash, nonce, merkle_root = row
                
                cursor.execute("SELECT data FROM transactions WHERE block_idx = ?", (idx,))
                tx_rows = cursor.fetchall()
                transactions = [json.loads(r[0]) for r in tx_rows]
                
                block_data = {
                    'index': idx,
                    'timestamp': timestamp,
                    'previous_hash': previous_hash,
                    'hash': block_hash,
                    'nonce': nonce,
                    'merkle_root': merkle_root,
                    'transactions': transactions
                }
                chain_data.append(block_data)
            return chain_data
        except Exception as e:
            print(f"Error loading blockchain from SQLite: {e}")
            return []

    def clear_chain(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM blocks")
        self.conn.commit()

    def find_transaction_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM transactions WHERE image_hash = ?", (image_hash,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None


class InMemoryBackend(StorageBackend):
    """Storage backend using memory (for testing)."""

    def __init__(self):
        self.blocks = []
        self.transactions_map = {} # Map image_hash -> transaction

    def initialize(self):
        pass

    def save_block(self, block_data: Dict[str, Any], transactions: List[Dict[str, Any]]):
        # Store block
        # We store a copy to simulate persistence
        block_copy = block_data.copy()
        block_copy['transactions'] = transactions
        self.blocks.append(block_copy)
        
        # Index transactions
        for tx in transactions:
            if 'image_hash' in tx:
                self.transactions_map[tx['image_hash']] = tx

    def load_chain(self) -> List[Dict[str, Any]]:
        return self.blocks

    def clear_chain(self):
        self.blocks = []
        self.transactions_map = {}

    def find_transaction_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        return self.transactions_map.get(image_hash)
