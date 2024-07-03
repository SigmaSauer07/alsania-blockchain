import requests
import string

def safe_add(a, b):
    if a + b < a:
        raise OverflowError("Addition result out of range")
    return a + b

def safe_subtract(a, b):
    if a - b > a:
        raise OverflowError("Subtraction result out of range")
    return a - b

def connect_to_ipfs():
    try:
        response = requests.post('http://127.0.0.1:5001/api/v0/version')
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to IPFS daemon: {e}")
        return None
    
PRIVATE_KEY_LENGTH = 64  # Length of a hexadecimal private key

VALID_CHARACTERS = string.hexdigits[:-6]  # Valid characters for a private key (0-9, a-f)

MAX_FUTURE_BLOCK_TIME = 60  # Maximum allowable future block time in seconds (e.g., 1 minute)

ERC20_BYTECODE = '0x60d4b9'

ERC20_ABI = [
    'function name() view returns (string)',
    'function symbol() view returns (string)',
    'function decimals() view returns (uint8)'
]
