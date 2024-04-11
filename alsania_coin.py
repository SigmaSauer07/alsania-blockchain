import time
import hashlib
import json
from collections import defaultdict
from external_oracle import ExternalOracle
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils

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
        self.decimals = 18  # Updated to reflect the smallest denomination called Embers
        self.total_supply = 50000000
        
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

        # Define the new smallest denomination
        self.embers_per_coin = 10 ** self.decimals

        # Gas fee parameters
        self.base_gas_fee = 1  # Initial base gas fee
        self.dynamic_gas_fee_multiplier = 1.0  # Multiplier to adjust gas fee dynamically
        
        # External Oracle for price data
        self.price_oracle = ExternalOracle()

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

    def transfer(self, sender, recipient, amount, private_key=None):
        """Transfer coins between two users."""
        if not isinstance(sender, str) or not isinstance(recipient, str) or not isinstance(amount, int):
            raise ValueError("Invalid input types")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balances[sender] < amount:
            raise InsufficientBalanceError("Insufficient balance")
        
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
        zk_proof = self.generate_proof(sender, recipient, amount, private_key, self.balances[sender])
        transaction['zk_proof'] = zk_proof

        if self.is_double_spending(sender, amount):
            raise DoubleSpendingError("Double spending detected")

        self._transfer(sender, recipient, total_amount)

    def _transfer(self, sender, recipient, amount):
        """Update balances after transferring coins."""
        self.balances[sender] -= amount
        self.balances[recipient] += amount

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
        return hashlib.sha256(serialized_tx + sender_public_key.encode()).hexdigest() == signature

    def is_double_spending(self, sender, amount):
        """Check if a transaction tries to spend the same coins twice."""
        # Check if the sender has already spent coins in previous transactions
        for transaction in self.pending_transactions:
            if transaction['sender'] == sender:
                if transaction['amount'] == amount:
                    return True
        return False

    def deploy_contract(self, sender, contract_code, gas_limit):
        """Deploy a smart contract."""
        # Placeholder implementation
        contract_address = "0x1234567890"  # Dummy address
        return contract_address

    def invoke_contract_method(self, sender, contract_address, method, args, gas_limit):
        """Call a method on a smart contract."""
        # Placeholder implementation
        pass

    def handle_contract_event(self, event):
        """Handle an event emitted by a smart contract."""
        # Placeholder implementation
        pass

    def delegate_stake(self, delegator, validator, amount):
        """Delegate stake from one user to another."""
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
        """Remove stake delegation from a validator."""
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

    def get_public_key(self, address):
        """Get the public key associated with an address."""
        # Placeholder implementation
        return "PUBLIC_KEY"

    def get_nonce(self, address):
        """Get the nonce associated with an address."""
        # Placeholder implementation
        return "NONCE"

    def get_price_of_crypto(self, crypto_symbol):
        """Fetch the current price of a cryptocurrency from an external API."""
        return self.price_oracle.get_price(crypto_symbol)

    def log_event(self, event_name, **kwargs):
        """Emit an event from the smart contract."""
        event = {'name': event_name, 'data': kwargs}
        # Placeholder implementation: Print event data for demonstration
        print(f"Event: {event_name}, Data: {kwargs}")

    def generate_proof(self, sender, recipient, amount, private_key, sender_balance):
        """
        Generate a zero-knowledge proof for a transaction.
        This is a placeholder function and needs to be replaced with an actual implementation.
        """
        # Placeholder implementation
        zk_proof = {
            'proof_type': 'placeholder',
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'sender_balance': sender_balance,
            'private_key': private_key  # This might not be necessary in a real implementation
        }
        return zk_proof
