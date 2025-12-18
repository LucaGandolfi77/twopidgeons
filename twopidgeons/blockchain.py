import time
import json
import hashlib
import os
from typing import List, Dict, Any

class Block:
    def __init__(self, index: int, transactions: List[Dict], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Calculates the block hash based on its content."""
        # Create a copy of the dictionary to avoid modifying the original
        block_data = self.__dict__.copy()
        # Remove the hash if present, to avoid recursion/inconsistency
        if 'hash' in block_data:
            del block_data['hash']
            
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self, chain_file: str = None):
        self.unconfirmed_transactions: List[Dict] = []
        self.chain: List[Block] = []
        self.chain_file = chain_file
        
        if self.chain_file and os.path.exists(self.chain_file):
            self.load_chain()
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        """Creates the genesis block (the first block in the chain)."""
        genesis_block = Block(0, [], 0.0, "0")
        self.chain.append(genesis_block)
        self.save_chain()

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_new_transaction(self, transaction: Dict):
        """Adds a transaction to the list of unconfirmed transactions."""
        self.unconfirmed_transactions.append(transaction)

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

        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        self.save_chain()
        return new_block.index

    def save_chain(self):
        """Saves the chain to a JSON file."""
        if not self.chain_file:
            return
            
        chain_data = [block.__dict__ for block in self.chain]
        with open(self.chain_file, 'w') as f:
            json.dump(chain_data, f, indent=4)

    def load_chain(self):
        """Loads the chain from a JSON file."""
        if not self.chain_file or not os.path.exists(self.chain_file):
            return

        try:
            with open(self.chain_file, 'r') as f:
                chain_data = json.load(f)
                
            self.chain = []
            for block_data in chain_data:
                # Reconstruct the Block object
                block = Block(
                    index=block_data['index'],
                    transactions=block_data['transactions'],
                    timestamp=block_data['timestamp'],
                    previous_hash=block_data['previous_hash']
                )
                # The hash is recalculated in the constructor, but we can verify if it matches
                # Note: if we recalculate the hash here, it must match the saved one.
                
                self.chain.append(block)
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.chain = []
            self.create_genesis_block()

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
        return True

    def replace_chain(self, new_chain: List[Block]) -> bool:
        """
        Replaces the current chain with a new one if it is valid and longer.
        """
        if len(new_chain) > len(self.chain) and self.is_valid_chain(new_chain):
            self.chain = new_chain
            self.save_chain()
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
        """Searches for a transaction based on the image hash."""
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('image_hash') == image_hash:
                    return tx
        return None
