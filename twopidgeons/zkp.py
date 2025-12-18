import os
import hashlib
import base64
from .crypto_utils import encrypt_data_hybrid, decrypt_data_hybrid, deserialize_public_key

class ZKProof:
    """
    Implements a Challenge-Response Zero-Knowledge Proof of Ownership.
    Protocol:
    1. Verifier generates random secret 'r'.
    2. Verifier encrypts 'r' with Prover's Public Key -> 'C'.
    3. Verifier keeps H('r').
    4. Prover decrypts 'C' -> 'r'.
    5. Prover sends H('r') back.
    6. Verifier checks if received hash matches H('r').
    
    This proves Prover has the Private Key corresponding to the Public Key,
    without revealing the Private Key or the secret 'r' (since only hash is sent back).
    """
    
    @staticmethod
    def create_challenge(public_key_pem: bytes) -> tuple[str, str]:
        """
        Generates a challenge for the owner of the public key.
        Returns: (encrypted_challenge_b64, expected_response_hash)
        """
        # 1. Generate random secret
        secret = os.urandom(32)
        
        # 2. Calculate expected response (Hash of secret)
        expected_response = hashlib.sha256(secret).hexdigest()
        
        # 3. Encrypt secret with Public Key
        # We use the existing hybrid encryption from crypto_utils
        public_key = deserialize_public_key(public_key_pem)
        encrypted_secret = encrypt_data_hybrid(secret, public_key)
        
        # 4. Encode for transport
        encrypted_challenge_b64 = base64.b64encode(encrypted_secret).decode('utf-8')
        
        return encrypted_challenge_b64, expected_response

    @staticmethod
    def solve_challenge(private_key, encrypted_challenge_b64: str) -> str:
        """
        Solves the challenge using the Private Key.
        Returns: response_hash
        """
        try:
            # 1. Decode
            encrypted_secret = base64.b64decode(encrypted_challenge_b64)
            
            # 2. Decrypt
            secret = decrypt_data_hybrid(encrypted_secret, private_key)
            
            # 3. Hash
            response = hashlib.sha256(secret).hexdigest()
            return response
        except Exception as e:
            print(f"ZKP Failed: {e}")
            return None
