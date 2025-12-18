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
        """Calcola l'hash del blocco basato sul suo contenuto."""
        # Creiamo una copia del dizionario per non modificare l'originale
        block_data = self.__dict__.copy()
        # Rimuoviamo l'hash se presente, per evitare ricorsione/incoerenza
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
        """Crea il blocco genesi (il primo blocco della catena)."""
        genesis_block = Block(0, [], 0.0, "0")
        self.chain.append(genesis_block)
        self.save_chain()

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
        self.save_chain()
        return new_block.index

    def save_chain(self):
        """Salva la catena su file JSON."""
        if not self.chain_file:
            return
            
        chain_data = [block.__dict__ for block in self.chain]
        with open(self.chain_file, 'w') as f:
            json.dump(chain_data, f, indent=4)

    def load_chain(self):
        """Carica la catena da file JSON."""
        if not self.chain_file or not os.path.exists(self.chain_file):
            return

        try:
            with open(self.chain_file, 'r') as f:
                chain_data = json.load(f)
                
            self.chain = []
            for block_data in chain_data:
                # Ricostruiamo l'oggetto Block
                block = Block(
                    index=block_data['index'],
                    transactions=block_data['transactions'],
                    timestamp=block_data['timestamp'],
                    previous_hash=block_data['previous_hash']
                )
                # L'hash viene ricalcolato nel costruttore, ma possiamo verificare se corrisponde
                # Nota: se ricalcoliamo l'hash qui, deve matchare quello salvato.
                # Se il json è stato modificato a mano, questo check fallirà se controlliamo block.hash vs block_data['hash']
                # Ma Block.__init__ chiama compute_hash().
                
                self.chain.append(block)
        except Exception as e:
            print(f"Errore nel caricamento della blockchain: {e}")
            self.chain = []
            self.create_genesis_block()

    @staticmethod
    def is_valid_chain(chain: List[Block]) -> bool:
        """
        Verifica se una data catena è valida.
        """
        if not chain:
            return False
            
        # Verifica il blocco genesi (semplificato, controlliamo solo indice e prev_hash)
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
        """Verifica la validità di un singolo blocco rispetto al precedente."""
        if block.previous_hash != previous_block.hash:
            return False
        if block.index != previous_block.index + 1:
            return False
        if block.hash != block.compute_hash():
            return False
        return True

    def replace_chain(self, new_chain: List[Block]) -> bool:
        """
        Sostituisce la catena corrente con una nuova se è valida e più lunga.
        """
        if len(new_chain) > len(self.chain) and self.is_valid_chain(new_chain):
            self.chain = new_chain
            self.save_chain()
            return True
        return False

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
