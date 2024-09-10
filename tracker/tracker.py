import os
import logging
from web3 import Web3
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from bson.decimal128 import Decimal128
from decimal import Decimal
# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(filename="tracker.log", level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

# Telegram Notification Setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_NOTIFICATIONS_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_NOTIFICATIONS_CHAT_ID")

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            raise Exception(f"Error in sending message: {response.text}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {str(e)}")

# Connect to Ethereum node using Alchemy RPC URL
alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
web3 = Web3(Web3.HTTPProvider(alchemy_url))

if web3.is_connected():
    logging.info("Connected to Ethereum node successfully!")
else:
    logging.error("Failed to connect to Ethereum node")

# Beacon Deposit Contract address
DEPOSIT_CONTRACT_ADDRESS = web3.to_checksum_address("0x00000000219ab540356cBB839Cbe05303d7705Fa")

# MongoDB setup (assuming you've set up MongoDB correctly)
from pymongo import MongoClient
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database("EthereumTracker")
deposit_collection = db.deposits

# Function to save deposit data to MongoDB
def save_deposit(deposit):
    try:
        # Convert Decimal values to Decimal128 (compatible with MongoDB)
        deposit['fee'] = Decimal128(deposit['fee'])
        deposit_collection.insert_one(deposit)
        logging.info(f"Deposit saved: {deposit}")
    except Exception as e:
        logging.error(f"Error saving deposit to MongoDB: {str(e)}")


# Main logic to track ETH deposits to the contract
def track_deposits(from_block):
    logging.info(f"Starting to track deposits from block {from_block}")
    latest_block = web3.eth.get_block_number()

    for block_number in range(from_block, latest_block + 1):
        block = web3.eth.get_block(block_number, full_transactions=True)
        block_timestamp = datetime.utcfromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # Iterate through the transactions in each block
        for tx in block.transactions:
            tx_details = web3.eth.get_transaction(tx)  # Fetch transaction details

            if tx_details.to and tx_details.to.lower() == DEPOSIT_CONTRACT_ADDRESS.lower():
                # Fetch transaction receipt
                receipt = web3.eth.get_transaction_receipt(tx_details.hash)

                # Extract deposit data (e.g., sender, amount, fee)
                deposit_data = {
                    'blockNumber': block_number,
                    'blockTimestamp': block_timestamp,
                    'fee': web3.from_wei(tx_details.gasPrice * receipt.gasUsed, 'ether'),
                    'hash': tx_details.hash.hex(),
                    'pubkey': tx_details.input  # Extract pubkey from input if needed
                }

                # Save deposit to database
                save_deposit(deposit_data)

                # Send Telegram notification
                message = f"New deposit detected:\nBlock: {block_number}\nHash: {tx_details.hash.hex()}\nAmount: {web3.from_wei(tx_details.value, 'ether')} ETH\nSender: {tx_details['from']}"
                send_telegram_message(message)
                
                logging.info(f"New deposit found in block {block_number}: {tx_details.hash.hex()}")

    logging.info("Deposit tracking completed.")

# Start tracking from the desired block
if __name__ == "__main__":
    try:
        track_deposits(int(os.getenv("ETH_BLOCK_FROM")))
    except Exception as e:
        logging.error(f"An error occurred during tracking: {str(e)}")
