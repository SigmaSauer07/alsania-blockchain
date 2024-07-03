class Shard:
    def __init__(self, shard_id, validators):
        self.shard_id = shard_id
        self.validators = validators
        self.transactions = []
    
    def add_transaction(self, transaction):
        self.transactions.append(transaction)