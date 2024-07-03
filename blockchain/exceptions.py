class AlsaniaCoinError(Exception):
    """Base class for exceptions in AlsaniaCoin."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InsufficientBalanceError(AlsaniaCoinError):
    """Raised when an account has insufficient balance for a transaction."""
    def __init__(self, message="Insufficient balance for transaction"):
        self.message = message
        super().__init__(self.message)


class InvalidTransactionError(AlsaniaCoinError):
    """Raised when a transaction is invalid."""
    def __init__(self, message="Invalid transaction"):
        self.message = message
        super().__init__(self.message)


class ValidationFailedError(AlsaniaCoinError):
    """Raised when validation of a block or transaction fails."""
    def __init__(self, message="Validation failed"):
        self.message = message
        super().__init__(self.message)


class BlockchainError(AlsaniaCoinError):
    """Raised for general blockchain errors."""
    def __init__(self, message="Blockchain error occurred"):
        self.message = message
        super().__init__(self.message)


class DoubleSpendingError(AlsaniaCoinError):
    """Raised when double spending is detected."""
    def __init__(self, message="Double spending detected"):
        self.message = message
        super().__init__(self.message)


class InvalidSignatureError(AlsaniaCoinError):
    """Raised when a signature is invalid."""
    def __init__(self, message="Invalid signature"):
        self.message = message
        super().__init__(self.message)


class ContractError(AlsaniaCoinError):
    """Raised for smart contract-related errors."""
    def __init__(self, message="Smart contract error occurred"):
        self.message = message
        super().__init__(self.message)


class OracleError(AlsaniaCoinError):
    """Raised for errors related to the external oracle."""
    def __init__(self, message="External oracle error occurred"):
        self.message = message
        super().__init__(self.message)

class AtomicSwapError(AlsaniaCoinError):
    """Raised for errors related to atomic swaps."""
    def __init__(self, message="Atomic swap error occurred"):
        self.message = message
        super().__init__(self.message)