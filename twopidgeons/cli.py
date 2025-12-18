import argparse
import os
from .node import Node

def main():
    parser = argparse.ArgumentParser(description="TwoPidgeons: Blockchain Image Manager")
    subparsers = parser.add_subparsers(dest="command", help="Comandi disponibili")

    # Comando: store
    parser_store = subparsers.add_parser("store", help="Salva un'immagine nel nodo")
    parser_store.add_argument("source", help="Percorso immagine sorgente")
    parser_store.add_argument("name", help="Nome destinazione (es. abcde.2pg)")
    parser_store.add_argument("--node-dir", default="./node_storage", help="Directory del nodo")
    parser_store.add_argument("--node-id", default="cli_node", help="ID del nodo")

    # Comando: validate
    parser_validate = subparsers.add_parser("validate", help="Valida un'immagine locale")
    parser_validate.add_argument("name", help="Nome file da validare (es. abcde.2pg)")
    parser_validate.add_argument("--node-dir", default="./node_storage", help="Directory del nodo")

    # Comando: serve
    parser_serve = subparsers.add_parser("serve", help="Avvia il server P2P")
    parser_serve.add_argument("--port", type=int, default=5000, help="Porta del server")
    parser_serve.add_argument("--node-dir", default="./node_storage", help="Directory del nodo")
    parser_serve.add_argument("--node-id", default="server_node", help="ID del nodo")

    args = parser.parse_args()

    if args.command == "store":
        node = Node(node_id=args.node_id, storage_dir=args.node_dir)
        node.store_image(args.source, args.name)
    
    elif args.command == "validate":
        node = Node(node_id="validator", storage_dir=args.node_dir)
        node.validate_local_image(args.name)

    elif args.command == "serve":
        from .server import P2PServer
        node = Node(node_id=args.node_id, storage_dir=args.node_dir)
        server = P2PServer(node, port=args.port)
        server.run()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
