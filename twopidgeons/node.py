import os
import shutil
from PIL import Image
from .blockchain import Blockchain
from .utils import is_valid_filename, calculate_hash

class Node:
    def __init__(self, node_id: str, storage_dir: str):
        self.node_id = node_id
        self.storage_dir = storage_dir
        self.blockchain = Blockchain()
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

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
