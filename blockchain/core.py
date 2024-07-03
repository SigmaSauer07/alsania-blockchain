import time
import json
import hashlib
import requests
import web3
import secrets

from collections import defaultdict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from blockchain.exceptions import InsufficientBalanceError, DoubleSpendingError, ValidationFailedError, BlockchainError, InvalidTransactionError
from blockchain.oracle import ExternalOracle
from blockchain.utils import safe_add, safe_subtract, VALID_CHARACTERS, PRIVATE_KEY_LENGTH, ERC20_BYTECODE, ERC20_ABI
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from blockchain.shard import Shard

class AlsaniaCoin:  #A digital currency used within the Alsania blockchain

    def __init__(self):
        self.name = "AlsaniaCoin"
        self.symbol = "ALSC"
        self.total_supply = 50000000
        self.embers_per_coin = 10 ** 18
        self.balances = defaultdict(int)
        self.locked_balances = defaultdict(int)
        self.token_holders = set()
        self.voting_power = defaultdict(int)
        self.governance_contract = None
        self.privacy_enabled = True
        self.smart_contract_integration = True
        self.staking_enabled = True
        self.total_staked = 0
        self.transaction_fee = 1
        self.delegations = defaultdict(dict)  # Track stake delegations
        self.pending_transactions = []  # Track pending transactions
        self.base_gas_fee = 1  # Initial base gas fee
        self.dynamic_gas_fee_multiplier = 1.0  # Multiplier to adjust gas fee dynamically
        self.price_oracle = ExternalOracle(1)
        self.shards = {}
        initial_address = "initial_address_here"  # Replace with the desired address
        initial_amount = 1000000  # Initial amount of AlsaniaCoins
        self.balances[initial_address] = initial_amount
        self.token_holders.add(initial_address)

    def set_dynamic_gas_fee_multiplier(self, multiplier):
        self.dynamic_gas_fee_multiplier = multiplier

    def calculate_gas_fee(self):
        return int(self.base_gas_fee * self.dynamic_gas_fee_multiplier)

    def distribute_reward(self, recipient, amount):
        self._transfer(None, recipient, amount)

    def collect_fee(self, recipient, amount):
        self._transfer(recipient, None, amount)

    def generate_proof(self, sender, recipient, amount, private_key, sender_balance):
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

    def transfer(self, sender, recipient, amount, private_key=None):  #Transfer coins between two users.
        if not isinstance(sender, str) or not isinstance(recipient, str) or not isinstance(amount, int):
            raise ValueError("Invalid input types")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balances[sender] < amount:
            raise InsufficientBalanceError("Insufficient balance")
        if recipient not in self.token_holders:
            raise ValueError("Recipient address is not a token holder")
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
            zk_proof = self.generate_proof(sender, recipient, amount, private_key, self.balances[sender])
            transaction['zk_proof'] = zk_proof
        if self.is_double_spending(sender, amount):
            raise DoubleSpendingError("Double spending detected")
        self._transfer(sender, recipient, total_amount)

    def _transfer(self, sender, recipient, amount):  #Perform the actual transfer of coins.
        self.balances[sender] = safe_subtract(self.balances[sender], amount)
        self.balances[recipient] = safe_add(self.balances[recipient], amount)

    def sign_transaction(self, transaction, private_key):  #Create a digital signature for a transaction.
        serialized_tx = json.dumps(transaction, sort_keys=True).encode()
        signature = hashlib.sha256(serialized_tx + private_key.encode()).hexdigest()
        return signature

    def verify_transaction_signature(self, transaction):  #Verify the digital signature of a transaction.
        signature = transaction.get('signature')
        if not signature:
            raise InvalidTransactionError("Transaction is not signed")
        sender = transaction['sender']
        expected_signature = self.sign_transaction(transaction, sender)
        if signature != expected_signature:
            raise InvalidTransactionError("Invalid transaction signature")

    def add_pending_transaction(self, transaction):  #Add a transaction to the list of pending transactions.
        self.pending_transactions.append(transaction)

    def process_pending_transactions(self):  #Process all pending transactions.
        for transaction in self.pending_transactions:
            try:
                self.verify_transaction_signature(transaction)
                sender = transaction['sender']
                recipient = transaction['recipient']
                amount = transaction['amount']
                gas_fee = transaction['fee']
                zk_proof = transaction.get('zk_proof')
                sender_balance = self.balances[sender]
                if zk_proof:
                    if not self.validate_proof(sender, recipient, amount, zk_proof, sender_balance):
                        raise ValidationFailedError("Zero-knowledge proof validation failed")
                self._transfer(sender, recipient, amount + gas_fee)
                self.pending_transactions.remove(transaction)
            except (InvalidTransactionError, ValidationFailedError):
                continue

    def validate_proof(self, sender, recipient, amount, zk_proof, sender_balance):
        data = f"{sender}{recipient}{amount}{sender_balance}".encode()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(data)
        hashed_data = digest.finalize()
        pk = ec.derive_public_key(int(sender, 16), ec.SECP256R1(), default_backend())
        try:
            pk.verify(zk_proof, hashed_data, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False

    def generate_private_key(self):  #Generate a random private key.
        return ''.join(secrets.choice(VALID_CHARACTERS) for _ in range(PRIVATE_KEY_LENGTH))

    def get_public_key(self, private_key):  #Get the public key from a private key.
        try:
            private_key_int = int(private_key, 16)
        except ValueError:
            raise ValueError("Private key must be a hexadecimal string")
        sk = ec.derive_private_key(private_key_int, ec.SECP256R1(), default_backend())
        public_key = sk.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_key_hex = public_key_bytes.hex()
        return public_key_hex

    def is_double_spending(self, sender, amount):  #Check for double spending.
        for transaction in self.pending_transactions:
            if transaction['sender'] == sender and transaction['amount'] == amount:
                return True
        return False

    def mint(self, recipient, amount):  #Mint new AlsaniaCoins and distribute them to the recipient.
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if recipient not in self.token_holders:
            raise ValueError("Recipient address is not a token holder")
        self.total_supply += amount
        self.balances[recipient] += amount
        self.token_holders.add(recipient)

    def deploy_contract(self, sender, contract_code, gas_limit):  #Deploy a smart contract.
        compiled_contract = web3.eth.contract(abi=contract_code['abi'], bytecode=contract_code['bytecode'])
        tx_hash = compiled_contract.constructor().transact({'from': sender, 'gas': gas_limit})
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt.contractAddress
    
    def create_token(self, name, symbol, decimals, initial_supply, deployer_address, gas_limit):
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.total_supply = initial_supply
        self.balances[deployer_address] = initial_supply
        try:
            compiled_contract = self.web3.eth.contract(abi=ERC20_ABI, bytecode=ERC20_BYTECODE)
            tx_hash = compiled_contract.constructor(name, symbol, initial_supply, decimals).transact({'from': deployer_address, 'gas': gas_limit})
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            return tx_receipt.contractAddress
        except Exception as e:
            raise BlockchainError(f"Failed to create token: {e}")

    def get_token_balance(self, token_contract_address, address):
        self.token_contract_address = web3.toChecksumAddress(token_contract_address)
        self.address = web3.toChecksumAddress(address)
        try:
            contract = self.web3.eth.contract(address=token_contract_address, abi=ERC20_ABI)
            balance = contract.functions.balanceOf(address).call()
            return balance
        except Exception as e:
            raise BlockchainError(f"Failed to get token balance: {e}")

    def propose_governance_change(self, proposer_address, proposal_description, gas_limit):
        try:
            if self.governance_contract is None:
                raise ValueError("Governance contract not deployed")
            tx_hash = self.governance_contract.functions.propose(proposal_description).transact({'from': proposer_address, 'gas': gas_limit})
            return tx_hash
        except Exception as e:
            raise BlockchainError(f"Failed to propose governance change: {e}")

    def vote_on_proposal(self, voter_address, proposal_id, vote, gas_limit):    
        try:
            if self.governance_contract is None:
                raise ValueError("Governance contract not deployed")
            tx_hash = self.governance_contract.functions.vote(proposal_id, vote).transact({'from': voter_address, 'gas': gas_limit})
            return tx_hash
        except Exception as e:
            raise BlockchainError(f"Failed to vote on proposal: {e}")

    def encrypt_transaction_data(self, transaction, public_key):
        f = Fernet(public_key.encode())
        encrypted_transaction = f.encrypt(json.dumps(transaction).encode())
        return encrypted_transaction.decode()
    
    def decrypt_transaction_data(self, encrypted_transaction, private_key):
        f = Fernet(private_key.encode())
        decrypted_transaction = f.decrypt(encrypted_transaction.encode()).decode()
        return json.loads(decrypted_transaction)
    
    def invoke_contract_method(self, sender, contract_address, method, args, gas_limit, contract_abi):  #Call a method on a smart contract.
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

    def handle_contract_event(self, event):  #Handle an event emitted by a smart contract.
        event_name = event['name']
        event_data = event['data']
        if event_name == 'Transfer':
            sender = event_data['sender']
            recipient = event_data['recipient']
            amount = event_data['amount']
            print(f"Transfer event: {amount} tokens transferred from {sender} to {recipient}")
        elif event_name == 'Approval':
            owner = event_data['owner']
            spender = event_data['spender']
            allowance = event_data['allowance']
            print(f"Approval event: Allowance of {allowance} tokens granted by {owner} to {spender}")
        else:
            print(f"Unhandled contract event: {event_name}, Data: {event_data}")

    def delegate_stake(self, delegator, validator, amount):  #Delegate stake from one user to another.
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if validator not in self.stakeholders:
            raise ValueError("Validator is not a stakeholder")
        if self.balances[delegator] < amount:
            raise InsufficientBalanceError("Insufficient balance for delegation")
        self.total_staked += amount
        self.balances[validator] += amount
        try:
            self.delegations[validator][delegator] += amount
        except KeyError:
            self.delegations[validator] = {delegator: amount}
        except Exception as e:
            raise BlockchainError(f"Stake delegation failed: {str(e)}")

    def revoke_delegation(self, delegator, validator):  #Remove stake delegation from a validator.
        if validator not in self.stakeholders:
            raise ValueError("Validator is not a stakeholder")
        try:
            amount = self.delegations[validator].pop(delegator, 0)
            if amount > 0:
                self.total_staked -= amount
                self.balances[validator] -= amount
        except Exception as e:
            raise BlockchainError(f"Revoking stake delegation failed: {str(e)}")

    def get_delegated_stake(self, validator):  #Get the total delegated stake for a validator.
        if validator not in self.stakeholders:
            raise ValueError("Validator is not a stakeholder")
        try:
            return sum(self.delegations[validator].values())
        except Exception as e:
            raise BlockchainError(f"Failed to get delegated stake: {str(e)}")

    def get_delegators(self, validator):  #Get the list of delegators and their delegated stakes for a validator.
        try:
            if validator not in self.stakeholders:
                raise ValueError("Validator is not a stakeholder")
            delegators = self.delegations.get(validator, {})
            return delegators.items()
        except Exception as e:
            raise BlockchainError(f"Failed to get delegators: {str(e)}")

    def get_nonce(self, address):  #Get the nonce associated with an address.
        return self.nonces.get(address, 0)

    def get_price_of_crypto(self, crypto_symbol):  #Fetch the current price of a cryptocurrency from an external API.
        try:
            if crypto_symbol == "ALSC":
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

    def log_event(self, contract_instance, event_name, **kwargs):  #Emit an event from the smart contract.
        try:
            event_data = {'name': event_name, 'data': kwargs}
            contract_event = contract_instance.events[event_name]
            tx_hash = contract_event().createFilter().deploy({'from': YOUR_ACCOUNT_ADDRESS}).transact()
            receipt = web3.eth.waitForTransactionReceipt(tx_hash)
            print(f"Event emitted: {event_name}, Data: {event_data}, Transaction Hash: {receipt.transactionHash.hex()}")
        except ValueError as ve:
            raise BlockchainError(f"Failed to emit event: {ve}")
        except Exception as e:
            raise BlockchainError(f"Error occurred while emitting event: {str(e)}")
        
    def add_transaction(self, transaction):
        self.transactions.append(transaction)
    
    def create_shard(self, shard_id, validators):
        self.shards[shard_id] = Shard(shard_id, validators)

    def get_shard(self, shard_id):
        return self.shards[shard_id]
    
    def send_transaction_to_shard(self, shard_id, transaction):
        self.shards[shard_id].add_transaction(transaction)

class PaLaConsensus:  #HPaLa consensus mechanism for the Alsania Blockchain.

    def __init__(self, validators, transaction_pool, chain):
        self.validators = validators
        self.transaction_pool = transaction_pool
        self.consensus_type = 'POS'
        self.block_proposal_timeout = 10
        self.consensus_threshold = 2/3
        self.coin = AlsaniaCoin()
        self.pending_blocks = defaultdict(list)
        self.last_reward_distribution_time = time.time()
        self.total_staked_amount = sum(v['staked_amount'] for v in validators)
        self.chain = chain

    def propose_block(self):  #Propose a new block using the POS consensus.
        block = {
            'hash': self.calculate_block_hash(),
            'transactions': self.transaction_pool.get_pending_transactions(),
            'timestamp': time.time(),
            'previous_hash': self.get_previous_block_hash(),
            'nonce': self.generate_nonce()
        }
        self.pending_blocks[block['hash']].append(block)
        if len(self.pending_blocks[block['hash']]) >= len(self.validators) * self.consensus_threshold:
            return block
        return None

    def validate_block(self, block, blockchain):
        if self._validate_block_pos(block, blockchain):
            if self._prepare_block_pos(block):
                return self._commit_block_pos(block)
        return False

    def confirm_block(self, block):  #Confirm a block using POS.
        if self.confirm_block_pos(block):
            self.pending_blocks['commit'].append(block)
            return True
        return False

    def _propose_block_pos(self):  #Propose a new block using the POS consensus.
        return {'hash': 'block_hash', 'data': 'block_data'}

    def _validate_block_pos(self, block, blockchain):  # Validate a block before adding it to the blockchain.
        if len(blockchain) > 0 and block['previous_hash'] != blockchain[-1].hash:
            return False
        if not block['hash'].startswith('0' * 4):
            return False
        for transaction in block['transactions']:
            if not self._verify_transaction_signature(transaction):
                return False
        return True

    def _prepare_block_pos(self, block):  #Prepare a block for commit using POS.
        prepare_count = len(self.pending_blocks[block['hash']])
        return prepare_count >= len(self.validators) * self.consensus_threshold

    def _commit_block_pos(self, block):  #Commit a block using POS.
        if block['hash'] == 'block_hash' and block['data'] == 'block_data':
            self.chain.append(block)
            return True
        return False

    def _apply_pos_consensus_rules(self, block):  #Apply consensus rules specific to proof of stake.
        if block['hash'] == 'block_hash' and block['data'] == 'block_data':
            return True
        return False

    def _confirm_block_pos(self, block):  #Confirm a block using POS.
        if block['hash'] == 'block_hash' and block['data'] == 'block_data':
            return True
        return False

    def _verify_transaction_signature(self, transaction):  #Verify the digital signature of a transaction.
        if 'signature' not in transaction:
            return False
        public_key = self.coin.get_public_key(transaction['sender'])
        signature = transaction['signature']
        transaction_copy = transaction.copy()
        del transaction_copy['signature']
        serialized_tx = json.dumps(transaction_copy, sort_keys=True).encode()
        try:
            public_key.verify(
                signature,
                serialized_tx,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            return False

    def distribute_staking_rewards(self): # Calculate the elapsed time since the last reward distribution
        current_time = time.time()
        elapsed_time = current_time - self.last_reward_distribution_time
        elapsed_years = elapsed_time / (365 * 24 * 3600)
        reward_per_validator = 0.05 * self.total_staked_amount * elapsed_years / len(self.validators)
        for validator in self.validators:
            reward_amount = validator['staked_amount'] * reward_per_validator
            self.coin.transfer('Staking Rewards', validator['address'], reward_amount)
        self.last_reward_distribution_time = current_time

    def mint_new_coins(self, validator, amount):
        if validator in self.validators:
            each_share = amount / len(self.validators)
            for v in self.validators:
                self.coin.mint(v, each_share)
            self.distribute_staking_rewards()
            return True
        else:
            return False

    def calculate_block_hash(self):
        block_header = json.dumps({
            'transactions': self.transaction_pool.get_pending_transactions(),
            'timestamp': time.time(),
            'previous_hash': self.get_previous_block_hash(),
            'nonce': self.generate_nonce()
        }, sort_keys=True).encode()
        return hashlib.sha256(block_header).hexdigest()

    def get_previous_block_hash(self):
        if len(self.chain) == 0:
            return "0"  # Genesis block hash
        return self.chain[-1].hash

    def generate_nonce(self):
        return int(time.time() * 1000)
    
class Block:  #A block within the blockchain.

    def __init__(self, index, transactions, previous_hash):  #Initialize the block with its index, transactions, and the hash of the previous block.
        self.index = index
        self.transactions = transactions
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.hash_block()
        self.merkle_root = self.calculate_merkle_root()

    def calculate_merkle_root(self):
        transaction_hashes = [hashlib.sha256(tx.encode()).digest() for tx in self.transactions]
        return self._calculate_merkle_root(transaction_hashes)

    def _calculate_merkle_root(self, data):
        print(f"Data: {data}")  # Debugging: Print data at each step
        if not data:  # Handle empty list
            return b''  # Return an empty byte string
        if len(data) == 1:
            return data[0]  # Base case: If only one item, it's the root
        new_data = []
        for i in range(0, len(data) - 1, 2):  # Pair and hash adjacent nodes
            combined_hash = hashlib.sha256(data[i] + data[i + 1]).digest()
            new_data.append(combined_hash)
        if len(data) % 2 == 1:  # If odd number of nodes, duplicate last node
            new_data.append(data[-1])
        return self._calculate_merkle_root(new_data)

    def hash_block(self):
        block_header = str(self.index) + str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(self.nonce)
        sha = hashlib.sha256()
        sha.update(block_header.encode('utf-8'))
        return sha.hexdigest()
    
class TransactionPool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def remove_transaction(self, transaction):
        self.transactions.remove(transaction)

    def get_pending_transactions(self):
        return self.transactions