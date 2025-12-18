# TwoPidgeons

TwoPidgeons is a Python library for distributed image management secured by a blockchain. It allows nodes to store, validate, and share images in a secure and decentralized manner.

## Features

*   **High Performance API**: Built with **FastAPI** and **Uvicorn** for asynchronous, high-throughput request handling.
*   **Blockchain-based Validation**: Every image stored is hashed and recorded on a local blockchain.
*   **SQLite Storage**: Blockchain data is persistently stored in a SQLite database (`blockchain.db`) for reliability and scalability.
*   **Merkle Trees**: Blocks utilize Merkle Trees to ensure efficient and secure verification of transaction integrity.
*   **Hybrid Encryption**: Images are secured using a hybrid approach (RSA for key exchange, AES for data encryption).
*   **Proof of Work (PoW)**: Blocks are mined using a computational puzzle to secure the chain.
*   **Digital Signatures**: Transactions are signed (RSA) to ensure authenticity.
*   **Steganography**: Metadata is embedded invisibly into image EXIF data.
*   **Docker Support**: Includes Dockerfile and Compose setup for easy deployment.

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
# Run the FastAPI server
python3 twopidgeons/server.py --port 5000
```

You can configure the node ID and storage directory using environment variables:

```bash
export NODE_ID="node_A"
export STORAGE_DIR="./node_A_storage"
python3 twopidgeons/server.py --port 5000
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

#### 4. Inspect Steganography
Reads the hidden metadata (Origin Node and Timestamp) embedded in the image.

```bash
twopidgeons inspect abcde.2pg --node-dir ./node_A
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

## Docker Support (Simulated Network)

You can instantly spin up a simulated P2P network with multiple nodes using Docker Compose.

1.  **Build and Start the Network**:
    This command starts 1 bootstrap node and 5 worker nodes.
    ```bash
    docker-compose up --build --scale node=5
    ```

2.  **Interact with the Network**:
    You can execute commands inside any running container.

    *Store an image on a specific node:*
    ```bash
    # Copy an image into the container first (or use a volume)
    docker cp myphoto.jpg twopidgeons_node_1:/app/myphoto.jpg
    
    # Run the store command inside the container
    docker exec -it twopidgeons_node_1 twopidgeons store /app/myphoto.jpg abcde.2pg --node-dir /data
    ```

    *Check logs to see mining and broadcasting:*
    ```bash
    docker-compose logs -f
    ```

## P2P Network Setup (Manual)

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