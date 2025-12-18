import requests
import os

class IPFSClient:
    def __init__(self, api_url: str, gateway_url: str):
        self.api_url = api_url.rstrip('/')
        self.gateway_url = gateway_url.rstrip('/')

    def add(self, data: bytes) -> str:
        """
        Uploads bytes to IPFS and returns the CID (Hash).
        """
        try:
            files = {'file': data}
            response = requests.post(f"{self.api_url}/add", files=files)
            response.raise_for_status()
            return response.json()['Hash']
        except requests.RequestException as e:
            print(f"IPFS Upload Error: {e}")
            return None

    def get(self, cid: str) -> bytes:
        """
        Retrieves data from IPFS by CID.
        """
        try:
            # Use the API 'cat' endpoint to get the raw data
            params = {'arg': cid}
            response = requests.post(f"{self.api_url}/cat", params=params)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"IPFS Download Error (API): {e}")
            # Fallback to gateway if API fails
            try:
                response = requests.get(f"{self.gateway_url}/{cid}")
                response.raise_for_status()
                return response.content
            except requests.RequestException as e2:
                print(f"IPFS Download Error (Gateway): {e2}")
                return None
