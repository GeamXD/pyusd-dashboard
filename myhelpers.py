import streamlit as st
import requests
from datetime import datetime
import gspread
import numpy as np
from google.oauth2.service_account import Credentials
import time
import pandas as pd
from datetime import datetime

# Define the scope and authorize the service account
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_info(st.secrets['gcp_service_account'], scopes=SCOPES)
# Auth
gc = gspread.authorize(CREDS)

# Get key for etherscan
etherscan_ky = st.secrets['etherscan_key']['api_key']

def get_token_supply(api_key, contract_address)-> str:
  """
    Gets contract address token supply
    Params:
        api_key: api key to access etherscan
        contract_address: the contract address of the token
    Returns:
        Token supply string
  """
  url = "https://api.etherscan.io/v2/api"
  params = {
      "module": "stats",
      "action": "tokensupply",
      "contractaddress": contract_address,
      "apikey": api_key,
      "chainid": 1
  }

  try:
      response = requests.get(url, params=params)
      response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
      data = response.json()

      if data["status"] == "1":
          return data["result"]  # Return token supply
      else:
          print(f"Error: {data['message']}")
          return None

  except requests.exceptions.RequestException as e:
      print(f"An error occurred: {e}")
      return None

def get_latest_eth_price(api_key: str)-> tuple:
    """
    Gets eth latest price and date
    Params: 
        api_key: auth key for etherscan
    Returns:
        Tuple: eth_price, eth_timestamp
    """
    url = "https://api.etherscan.io/v2/api"
    params = {
      "module": "stats",
      "action": "ethprice",
      "apikey": api_key,
      "chainid": 1
  }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "1":
            eth_data = data['result']
            eth_price = eth_data['ethusd']
            eth_timestamp = eth_data['ethusd_timestamp']
            return eth_price, eth_timestamp
        else:
            print(f"Error: {data['message']}")
            return ()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return ()

def get_and_format(contract_address: str = '0x6c3ea9036406852006290770BEdFcAbA0e23A0e8')-> tuple:
    """
    Gets data from etherscan and formats it
    Params:
        contract_address: the contract address of the token
    Returns:
        Tuple: 
    """
    # Get supply
    token_supply = get_token_supply(etherscan_ky, contract_address)
    # Get Price and Time
    eth_price = get_latest_eth_price(etherscan_ky)
    # Format token supply
    token_supply_formated = round(int(token_supply) / 10**12, 3) # Million
    # Format eth price
    eth_price_formated = round(float(eth_price[0]), 3)
    # Format eth price timestamp
    eth_timestamp_formated = datetime.fromtimestamp(int(eth_price[1])).strftime("%Y-%m-%d %H:%M:%S")

    # Return
    return token_supply_formated, eth_price_formated, eth_timestamp_formated

def upload_sheets(df: pd.DataFrame):
    # Clean df timestamp for sheets
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp'] = df['timestamp'].dt.date
    df.rename(columns={'timestamp': 'date'}, inplace=True)
    df['date'] = df['date'].astype(str)
    df.sort_values(by='date', inplace=True)

    # Open the Google Sheet
    SHEET_NAME = "PYUSD SHEETS"

    # Open spreadsheet
    try:
        sheet = gc.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f'Error: {e}')

    # Ensure the sheet has headers
    headers = ['date', 'block_number', 'from_address',
            'to_address', 'tx_hash', 'amount', 'gas_fees_eth', 'gas_fees_usd']
    if not ensure_headers(sheet, headers):
        raise ValueError("Sheet headers don't match expected format")

    # Upload Data to spreadsheet
    try:
        sheet.update(range_name='A2', values=df.values.tolist(), raw=False)
        print(f'\n {SHEET_NAME} successfully update')
    except Exception as e:
        print(f'Error: {e}')

def append_sheets(df):
    
    # Open the Google Sheet
    SHEET_NAME = "PYUSD SHEETS"
    
    # Open spreadsheet
    try:
        sheet = gc.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f'Error: {e}')

    # # Append future data to sheets
    # try:
    #     sheet.append_rows(df_new.values.tolist(), value_input_option='USER_ENTERED')
    #     print(f'\n {SHEET_NAME} successfully appended')
    # except Exception as e:
    #     print(f'Error: {e}')