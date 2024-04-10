import hashlib
import time
import random
import json
import socket
import threading
import pickle
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from ipfshttpclient import connect  # Import IPFS client
from ethereum import utils, abi
from web3 import Web3

# Connect to IPFS daemon
ipfs_client = connect()

class BlockchainError(Exception):
    """Base class for blockchain-related errors."""
    pass

class ValidationFailedError(BlockchainError):
    """Error raised when block validation fails."""
    pass

class InsufficientBalanceError(BlockchainError):
    """Error raised when there's insufficient balance for a transaction."""
    pass

class InvalidTransactionError(BlockchainError):
    """Error raised when a transaction is invalid."""
    pass

class DoubleSpendingError(BlockchainError):
    """Error raised when a double spending attempt is detected."""
    pass

class AlsaniaCoin:
    """Class representing the native coin of the Alsania blockchain."""
    def __init__(self):
        self.name = "Alsania"
        self.symbol = "ALS"
        self.decimals = 18
        self.total_supply = 50000000
        self.balances = defaultdict(int)
        self.locked_balances = defaultdict(int)
        self.token_holders = set()
        self.voting_power = defaultdict(int)
        self.governance_contract = None
        self.privacy_enabled = True
        self.smart_contract_integration = True
        self.staking_enabled = True
        self.total_staked = 0
        self.transaction_fee = 1  # Transaction fee for each transfer
        self.delegations = defaultdict(dict)  # Track stake delegations

    def distribute_reward(self, recipient, amount):
        """Distribute rewards to a recipient."""
        self._transfer(None, recipient, amount)

    def collect_fee(self, recipient, amount):
        """Collect fees from a recipient."""
        self._transfer(recipient, None, amount)

    def transfer(self, sender, recipient, amount, private_key=None):
        """Transfer coins between addresses."""
        if not isinstance(sender, str) or not isinstance(recipient, str) or not isinstance(amount, int):
            raise ValueError("Invalid input types")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balances[sender] < amount:
            raise InsufficientBalanceError("Insufficient balance")
        
        fee = self.transaction_fee  # Include transaction fee
        total_amount = amount + fee

        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,  # Add transaction fee to the transaction data
            'timestamp': time.time()
        }

        if private_key:
            signature = self.sign_transaction(transaction, private_key)
            transaction['signature'] = signature
        
        if self.is_double_spending(sender, amount):
            raise DoubleSpendingError("Double spending detected")

        self._transfer(sender, recipient, total_amount)

    def _transfer(self, sender, recipient, amount):
        """Internal method to transfer coins."""
        self.balances[sender] -= amount
        self.balances[recipient] += amount

    def sign_transaction(self, transaction, private_key):
        """Sign a transaction with the sender's private key."""
        serialized_tx = json.dumps(transaction, sort_keys=True).encode()
        signature = hashlib.sha256(serialized_tx + private_key.encode()).hexdigest()
        return signature

    def verify_transaction_signature(self, transaction):
        """Verify the signature of a transaction."""
        sender_public_key = self.get_public_key(transaction['sender'])
        signature = transaction['signature']
        transaction_copy = transaction.copy()
        del transaction_copy['signature']
        serialized_tx = json.dumps(transaction_copy, sort_keys=True).encode()
        return hashlib.sha256(serialized_tx + sender_public_key.encode()).hexdigest() == signature

    def is_double_spending(self, sender, amount):
        """Check if a transaction would result in double spending."""
        return False

    def deploy_contract(self, sender, contract_code, gas_limit):
        """Deploy a smart contract to the blockchain."""
        # Placeholder implementation for contract deployment
        contract_address = "0x1234567890"  # Dummy contract address
        return contract_address

    def invoke_contract_method(self, sender, contract_address, method, args, gas_limit):
        """Invoke a method on a deployed smart contract."""
        # Placeholder implementation for contract method invocation
        pass

    def handle_contract_event(self, event):
        """Handle an event emitted by a smart contract."""
        # Placeholder implementation for event handling
        pass

    def delegate_stake(self, delegator, validator, amount):
        """Delegate stake from a delegator to a validator."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balances[delegator] < amount:
            raise InsufficientBalanceError("Insufficient balance for delegation")
        
        # Update delegation record
        self.delegations[validator][delegator] += amount
        
        # Update validator's total staked amount
        self.total_staked += amount
        self.balances[validator] += amount

    def revoke_delegation(self, delegator, validator):
        """Revoke stake delegation from a validator."""
        amount = self.delegations[validator].pop(delegator, 0)
        if amount > 0:
            # Update validator's total staked amount
            self.total_staked -= amount
            self.balances[validator] -= amount

    def get_delegated_stake(self, validator):
        """Get the total delegated stake for a validator."""
        return sum(self.delegations[validator].values())

    def get_delegators(self, validator):
        """Get the list of delegators and their delegated stakes for a validator."""
        return self.delegations[validator].items()

class ProofOfWork:
    """Class representing the proof-of-work mechanism."""
    def __init__(self, difficulty):
        self.difficulty = difficulty

    def mine_block(self, block):
        """Perform proof-of-work for the given block."""
        while not self.is_valid_proof(block.hash, self.difficulty):
            block.nonce += 1
            block.hash = block.hash_block()
        return block

    def is_valid_proof(self, block_hash, difficulty):
        """Check if the block hash satisfies the proof-of-work difficulty target."""
        return block_hash.startswith('0' * difficulty)

class ProofOfStake:
    """Class representing the proof-of-stake mechanism."""
    def __init__(self, blockchain):
        self.blockchain = blockchain

    def mine_block(self, block):
        """Perform proof-of-stake for the given block."""
        # Simple PoS mechanism: Probability of mining is proportional to stake
        stake = self.blockchain.coin.balances[block.miner_address]
        if random.random() < (stake / self.blockchain.total_staked):
            return block
        return None

class PracticalByzantineFaultTolerance:
    """Class representing the Practical Byzantine Fault Tolerance (PBFT) consensus."""
    def __init__(self, blockchain):
        self.blockchain = blockchain

    def mine_block(self, block):
        """Perform PBFT consensus for the given block."""
        # Placeholder for PBFT implementation
        # In PBFT, a multi-round voting process among validators would take place
        return block  # For now, just return the block as is

class SmartContract:
    """Class representing a smart contract in the blockchain."""
    def __init__(self, code):
        self.code = code
        self.address = None

    def deploy(self, blockchain, sender, gas_limit):
        """Deploy the smart contract to the blockchain."""
        self.address = blockchain.coin.deploy_contract(sender, self.code, gas_limit)
        blockchain.contracts[self.address] = self

    def invoke_method(self, blockchain, sender, method, args, gas_limit):
        """Invoke a method on the smart contract."""
        blockchain.coin.invoke_contract_method(sender, self.address, method, args, gas_limit)

    def emit_event(self, event):
        """Emit an event from the smart contract."""
        pass  # Placeholder for emitting events

class EVMIntegration:
    """Class for integration with the Ethereum Virtual Machine (EVM)."""
    def __init__(self, rpc_url):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

    def execute_contract(self, sender, sender_private_key, bytecode, gas_limit):
        """Execute smart contract bytecode on the EVM."""
        nonce = self.w3.eth.getTransactionCount(sender)
        gas_price = self.w3.eth.gasPrice
        transaction = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': None,
            'data': bytecode,
        }
        signed_txn = self.w3.eth.account.signTransaction(transaction, sender_private_key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        return tx_hash.hex()

class AlsaniaBlockchain:
    """Class representing the Alsania blockchain."""
    def __init__(self, host, port, redundancy_factor, rpc_url, consensus_algorithm='ProofOfWork', difficulty=2):
        self.coin = AlsaniaCoin()
        self.chain = []
        self.load_chain_from_ipfs()  # Load blockchain from IPFS
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
        self.last_reward_halving_time = time.time()
        self.mining_reward = 10
        self.peers = set()  # Set to store peer addresses (host, port)
        self.broadcast_period = 60  # Period for broadcasting node information (in seconds)
        self.discovery_thread = threading.Thread(target=self.broadcast_node_info)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        self.evm_integration = EVMIntegration(rpc_url)
        
        # Initialize consensus algorithm
        if consensus_algorithm == 'ProofOfWork':
            self.consensus_mechanism = ProofOfWork(self.difficulty)
        elif consensus_algorithm == 'ProofOfStake':
            self.consensus_mechanism = ProofOfStake(self)
        elif consensus_algorithm == 'PracticalByzantineFaultTolerance':
            self.consensus_mechanism = PracticalByzantineFaultTolerance(self)
        else:
            raise ValueError("Invalid consensus algorithm")

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
        
        # Perform consensus algorithm to mine the block
        new_block = self.consensus_mechanism.mine_block(new_block)
        if new_block is None:
            return False
        
        self.pending_transactions = self.pending_transactions[max_transactions_per_block:]

        if time.time() - self.last_reward_halving_time >= 2 * 365 * 24 * 60 * 60: 
            self.mining_reward /= 2  
            self.last_reward_halving_time = time.time()  

        # Save blockchain data to IPFS
        self.save_chain_to_ipfs()

        return new_block

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
        for peer in self.peers:
            self.send_block_to_peer(peer[0], peer[1], block)

    def get_connected_peers(self):
        """Retrieve a list of connected peers."""
        return self.peers

    def send_block_to_peer(self, host, port, block):
        """Send a block to a peer in the network."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(pickle.dumps(block))
                print(f"Block broadcasted to peer {host}:{port}")
        except Exception as e:
            print(f"Failed to broadcast block to peer {host}:{port}: {e}")

    def get_contract_transaction_from_block(self, block):
        """Retrieve contract transactions from a block."""
        return block.contract_transactions

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
        sender = transaction['sender']
        recipient = transaction['recipient']
        amount = transaction['amount']

        # Check for double spending
        if self.is_double_spending(sender, amount):
            raise DoubleSpendingError("Double spending detected")

        # Verify transaction signature
        if not self.coin.verify_transaction_signature(transaction):
            raise InvalidTransactionError("Invalid transaction signature")

        # Check sender balance sufficiency
        if self.coin.balances[sender] < amount:
            raise InsufficientBalanceError("Insufficient balance")

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
        self.save_chain_to_ipfs()  # Save blockchain to IPFS  

    def load_chain_from_ipfs(self):
        """Load the blockchain from IPFS."""
        try:
            data_bytes = ipfs_client.cat('/blockchain_data/blockchain.json')
            chain_data = json.loads(data_bytes)
            for block_data in chain_data:
                block = Block(block_data['index'], block_data['timestamp'], block_data['transactions'], block_data['previous_hash'])
                block.hash = block_data['hash']  
                self.chain.append(block)
            print("Blockchain loaded from IPFS.")
        except Exception as e:
            print("Error loading blockchain from IPFS:", e)

    def save_chain_to_ipfs(self):
        """Save the blockchain to IPFS."""
        chain_data = []
        for block in self.chain:
            chain_data.append(block.__dict__)

        try:
            ipfs_client.write('/blockchain_data/blockchain.json', json.dumps(chain_data))
            print("Blockchain saved to IPFS.")
        except Exception as e:
            print("Error saving blockchain to IPFS:", e)

    def broadcast_node_info(self):
        """Periodically broadcast node information to discover peers."""
        while True:
            # Broadcast node information to peers
            self.broadcast_to_peers({'host': self.node.host, 'port': self.node.port})
            time.sleep(self.broadcast_period)

    def broadcast_to_peers(self, message):
        """Broadcast a message to all known peers."""
        for peer in self.peers:
            self.send_message(peer[0], peer[1], message)

    def handle_peer_broadcast(self, peer_info):
        """Handle broadcasted node information from peers."""
        self.peers.add((peer_info['host'], peer_info['port']))

    def connect_to_peers(self):
        """Connect to known peers."""
        for peer in self.peers:
            # Connect to peer and perform handshake
            pass

    def run(self):
        """Start the blockchain node."""
        self.node.start()
        self.connect_to_peers()
        # Other initialization code

