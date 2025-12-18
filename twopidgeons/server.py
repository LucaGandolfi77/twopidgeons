import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import time
import uuid
import threading

# Aggiungi la directory parent al path per importare i moduli locali
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twopidgeons.node import Node

# --- Pydantic Models ---
class TransactionModel(BaseModel):
    sender: str
    recipient: str
    amount: float
    signature: str
    image_data: Optional[str] = None
    encrypted_aes_key: Optional[str] = None
    iv: Optional[str] = None

class BlockModel(BaseModel):
    index: int
    timestamp: float
    transactions: List[TransactionModel]
    proof: int
    previous_hash: str
    merkle_root: str

class ChainResponse(BaseModel):
    chain: List[Dict[str, Any]]
    length: int

class MineResponse(BaseModel):
    message: str
    index: int
    transactions: List[TransactionModel]
    proof: int
    previous_hash: str
    merkle_root: str

class TransactionResponse(BaseModel):
    message: str

class RegisterNodesRequest(BaseModel):
    nodes: List[str]

class RegisterNodesResponse(BaseModel):
    message: str
    total_nodes: List[str]

class ResolveResponse(BaseModel):
    message: str
    chain: List[Dict[str, Any]]

# --- Server Class ---
class P2PServer:
    def __init__(self, node: Node, host: str = "0.0.0.0", port: int = 5000):
        self.node = node
        self.host = host
        self.port = port
        self.app = FastAPI(title="TwoPidgeons Node API")
        self.templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
        
        # Register routes
        self.setup_routes()

    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """
            Dashboard principale del nodo.
            """
            return self.templates.TemplateResponse("index.html", {
                "request": request,
                "node_id": self.node.node_id,
                "peers": list(self.node.nodes),
                "chain_length": len(self.node.blockchain.chain)
            })

        @self.app.get("/mine", response_model=MineResponse)
        async def mine():
            """
            Endpoint per minare un nuovo blocco.
            """
            # Ricompensa per il miner
            reward_transaction = {
                "sender": "0",
                "recipient": self.node.node_identifier,
                "amount": 1,
                "signature": "", 
                "timestamp": time.time()
            }
            # Use node wrapper to trigger events
            self.node.add_transaction(reward_transaction)

            block_index = self.node.mine_block()
            
            if block_index == -1:
                raise HTTPException(status_code=400, detail="Nessuna transazione da minare (eccetto reward)")

            block = self.node.blockchain.last_block

            response = {
                'message': "Nuovo blocco forgiato",
                'index': block.index,
                'transactions': [tx for tx in block.transactions],
                'proof': block.nonce,
                'previous_hash': block.previous_hash,
                'merkle_root': block.merkle_root
            }
            return response

        @self.app.post("/transactions/new", response_model=TransactionResponse, status_code=201)
        async def new_transaction(transaction: TransactionModel):
            """
            Endpoint per creare una nuova transazione.
            """
            tx_data = transaction.dict(exclude_none=True)
            tx_data['timestamp'] = time.time()
            
            # Use node wrapper to trigger events
            success = self.node.add_transaction(tx_data)
            
            if not success:
                raise HTTPException(status_code=400, detail="Transazione non valida")

            response = {'message': f'La transazione sarà aggiunta al prossimo blocco'}
            return response

        @self.app.get("/chain", response_model=ChainResponse)
        async def full_chain():
            """
            Restituisce l'intera blockchain.
            """
            chain_data = []
            for block in self.node.blockchain.chain:
                block_dict = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'transactions': block.transactions,
                    'proof': block.nonce,
                    'previous_hash': block.previous_hash,
                    'merkle_root': block.merkle_root,
                    'hash': block.hash
                }
                chain_data.append(block_dict)

            response = {
                'chain': chain_data,
                'length': len(chain_data),
            }
            return response

        @self.app.post("/nodes/register", response_model=RegisterNodesResponse, status_code=201)
        async def register_nodes(request: RegisterNodesRequest):
            """
            Registra nuovi nodi nella rete.
            """
            nodes = request.nodes
            if not nodes:
                raise HTTPException(status_code=400, detail="Fornire una lista valida di nodi")

            for node_url in nodes:
                self.node.register_node(node_url)

            response = {
                'message': 'Nuovi nodi aggiunti',
                'total_nodes': list(self.node.nodes),
            }
            return response

        @self.app.get("/nodes/resolve", response_model=ResolveResponse)
        async def consensus():
            """
            Risolve i conflitti rimpiazzando la catena con la più lunga nella rete.
            """
            replaced = self.node.resolve_conflicts()

            if replaced:
                response = {
                    'message': 'La catena è stata sostituita',
                    'chain': self.node.blockchain.chain
                }
            else:
                response = {
                    'message': 'La catena è autorevole',
                    'chain': self.node.blockchain.chain
                }
            return response

    def run(self):
        """Avvia il server Uvicorn."""
        uvicorn.run(self.app, host=self.host, port=self.port)

# --- Main Execution ---
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='Porta su cui ascoltare')
    args = parser.parse_args()
    
    # Configurazione da variabili d'ambiente o default
    NODE_ID = os.getenv("NODE_ID", str(uuid.uuid4()).replace('-', ''))
    STORAGE_DIR = os.getenv("STORAGE_DIR", "node_storage")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "sqlite")

    # Assicuriamoci che la directory esista
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

    # Inizializzazione del nodo
    node = Node(node_id=NODE_ID, storage_dir=STORAGE_DIR, storage_backend=STORAGE_BACKEND)
    
    # Inizializzazione e avvio del server
    server = P2PServer(node, port=args.port)
    server.run()
