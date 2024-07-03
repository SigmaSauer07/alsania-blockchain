from alsaniawallet import AlsaniaWallet
import tkinter as tk
from tkinter import messagebox

class AlsaniaWalletGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AlsaniaCoin Wallet")

        # Initialize wallet with the node server URL
        self.node_url = "http://127.0.0.1:5000"  # Replace with your actual node URL
        self.wallet = AlsaniaWallet(self.node_url)

        # Create GUI elements
        self.label_balance = tk.Label(root, text="Balance: 0 ALSC")
        self.label_balance.pack(pady=10)

        self.label_address = tk.Label(root, text=f"Address: {self.wallet.address}")
        self.label_address.pack()

        self.label_send_to = tk.Label(root, text="Send ALSC to:")
        self.label_send_to.pack(pady=5)

        self.entry_send_to = tk.Entry(root, width=50)
        self.entry_send_to.pack()

        self.label_amount = tk.Label(root, text="Amount:")
        self.label_amount.pack(pady=5)

        self.entry_amount = tk.Entry(root, width=20)
        self.entry_amount.pack()

        self.button_get_balance = tk.Button(root, text="Refresh Balance", command=self.refresh_balance)
        self.button_get_balance.pack(pady=10)

        self.button_send = tk.Button(root, text="Send ALSC", command=self.send_transaction)
        self.button_send.pack(pady=10)

        # Bind Enter key to send transaction
        self.root.bind('<Return>', lambda event: self.send_transaction())

        # Display initial balance
        self.refresh_balance()

    def refresh_balance(self):
        self.wallet.get_balance()
        self.label_balance.config(text=f"Balance: {self.wallet.balance} ALSC")

    def send_transaction(self):
        to_address = self.entry_send_to.get()
        amount = float(self.entry_amount.get())

        if not to_address:
            messagebox.showerror("Error", "Please enter a recipient address.")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Please enter a valid amount greater than 0.")
            return

        try:
            self.wallet.send_transaction(to_address, amount)
            messagebox.showinfo("Success", "Transaction sent successfully.")
            self.refresh_balance()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send transaction: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AlsaniaWalletGUI(root)
    root.mainloop()
