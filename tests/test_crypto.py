import pytest
import json
from twopidgeons.crypto_utils import generate_keys, sign_data, serialize_public_key
from twopidgeons.blockchain import Blockchain

@pytest.fixture
def blockchain(tmp_path):
    chain_file = tmp_path / "test_chain_crypto.json"
    # Lower difficulty
    original_difficulty = Blockchain.difficulty
    Blockchain.difficulty = 1
    bc = Blockchain(chain_file=str(chain_file))
    yield bc
    Blockchain.difficulty = original_difficulty

def test_signed_transaction(blockchain):
    private_key, public_key = generate_keys()
    public_key_pem = serialize_public_key(public_key)
    
    tx = {
        "sender": "Alice",
        "amount": 100,
        "public_key": public_key_pem
    }
    
    # Sign
    tx_bytes = json.dumps(tx, sort_keys=True).encode()
    signature = sign_data(private_key, tx_bytes)
    
    tx['signature'] = signature
    
    # Add to blockchain
    assert blockchain.add_new_transaction(tx) is True
    assert len(blockchain.unconfirmed_transactions) == 1

def test_invalid_signature(blockchain):
    private_key, public_key = generate_keys()
    public_key_pem = serialize_public_key(public_key)
    
    tx = {
        "sender": "Bob",
        "amount": 50,
        "public_key": public_key_pem
    }
    
    # Sign
    tx_bytes = json.dumps(tx, sort_keys=True).encode()
    signature = sign_data(private_key, tx_bytes)
    
    tx['signature'] = signature
    
    # Tamper with data
    tx['amount'] = 1000
    
    # Add to blockchain (should fail)
    assert blockchain.add_new_transaction(tx) is False
    assert len(blockchain.unconfirmed_transactions) == 0

def test_invalid_public_key(blockchain):
    private_key, public_key = generate_keys()
    
    tx = {
        "sender": "Charlie",
        "public_key": "invalid_key_string"
    }
    
    # Sign (doesn't matter if signature is valid for the data, key is invalid)
    tx_bytes = json.dumps(tx, sort_keys=True).encode()
    signature = sign_data(private_key, tx_bytes)
    tx['signature'] = signature
    
    assert blockchain.add_new_transaction(tx) is False
