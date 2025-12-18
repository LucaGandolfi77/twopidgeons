import os
import shutil
import requests
from urllib.parse import urlparse
from PIL import Image
from .blockchain import Blockchain, Block
from .utils import is_valid_filename, calculate_hash

class Node:
    def __init__(self, node_id: str, storage_dir: str):
        self.node_id = node_id
        self.storage_dir = storage_dir
        self.nodes = set() # Insieme dei nodi peer (es. 'http://192.168.0.5:5000')
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            
        # La blockchain viene salvata nella stessa directory del nodo
        chain_path = os.path.join(self.storage_dir, "blockchain.json")
        self.blockchain = Blockchain(chain_file=chain_path)

    def register_node(self, address: str):
        """Aggiunge un nuovo nodo alla lista dei peer."""
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.scheme + "://" + parsed_url.netloc)
        elif parsed_url.path:
            # Accetta anche indirizzi senza scheme (es. 'localhost:5000')
            self.nodes.add("http://" + parsed_url.path)

    def broadcast_block(self, block: Block):
        """Invia un nuovo blocco a tutti i nodi conosciuti."""
        print(f"Broadcasting block #{block.index} to peers...")
        block_data = block.__dict__
        for node in self.nodes:
            try:
                requests.post(f"{node}/block/receive", json=block_data, timeout=2)
            except requests.RequestException:
                print(f"Impossibile contattare il nodo {node}")

    def receive_block(self, block_data: dict) -> bool:
        """
        Gestisce la ricezione di un blocco da un altro nodo.
        Ritorna True se il blocco è stato accettato.
        """
        # Ricostruiamo l'oggetto Block
        new_block = Block(
            index=block_data['index'],
            transactions=block_data['transactions'],
            timestamp=block_data['timestamp'],
            previous_hash=block_data['previous_hash']
        )
        
        last_block = self.blockchain.last_block
        
        # Caso 1: Il blocco è il successivo esatto della nostra catena
        if new_block.index == last_block.index + 1:
            if Blockchain.is_valid_block(new_block, last_block):
                self.blockchain.chain.append(new_block)
                self.blockchain.save_chain()
                print(f"Blocco #{new_block.index} ricevuto e aggiunto alla catena.")
                return True
        
        # Caso 2: Il blocco è molto più avanti (siamo desincronizzati)
        elif new_block.index > last_block.index + 1:
            print("Ricevuto blocco futuro. La nostra catena è obsoleta. Risoluzione conflitti...")
            self.resolve_conflicts()
            
        return False

    def resolve_conflicts(self) -> bool:
        """
        Algoritmo di Consenso: risolve i conflitti sostituendo la catena
        con la più lunga valida nella rete.
        Ritorna True se la catena è stata sostituita, False altrimenti.
        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.blockchain.chain)

        for node in neighbours:
            try:
                response = requests.get(f'{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain_data = response.json()['chain']

                    # Se troviamo una catena più lunga, verifichiamo la validità
                    if length > max_length:
                        # Ricostruiamo la catena di oggetti Block
                        temp_chain = []
                        for b_data in chain_data:
                            block = Block(
                                index=b_data['index'],
                                transactions=b_data['transactions'],
                                timestamp=b_data['timestamp'],
                                previous_hash=b_data['previous_hash']
                            )
                            temp_chain.append(block)
                        
                        if Blockchain.is_valid_chain(temp_chain):
                            max_length = length
                            new_chain = temp_chain
            except requests.RequestException:
                continue

        if new_chain:
            self.blockchain.replace_chain(new_chain)
            return True

        return False

    def store_image(self, source_path: str, target_filename: str) -> bool:
        """
        Carica un'immagine, la valida, la salva come .2pg e la registra sulla blockchain.
        """
        # 1. Validazione nome file
        if not is_valid_filename(target_filename):
            print(f"Errore: Il nome file '{target_filename}' non è valido. Deve essere 5 lettere minuscole + .2pg")
            return False

        # 2. Validazione formato immagine (deve essere compatibile con JPEG)
        try:
            with Image.open(source_path) as img:
                if img.format not in ['JPEG', 'MPO']: # MPO è simile a JPEG
                    # Proviamo a convertirla se non è jpeg, oppure rifiutiamo.
                    # Per rigore, convertiamo in RGB e salviamo come JPEG
                    img = img.convert('RGB')
        except Exception as e:
            print(f"Errore: Il file sorgente non è un'immagine valida. {e}")
            return False

        # 3. Calcolo Hash del contenuto
        with open(source_path, "rb") as f:
            file_data = f.read()
        
        img_hash = calculate_hash(file_data)

        # 4. Verifica se esiste già
        if self.blockchain.find_transaction(img_hash):
            print("Errore: Questa immagine è già registrata nella blockchain.")
            return False

        # 5. Salvataggio fisico del file
        dest_path = os.path.join(self.storage_dir, target_filename)
        # Riscriviamo il file per assicurarci che sia un JPEG valido rinominato in .2pg
        with Image.open(source_path) as img:
            img.convert('RGB').save(dest_path, format='JPEG')
        
        # Ricalcoliamo l'hash del file effettivamente salvato (potrebbe cambiare leggermente per la compressione se riconvertito)
        # Per coerenza con la richiesta "stesso formato del jpeg", assumiamo che il file salvato sia quello che conta.
        with open(dest_path, "rb") as f:
            final_data = f.read()
        final_hash = calculate_hash(final_data)

        # 6. Creazione Transazione Blockchain
        transaction = {
            'node_id': self.node_id,
            'filename': target_filename,
            'image_hash': final_hash,
            'timestamp': time.time()
        }
        
        self.blockchain.add_new_transaction(transaction)
        self.blockchain.mine()
        
        # Dopo aver minato, diffondiamo il nuovo blocco alla rete
        self.broadcast_block(self.blockchain.last_block)
        
        print(f"Immagine salvata in {dest_path} e registrata nel blocco #{self.blockchain.last_block.index}")
        return True

    def validate_local_image(self, filename: str) -> bool:
        """
        Verifica se un file locale è valido controllando la blockchain.
        """
        file_path = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(file_path):
            print("File non trovato localmente.")
            return False

        with open(file_path, "rb") as f:
            data = f.read()
        
        current_hash = calculate_hash(data)
        
        tx = self.blockchain.find_transaction(current_hash)
        
        if tx:
            print(f"Validazione OK: Immagine autentica registrata dal nodo {tx['node_id']}.")
            return True
        else:
            print("Validazione FALLITA: Hash immagine non trovato nella blockchain.")
            return False

import time
