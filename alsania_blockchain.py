import socket
import pickle
import time
import hashlib

class AlsaniaBlockchain:
    """A blockchain implementation based on the AlsaniaCoin."""
    def __init__(self, coin, consensus):
        """Initialize the blockchain with a specific digital currency and consensus mechanism."""
        self.coin = coin
        self.consensus = consensus
        self.chain = []
        self.pending_transactions = []
        self.node = None
        self.peers = []
        self.stakeholders = []
        self.contracts = {}

    def create_genesis_block(self):
        """Create the genesis block of the blockchain."""
        genesis_block = Block(0, [], "0")
        genesis_block.timestamp = time.time()
        genesis_block.hash = genesis_block.hash_block()
        self.chain.append(genesis_block)

    def add_node(self, host, port):
        """Add a node to the blockchain network."""
        self.node = Node(host, port)

    def add_peer(self, host, port):
        """Add a peer node to the blockchain network."""
        self.peers.append((host, port))

    def add_stakeholder(self, address):
        """Add a stakeholder to the blockchain network."""
        self.stakeholders.append(address)

    def create_transaction(self, sender, recipient, amount, private_key=None):
        """Create a new transaction to be added to the blockchain."""
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time()
        }
        if private_key:
            signature = self.coin.sign_transaction(transaction, private_key)
            transaction['signature'] = signature
        self.pending_transactions.append(transaction)
        return transaction

    def validate_block(self, block):
        """Validate a block before adding it to the blockchain."""
        return self.consensus.validate_block(block)

    def add_block_to_chain(self, block):
        """Add a validated block to the blockchain."""
        self.chain.append(block)

    def send_block_to_peer(self, host, port, block):
        """Send a block to a peer node."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(pickle.dumps(block))

    def receive_block_from_peer(self, conn):
        """Receive a block from a peer node."""
        with conn:
            data = conn.recv(4096)
            return pickle.loads(data)
        
class Block:
    """A block within the blockchain."""
    def __init__(self, index, transactions, previous_hash):
        """Initialize the block with its index, transactions, and the hash of the previous block."""
        self.index = index
        self.transactions = transactions
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.hash_block()

    def hash_block(self):
        """Calculate the hash of the block."""
        block_header = str(self.index) + str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(self.nonce)
        return hashlib.sha256(block_header.encode()).hexdigest()
    
class Node:
    """A node within the blockchain network."""
    def __init__(self, host, port):
        """Initialize the node with its host address and port number."""
        self.host = host
        self.port = port
