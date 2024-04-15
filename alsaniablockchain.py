import secrets  # For secure random number generation
import string  # For string manipulation operations
import pickle  # For object serialization
import hashlib
import time
import json
import socket
import requests
from contextlib import suppress  # For handling exceptions gracefully
from collections import defaultdict
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from ipfshttpclient import connect  # Import IPFS client
from ethereum import utils, abi
from web3 import Web3
from eth_hash.auto import keccak
from eth_abi import encode_abi
from eth_utils import to_checksum_address
from typing import List
from typing import Optional
# Connect to IPFS daemon
ipfs_client = connect()
web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # Example RPC endpoint
# Define constants for security
PRIVATE_KEY_LENGTH = 64  # Length of a hexadecimal private key
VALID_CHARACTERS = string.hexdigits[:-6]  # Valid characters for a private key (0-9, a-f)
MAX_FUTURE_BLOCK_TIME = 60  # Maximum allowable future block time in seconds (e.g., 1 minute)

class BlockchainError(Exception):
    """Base class for errors related to the blockchain."""
    pass

class ValidationFailedError(BlockchainError):
    """Error raised when something goes wrong during validation of a block."""
    pass

class InsufficientBalanceError(BlockchainError):
    """Error raised when someone tries to spend more coins than they have."""
    pass

class InvalidTransactionError(BlockchainError):
    """Error raised when a transaction is not valid."""
    pass

class DoubleSpendingError(BlockchainError):
    """Error raised when someone tries to spend the same coins twice."""
    pass

class AtomicSwapError(BlockchainError):
    """Error raised when an atomic swap fails."""
    pass

