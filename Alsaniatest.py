import hashlib
import time
import random
import json
import socket
import threading
import pickle
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)

class BlockchainError(Exception):
    """Base class for blockchain-related errors."""
    pass

class AlsaniaCoin:
    """Class representing the native coin of the Alsania blockchain."""
    def __init__(self):
        self.name = "Alsania"
        self.symbol = "ALS"
        self.decimals = 18
        self.max_supply = 50000000
        self.total_supply = 0
        self.balances = defaultdict(int)  
        self.locked_balances = defaultdict(int)  
        self.token_holders = set()  
        self.voting_power = defaultdict(int)  
        self.governance_contract = None  
        self.privacy_enabled = False  
        self.smart_contract_integration = False  
        self.staking_enabled = False  
        self.total_staked = 0  

    def distribute_reward(self, recipient, amount):
        """Distribute rewards to a recipient."""
        self._transfer(None, recipient, amount)

    def collect_fee(self, recipient, amount):
        """Collect fees from a recipient."""
        self._transfer(recipient, None, amount)

    def transfer(self, sender, recipient, amount):
        """Transfer coins between addresses."""
        if not isinstance(sender, str) or not isinstance(recipient, str) or not isinstance(amount, int):
            raise ValueError("Invalid input types")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balances[sender] < amount:
            raise ValueError("Insufficient balance")

        if self.is_double_spending(sender, amount):
            raise ValueError("Double spending detected")

        self._transfer(sender, recipient, amount)

    def _transfer(self, sender, recipient, amount):
        """Internal method to transfer coins."""
        self.balances[sender] -= amount
        self.balances[recipient] += amount

    def is_double_spending(self, sender, amount):
        """Check if a transaction would result in double spending."""
        return False

