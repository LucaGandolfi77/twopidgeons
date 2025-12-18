import hashlib
import json
from typing import List, Dict

class MerkleTree:
    @staticmethod
    def hash_transaction(transaction: Dict) -> str:
        """Hashes a transaction dictionary."""
        tx_string = json.dumps(transaction, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    @staticmethod
    def compute_root(transactions: List[Dict]) -> str:
        """Computes the Merkle Root for a list of transactions."""
        if not transactions:
            # Return hash of empty string for empty block
            return hashlib.sha256(b"").hexdigest()

        hashes = [MerkleTree.hash_transaction(tx) for tx in transactions]

        while len(hashes) > 1:
            temp_hashes = []
            for i in range(0, len(hashes), 2):
                node1 = hashes[i]
                if i + 1 < len(hashes):
                    node2 = hashes[i + 1]
                else:
                    node2 = node1  # Duplicate last node if odd number

                combined = node1 + node2
                temp_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = temp_hashes

        return hashes[0]
