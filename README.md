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
*   **Web Dashboard**: A user-friendly web interface to monitor the node, view the blockchain, and mine blocks.
*   **Docker Support**: Includes Dockerfile and Compose setup for easy deployment.

## Installation

Clone the repository and install the package:

```bash
git clone https://github.com/LucaGandolfi77/twopidgeons.git
cd twopidgeons
pip install -e .
```

## Step-by-Step Guide

Follow this guide to set up a node, store an image, and verify it using the new Web Dashboard.

### 1. Start the Node
Open a terminal and start the server. This will launch the API and the Web Dashboard.

```bash
# Start the server on port 5000
python3 twopidgeons/server.py --port 5000
```

### 2. Access the Dashboard
Open your web browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

You will see the **Node Status** (ID, Peers) and the **Blockchain Explorer** (currently showing just the Genesis Block).

### 3. Store an Image
Open a second terminal window. Use the CLI to upload an image to your running node.

```bash
# Create a dummy image for testing if you don't have one
convert -size 100x100 xc:white test.jpg

# Store the image (must use a 5-letter filename + .2pg)
twopidgeons store test.jpg hello.2pg --node-dir ./node_storage
```

*Note: The `store` command automatically encrypts the image, creates a transaction, and mines a new block.*

### 4. Verify on Dashboard
Go back to your browser and refresh the page (or wait for auto-update if implemented).
You should see a **new block** in the Blockchain Explorer containing your transaction.

### 5. Mine Manually (Optional)
You can also mine a new block directly from the Dashboard by clicking the **"⛏️ Mine New Block"** button. This is useful for processing pending transactions or generating new blocks for testing.

---

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

Once started, access the **Web Dashboard** at `http://localhost:5000`.

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