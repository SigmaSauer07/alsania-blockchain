import hashlib
import time
import random
import json
import os

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

class AlsaniaBlockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
        self.difficulty = 2  # Initial difficulty
        self.pending_transactions = []
        self.mining_reward = 10  # Initial reward for mining a block
        self.last_halving_timestamp = time.time()  # Timestamp of the last halving event
        self.validators = []  # List of validators for DPoS
        self.encryption_key = Fernet.generate_key()  # Generate encryption key
        self.sidechains = []  # List of sidechains
        self.data_directory = 'alsania_blockchain_data'
        self.smart_contracts = {}  # Dictionary to store deployed smart contracts
        self.decimals = 18  # Number of decimals for Alsania
        self.symbol = "Asi"  # Symbol for Alsania
        self.total_supply = 50000000 * 10**self.decimals  # Total supply of Alsania tokens
        self.stakeholders = []

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        genesis_block.stake = 100  # Initial stake for the creator
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
        # Implement sharding logic to distribute transactions among shards
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
            raise FileIOError("Error backing upblockchain data.") from e

    def verify_chain_integrity(self):
        try:
            for i in range(1, len(self.chain)):
                if not self.validate_block(self.chain[i]):
                    return False
            return True
        except Exception as e:
            raise BlockchainError("Blockchain data integrity check failed.") from e

    def halve_mining_reward(self):
        # Halve the mining reward
        self.mining_reward /= 2
        self.last_halving_timestamp = time.time()

    def adjust_mining_reward(self):
        current_time = time.time()
        time_since_last_halving = current_time - self.last_halving_timestamp
        # Check if 2 years (in seconds) have passed since the last halving
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

class Stakeholder:
    def __init__(self, name):
        self.name = name
        self.stake = 0

class Validator:
    def __init__(self, name):
        self.name = name

    def vote(self, block):
        # Simulate voting process (e.g., by checking block validity)
        return True

class Transaction:
    def __init__(self, sender, recipient, amount, fee):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee
