import requests
from flask import Flask, jsonify, request
from .node import Node
from .blockchain import Block

class P2PServer:
    def __init__(self, node: Node, host: str = '0.0.0.0', port: int = 5000):
        self.node = node
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            chain_data = [block.__dict__ for block in self.node.blockchain.chain]
            return jsonify({
                'chain': chain_data,
                'length': len(chain_data)
            }), 200

        @self.app.route('/nodes/register', methods=['POST'])
        def register_nodes():
            values = request.get_json()
            nodes = values.get('nodes')
            if nodes is None:
                return "Error: Please supply a valid list of nodes", 400

            for node_url in nodes:
                self.node.register_node(node_url)

            return jsonify({
                'message': 'New nodes have been added',
                'total_nodes': list(self.node.nodes)
            }), 201

        @self.app.route('/nodes/resolve', methods=['GET'])
        def consensus():
            replaced = self.node.resolve_conflicts()
            if replaced:
                response = {
                    'message': 'Our chain was replaced',
                    'new_chain': [b.__dict__ for b in self.node.blockchain.chain]
                }
            else:
                response = {
                    'message': 'Our chain is authoritative',
                    'chain': [b.__dict__ for b in self.node.blockchain.chain]
                }
            return jsonify(response), 200
            
        @self.app.route('/block/receive', methods=['POST'])
        def receive_block():
            block_data = request.get_json()
            if not block_data:
                return "Invalid data", 400
                
            accepted = self.node.receive_block(block_data)
            if accepted:
                return jsonify({'message': 'Block accepted'}), 201
            else:
                return jsonify({'message': 'Block rejected or triggered sync'}), 200
        
        @self.app.route('/mine', methods=['GET'])
        def mine():
            # Endpoint to force mining (useful for testing)
            index = self.node.blockchain.mine()
            if index == -1:
                return jsonify({'message': 'No transactions to mine'}), 200
            
            # After mining, we might want to notify other nodes,
            # but for now we rely on the consensus mechanism (resolve) called by others.
            return jsonify({
                'message': 'New block mined',
                'index': index,
                'block': self.node.blockchain.last_block.__dict__
            }), 200

    def run(self):
        print(f"Starting P2P server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)
