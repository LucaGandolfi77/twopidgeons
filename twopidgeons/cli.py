import argparse
import os
from .node import Node

def main():
    parser = argparse.ArgumentParser(description="TwoPidgeons: Blockchain Image Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: store
    parser_store = subparsers.add_parser("store", help="Stores an image in the node")
    parser_store.add_argument("source", help="Source image path")
    parser_store.add_argument("name", help="Destination name (e.g. abcde.2pg)")
    parser_store.add_argument("--node-dir", default="./node_storage", help="Node directory")
    parser_store.add_argument("--node-id", default="cli_node", help="Node ID")

    # Command: validate
    parser_validate = subparsers.add_parser("validate", help="Validates a local image")
    parser_validate.add_argument("name", help="Filename to validate (e.g. abcde.2pg)")
    parser_validate.add_argument("--node-dir", default="./node_storage", help="Node directory")

    # Command: inspect
    parser_inspect = subparsers.add_parser("inspect", help="Inspects hidden steganographic data")
    parser_inspect.add_argument("name", help="Filename to inspect")
    parser_inspect.add_argument("--node-dir", default="./node_storage", help="Node directory")

    # Command: serve
    parser_serve = subparsers.add_parser("serve", help="Starts the P2P server")
    parser_serve.add_argument("--port", type=int, default=5000, help="Server port")
    parser_serve.add_argument("--node-dir", default="./node_storage", help="Node directory")
    parser_serve.add_argument("--node-id", default="server_node", help="Node ID")

    args = parser.parse_args()

    if args.command == "store":
        node = Node(node_id=args.node_id, storage_dir=args.node_dir)
        node.store_image(args.source, args.name)
    
    elif args.command == "validate":
        node = Node(node_id="validator", storage_dir=args.node_dir)
        node.validate_local_image(args.name)

    elif args.command == "inspect":
        from .steganography import Steganography
        file_path = os.path.join(args.node_dir, args.name)
        if os.path.exists(file_path):
            data = Steganography.extract(file_path)
            print(f"Hidden Data: {data}")
        else:
            print("File not found.")

    elif args.command == "serve":
        from .server import P2PServer
        node = Node(node_id=args.node_id, storage_dir=args.node_dir)
        server = P2PServer(node, port=args.port)
        server.run()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
