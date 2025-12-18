import time
import json
import hashlib
import os
import sqlite3
from typing import List, Dict, Any
from .crypto_utils import verify_signature, deserialize_public_key
from .merkle_tree import MerkleTree

class Block:
    def __init__(self, index: int, transactions: List[Dict], timestamp: float, previous_hash: str, nonce: int = 0, merkle_root: str = None):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        
        if merkle_root:
            self.merkle_root = merkle_root
        else:
            self.merkle_root = MerkleTree.compute_root(self.transactions)
            
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Calculates the block hash based on header (including Merkle Root)."""
        block_header = {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root
        }
        block_string = json.dumps(block_header, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 4

    def __init__(self, db_file: str = "blockchain.db"):
        self.unconfirmed_transactions: List[Dict] = []
        self.chain: List[Block] = []
        self.db_file = db_file
        
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.create_tables()
        
        self.load_chain()
        
        if not self.chain:
            self.create_genesis_block()

    def create_tables(self):
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
            print("Migrating database: adding merkle_root column...")
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

    def create_genesis_block(self):
        """Creates the genesis block (the first block in the chain)."""
        genesis_block = Block(0, [], 0.0, "0")
        # Genesis block also needs to satisfy PoW or be exempt. 
        # Usually genesis is hardcoded, but here we can just mine it to be consistent.
        self.proof_of_work(genesis_block)
        self.chain.append(genesis_block)
        self.save_block(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_new_transaction(self, transaction: Dict) -> bool:
        """Adds a transaction to the list of unconfirmed transactions."""
        # Verify signature if present
        if 'signature' in transaction and 'public_key' in transaction:
            signature = transaction['signature']
            public_key_pem = transaction['public_key']
            
            # Reconstruct signed data
            tx_copy = transaction.copy()
            del tx_copy['signature']
            
            tx_bytes = json.dumps(tx_copy, sort_keys=True).encode()
            
            try:
                public_key = deserialize_public_key(public_key_pem)
                if not verify_signature(public_key, tx_bytes, signature):
                    print("Invalid transaction signature!")
                    return False
            except Exception as e:
                print(f"Error verifying signature: {e}")
                return False

        self.unconfirmed_transactions.append(transaction)
        return True

    def proof_of_work(self, block: Block) -> str:
        """
        Proof of Work algorithm.
        Increments the nonce until the hash starts with 'difficulty' zeros.
        """
        # Try to use C extension for performance
        try:
            from . import pow_module
            
            # Construct the block header dict with a placeholder nonce
            block_header = {
                'index': block.index,
                'timestamp': block.timestamp,
                'previous_hash': block.previous_hash,
                'nonce': 0, 
                'merkle_root': block.merkle_root
            }
            
            # Serialize to JSON to get the exact format
            full_str = json.dumps(block_header, sort_keys=True)
            
            # We look for the pattern '"nonce": 0'
            split_pattern = '"nonce": 0'
            
            if split_pattern in full_str:
                parts = full_str.split(split_pattern)
                if len(parts) == 2:
                    # Reconstruct parts for C module
                    # Part 1 ends with '"nonce": '
                    part1 = parts[0] + '"nonce": '
                    part2 = parts[1]
                    
                    # Call C module
                    nonce, hash_val = pow_module.find_proof(part1, part2, Blockchain.difficulty)
                    
                    if nonce is not None:
                        block.nonce = nonce
                        block.hash = hash_val
                        return hash_val
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: C extension failed ({e}), falling back to Python.")

        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        block.hash = computed_hash
        return computed_hash

    def mine(self) -> int:
        """
        Packages pending transactions into a new block and adds it to the chain.
        Returns the index of the new block.
        """
        if not self.unconfirmed_transactions:
            return -1

        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        self.proof_of_work(new_block)
        
        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        self.save_block(new_block)
        return new_block.index

    def save_block(self, block: Block):
        """Saves a single block to the database."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO blocks (idx, timestamp, previous_hash, hash, nonce, merkle_root) VALUES (?, ?, ?, ?, ?, ?)",
                       (block.index, block.timestamp, block.previous_hash, block.hash, block.nonce, block.merkle_root))
        
        for tx in block.transactions:
            # We store the full JSON for reconstruction, and hashes for indexing
            tx_json = json.dumps(tx)
            img_hash = tx.get('image_hash')
            src_hash = tx.get('source_hash')
            cursor.execute("INSERT INTO transactions (block_idx, image_hash, source_hash, data) VALUES (?, ?, ?, ?)",
                           (block.index, img_hash, src_hash, tx_json))
        self.conn.commit()

    def load_chain(self):
        """Loads the chain from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT idx, timestamp, previous_hash, hash, nonce, merkle_root FROM blocks ORDER BY idx ASC")
            rows = cursor.fetchall()
            self.chain = []
            for row in rows:
                idx, timestamp, previous_hash, block_hash, nonce, merkle_root = row
                # Load transactions
                cursor.execute("SELECT data FROM transactions WHERE block_idx = ?", (idx,))
                tx_rows = cursor.fetchall()
                transactions = [json.loads(r[0]) for r in tx_rows]
                
                block = Block(idx, transactions, timestamp, previous_hash, nonce, merkle_root)
                # Verify hash consistency? Maybe skip for speed or check.
                # block.hash should match block_hash
                self.chain.append(block)
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.chain = []
            # Genesis block will be created in __init__ if chain is empty

    @staticmethod
    def is_valid_chain(chain: List[Block]) -> bool:
        """
        Verifies if a given chain is valid.
        """
        if not chain:
            return False
            
        # Verify genesis block (simplified, checking only index and prev_hash)
        first_block = chain[0]
        if first_block.index != 0 or first_block.previous_hash != "0":
            return False

        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            
            if not Blockchain.is_valid_block(current, previous):
                return False
                
        return True

    @staticmethod
    def is_valid_block(block: Block, previous_block: Block) -> bool:
        """Verifies the validity of a single block against the previous one."""
        if block.previous_hash != previous_block.hash:
            return False
        if block.index != previous_block.index + 1:
            return False
        if block.hash != block.compute_hash():
            return False
        # Check Proof of Work
        if not block.hash.startswith('0' * Blockchain.difficulty):
            return False
        return True

    def replace_chain(self, new_chain: List[Block]) -> bool:
        """
        Replaces the current chain with a new one if it is valid and longer.
        """
        if len(new_chain) > len(self.chain) and self.is_valid_chain(new_chain):
            self.chain = new_chain
            
            # Wipe DB and save new chain
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM blocks")
            self.conn.commit()
            
            for block in new_chain:
                self.save_block(block)
            return True
        return False

    def is_chain_valid(self) -> bool:
        """Verifies the integrity of the blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def find_transaction(self, image_hash: str) -> Dict:
        """Searches for a transaction based on the image hash or source hash."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM transactions WHERE image_hash = ? OR source_hash = ?", (image_hash, image_hash))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