class AlsaniaBlockchain:
    """Class representing the Alsania blockchain."""
    def __init__(self, host, port, redundancy_factor, difficulty=2):
        self.coin = AlsaniaCoin()
        self.chain = []
        self.load_chain_from_disk()
        if not self.chain:
            self.create_genesis_block()
        self.difficulty = difficulty
        self.pending_transactions = []
        self.node = Node(host, port)
        self.node.start()
        self.stakeholders = []
        self.validators = []
        self.consensus_threshold = 0.5
        self.chain_replicas = defaultdict(list)
        self.redundancy_factor = redundancy_factor
        self.validated_blocks = set()
        self.contracts = {}
        self.consensus_mechanism = ProofOfWork(self.difficulty)
        self.last_reward_halving_time = time.time()  
        self.mining_reward = 10  

    def add_stakeholder(self, stakeholder):
        """Add a stakeholder to the blockchain."""
        self.stakeholders.append(stakeholder)

    def create_genesis_block(self):
        """Create the genesis block of the blockchain."""
        genesis_block = Block(0, time.time(), [], "0")
        genesis_block.stake = 100
        self.chain.append(genesis_block)

    def mine_block(self, max_transactions_per_block=10):
        """Mine a block with pending transactions."""
        if not self.pending_transactions:
            return False
        
        previous_block = self.chain[-1]
        selected_transactions = self.pending_transactions[:max_transactions_per_block]
        new_block = self._create_block(previous_block, selected_transactions)
        new_block = self.consensus_mechanism.mine_block(new_block)  
        self.broadcast_mined_block(new_block)
        self.pending_transactions = self.pending_transactions[max_transactions_per_block:]

        if time.time() - self.last_reward_halving_time >= 2 * 365 * 24 * 60 * 60: 
            self.mining_reward /= 2  
            self.last_reward_halving_time = time.time()  

        return new_block

    def mine_blocks_parallel(self, num_blocks):
        """Mine multiple blocks in parallel."""
        threads = []
        for _ in range(num_blocks):
            thread = threading.Thread(target=self.mine_block)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def _create_block(self, previous_block, transactions):
        """Create a new block."""
        block = Block(previous_block.index + 1, time.time(), transactions, previous_block.hash)
        block.stake = self.calculate_stake(block)
        return block

    def calculate_stake(self, block):
        """Calculate the stake for mining a block."""
        return 1

    def broadcast_mined_block(self, block):
        """Broadcast a mined block to the network."""
        for peer in self.get_connected_peers():
            self.send_block_to_peer(peer, block)

    def get_connected_peers(self):
        """Retrieve a list of connected peers."""
        return ['peer1', 'peer2', 'peer3']  

    def send_block_to_peer(self, peer, block):
        """Send a block to a peer in the network."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer['host'], peer['port']))
                s.sendall(pickle.dumps(block))
                print(f"Block broadcasted to peer {peer['host']}:{peer['port']}")
        except Exception as e:
            print(f"Failed to broadcast block to peer {peer['host']}:{peer['port']}: {e}")

    def validate_block(self, block):
        """Validate a block before adding it to the chain."""
        if block.index == 0:
            return True
        
        for tx in block.transactions:
            if not self.validate_transaction(tx):
                print("Transaction validation failed.")
                return False
        
        if block.hash != block.hash_block():
            print("Block integrity verification failed.")
            return False
        
        return True

    def validate_transaction(self, transaction):
        """Validate a transaction."""
        return True  

    def is_double_spending(self, sender, amount):
        """Check if a transaction would result in double spending."""
        return False  

    def add_block_to_chain(self, block):
        """Add a validated block to the blockchain."""
        if block.index in self.validated_blocks:
            raise ValidationFailedError("Block already added to chain")
        self.chain.append(block)
        self.validated_blocks.add(block.index)
        self.save_chain_to_disk()  

    def load_chain_from_disk(self):
        """Load the blockchain from disk."""
        try:
            with open('blockchain.json', 'r') as file:
                chain_data = json.load(file)
                for block_data in chain_data:
                    block = Block(block_data['index'], block_data['timestamp'], block_data['transactions'], block_data['previous_hash'])
                    block.hash = block_data['hash']  
                    self.chain.append(block)
            print("Blockchain loaded from disk.")
        except FileNotFoundError:
            print("No blockchain data found on disk.")

    def save_chain_to_disk(self):
        """Save the blockchain to disk."""
        chain_data = []
        for block in self.chain:
            chain_data.append(block.__dict__)

        with open('blockchain.json', 'w') as file:
            json.dump(chain_data, file, indent=4)
        
        print("Blockchain saved to disk.")

class Node:
    """Class representing a node in the blockchain network."""
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        """Start the node."""
        pass

    def stop(self):
        """Stop the node."""
        pass

class Block:
    """Class representing a block in the blockchain."""
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.hash_block()

    def hash_block(self):
        """Generate the hash of the block."""
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    balance = blockchain.coin.balances[address]
    return jsonify({'balance': balance})

@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    data = request.json
    sender = data['sender']
    recipient = data['recipient']
    amount = data['amount']
    try:
        blockchain.coin.transfer(sender, recipient, amount)
        return jsonify({'message': 'Transaction processed successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/mine_block', methods=['POST'])
def mine_block():
    new_block = blockchain.mine_block()
    if new_block:
        return jsonify({'message': 'Block mined successfully', 'block': new_block.__dict__}), 200
    else:
        return jsonify({'message': 'No pending transactions to mine', 'block': None}), 400

@app.route('/add_stakeholder', methods=['POST'])
def add_stakeholder():
    data = request.json
    stakeholder = data['stakeholder']
    blockchain.add_stakeholder(stakeholder)
    return jsonify({'message': 'Stakeholder added successfully'}), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return jsonify({'length': len(chain_data), 'chain': chain_data}), 200

if __name__ == "__main__":
    blockchain = AlsaniaBlockchain('localhost', 8888, redundancy_factor=3)
    app.run(debug=True)