class AlsaniaCoin:
    """A digital currency used within the Alsania blockchain."""
    def __init__(self):
        # Basic details about the currency
        self.name = "Alsania"
        self.symbol = "ALS"
        self.total_supply = 50000000
        # Define the smallest denomination called Embers
        self.embers_per_coin = 10 ** 18
        # Balances of users
        self.balances = defaultdict(int)
        # Locked balances, for special cases
        self.locked_balances = defaultdict(int)
        # Addresses of token holders
        self.token_holders = set()
        # Voting power of users
        self.voting_power = defaultdict(int)
        # Contract for governing the blockchain
        self.governance_contract = None
        
        # Features of the coin
        self.privacy_enabled = True
        self.smart_contract_integration = True
        self.staking_enabled = True
        
        # Staking details
        self.total_staked = 0
        self.transaction_fee = 1
        self.delegations = defaultdict(dict)  # Track stake delegations
        self.pending_transactions = []  # Track pending transactions

        # Gas fee parameters
        self.base_gas_fee = 1  # Initial base gas fee
        self.dynamic_gas_fee_multiplier = 1.0  # Multiplier to adjust gas fee dynamically
        
        # External Oracle for price data
        self.price_oracle = ExternalOracle()

        # KYC verified users
        self.kyc_verified_users = set()  # Initialize empty set for KYC verified users

        # Initialize balances with initial amount for a specific address
        initial_address = "initial_address_here"  # Replace with the desired address
        initial_amount = 1000000  # Initial amount of AlsaniaCoins
        self.balances[initial_address] = initial_amount
        self.token_holders.add(initial_address)

    def set_dynamic_gas_fee_multiplier(self, multiplier):
        """Set the multiplier for dynamic gas fee adjustment."""
        self.dynamic_gas_fee_multiplier = multiplier
        
    def calculate_gas_fee(self):
        """Calculate the current gas fee based on the dynamic multiplier."""
        return int(self.base_gas_fee * self.dynamic_gas_fee_multiplier)

    def distribute_reward(self, recipient, amount):
        """Give coins to a recipient as a reward."""
        self._transfer(None, recipient, amount)

    def collect_fee(self, recipient, amount):
        """Take coins from a recipient as a fee."""
        self._transfer(recipient, None, amount)

    def verify_kyc(self, user_id):
        """Verify KYC compliance for a user."""
        # Check if user's KYC information is verified
        return user_id in self.kyc_verified_users

    def perform_kyc_verification(self, user_id, identity_documents):
        """Perform KYC verification for a user."""
        # Placeholder implementation: Verify user's identity documents
        # Store KYC information securely
        self.kyc_verified_users.add(user_id)

    def transfer(self, sender, recipient, amount, private_key=None):
        """Transfer coins between two users."""
        if not self.verify_kyc(sender) or not self.verify_kyc(recipient):
            raise KYCVerificationError("KYC verification required for sender and recipient")
        if not isinstance(sender, str) or not isinstance(recipient, str) or not isinstance(amount, int):
            raise ValueError("Invalid input types")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balances[sender] < amount:
            raise InsufficientBalanceError("Insufficient balance")
        if recipient not in self.token_holders:
            raise ValueError("Recipient address is not a token holder")
        
        # Include transaction fee
        gas_fee = self.calculate_gas_fee()
        total_amount = amount + gas_fee

        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': gas_fee,
            'timestamp': time.time()
        }

        if private_key:
            signature = self.sign_transaction(transaction, private_key)
            transaction['signature'] = signature
        
        # Generate proof to keep transaction private
        zk_proof = generate_proof(sender, recipient, amount, private_key, self.balances[sender])
        transaction['zk_proof'] = zk_proof

        if self.is_double_spending(sender, amount):
            raise DoubleSpendingError("Double spending detected")

        self._transfer(sender, recipient, total_amount)

    def _transfer(self, sender, recipient, amount):
        """Update balances after transferring coins."""
        self.balances[sender] = safe_subtract(self.balances[sender], amount)  # Safe subtraction
        self.balances[recipient] = safe_add(self.balances[recipient], amount)  # Safe addition


    def sign_transaction(self, transaction, private_key):
        """Create a digital signature for a transaction."""
        serialized_tx = json.dumps(transaction, sort_keys=True).encode()
        signature = hashlib.sha256(serialized_tx + private_key.encode()).hexdigest()
        return signature

    def verify_transaction_signature(self, transaction):
        """Check if a transaction's signature is valid."""
        sender_public_key = self.get_public_key(transaction['sender'])
        signature = transaction['signature']
        transaction_copy = transaction.copy()
        del transaction_copy['signature']
        serialized_tx = json.dumps(transaction_copy, sort_keys=True).encode()
        expected_signature = hashlib.sha256(serialized_tx + sender_public_key.encode()).hexdigest()
        return signature == expected_signature
    
    def generate_private_key(self):
        """Generate a random private key."""
        return ''.join(secrets.choice(VALID_CHARACTERS) for _ in range(PRIVATE_KEY_LENGTH))

    def get_public_key(self, private_key):
        """Derive the public key from a private key."""
        # Placeholder implementation: This could be an actual cryptographic operation
        return hashlib.sha256(private_key.encode()).hexdigest()

    def is_double_spending(self, sender, amount):
        """Check if a transaction tries to spend the same coins twice."""
        # Check if the sender has already spent coins in previous transactions
        for transaction in self.pending_transactions:
            if transaction['sender'] == sender:
                if transaction['amount'] == amount:
                    return True
        return False
    
    def generate_proof(sender, recipient, amount, private_key, sender_balance):
        """Generate a zero-knowledge proof for a transaction."""
        # Placeholder implementation: This could involve complex cryptographic operations
        return "ProofPlaceholder"

    def deploy_contract(self, sender, contract_code, gas_limit):
        """Deploy a smart contract."""
        # Compile contract code (assuming you have compiled contract code)
        compiled_contract = web3.eth.contract(abi=contract_code['abi'], bytecode=contract_code['bytecode'])

        # Deploy contract
        tx_hash = compiled_contract.constructor().transact({'from': sender, 'gas': gas_limit})

        # Wait for the transaction to be mined
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        return tx_receipt.contractAddress

    def invoke_contract_method(self, sender, contract_address, method, args, gas_limit):
        """Call a method on a smart contract."""
        # Create contract instance
        contract_instance = web3.eth.contract(address=contract_address, abi=contract_abi)

        # Execute contract method
        tx_hash = contract_instance.functions[method](*args).transact({'from': sender, 'gas': gas_limit})

        # Wait for the transaction to be mined
        web3.eth.waitForTransactionReceipt(tx_hash)

    def handle_contract_event(self, event):
        """Handle an event emitted by a smart contract."""
        # Placeholder implementation: You can define your logic to handle contract events here
        print(f"Contract event handled: {event}")


    def delegate_stake(self, delegator, validator, amount):
        """Delegate stake from one user to another."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if validator not in self.stakeholders:
            raise ValueError("Validator is not a stakeholder")
        if self.balances[delegator] < amount:
            raise InsufficientBalanceError("Insufficient balance for delegation")
        # Update validator's total staked amount
        self.total_staked += amount
        self.balances[validator] += amount
        # Update delegation record
        try:
            self.delegations[validator][delegator] += amount
        except KeyError:
            # If the validator does not have any existing delegations, create a new entry
            self.delegations[validator] = {delegator: amount}
        except Exception as e:
            # Catch any unexpected exceptions and raise a BlockchainError
            raise BlockchainError(f"Stake delegation failed: {str(e)}")
    
    def revoke_delegation(self, delegator, validator):
        """Remove stake delegation from a validator."""
        if validator not in self.stakeholders:
            raise ValueError("Validator is not a stakeholder")
        try:
            amount = self.delegations[validator].pop(delegator, 0)
            if amount > 0:
                # Update validator's total staked amount
                self.total_staked -= amount
                self.balances[validator] -= amount
        except Exception as e:
            raise BlockchainError(f"Revoking stake delegation failed: {str(e)}")

    def get_delegated_stake(self, validator):
        """Get the total delegated stake for a validator."""
        return sum(self.delegations[validator].values())
        if validator not in self.stakeholders:
            raise ValueError("Validator is not a stakeholder")
        try:
            return sum(self.delegations[validator].values())
        except Exception as e:
            raise BlockchainError(f"Failed to get delegated stake: {str(e)}")

    def get_delegators(self, validator):
        """Get the list of delegators and their delegated stakes for a validator."""
        try:
            if validator not in self.stakeholders:
                raise ValueError("Validator is not a stakeholder")
            delegators = self.delegations.get(validator, {})
            return delegators.items()
        except Exception as e:
            raise BlockchainError(f"Failed to get delegators: {str(e)}")

    def get_public_key(self, address):
        """Get the public key associated with an address."""
        # Placeholder implementation
        return "PUBLIC_KEY"

    def get_nonce(self, address):
        """Get the nonce associated with an address."""
        # Assuming you have a dictionary mapping addresses to their nonces
        return self.nonces.get(address, 0)

    def get_price_of_crypto(self, crypto_symbol):
        """Fetch the current price of a cryptocurrency from an external API."""
        try:
            if crypto_symbol == "ALS":
                return 10  # Placeholder price for AlsaniaCoin
            elif crypto_symbol == "BTC":
                response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
                response.raise_for_status()  # Raise exception for HTTP errors
                return response.json()["bitcoin"]["usd"]
            elif crypto_symbol == "ETH":
                response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
                response.raise_for_status()  # Raise exception for HTTP errors
                return response.json()["ethereum"]["usd"]
            else:
                return None
        except requests.RequestException as e:
            print(f"Error occurred while fetching cryptocurrency price: {e}")
            return None
        except KeyError as e:
            print(f"Invalid response format while fetching cryptocurrency price: {e}")
            return None

    def log_event(self, event_name, **kwargs):
        """Emit an event from the smart contract."""
        event = {'name': event_name, 'data': kwargs}
        # Placeholder implementation: Print event data for demonstration
        print(f"Event: {event_name}, Data: {kwargs}")

class ProofOfStake:
    """A method for validating and adding blocks to the blockchain based on stake."""
    def __init__(self, coin):
        """Initialize the proof-of-stake mechanism with the digital currency."""
        self.coin = coin

    def validate_block(self, block):
        """Validate a block before adding it to the blockchain."""
        return block.hash.startswith('0')  # Example condition for validity

class ByzantineFaultTolerance:
    """A method for achieving consensus in the presence of Byzantine faults."""
    def __init__(self):
        pass

    def validate_block(self, block, blockchain):
        """Validate a block before adding it to the blockchain."""
        if not self.is_valid_block_structure(block):
            return False
        if block.timestamp > time.time() + MAX_FUTURE_BLOCK_TIME:
            return False
        previous_block = blockchain.get_block_by_hash(block.previous_hash)
        if previous_block is None:
            return False
        if not self.is_valid_nonce(block, blockchain.difficulty):
            return False
        for transaction in block.transactions:
            if not self.is_valid_transaction(transaction, blockchain):
                return False
        return True

    def is_valid_block_structure(self, block):
        """Check if the block structure is valid."""
        if not isinstance(block, Block):
            return False  # Block must be an instance of the Block class
        required_attributes = ['index', 'transactions', 'timestamp', 'previous_hash', 'nonce', 'hash']
        for attr in required_attributes:
            if not hasattr(block, attr):
                return False
        if not isinstance(block.index, int) or block.index < 0:
            return False  # Index must be a non-negative integer
        if not isinstance(block.transactions, list):
            return False  # Transactions must be a list
        if not isinstance(block.timestamp, float) or block.timestamp <= 0:
            return False  # Timestamp must be a positive floating-point number
        if not isinstance(block.previous_hash, str):
            return False  # Previous hash must be a string
        if not isinstance(block.nonce, int) or block.nonce < 0:
            return False  # Nonce must be a non-negative integer
        if not isinstance(block.hash, str):
            return False  # Hash must be a string
        return True  # If all checks pass, the block structure is considered valid

    def is_valid_nonce(self, block, difficulty):
        """Check if the nonce meets the difficulty target."""
        block_hash = block.hash_block()
        return block_hash.startswith('0' * difficulty)  # Example difficulty check

    def is_valid_transaction(self, transaction, blockchain):
        """Check if a transaction is valid."""
        if not isinstance(transaction, dict):
            return False  # Transaction must be a dictionary
        required_fields = ['sender', 'recipient', 'amount', 'timestamp']
        for field in required_fields:
            if field not in transaction:
                return False
        if not isinstance(transaction['sender'], str) or not isinstance(transaction['recipient'], str):
            return False  # Sender and recipient must be strings representing addresses
        if not isinstance(transaction['amount'], int) or transaction['amount'] <= 0:
            return False  # Amount must be a positive integer
        if not isinstance(transaction['timestamp'], float) or transaction['timestamp'] <= 0:
            return False  # Timestamp must be a positive floating-point number
        if 'signature' in transaction:
            if not self.coin.verify_transaction_signature(transaction):
                return False  # Signature verification failed
        if blockchain.is_double_spending(transaction['sender'], transaction['amount']):
            return False  # Double spending detected
        return True  # If all checks pass, the transaction is considered valid

class HybridConsensus:
    """A hybrid consensus mechanism combining PoS and BFT."""
    def __init__(self, pos_consensus, bft_consensus):
        self.pos_consensus = pos_consensus
        self.bft_consensus = bft_consensus

    def propose_block(self):
        """Propose a new block using the Proof of Stake consensus."""
        return self.pos_consensus.propose_block()

    def validate_block(self, block, blockchain):
        """Validate a block before adding it to the blockchain."""
        pos_valid = self.pos_consensus.validate_block(block, blockchain)
        bft_valid = self.bft_consensus.validate_block(block, blockchain)
        return pos_valid and bft_valid
    
    def confirm_block(self, block):
        """Confirm a block using BFT."""
        return self.bft_consensus.confirm_block(block)

    def fallback_to_pos(self):
        """Fallback to PoS in case of BFT failure."""
        print("Fallback to PoS mechanism")

    def propose_block(self):
        """Propose a new block using the Proof of Stake consensus."""
        return self.pos_consensus.propose_block()

    def confirm_block(self, block):
        """Confirm a block using BFT."""
        return self.bft_consensus.confirm_block(block)

    def fallback_to_pos(self):
        """Fallback to PoS in case of BFT failure."""
        # Placeholder implementation: You can define your fallback mechanism here
        print("Fallback to PoS mechanism")

class ExternalOracle:
    """External oracle for fetching real-world data."""
    def get_price(self, crypto_symbol):
        """Fetch the current price of a cryptocurrency."""
        if crypto_symbol == "ALS":
            return 10  # Placeholder price for AlsaniaCoin
        elif crypto_symbol == "BTC":
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            return response.json()["bitcoin"]["usd"]
        elif crypto_symbol == "ETH":
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
            return response.json()["ethereum"]["usd"]
        else:
            return None

class AlsaniaBlockchain:
    """A blockchain implementation based on the AlsaniaCoin."""
    def __init__(self, coin, hybrid_consensus):
        """Initialize the blockchain with a specific digital currency and consensus mechanism."""
        self.coin = coin
        self.hybrid_consensus = hybrid_consensus
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
        pos_valid = self.hybrid_consensus.pos_consensus.validate_block(block)
        bft_valid = self.hybrid_consensus.bft_consensus.validate_block(block)
        return pos_valid and bft_valid

    def add_block_to_chain(self, block):
        """Add a validated block to the blockchain."""
        if not self.hybrid_consensus.pos_consensus.validate_block(block):
            raise ValidationFailedError("PoS validation failed")
        if not self.hybrid_consensus.confirm_block(block):
            self.hybrid_consensus.fallback_to_pos()  # Fallback to PoS
            raise ValidationFailedError("BFT confirmation failed")
        if not self.validate_block(block):
            raise ValidationFailedError("Block validation failed")
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
        
    def deploy_contract(self, sender, contract_code, gas_limit):
        """Deploy a smart contract."""
        try:
            compiled_contract = web3.eth.contract(abi=contract_code['abi'], bytecode=contract_code['bytecode'])
            tx_hash = compiled_contract.constructor().transact({'from': sender, 'gas': gas_limit})
            tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
            contract_address = tx_receipt.contractAddress
            self.contracts[contract_code['name']] = contract_address
            return contract_address
        except ValueError as ve:
            raise BlockchainError(f"Failed to deploy contract: {ve}")
        except Exception as e:
            raise BlockchainError(f"Contract deployment failed: {str(e)}")

    def invoke_contract_method(self, sender, contract_address, method, args, gas_limit):
        """Call a method on a smart contract."""
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

    def get_contract_abi(self, contract_address):
        """Retrieve the ABI (Application Binary Interface) of a deployed contract."""
        if contract_address in self.contracts:
            return self.contracts[contract_address]['abi']
        else:
            raise ValueError("ABI not found for the contract address")

    def transfer_token(self, token_contract_name: str, sender: str, recipient: str, amount: int, private_key=None):
        """Transfer tokens between addresses."""
        if token_contract_name not in self.contracts:
            raise ValueError("Token contract not deployed")
        token_contract_address = self.contracts[token_contract_name]
        transfer_abi = [func for func in abi if func['name'] == 'transfer'][0]
        encoded_data = encode_abi([transfer_abi['inputs'][0]['type'], transfer_abi['inputs'][1]['type']], [to_checksum_address(recipient), amount])
        try:
            transaction = {
                'from': sender,
                'to': token_contract_address,
                'data': encoded_data
            }
            if private_key:
                signed_tx = web3.eth.account.signTransaction(transaction, private_key)
                tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            else:
                tx_hash = web3.eth.sendTransaction(transaction)
            return tx_hash
        except Exception as e:
            raise BlockchainError(f"Token transfer failed: {str(e)}")

    def get_token_balance(self, token_contract_name: str, address: str):
        """Query token balance."""
        if token_contract_name not in self.contracts:
            raise ValueError("Token contract not deployed")
        token_contract_address = self.contracts[token_contract_name]
        balance_of_abi = [func for func in abi if func['name'] == 'balanceOf'][0]
        encoded_data = encode_abi([balance_of_abi['inputs'][0]['type']], [to_checksum_address(address)])
        result = web3.eth.call({'to': token_contract_address, 'data': encoded_data})
        return int(result, 0)

    def handle_token_event(self, event):
        """Handle an event emitted by a token contract."""
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
        return keccak(block_header.encode()).hex()

class Node:
    """A node within the blockchain network."""
    def __init__(self, blockchain: AlsaniaBlockchain, address: str, host, port: int):
        """Initialize the node with its host address and port number."""
        self.blockchain = blockchain
        self.address = address
        self.host = host
        self.port = port
        self.private_key = self.blockchain.generate_private_key()
        self.public_key = self.blockchain.get_public_key(self.private_key)
    
    @staticmethod
    def generate_proof(sender, recipient, amount, private_key, sender_balance):
        """
        Generate a zero-knowledge proof for a transaction to maintain privacy.
        Args:
            sender (str): The sender's address.
            recipient (str): The recipient's address.
            amount (int): The amount of the transaction.
            private_key (str): The sender's private key in hexadecimal format.
            sender_balance (int): The sender's balance.
        Returns:
            bytes: The zero-knowledge proof.
        """
        try:
            private_key_int = int(private_key, 16)
        except ValueError:
            raise ValueError("Private key must be a hexadecimal string")
        if sender_balance < amount:
            raise ValueError("Sender balance is insufficient for the transaction amount")
        data = f"{sender}{recipient}{amount}{sender_balance}".encode()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(data)
        hashed_data = digest.finalize()
        sk = ec.derive_private_key(private_key_int, ec.SECP256R1(), default_backend())
        signature = sk.sign(hashed_data, ec.ECDSA(hashes.SHA256()))
        try:
            sk.public_key().verify(signature, hashed_data, ec.ECDSA(hashes.SHA256()))
        except InvalidSignature:
            raise ValueError("Invalid signature generated")

        return signature
