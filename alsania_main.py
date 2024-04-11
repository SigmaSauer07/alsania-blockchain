from alsania_coin import AlsaniaCoin
from consensus import ProofOfStake, ByzantineFaultTolerance
from alsania_blockchain import AlsaniaBlockchain, Block, Node
from alsania_coin import ValidationFailedError

if __name__ == "__main__":
    # Initialize the AlsaniaCoin
    alsania_coin = AlsaniaCoin()

    # Initialize the blockchain with PoS consensus
    alsania_blockchain_pos = AlsaniaBlockchain(alsania_coin, ProofOfStake(alsania_coin))
    alsania_blockchain_pos.create_genesis_block()

    # Initialize the blockchain with BFT consensus
    alsania_blockchain_bft = AlsaniaBlockchain(alsania_coin, ByzantineFaultTolerance())
    alsania_blockchain_bft.create_genesis_block()

    # Initialize the node and peers for PoS blockchain
    alsania_blockchain_pos.add_node("localhost", 5000)
    alsania_blockchain_pos.add_peer("localhost", 5001)
    alsania_blockchain_pos.add_peer("localhost", 5002)

    # Initialize stakeholders for PoS blockchain
    alsania_blockchain_pos.add_stakeholder("0x1234567890abcdef")
    alsania_blockchain_pos.add_stakeholder("0xabcdef1234567890")

    # Initialize the node and peers for BFT blockchain
    alsania_blockchain_bft.add_node("localhost", 6000)
    alsania_blockchain_bft.add_peer("localhost", 6001)
    alsania_blockchain_bft.add_peer("localhost", 6002)

    # Create transactions for PoS blockchain
    transaction1_pos = alsania_blockchain_pos.create_transaction("0x1234567890abcdef", "0xabcdef1234567890", 100)
    transaction2_pos = alsania_blockchain_pos.create_transaction("0xabcdef1234567890", "0x1234567890abcdef", 50)

    # Create transactions for BFT blockchain
    transaction1_bft = alsania_blockchain_bft.create_transaction("0x1234567890abcdef", "0xabcdef1234567890", 100)
    transaction2_bft = alsania_blockchain_bft.create_transaction("0xabcdef1234567890", "0x1234567890abcdef", 50)

    # Validate transactions for PoS blockchain
    try:
        alsania_blockchain_pos.validate_block(Block(1, [transaction1_pos, transaction2_pos], alsania_blockchain_pos.chain[-1].hash))
    except ValidationFailedError as e:
        print(f"Validation failed (PoS): {e}")
    else:
        print("Transactions are valid (PoS)")

    # Validate transactions for BFT blockchain
    try:
        alsania_blockchain_bft.validate_block(Block(1, [transaction1_bft, transaction2_bft], alsania_blockchain_bft.chain[-1].hash))
    except ValidationFailedError as e:
        print(f"Validation failed (BFT): {e}")
    else:
        print("Transactions are valid (BFT)")

    # Mine a new block for PoS blockchain
    new_block_pos = Block(1, [transaction1_pos, transaction2_pos], alsania_blockchain_pos.chain[-1].hash)
    mined_block_pos = alsania_blockchain_pos.consensus.mine_block(new_block_pos)
    if mined_block_pos:
        alsania_blockchain_pos.add_block_to_chain(mined_block_pos)
        print("Block successfully mined (PoS)")
    else:
        print("Mining failed (PoS)")

    # Mine a new block for BFT blockchain
    new_block_bft = Block(1, [transaction1_bft, transaction2_bft], alsania_blockchain_bft.chain[-1].hash)
    mined_block_bft = alsania_blockchain_bft.consensus.mine_block(new_block_bft)
    if mined_block_bft:
        alsania_blockchain_bft.add_block_to_chain(mined_block_bft)
        print("Block successfully mined (BFT)")
    else:
        print("Mining failed (BFT)")
