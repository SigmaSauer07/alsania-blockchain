from flask import Flask, request, jsonify
from blockchain.alsaniablockchain import AlsaniaBlockchain

app = Flask(__name__)
blockchain = AlsaniaBlockchain()

@app.route('/get_balance/<address>')
def get_balance(address):
    balance = blockchain.coin.balances.get(address, 0)
    return jsonify({"balance": balance})

@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    try:
        transaction = request.get_json()
        # Add transaction validation here
        # ...
        blockchain.create_transaction(transaction["from"], transaction["to"], transaction["amount"])
        return jsonify({"message": "Transaction sent successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400  # Return error message with 400 status code

if __name__ == '__main__':
    app.run(debug=True)