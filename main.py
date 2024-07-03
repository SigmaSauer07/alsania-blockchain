from blockchain.alsaniablockchain import AlsaniaBlockchain
from blockchain.network_node import Node
import threading
import time

# Configuration
NODE_HOST = "localhost"
NODE_PORT = 5001  # Adjust as needed
NUM_NODES = 3 # Number of nodes in the network
IPFS_HOST = "127.0.0.1"  # IPFS daemon host
IPFS_PORT = 5001  # IPFS daemon port

def create_and_run_node(node_id):
    node = Node(
        f"node_{node_id}",
        NODE_HOST,
        NODE_PORT + node_id,  # Use the correct port for the node
        ipfs_host=IPFS_HOST,
        ipfs_port=IPFS_PORT
    )
    blockchain = AlsaniaBlockchain()
    blockchain.add_node(NODE_HOST, NODE_PORT + node_id)  # Pass the node's port
    blockchain.add_peer(NODE_HOST, NODE_PORT + node_id)
    blockchain.pala_consensus.validators = [
        {"address": node.address, "staked_amount": 1000} # Set initial stake for the node
    ]
    print(f"Node {node_id} initialized")
    blockchain.run()

if __name__ == "__main__":
    print("Starting Alsania Blockchain Network")
    # Start each node in a separate thread
    for i in range(NUM_NODES):
        thread = threading.Thread(target=create_and_run_node, args=(i,))
        thread.start()
    # Keep the main thread running to prevent the program from exiting
    while True:
        time.sleep(1)