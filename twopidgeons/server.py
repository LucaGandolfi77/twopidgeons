import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import time

# Aggiungi la directory parent al path per importare i moduli locali
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twopidgeons.node import Node

app = FastAPI(title="TwoPidgeons Node API")

import uuid

# Inizializzazione del nodo
# Usiamo variabili d'ambiente o valori di default
NODE_ID = os.getenv("NODE_ID", str(uuid.uuid4()).replace('-', ''))
STORAGE_DIR = os.getenv("STORAGE_DIR", "node_storage")

# Assicuriamoci che la directory esista
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

node = Node(node_id=NODE_ID, storage_dir=STORAGE_DIR)

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

@app.get("/mine", response_model=MineResponse)
async def mine():
    """
    Endpoint per minare un nuovo blocco.
    """
    # Ricompensa per il miner
    # Il mittente è "0" per indicare che è una nuova moneta minata
    reward_transaction = {
        "sender": "0",
        "recipient": node.node_identifier,
        "amount": 1,
        "signature": "", # Nessuna firma necessaria per il mining reward
        "timestamp": time.time()
    }
    node.blockchain.add_new_transaction(reward_transaction)

    # Il metodo mine() si occupa di creare il blocco, calcolare la PoW e salvarlo
    block_index = node.blockchain.mine()
    
    if block_index == -1:
        raise HTTPException(status_code=400, detail="Nessuna transazione da minare (eccetto reward)")

    block = node.blockchain.last_block

    response = {
        'message': "Nuovo blocco forgiato",
        'index': block.index,
        'transactions': [tx for tx in block.transactions], # Assumiamo che siano già dict
        'proof': block.nonce,
        'previous_hash': block.previous_hash,
        'merkle_root': block.merkle_root
    }
    return response

@app.post("/transactions/new", response_model=TransactionResponse, status_code=201)
async def new_transaction(transaction: TransactionModel):
    """
    Endpoint per creare una nuova transazione.
    """
    tx_data = transaction.dict(exclude_none=True)
    tx_data['timestamp'] = time.time()
    
    # Se c'è una chiave pubblica nel nodo (per verificare la firma), dovremmo passarla?
    # Per ora assumiamo che la firma sia verificata dentro add_new_transaction se i campi sono presenti
    # Ma TransactionModel non ha public_key. 
    # Se la logica richiede public_key per la verifica, il client deve inviarla.
    # Aggiungiamo public_key al modello se necessario, o assumiamo che sia gestita altrove.
    # Per ora passiamo i dati così come sono.
    
    success = node.blockchain.add_new_transaction(tx_data)
    
    if not success:
         raise HTTPException(status_code=400, detail="Transazione non valida")

    response = {'message': f'La transazione sarà aggiunta al prossimo blocco'}
    return response

@app.get("/chain", response_model=ChainResponse)
async def full_chain():
    """
    Restituisce l'intera blockchain.
    """
    chain_data = []
    for block in node.blockchain.chain:
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

@app.post("/nodes/register", response_model=RegisterNodesResponse, status_code=201)
async def register_nodes(request: RegisterNodesRequest):
    """
    Registra nuovi nodi nella rete.
    """
    nodes = request.nodes
    if not nodes:
        raise HTTPException(status_code=400, detail="Fornire una lista valida di nodi")

    for node_url in nodes:
        node.register_node(node_url)

    response = {
        'message': 'Nuovi nodi aggiunti',
        'total_nodes': list(node.nodes),
    }
    return response

@app.get("/nodes/resolve", response_model=ResolveResponse)
async def consensus():
    """
    Risolve i conflitti rimpiazzando la catena con la più lunga nella rete.
    """
    replaced = node.resolve_conflicts()

    if replaced:
        response = {
            'message': 'La catena è stata sostituita',
            'chain': node.blockchain.chain
        }
    else:
        response = {
            'message': 'La catena è autorevole',
            'chain': node.blockchain.chain
        }
    return response

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='Porta su cui ascoltare')
    args = parser.parse_args()
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)
