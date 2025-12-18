import time
import json
import hashlib
import os
from typing import List, Dict, Any, Union
from .crypto_utils import verify_signature, deserialize_public_key
from .merkle_tree import MerkleTree
from .storage import StorageBackend, SQLiteBackend

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

    def __init__(self, storage: Union[StorageBackend, str] = "blockchain.db"):
        self.unconfirmed_transactions: List[Dict] = []
        self.chain: List[Block] = []
        
        # Initialize storage backend
        if isinstance(storage, str):
            # Backward compatibility: if string, assume SQLite path
            self.storage = SQLiteBackend(storage)
        elif isinstance(storage, StorageBackend):
            self.storage = storage
        else:
            raise ValueError("Invalid storage backend")
        
        self.load_chain()
        
        if not self.chain:
            self.create_genesis_block()

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
        """Saves a single block to the storage backend."""
        block_data = {
            'index': block.index,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'nonce': block.nonce,
            'merkle_root': block.merkle_root
        }
        self.storage.save_block(block_data, block.transactions)

    def load_chain(self):
        """Loads the chain from the storage backend."""
        chain_data = self.storage.load_chain()
        self.chain = []
        for b_data in chain_data:
            block = Block(
                index=b_data['index'],
                transactions=b_data['transactions'],
                timestamp=b_data['timestamp'],
                previous_hash=b_data['previous_hash'],
                nonce=b_data['nonce'],
                merkle_root=b_data['merkle_root']
            )
            # Ensure hash matches loaded hash
            block.hash = b_data['hash']
            self.chain.append(block)
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
            
            # Wipe storage and save new chain
            self.storage.clear_chain()
            
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
        return self.storage.find_transaction_by_hash(image_hash)