class FullNode(AlsaniaBlockchain):
    """Class representing a full node in the blockchain network."""
    def __init__(self, host, port, redundancy_factor, rpc_url, consensus_algorithm='ProofOfWork', difficulty=2):
        super().__init__(host, port, redundancy_factor, rpc_url, consensus_algorithm, difficulty)

    def handle_client_request(self, client_socket):
        """Handle incoming client requests."""
        try:
            while True:
                message = client_socket.recv(4096)
                if not message:
                    break
                print(f"Received message from {client_socket.getpeername()}: {message.decode()}")
                # Process the received message here, including smart contract interactions
        except Exception as e:
            print(f"Error handling client request: {e}")
        finally:
            client_socket.close()

    def run_server(self):
        """Start listening for incoming connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.node.host, self.node.port))
            server_socket.listen()

            print(f"Full Node listening for incoming connections on {self.node.host}:{self.node.port}...")

            while True:
                client_socket, client_address = server_socket.accept()
                print(f"Connection established with {client_address}")
                client_handler = threading.Thread(target=self.handle_client_request, args=(client_socket,))
                client_handler.start()

class Block:
    """Class representing a block in the blockchain."""
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.hash_block()
        self.miner_address = None
        self.stake = None

    def hash_block(self):
        """Generate the hash of the block."""
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Node:
    """Class representing a network node."""
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        """Start the node."""
        pass  # Placeholder for node startup actions

if __name__ == "__main__":
    full_node = FullNode('localhost', 8888, 3, 'http://localhost:8545')
    full_node.run_server()
