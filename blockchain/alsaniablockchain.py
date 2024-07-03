import time
import socket
import pickle
import string
import web3
from web3 import Web3
from blockchain.core import *
from blockchain.network_node import Node
from blockchain.exceptions import ValidationFailedError, BlockchainError, InsufficientBalanceError
from blockchain.utils import connect_to_ipfs
from blockchain.shard import Shard

class AlsaniaBlockchain:  # A blockchain implementation based on the AlsaniaCoin.

    def __init__(self):  # Initialize the blockchain with a specific digital currency and consensus mechanism.
        self.coin = AlsaniaCoin()
        self.nodes = set()
        self.chain = []
        self.pala_consensus = PaLaConsensus(validators=[], transaction_pool=TransactionPool(), chain=self.chain)  # Initialize with empty validators for now
        self.current_transactions = []
        self.pending_transactions = []
        self.peers = []
        self.stakeholders = []
        self.contracts = {}
        self.deployed_contracts = {}
        self.ipfs_version = connect_to_ipfs()
        if self.ipfs_version:
            print(f"Connected to IPFS daemon: {self.ipfs_version}")
        self.web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # Connect to local Ethereum node
        self.PRIVATE_KEY_LENGTH = 64  # Length of a hexadecimal private key
        self.VALID_CHARACTERS = string.hexdigits[:-6]  # Valid characters for a private key (0-9, a-f)
        self.MAX_FUTURE_BLOCK_TIME = 60  # Maximum allowable future block time in seconds (e.g., 1 minute)
        self.transaction_pool = TransactionPool()  # Initialize the transaction pool
        self.create_genesis_block()

    def create_genesis_block(self):  # Create the genesis block of the blockchain.
        genesis_block = Block(0, [], "0")
        genesis_block.timestamp = time.time()
        genesis_block.hash = genesis_block.hash_block()
        self.chain.append(genesis_block)

    def add_node(self, host, port):  # Add a node to the blockchain network.
        self.nodes.add((host, port))

    def add_peer(self, host, port):  # Add a peer node to the blockchain network.
        self.peers.append((host, port))

    def add_stakeholder(self, address):  # Add a stakeholder to the blockchain network.
        self.stakeholders.append(address)

    def create_transaction(self, sender, recipient, amount, private_key=None):  # Create a new transaction to be added to the blockchain.
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time()
        }
        if private_key:
            signature = self.coin.sign_transaction(transaction, private_key)
            transaction['signature'] = signature
        self.transaction_pool.add_transaction(transaction)  # Add transaction to the pool
        return transaction

    def validate_block(self, block):  # Validate a block before adding it to the blockchain.
        calculated_merkle_root = block.calculate_merkle_root()
        return (block.previous_hash == self.chain[-1].hash and
                block.hash.startswith('0') and
                block.merkle_root == calculated_merkle_root and
                self.pala_consensus.validate_block(block, self.chain))

    def reach_consensus(self):  # Reach consensus on adding a block to the chain.
        proposed_block = self.pala_consensus.propose_block()
        if proposed_block and self.pala_consensus.validate_block(proposed_block, self.chain):
            self.add_block_to_chain(proposed_block)
            for peer in self.peers:
                self.send_block_to_peer(peer[0], peer[1], proposed_block)
        else:
            print("Proposed block failed validation, consensus not reached")

    def add_block_to_chain(self, block):  # Add a validated block to the blockchain.
        if not self.pala_consensus.validate_block(block, self.chain):
            raise ValidationFailedError("Consensus validation failed")
        if not self.validate_block(block):
            raise ValidationFailedError("Block validation failed")
        if self.validate_block(block):
            self.chain.append(block)
            self.transaction_pool.remove_transactions(block.transactions)  # Remove transactions from the pool

    def send_block_to_peer(self, host, port, block):  # Send a block to a peer node.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(pickle.dumps(block))

    def receive_block_from_peer(self, conn):  # Receive a block from a peer node.
        with conn:
            data = conn.recv(4096)
            return pickle.loads(data)

    def handle_token_transfer(self, transaction):  # Handle AlsaniaCoin token transfer.
        sender = transaction['sender']
        recipient = transaction['recipient']
        amount = transaction['amount']
        self.coin.transfer_token(sender, recipient, amount)
        return f"Token transfer successful. Sender: {sender}, Recipient: {recipient}, Amount: {amount}"

    def deploy_contract(self, sender, contract_name, contract_code, gas_limit):  # Deploy a smart contract.
        if contract_name in self.deployed_contracts:
            raise ValueError(f"Contract with name '{contract_name}' already deployed")
        try:
            compiled_contract = web3.eth.contract(abi=contract_code['abi'], bytecode=contract_code['bytecode'])
            tx_hash = compiled_contract.constructor().transact({'from': sender, 'gas': gas_limit})
            tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
            contract_address = tx_receipt.contractAddress
            self.deployed_contracts[contract_name] = contract_address
            return contract_address
        except ValueError as ve:
            raise BlockchainError(f"Failed to deploy contract: {ve}")
        except Exception as e:
            raise BlockchainError(f"Contract deployment failed: {str(e)}")

    def invoke_contract_method(self, sender, contract_address, method, args, gas_limit):  # Call a method on a smart contract.
        try:
            if contract_address not in self.contracts.values():
                raise ValueError("Contract address not found")
            contract_abi = self.get_contract_abi(contract_address)
            contract_instance = web3.eth.contract(address=contract_address, abi=contract_abi)
            tx_hash = contract_instance.functions[method](*args).transact({'from': sender, 'gas': gas_limit})
            web3.eth.waitForTransactionReceipt(tx_hash)
        except ValueError as ve:
            raise BlockchainError(f"Failed to invoke contract method: {ve}")
        except KeyError:
            raise BlockchainError("Contract address not found in the contracts dictionary")
        except Exception as e:
            raise BlockchainError(f"Contract method invocation failed: {str(e)}")

    def get_contract_abi(self, contract_address):  # Retrieve the ABI of a deployed contract.
        if contract_address in self.contracts:
            return self.contracts[contract_address]['abi']
        else:
            raise ValueError("ABI not found for the contract address")

    def transfer_token(self, token_contract_name: str, sender: str, recipient: str, amount: int, private_key=None):
        if token_contract_name not in self.deployed_contracts:
            raise ValueError("Token contract not deployed")
        token_contract_address = self.deployed_contracts[token_contract_name]
        if self.coin.get_token_balance(token_contract_name, sender) < amount:
            raise InsufficientBalanceError("Insufficient balance")
        transaction = {
            'token_contract_name': token_contract_name,
            'from': sender,
            'to': token_contract_address,
            'value': amount
        }
        self.coin.create_transaction(sender, recipient, amount)
        if private_key:
            transaction['private_key'] = private_key
        self.send_transaction(transaction)
        return f"Token transfer successful. Sender: {sender}, Recipient: {recipient}, Amount: {amount}"

    def get_token_balance(self, token_contract_name: str, address: str):  # Query token balance.
        if token_contract_name not in self.contracts:
            raise ValueError("Token contract not deployed")
        token_contract_address = self.contracts[token_contract_name]
        balance = self.get_balance_from_blockchain(token_contract_address, address)
        return balance

    def handle_token_event(self, event):  # Handle an event emitted by a token contract.
        event_name = event['name']
        event_data = event['data']
        if event_name == 'Transfer':
            sender = event_data['from']
            recipient = event_data['to']
            amount = event_data['amount']
            print(f"Transfer event: {amount} tokens transferred from {sender} to {recipient}")
        elif event_name == 'Approval':
            owner = event_data['owner']
            spender = event_data['spender']
            allowance = event_data['allowance']
            print(f"Approval event: Allowance of {allowance} tokens granted by {owner} to {spender}")
        else:
            print(f"Unhandled token event: {event_name}, Data: {event_data}")

    def send_transaction(self, transaction):
        self.coin.add_pending_transaction(transaction)

    def get_balance_from_blockchain(self, token_contract_address, address):
        if token_contract_address in self.contracts:
            contract = self.web3.eth.contract(address=token_contract_address, abi=self.contracts[token_contract_address]['abi'])
            balance = contract.functions.balanceOf(address).call()
            return balance
        else:
            raise ValueError("Token contract not found in the contracts dictionary")

    def get_stakeholders(self):
        stakeholders = []
        for validator in self.pala_consensus.validators:
            stakeholders.append(validator['address'])
        return stakeholders
    
    def create_shard(self, shard_id, validators):
        self.shards[shard_id] = Shard(shard_id, validators)
        self.pala_consensus.validators.extend(validators)  # Add validators to consensus
        self.pala_consensus.total_staked_amount = sum(v['staked_amount'] for v in self.pala_consensus.validators)

    def get_shard(self, shard_id):
        return self.shards.get(shard_id)

    def send_transaction_to_shard(self, shard_id, transaction):
        shard = self.get_shard(shard_id)
        if shard:
            shard.add_transaction(transaction)
        else:
            raise ValueError(f"Shard with ID {shard_id} not found.")

    def process_shards(self):
        for self.shard_id, shard in self.shards.items():
            for transaction in shard.transactions:
                self.coin.add_pending_transaction(transaction)
            shard.transactions = []  # Clear transactions after processing
        self.coin.process_pending_transactions()

    def run(self):
        while True:
            # 1.  Process Pending Transactions in each Blockchain
            self.coin.process_pending_transactions()
            # 2.  Check for Consensus and Add Blocks 
            self.reach_consensus()
            # 3.  Handle Peer Communication (Exchange Blocks, etc.)
            for peer in self.peers:
                self.send_block_to_peer(peer[0], peer[1], self.chain[-1])  # Send latest block
            time.sleep(1)