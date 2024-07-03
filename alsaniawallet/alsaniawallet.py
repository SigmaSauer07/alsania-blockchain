import requests
import json
import hashlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_OAEP

class AlsaniaWallet:
    def __init__(self, node_url):
        self.node_url = node_url
        self.private_key = None
        self.public_key = None
        self.address = None
        self.balance = 0
    
    def generate_key_pair(self):
        key = RSA.generate(2048)
        self.private_key = key.export_key()
        self.public_key = key.publickey().export_key()
        self.address = hashlib.sha256(self.public_key).hexdigest()
    
    def import_private_key(self, private_key):
        self.private_key = private_key
        key = RSA.import_key(private_key)
        self.public_key = key.publickey().export_key()
        self.address = hashlib.sha256(self.public_key).hexdigest()
    
    def get_balance(self):
        response = requests.get(f"{self.node_url}/get_balance/{self.address}")
        if response.status_code == 200:
            self.balance = int(response.json()["balance"])
        else:
            print(f"Failed to fetch balance: {response.text}")
    
    def send_transaction(self, to_address, amount):
        if self.private_key is None:
            print("Private key not set. Import or generate a private key.")
            return
        
        nonce = self.get_nonce()
        transaction = {
            "from": self.address,
            "to": to_address,
            "amount": amount,
            "nonce": nonce
        }
        signature = self.sign_transaction(transaction)
        transaction["signature"] = base64.b64encode(signature).decode('utf-8')
        
        response = requests.post(f"{self.node_url}/send_transaction", json=transaction)
        if response.status_code == 200:
            print("Transaction sent successfully.")
        else:
            print(f"Failed to send transaction: {response.text}")
    
    def sign_transaction(self, transaction):
        if self.private_key is None:
            print("Private key not set. Import or generate a private key.")
            return
        
        private_key = RSA.import_key(self.private_key)
        h = SHA256.new(json.dumps(transaction, sort_keys=True).encode('utf-8'))
        signature = pkcs1_15.new(private_key).sign(h)
        return signature
    
    def get_nonce(self):
        response = requests.get(f"{self.node_url}/get_nonce/{self.address}")
        if response.status_code == 200:
            return int(response.json()["nonce"])
        else:
            print(f"Failed to fetch nonce: {response.text}")
            return 0
    
    def encrypt_message(self, recipient_public_key, message):
        recipient_key = RSA.import_key(recipient_public_key)
        cipher = PKCS1_OAEP.new(recipient_key)
        encrypted_message = cipher.encrypt(message.encode())
        return base64.b64encode(encrypted_message).decode('utf-8')
    
    def decrypt_message(self, encrypted_message):
        private_key = RSA.import_key(self.private_key)
        cipher = PKCS1_OAEP.new(private_key)
        decrypted_message = cipher.decrypt(base64.b64decode(encrypted_message.encode()))
        return decrypted_message.decode('utf-8')

# Example Usage
if __name__ == "__main__":
    # Assuming your Alsania node URL
    node_url = "http://localhost:5001"
    
    # Initialize wallet
    wallet = AlsaniaWallet(node_url)
    
    # Generate or import private key
    wallet.generate_key_pair()
    # Alternatively, import an existing private key:
    # wallet.import_private_key(existing_private_key)
    
    # Get wallet balance
    wallet.get_balance()
    print(f"Your balance: {wallet.balance} ALSC")
    
    # Send a transaction
    recipient_address = "recipient_address_here"
    amount_to_send = 10  # Example amount
    wallet.send_transaction(recipient_address, amount_to_send)
