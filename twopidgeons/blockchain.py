import time
import json
import hashlib
from typing import List, Dict, Any

class Block:
    def __init__(self, index: int, transactions: List[Dict], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Calcola l'hash del blocco basato sul suo contenuto."""
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions: List[Dict] = []
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Crea il blocco genesi (il primo blocco della catena)."""
        genesis_block = Block(0, [], 0.0, "0")
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_new_transaction(self, transaction: Dict):
        """Aggiunge una transazione alla lista delle non confermate."""
        self.unconfirmed_transactions.append(transaction)

    def mine(self) -> int:
        """
        Impacchetta le transazioni pendenti in un nuovo blocco e lo aggiunge alla catena.
        Ritorna l'indice del nuovo blocco.
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
        return new_block.index

    def is_chain_valid(self) -> bool:
        """Verifica l'integrità della blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def find_transaction(self, image_hash: str) -> Dict:
        """Cerca una transazione basata sull'hash dell'immagine."""
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('image_hash') == image_hash:
                    return tx
        return None
