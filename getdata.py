import streamlit as st
from web3 import Web3
from datetime import datetime
import json
import pandas as pd
from tqdm import tqdm

# Get json rpc
json_rpc = st.secrets['json_rpc']['rpc']

# Connecting to Google RPC via Web3
try:
    w3_eth = Web3(Web3.HTTPProvider(json_rpc))
    print("Successfully connected to google rpc: ",w3_eth.is_connected())
except Exception as e:
    print('Failed to connect to Ethereum Node, Error: ',e)


# Get data
def get_data(num_blocks: int, contract_address: str, start_blocks: int = 22224385)-> pd.DataFrame:
    """
    Gets PYUSD recent transactions from the Ethereum blockchain.
    Parameters:
        start_blocks (int): Starting block number
        num_blocks (int): Number of blocks to process
        contract_address (str): Contract address
    Returns: Dataframe containing most recent transactions
    """
    # Get signature for transfer events
    TRANSFER_EVENT_SIGNATURE = Web3.keccak(text="Transfer(address,address,uint256)").hex()

    # Logic for getting blocks:
    latest_block = w3_eth.eth.block_number

    # total blocks
    tt_blocks = start_blocks - latest_block

    # Check for overflow
    if num_blocks > tt_blocks:
        num_blocks = tt_blocks

    # End blocks
    end_blocks = start_blocks + num_blocks

    print("=================================================================")
    print(f"Processing blocks from {start_blocks} to {end_blocks}: Total block : {end_blocks-start_blocks}")
    print('==================================================================')
    print("Current Date: ",datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("==================================================================")

    # Empty list to store transactions
    transactions = []

    # Loop backwards through blocks
    for block_number in tqdm(range(end_blocks, start_blocks - 1, -1)):
        try:
            # Fetch block with full transactions and get the timestamp
            block = w3_eth.eth.get_block(block_number, full_transactions=True)

             # Unix timestamp of the block
            timestamp = block['timestamp']

            # Convert to human-readable format
            timestamp = datetime.fromtimestamp(timestamp)

            # Fetch all receipts for the block
            receipts = w3_eth.eth.get_block_receipts(block_number)

            # Pair transactions with their receipts
            for tx, receipt in zip(block["transactions"], receipts):
                for log in receipt["logs"]:
                    # Check if log is from the target contract and is a Transfer event
                    if (log["address"].lower() == contract_address.lower() and
                        log["topics"][0].hex() == TRANSFER_EVENT_SIGNATURE):
                        # Extract from and to addresses (last 20 bytes of 32-byte topics)
                        from_address = "0x" + log["topics"][1][-20:].hex()
                        to_address = "0x" + log["topics"][2][-20:].hex()

                        # Extract value from data (32-byte uint256)
                        value = int.from_bytes(log["data"], "big")
                        value = value / 10**6

                        # Calculate gas fees (in ETH)
                        gas_used = receipt["gasUsed"]
                        gas_price = receipt.get("effectiveGasPrice", tx["gasPrice"])
                        gas_fees = (gas_used * gas_price) / 1e18  # Convert wei to ETH

                        # Compile data including timestamp
                        transfer_data = {
                            "timestamp": str(timestamp),
                            "block_number": block_number,
                            "from_address": from_address,
                            "to_address": to_address,
                            "tx_hash": tx["hash"].hex(),
                            "amount": value,
                            "gas_fees_eth": gas_fees
                        }
                        # Append dictionary to transactions
                        transactions.append(transfer_data)
        except Exception as e:
            print(f"Error processing block {block_number}: {e}!!!")
            continue
    try:
        df = pd.DataFrame(transactions)
        print('\n Successfully created DataFrame')
        return df
    except Exception as e:
        print(f"Error creating dataframe: {e}")
        return pd.DataFrame()