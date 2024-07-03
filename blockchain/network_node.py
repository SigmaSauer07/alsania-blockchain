import secrets
import json
import requests
import time
import socket
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat
from ipfshttpclient import connect

class Node:
    VALID_CHARACTERS = "0123456789abcdefABCDEF"
    PRIVATE_KEY_LENGTH = 64

    def __init__(self, address, host, port, ipfs_host='127.0.0.1', ipfs_port=5001):
        self.address = address
        self.host = host
        self.port = port
        self.private_key = self.generate_private_key()
        self.public_key = self.derive_public_key()
        self.balance = 0
        self.ipfs_host = ipfs_host
        self.ipfs_port = ipfs_port
        self.ipfs_client = connect(f"/ip4/{self.ipfs_host}/tcp/{self.ipfs_port}/http")

    def generate_private_key(self):
        """Generate a private key."""
        private_key_int = secrets.randbits(256)
        sk = ec.derive_private_key(private_key_int, ec.SECP256R1(), default_backend())
        private_key = sk.private_numbers().private_value.to_bytes(32, byteorder='big').hex()
        return private_key
    
    def derive_public_key(self):
        """Derive a public key from the private key."""
        private_key_bytes = bytes.fromhex(self.private_key)
        private_key = ec.derive_private_key(int(private_key_bytes.hex(), 16), ec.SECP256R1(), default_backend())
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_key.hex()

    @staticmethod
    def create_message(sender, recipient, data):
        """Create a JSON-formatted message."""
        return json.dumps({
            "sender": sender,
            "recipient": recipient,
            "data": data
        })

    @staticmethod
    def register_node(host, port, new_node_info):
        """Register a new node with the specified host and port."""
        url = f"http://{host}:{port}/register"
        try:
            response = requests.post(url, json=new_node_info)
            response.raise_for_status()
            print("Node registered successfully")
        except requests.RequestException as e:
            print(f"Failed to register node: {e}")

    def send_transaction(self, transaction):
        """Send a transaction to another node."""
        payload = {'transaction': transaction}
        try:
            response = requests.post(f"http://{self.host}:{self.port}/transaction", json=payload)
            response.raise_for_status()
            print("Transaction sent successfully")
        except requests.RequestException as e:
            print(f"Error sending transaction: {e}")

    def send_block(self, block):
        """Send a block to another node."""
        payload = {'block': block}
        try:
            response = requests.post(f"http://{self.host}:{self.port}/block", json=payload)
            response.raise_for_status()
            print("Block sent successfully")
        except requests.RequestException as e:
            print(f"Error sending block: {e}")

    def add_file_to_ipfs(self, file_path):
        """Add a file to IPFS and return its hash."""
        try:
            res = self.ipfs_client.add(file_path)
            return res['Hash']
        except Exception as e:
            print(f"Failed to add file to IPFS: {e}")
            return None

    def get_file_from_ipfs(self, ipfs_hash, download_path):
        """Get a file from IPFS by its hash and save it to download_path."""
        try:
            self.ipfs_client.get(ipfs_hash, download_path)
            print(f"File retrieved from IPFS and saved to: {download_path}")
        except Exception as e:
            print(f"Failed to retrieve file from IPFS: {e}")

    def run(self):
        global AlsaniaBlockchain
        while True:
            # 1. Listen for incoming connections
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                s.listen()
                conn, addr = s.accept()
                with conn:
                    print(f'Connected by {addr}')
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        # 2. Handle incoming data (transactions or blocks)
                        message = json.loads(data.decode())
                        if message['type'] == 'transaction':
                            self.send_transaction(message['transaction'])
                        elif message['type'] == 'block':
                            self.send_block(message['block'])
                        else:
                            print(f"Unknown message type: {message['type']}")
            new_block = AlsaniaBlockchain.pala_consensus.propose_block()  
            if new_block:
                self.send_block(new_block)
            time.sleep(1)