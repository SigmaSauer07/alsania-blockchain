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
        except IndexError as e:
            raise ValidationFailedError("Genesis block is missing. Cannot add new block.") from e

    def proof_of_work(self, block):
        while block.hash_block()[:self.difficulty] != '0' * self.difficulty:
            block.nonce += 1
            block_hash = block.hash_block()
        return block_hash

    def proof_of_stake(self, block, stakeholder):
        if stakeholder.stake >= 10:
            stakeholder.stake -= 10
            block.stake += 10

    def adjust_difficulty(self):
        if len(self.chain) > 1:
            avg_time = sum(self.chain[-5:].timestamp[i] - self.chain[-5:].timestamp[i - 1] for i in range(1, len(self.chain[-5:]))) / 5
            if avg_time < 10:
                self.difficulty += 1
            elif avg_time > 30:
                self.difficulty -= 1
            self.difficulty = max(1, self.difficulty)

    def add_stakeholder(self, name):
        stakeholder = Stakeholder(name)
        self.stakeholders.append(stakeholder)
        return stakeholder

    def validate_block(self, block):
        if block.stake > 0:
            return True
        return False

    def delegate_proof_of_stake(self, validators):
        if validators:
            self.validators = validators
        else:
            raise ValidationFailedError("No validators provided for DPoS.")

    def proof_of_stake_selection(self, block):
        if self.validators:
            stakeholder_index = block.index % len(self.validators)
            return self.validators[stakeholder_index]
        else:
            raise ValidationFailedError("No validators available for PoS selection.")

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def encrypt_data(self, data):
        try:
            cipher_suite = Fernet(self.encryption_key)
            return cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            raise EncryptionError("Encryption error occurred.") from e

    def decrypt_data(self, encrypted_data):
        try:
            cipher_suite = Fernet(self.encryption_key)
            return cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise DecryptionError("Decryption error occurred.") from e

    def create_sidechain(self):
        sidechain = AlsaniaBlockchain()
        sidechain.create_genesis_block()
        self.sidechains.append(sidechain)
        return sidechain

    def shard_transactions(self):
        pass

    def backup_chain(self, filename='alsania_backup.json'):
        try:
            if not os.path.exists(self.data_directory):
                os.makedirs(self.data_directory)

            with open(os.path.join(self.data_directory, filename), 'w') as file:
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
        except Exception as e:
            raise FileIOError("Error backing up blockchain data.") from e

    def verify_chain_integrity(self):
        try:
            for i in range(1, len(self.chain)):
                if not self.validate_block(self.chain[i]):
                    return False
            return True
        except Exception as e:
            raise BlockchainError("Blockchain data integrity check failed.") from e

    def halve_mining_reward(self):
        self.mining_reward /= 2
        self.last_halving_timestamp = time.time()

    def adjust_mining_reward(self):
        current_time = time.time()
        time_since_last_halving = current_time - self.last_halving_timestamp
        if time_since_last_halving >= 2 * 365 * 24 * 60 * 60:
            self.halve_mining_reward()

    def deploy_smart_contract(self, contract_name, contract_code):
        self.smart_contracts[contract_name] = contract_code

    def execute_smart_contract(self, contract_name, function_name, *args):
        if contract_name in self.smart_contracts:
            contract_code = self.smart_contracts[contract_name]
            if function_name in contract_code:
                function = contract_code[function_name]
                return function(*args)
            else:
                raise BlockchainError("Function not found in the smart contract.")
        else:
            raise BlockchainError("Smart contract not found.")

    def upgrade_contract(self, contract_name, new_code, gas_limit, gas_price):
        gas_fee = gas_limit * gas_price
        sender_balance = self.get_account_balance(contract_name)
        if sender_balance >= gas_fee:
            sender_balance -= gas_fee
            self.smart_contracts[contract_name] = new_code
            return "Smart contract upgraded successfully"
        else:
            raise BlockchainError("Insufficient funds for gas fee")

    def get_account_balance(self, account):
        return 10000  # Example balance for testing

    def add_replica(self, replica):
        self.replicas[replica.name] = replica

    def get_primary_replica(self):
        if not self.primary_replica:
            self.primary_replica = list(self.replicas.values())[0]
        return self.primary_replica

    def pre_prepare(self, block):
        primary_replica = self.get_primary_replica()
        for replica in self.replicas.values():
            if replica != primary_replica:
                replica.pre_prepare(block)

    def prepare(self, block):
        prepare_messages = defaultdict(int)
        for replica in self.replicas.values():
            prepare_messages[replica.name] = replica.prepare(block)
        return prepare_messages

    def commit(self, block):
        commit_messages = defaultdict(int)
        for replica in self.replicas.values():
            commit_messages[replica.name] = replica.commit(block)
        return commit_messages

    def process_block(self, block):
        primary_replica = self.get_primary_replica()
        self.pre_prepare(block)
        prepare_messages = self.prepare(block)
        commit_messages = self.commit(block)

        prepare_count = sum(prepare_messages.values())
        commit_count = sum(commit_messages.values())

        if prepare_count >= 2 * len(self.replicas) - 1 and commit_count >= 2 * len(self.replicas) - 1:
            primary_replica.add_block(block)

    def trigger_view_change(self):
        faulty_replicas = [replica for replica in self.replicas.values() if replica.detect_faulty()]
        if len(faulty_replicas) >= self.view_change_threshold:
            self.current_view += 1
            self.primary_replica = None

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
