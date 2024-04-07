import hashlib
import time
import random
import json
import os

from cryptography.fernet import Fernet

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

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
        self.difficulty = 2  # Initial difficulty
        self.pending_transactions = []
        self.mining_reward = 10  # Reward for mining a block
        self.validators = []  # List of validators for DPoS
        self.encryption_key = Fernet.generate_key()  # Generate encryption key
        self.sidechains = []  # List of sidechains
        self.data_directory = 'blockchain_data'

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        genesis_block.stake = 100  # Initial stake for the creator
        self.chain.append(genesis_block)

    def add_block(self, new_block):
        try:
            new_block.previous_hash = self.chain[-1].hash_block()
            new_block.index = len(self.chain)
            self.chain.append(new_block)
        except IndexError:
            print("Error: Genesis block is missing. Cannot add new block.")

    def proof_of_work(self, block):
        while block.hash_block()[:self.difficulty] != '0' * self.difficulty:
            block.nonce += 1
        return block.hash_block()

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
            self.difficulty = max(1, self.difficulty)  # Ensure difficulty is not less than 1

    def add_stakeholder(self, name):
        return Stakeholder(name)

    def validate_block(self, block, stakeholder):
        if block.stake > 0 and stakeholder.stake >= 10:
            return True
        return False

    def delegate_proof_of_stake(self, validators):
        if validators:
            self.validators = validators
        else:
            print("Error: No validators provided for DPoS.")

    def proof_of_stake_selection(self, block):
        if self.validators:
            if block.index % len(self.validators) == 0:
                return self.validators[block.index % len(self.validators)]
            else:
                return self.validators[block.index % len(self.validators) - 1]
        else:
            print("Error: No validators available for PoS selection.")
            return None

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def encrypt_data(self, data):
        try:
            cipher_suite = Fernet(self.encryption_key)
            return cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            print(f"Encryption Error: {e}")
            return None

    def decrypt_data(self, encrypted_data):
        try:
            cipher_suite = Fernet(self.encryption_key)
            return cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            print(f"Decryption Error: {e}")
            return None

    def create_sidechain(self):
        sidechain = Blockchain()
        sidechain.create_genesis_block()
        self.sidechains.append(sidechain)
        return sidechain

    def shard_transactions(self):
        # Implement sharding logic to distribute transactions among shards
        pass

    def save_chain_to_file(self):
        try:
            if not os.path.exists(self.data_directory):
                os.makedirs(self.data_directory)

            with open(os.path.join(self.data_directory, 'blockchain.json'), 'w') as file:
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
            print(f"Error saving blockchain to file: {e}")

    def load_chain_from_file(self):
        try:
            if os.path.exists(os.path.join(self.data_directory, 'blockchain.json')):
                with open(os.path.join(self.data_directory, 'blockchain.json'), 'r') as file:
                    chain_data = json.load(file)
                    for block_data in chain_data:
                        block = Block(block_data['index'], block_data['timestamp'], block_data['transactions'], block_data['previous_hash'])
                        block.nonce = block_data['nonce']
                        block.stake = block_data['stake']
                        self.chain.append(block)
        except Exception as e:
            print(f"Error loading blockchain from file: {e}")

class Stakeholder:
    def __init__(self, name):
        self.name = name
        self.stake = 0

class Validator:
    def __init__(self, name):
        self.name = name

    def vote(self, block):
        # Simulate voting process (e.g., by checking block validity)
        return True  # Simplified for demonstration purposes

class Transaction:
    def __init__(self, sender, recipient, amount, fee):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee

# Example usage:
if __name__ == "__main__":
    alsania_chain = Blockchain()

    # Add stakeholders
    alice = alsania_chain.add_stakeholder("Alice")
    bob = alsania_chain.add_stakeholder("Bob")
    
    # Delegate Proof of Stake
    alsania_chain.delegate_proof_of_stake([Validator("Validator1"), Validator("Validator2"), Validator("Validator3")])

    # Add transactions
    alsania_chain.add_transaction(Transaction("Alice", "Bob", 50, 5))
    alsania_chain.add_transaction(Transaction("Bob", "Alice", 20, 3))
    alsania_chain.add_transaction(Transaction("Alice", "Charlie", 30, 4))

    # Mine pending transactions using DPoS
    validator = alsania_chain.proof_of_stake_selection(alsania_chain.chain[-1])
    alsania_chain.mine_pending_transactions(validator)
