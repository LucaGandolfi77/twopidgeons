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
    parser_store.add_argument("--condition", help="Smart Contract condition (e.g. \"amount > 5\")")

    # Command: transfer
    parser_transfer = subparsers.add_parser("transfer", help="Transfers an image to another node")
    parser_transfer.add_argument("name", help="Filename to transfer (e.g. abcde.2pg)")
    parser_transfer.add_argument("recipient", help="Recipient Node ID")
    parser_transfer.add_argument("--amount", type=float, default=0, help="Payment amount")
    parser_transfer.add_argument("--node-dir", default="./node_storage", help="Node directory")
    parser_transfer.add_argument("--node-id", default="cli_node", help="Node ID")

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
    
    from .config import Config
    
    # Helper to create config from args
    def get_config(args):
        c = Config()
        if hasattr(args, 'node_dir') and args.node_dir:
            c.storage_dir = args.node_dir
        if hasattr(args, 'node_id') and args.node_id:
            c.node_id = args.node_id
        if hasattr(args, 'port') and args.port:
            c.port = args.port
        return c

    if args.command == "store":
        node = Node(config=get_config(args))
        node.store_image(args.source, args.name, conditions=args.condition)
    
    elif args.command == "transfer":
        node = Node(config=get_config(args))
        node.transfer_image(args.name, args.recipient, args.amount)

    elif args.command == "validate":
        # Validator needs a temporary ID if not provided, but needs correct storage dir
        cfg = get_config(args)
        cfg.node_id = "validator"
        node = Node(config=cfg)
        
        cid = args.name
        # Try to resolve filename to CID if it doesn't look like a CID
        if not (cid.startswith("Qm") or cid.startswith("bafy")):
             resolved = node.get_cid_by_filename(args.name)
             if resolved:
                 print(f"Resolved filename '{args.name}' to CID: {resolved}")
                 cid = resolved
             else:
                 print(f"Warning: '{args.name}' does not look like a CID and was not found in blockchain. Trying as CID anyway.")
        
        node.validate_image(cid)

    elif args.command == "inspect":
        # Inspect now needs to decrypt the file first
        cfg = get_config(args)
        cfg.node_id = "inspector"
        node = Node(config=cfg)
        
        cid = args.name
        if not (cid.startswith("Qm") or cid.startswith("bafy")):
             resolved = node.get_cid_by_filename(args.name)
             if resolved:
                 print(f"Resolved filename '{args.name}' to CID: {resolved}")
                 cid = resolved
             else:
                 print(f"Warning: '{args.name}' does not look like a CID and was not found in blockchain. Trying as CID anyway.")

        print(f"Fetching from IPFS: {cid}")
        encrypted_data = node.ipfs.get(cid)
        
        if encrypted_data:
            try:
                from .crypto_utils import decrypt_data_hybrid
                from .steganography import Steganography
                
                print("Decrypting file...")
                decrypted_data = decrypt_data_hybrid(encrypted_data, node.private_key)
                
                temp_path = os.path.join(cfg.storage_dir, f"temp_inspect_{cid}.jpg")
                with open(temp_path, "wb") as f:
                    f.write(decrypted_data)
                
                data = Steganography.extract(temp_path)
                print(f"Hidden Data: {data}")
                
                os.remove(temp_path)
            except Exception as e:
                print(f"Error inspecting file (Decryption failed?): {e}")
        else:
            print("File not found on IPFS.")

    elif args.command == "serve":
        from .server import P2PServer
        cfg = get_config(args)
        node = Node(config=cfg)
        server = P2PServer(node, port=cfg.port)
        server.run()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
