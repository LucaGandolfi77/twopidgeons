import pytest
import os
import json
import time
from twopidgeons.blockchain import Blockchain, Block

@pytest.fixture
def blockchain(tmp_path):
    # Use a temporary file for the blockchain
    chain_file = tmp_path / "test_chain.json"
    # Lower difficulty for tests to speed up execution
    original_difficulty = Blockchain.difficulty
    Blockchain.difficulty = 1
    bc = Blockchain(chain_file=str(chain_file))
    yield bc
    Blockchain.difficulty = original_difficulty

def test_genesis_block(blockchain):
    assert len(blockchain.chain) == 1
    genesis = blockchain.chain[0]
    assert genesis.index == 0
    assert genesis.previous_hash == "0"
    assert genesis.transactions == []

def test_add_transaction(blockchain):
    tx = {"sender": "A", "receiver": "B", "amount": 10}
    blockchain.add_new_transaction(tx)
    assert len(blockchain.unconfirmed_transactions) == 1
    assert blockchain.unconfirmed_transactions[0] == tx

def test_mine_block(blockchain):
    tx = {"sender": "A", "receiver": "B", "amount": 10}
    blockchain.add_new_transaction(tx)
    
    index = blockchain.mine()
    
    assert index == 1
    assert len(blockchain.chain) == 2
    assert len(blockchain.unconfirmed_transactions) == 0
    
    last_block = blockchain.last_block
    assert last_block.index == 1
    assert last_block.transactions == [tx]
    assert last_block.previous_hash == blockchain.chain[0].hash

def test_chain_validity(blockchain):
    # Valid chain
    tx = {"data": "test"}
    blockchain.add_new_transaction(tx)
    blockchain.mine()
    assert blockchain.is_chain_valid() is True

    # Tamper with the chain
    blockchain.chain[1].transactions = [{"data": "hacked"}]
    # Hash mismatch
    assert blockchain.is_chain_valid() is False

def test_persistence(tmp_path):
    chain_file = tmp_path / "persistent_chain.json"
    bc1 = Blockchain(chain_file=str(chain_file))
    
    bc1.add_new_transaction({"data": "tx1"})
    bc1.mine()
    
    # Create a new instance pointing to the same file
    bc2 = Blockchain(chain_file=str(chain_file))
    
    assert len(bc2.chain) == 2
    assert bc2.chain[1].transactions == [{"data": "tx1"}]
    assert bc2.last_block.hash == bc1.last_block.hash

def test_is_valid_chain_static():
    # Lower difficulty for this test
    old_diff = Blockchain.difficulty
    Blockchain.difficulty = 1
    
    try:
        # Create a manual valid chain
        b0 = Block(0, [], time.time(), "0")
        # Mine b0
        while not b0.hash.startswith('0'):
            b0.nonce += 1
            b0.hash = b0.compute_hash()
            
        b1 = Block(1, [{"a": 1}], time.time(), b0.hash)
        # Mine b1
        while not b1.hash.startswith('0'):
            b1.nonce += 1
            b1.hash = b1.compute_hash()
            
        chain = [b0, b1]
        
        assert Blockchain.is_valid_chain(chain) is True
        
        # Invalid genesis
        b0_bad = Block(1, [], time.time(), "0")
        # Mine b0_bad
        while not b0_bad.hash.startswith('0'):
            b0_bad.nonce += 1
            b0_bad.hash = b0_bad.compute_hash()
            
        assert Blockchain.is_valid_chain([b0_bad]) is False
        
        # Broken link
        b2_bad = Block(2, [], time.time(), "wrong_hash")
        # Mine b2_bad
        while not b2_bad.hash.startswith('0'):
            b2_bad.nonce += 1
            b2_bad.hash = b2_bad.compute_hash()
            
        chain_bad = [b0, b1, b2_bad]
        assert Blockchain.is_valid_chain(chain_bad) is False
        
    finally:
        Blockchain.difficulty = old_diff
    chain_bad = [b0, b1, b2_bad]
    assert Blockchain.is_valid_chain(chain_bad) is False
