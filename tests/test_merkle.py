import pytest
from twopidgeons.merkle_tree import MerkleTree
from twopidgeons.blockchain import Block, Blockchain
import time

def test_merkle_root_calculation():
    tx1 = {"data": "tx1"}
    tx2 = {"data": "tx2"}
    tx3 = {"data": "tx3"}
    
    # Case 1: Empty
    assert MerkleTree.compute_root([]) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # sha256("")
    
    # Case 2: Single transaction
    root1 = MerkleTree.compute_root([tx1])
    assert root1 == MerkleTree.hash_transaction(tx1)
    
    # Case 3: Two transactions
    root2 = MerkleTree.compute_root([tx1, tx2])
    # Should be hash(hash(tx1) + hash(tx2))
    h1 = MerkleTree.hash_transaction(tx1)
    h2 = MerkleTree.hash_transaction(tx2)
    import hashlib
    expected = hashlib.sha256((h1 + h2).encode()).hexdigest()
    assert root2 == expected

def test_block_merkle_integration():
    txs = [{"a": 1}, {"b": 2}]
    block = Block(1, txs, time.time(), "0")
    
    assert block.merkle_root is not None
    assert block.merkle_root == MerkleTree.compute_root(txs)
    
    # Ensure hash depends on merkle root
    original_hash = block.hash
    
    # Tamper with transactions -> Merkle Root changes -> Block Hash changes
    # Note: In our implementation, if we modify transactions list in place, 
    # merkle_root doesn't auto-update unless we recompute it.
    # But if we create a new block with different transactions:
    block2 = Block(1, [{"a": 1}, {"b": 3}], block.timestamp, "0")
    assert block2.merkle_root != block.merkle_root
    assert block2.hash != block.hash

def test_spv_concept(tmp_path):
    # Simplified Payment Verification concept check
    # We can verify a block header without downloading transactions
    
    chain_file = tmp_path / "spv_chain.db"
    bc = Blockchain(db_file=str(chain_file))
    
    txs = [{"user": "Alice"}, {"user": "Bob"}]
    bc.add_new_transaction(txs[0])
    bc.add_new_transaction(txs[1])
    bc.mine()
    
    last_block = bc.last_block
    
    # Simulate SPV client having only the header
    header = {
        'index': last_block.index,
        'timestamp': last_block.timestamp,
        'previous_hash': last_block.previous_hash,
        'nonce': last_block.nonce,
        'merkle_root': last_block.merkle_root
    }
    
    # Recompute hash from header
    import json
    import hashlib
    header_string = json.dumps(header, sort_keys=True)
    header_hash = hashlib.sha256(header_string.encode()).hexdigest()
    
    assert header_hash == last_block.hash
