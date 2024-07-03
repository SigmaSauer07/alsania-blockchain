import requests

class ExternalOracle:  #External oracle for fetching real-world data.

    def __init__(self, price):
        self.price = price

    def update_price(self, price):
        self.price = price

    def get_price(self, crypto_symbol):  #Fetch the current price of a cryptocurrency.
        if crypto_symbol == "ALSC":
            return 10  # Placeholder price for AlsaniaCoin
        elif crypto_symbol == "BTC":
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            return response.json()["bitcoin"]["usd"]
        elif crypto_symbol == "ETH":
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
            return response.json()["ethereum"]["usd"]
        else:
            return None