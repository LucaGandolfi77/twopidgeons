import os
import shutil
import requests
from urllib.parse import urlparse
from PIL import Image
import json
from .blockchain import Blockchain, Block
from .utils import is_valid_filename, calculate_hash
from .steganography import Steganography
from .crypto_utils import (
    generate_keys, save_key_to_file, load_private_key_from_file, 
    load_public_key_from_file, serialize_public_key, sign_data
)

class Node:
    def __init__(self, node_id: str, storage_dir: str):
        self.node_id = node_id

        self.storage_dir = storage_dir
        self.nodes = set() # Set of peer nodes (e.g., 'http://192.168.0.5:5000')
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            
        # The blockchain is saved in the same directory as the node
        chain_path = os.path.join(self.storage_dir, "blockchain.db")
        self.blockchain = Blockchain(db_file=chain_path)

        # Key management
        self.private_key_path = os.path.join(self.storage_dir, "private_key.pem")
        self.public_key_path = os.path.join(self.storage_dir, "public_key.pem")
        
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
            self.private_key = load_private_key_from_file(self.private_key_path)
            self.public_key = load_public_key_from_file(self.public_key_path)
        else:
            print("Generating new key pair...")
            self.private_key, self.public_key = generate_keys()
            save_key_to_file(self.private_key, self.private_key_path, is_private=True)
            save_key_to_file(self.public_key, self.public_key_path, is_private=False)
            
        self.public_key_pem = serialize_public_key(self.public_key)

    def register_node(self, address: str):
        """Adds a new node to the list of peers."""
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.scheme + "://" + parsed_url.netloc)
        elif parsed_url.path:
            # Also accepts addresses without scheme (e.g., 'localhost:5000')
            self.nodes.add("http://" + parsed_url.path)

    def broadcast_block(self, block: Block):
        """Sends a new block to all known nodes."""
        print(f"Broadcasting block #{block.index} to peers...")
        block_data = block.__dict__
        for node in self.nodes:
            try:
                requests.post(f"{node}/block/receive", json=block_data, timeout=2)
            except requests.RequestException:
                print(f"Unable to contact node {node}")

    def receive_block(self, block_data: dict) -> bool:
        """
        Handles the reception of a block from another node.
        Returns True if the block was accepted.
        """
        # Reconstruct the Block object
        new_block = Block(
            index=block_data['index'],
            transactions=block_data['transactions'],
            timestamp=block_data['timestamp'],
            previous_hash=block_data['previous_hash']
        )
        
        last_block = self.blockchain.last_block
        
        # Case 1: The block is the exact next one in our chain
        if new_block.index == last_block.index + 1:
            if Blockchain.is_valid_block(new_block, last_block):
                self.blockchain.chain.append(new_block)
                self.blockchain.save_chain()
                print(f"Block #{new_block.index} received and added to the chain.")
                return True
        
        # Case 2: The block is far ahead (we are out of sync)
        elif new_block.index > last_block.index + 1:
            print("Received future block. Our chain is outdated. Resolving conflicts...")
            self.resolve_conflicts()
            
        return False

    def resolve_conflicts(self) -> bool:
        """
        Consensus Algorithm: resolves conflicts by replacing the chain
        with the longest valid one in the network.
        Returns True if the chain was replaced, False otherwise.
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

                    # If we find a longer chain, verify its validity
                    if length > max_length:
                        # Reconstruct the chain of Block objects
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
        Uploads an image, validates it, saves it as .2pg, and registers it on the blockchain.
        """
        # 1. Filename validation
        if not is_valid_filename(target_filename):
            print(f"Error: Filename '{target_filename}' is invalid. Must be 5 lowercase letters + .2pg")
            return False

        # 2. Image format validation (must be compatible with JPEG)
        try:
            with Image.open(source_path) as img:
                if img.format not in ['JPEG', 'MPO']: # MPO is similar to JPEG
                    # Try to convert if not jpeg, or reject.
                    # For strictness, convert to RGB and save as JPEG
                    img = img.convert('RGB')
        except Exception as e:
            print(f"Error: Source file is not a valid image. {e}")
            return False

        # 3. Content Hash Calculation
        with open(source_path, "rb") as f:
            file_data = f.read()
        
        img_hash = calculate_hash(file_data)

        # 4. Check if already exists
        if self.blockchain.find_transaction(img_hash):
            print("Error: This image is already registered in the blockchain.")
            return False

        # 5. Physical file saving
        dest_path = os.path.join(self.storage_dir, target_filename)
        # Rewrite the file to ensure it is a valid JPEG renamed to .2pg
        with Image.open(source_path) as img:
            img.convert('RGB').save(dest_path, format='JPEG')
            
        # 6. Steganography: Embed Node ID and Timestamp into the image
        # We do this BEFORE calculating the final hash, so the hash includes the hidden data.
        hidden_data = f"Origin: {self.node_id} | Time: {time.time()}"
        Steganography.embed(dest_path, hidden_data)
        
        # 7. Recalculate hash of the actually saved file (with steganography)
        with open(dest_path, "rb") as f:
            final_data = f.read()
        final_hash = calculate_hash(final_data)

        # 8. Blockchain Transaction Creation
        transaction_data = {
            'node_id': self.node_id,
            'filename': target_filename,
            'image_hash': final_hash,
            'source_hash': img_hash,
            'timestamp': time.time(),
            'hidden_data': hidden_data, # Optional: store what we hid
            'public_key': self.public_key_pem
        }
        
        # Sign the transaction
        tx_bytes = json.dumps(transaction_data, sort_keys=True).encode()
        signature = sign_data(self.private_key, tx_bytes)
        
        transaction_data['signature'] = signature
        
        self.blockchain.add_new_transaction(transaction_data)
        self.blockchain.mine()
        
        # After mining, broadcast the new block to the network
        self.broadcast_block(self.blockchain.last_block)
        
        print(f"Image saved in {dest_path} (with steganography) and registered in block #{self.blockchain.last_block.index}")
        return True

    def validate_local_image(self, filename: str) -> bool:
        """
        Verifies if a local file is valid by checking the blockchain.
        Also checks for steganographic signature.
        """
        file_path = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(file_path):
            print("File not found locally.")
            return False

        # Check Steganography
        hidden_msg = Steganography.extract(file_path)
        if hidden_msg:
            print(f"Steganography found: {hidden_msg}")
        else:
            print("Warning: No steganographic data found.")

        with open(file_path, "rb") as f:
            data = f.read()
        
        current_hash = calculate_hash(data)
        
        tx = self.blockchain.find_transaction(current_hash)
        
        if tx:
            print(f"Validation OK: Authentic image registered by node {tx['node_id']}.")
            return True
        else:
            print("Validation FAILED: Image hash not found in the blockchain.")
            return False

import time
