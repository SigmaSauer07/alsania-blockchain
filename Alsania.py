import hashlib
import time
import random
import json
import os
import socket
import threading
from collections import defaultdict
from cryptography.fernet import Fernet

class BlockchainError(Exception):
    pass

class ValidationFailedError(BlockchainError):
    def __init__(self, message="Validation failed."):
        super().__init__(message)

class FileIOError(BlockchainError):
    def __init__(self, message="File I/O error occurred."):
        super().__init__(message)

class EncryptionError(BlockchainError):
    def __init__(self, message="Encryption error occurred."):
        super().__init__(message)

class DecryptionError(BlockchainError):
    def __init__(self, message="Decryption error occurred."):
        super().__init__(message)

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.stake = 0

    def hash_block(self):
        block_content = str(self.index) + str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(self.nonce) + str(self.stake)
        return hashlib.sha256(block_content.encode()).hexdigest()

class Node:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = []

    def start(self):
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()

    def run_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        message = ""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message += data.decode()
        print(f"Received message: {message}")
        # Process the received message
        # Example: Broadcast the message to other peers
        self.broadcast(message)
        client_socket.close()

    def add_peer(self, peer):
        self.peers.append(peer)

    def broadcast(self, message):
        for peer in self.peers:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect(peer)
                peer_socket.sendall(message.encode())
                peer_socket.close()
            except Exception as e:
                print(f"Error broadcasting message to {peer}: {e}")

class AlsaniaBlockchain:
    def __init__(self, host, port):
        self.chain = []
        self.load_chain_from_disk()  # Load blockchain data from disk during initialization
        self.create_genesis_block()
        self.difficulty = 2
        self.pending_transactions = []
        self.mining_reward = 10
        self.node = Node(host, port)
        self.node.start()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        genesis_block.stake = 100
        self.chain.append(genesis_block)

    def add_block(self, new_block):
        try:
            new_block.previous_hash = self.chain[-1].hash_block()
            new_block.index = len(self.chain)
            self.chain.append(new_block)
            self.save_chain_to_disk()  # Save blockchain data to disk after adding new block
        except IndexError as e:
            raise ValidationFailedError("Genesis block is missing. Cannot add new block.") from e

    def load_chain_from_disk(self, filename='alsania_chain.json'):
        try:
            with open(filename, 'r') as file:
                chain_data = json.load(file)
                for block_data in chain_data:
                    block = Block(
                        block_data['index'],
                        block_data['timestamp'],
                        block_data['transactions'],
                        block_data['previous_hash']
                    )
                    block.nonce = block_data['nonce']
                    block.stake = block_data['stake']
                    self.chain.append(block)
        except FileNotFoundError:
            print("Blockchain file not found. Creating new chain.")
        except Exception as e:
            print(f"Error loading blockchain data from disk: {e}")

    def save_chain_to_disk(self, filename='alsania_chain.json'):
        try:
            with open(filename, 'w') as file:
                chain_data = []
                for block in self.chain:
                    block_data = {
                        'index': block.index,
                        'timestamp': block.timestamp,
                        'transactions': block.transactions,
                        'previous_hash': block.previous_hash,
                        'nonce': block.nonce,
                        'stake': block.stake
                    }
                    chain_data.append(block_data)
                json.dump(chain_data, file, indent=4)
            print("Blockchain data saved to disk successfully.")
        except Exception as e:
            print(f"Error saving blockchain data to disk: {e}")

    # Other methods remain unchanged...

class Stakeholder:
    def __init__(self, name):
        self.name = name
        self.stake = 0

class Validator:
    def __init__(self, name):
        self.name = name

    def vote(self, block):
        return True

class Transaction:
    def __init__(self, sender, recipient, amount, fee):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee

# Example usage:
# Create and start the blockchain node
blockchain_node = AlsaniaBlockchain("localhost", 5000)

# Add peer nodes
blockchain_node.add_peer(("localhost", 5001))
blockchain_node.add_peer(("localhost", 5002))

# When a new block is added, broadcast it to peers
new_block = Block(index, timestamp, transactions, previous_hash)
blockchain_node.add_block(new_block)
blockchain_node.broadcast_block(new_block)
