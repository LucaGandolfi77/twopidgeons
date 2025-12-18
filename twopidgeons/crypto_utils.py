import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import base64

def generate_keys():
    """Generates a new RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def save_key_to_file(key, filename, is_private=False):
    """Saves a key to a file."""
    if is_private:
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    else:
        pem = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    with open(filename, 'wb') as f:
        f.write(pem)

def load_private_key_from_file(filename):
    """Loads a private key from a file."""
    with open(filename, 'rb') as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )

def load_public_key_from_file(filename):
    """Loads a public key from a file."""
    with open(filename, 'rb') as f:
        return serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )

def serialize_public_key(public_key) -> str:
    """Converts a public key object to a PEM string."""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

def deserialize_public_key(pem_string: str):
    """Converts a PEM string back to a public key object."""
    return serialization.load_pem_public_key(
        pem_string.encode('utf-8'),
        backend=default_backend()
    )

def sign_data(private_key, data: bytes) -> str:
    """Signs data with the private key and returns the signature in base64."""
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(public_key, data: bytes, signature_b64: str) -> bool:
    """Verifies the signature of the data using the public key."""
    try:
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
