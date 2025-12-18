# TwoPidgeons

TwoPidgeons is a Python library for distributed image management secured by a blockchain. It allows nodes to store, validate, and share images in a secure and decentralized manner.

## Features

*   **Blockchain-based Validation**: Every image stored is hashed and recorded on a local blockchain. Any modification to the file is detected immediately.
*   **Strict Filename Policy**: Images must follow the format `[a-z]{5}.2pg` (e.g., `abcde.2pg`).
*   **JPEG Compatibility**: The `.2pg` format is fully compatible with JPEG.
*   **P2P Networking**: Nodes can communicate, broadcast new blocks, and synchronize their blockchains using a consensus algorithm (Longest Chain Rule).
*   **Persistence**: The blockchain is saved to disk (`blockchain.json`) and reloaded upon restart.
*   **CLI Interface**: Easy-to-use command line interface for managing nodes and images.

## Installation

Clone the repository and install the package:

```bash
git clone https://github.com/LucaGandolfi77/twopidgeons.git
cd twopidgeons
pip install -e .
```

## Usage

### Command Line Interface (CLI)

The library provides a `twopidgeons` command with three main subcommands:

#### 1. Start a P2P Node
Starts a server node that listens for connections and syncs with peers.

```bash
twopidgeons serve --port 5000 --node-dir ./node_A
```

#### 2. Store an Image
Uploads an image to a node, converts it to `.2pg`, and records it on the blockchain.

```bash
twopidgeons store path/to/photo.jpg abcde.2pg --node-dir ./node_A
```

#### 3. Validate an Image
Checks if a local file matches the hash recorded in the blockchain.

```bash
twopidgeons validate abcde.2pg --node-dir ./node_A
```

### Python API

You can also use the library directly in your Python scripts:

```python
from twopidgeons.node import Node

# Initialize a node
node = Node(node_id="my_node", storage_dir="./storage")

# Store an image
node.store_image("input.jpg", "abcde.2pg")

# Validate an image
is_valid = node.validate_local_image("abcde.2pg")
print(f"Is valid: {is_valid}")
```

## P2P Network Setup

To simulate a network locally:

1.  **Start Node A**:
    ```bash
    twopidgeons serve --port 5000 --node-dir ./node_A
    ```

2.  **Start Node B**:
    ```bash
    twopidgeons serve --port 5001 --node-dir ./node_B
    ```

3.  **Connect Node A to Node B**:
    ```bash
    curl -X POST http://localhost:5001/nodes/register \
      -H "Content-Type: application/json" \
      -d '{"nodes": ["http://localhost:5000"]}'
    ```

Now, when you store an image on Node A, the new block will be broadcasted to Node B automatically.

## Testing

Run the unit tests to ensure everything is working correctly:

```bash
pytest
```

## License

MIT