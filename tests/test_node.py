import pytest
import os
from PIL import Image
from twopidgeons.node import Node

@pytest.fixture
def node(tmp_path):
    storage_dir = tmp_path / "node_storage"
    return Node(node_id="test_node", storage_dir=str(storage_dir))

@pytest.fixture
def sample_image(tmp_path):
    img_path = tmp_path / "test_image.jpg"
    img = Image.new('RGB', (60, 30), color='red')
    img.save(img_path)
    return str(img_path)

def test_store_image_valid(node, sample_image):
    target_name = "abcde.2pg"
    success = node.store_image(sample_image, target_name)
    
    assert success is True
    assert os.path.exists(os.path.join(node.storage_dir, target_name))
    
    # Check blockchain
    assert len(node.blockchain.chain) == 2 # Genesis + 1 block
    tx = node.blockchain.last_block.transactions[0]
    assert tx['filename'] == target_name
    assert tx['node_id'] == "test_node"

def test_store_image_invalid_name(node, sample_image):
    assert node.store_image(sample_image, "invalid.2pg") is False
    assert len(node.blockchain.chain) == 1

def test_store_image_duplicate(node, sample_image):
    target_name = "abcde.2pg"
    node.store_image(sample_image, target_name)
    
    # Try to store the same image content again (even with different name, hash collision check)
    # Note: The current implementation checks hash. If content is same, hash is same.
    # Let's try same content, different name
    success = node.store_image(sample_image, "fghij.2pg")
    assert success is False # Should fail because hash already exists

def test_validate_local_image(node, sample_image):
    target_name = "abcde.2pg"
    node.store_image(sample_image, target_name)
    
    assert node.validate_local_image(target_name) is True
    
    # Tamper with file
    file_path = os.path.join(node.storage_dir, target_name)
    with open(file_path, "wb") as f:
        f.write(b"corrupted data")
        
    assert node.validate_local_image(target_name) is False

def test_validate_missing_file(node):
    assert node.validate_local_image("missi.2pg") is False
