import streamlit as st
import requests
from datetime import datetime
import gspread
import numpy as np
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import plotly.express as px

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
    eth_timestamp_formated = datetime.fromtimestamp(int(eth_price[1])).strftime("%B %d, %Y %H:%M")

    # Return
    return token_supply_formated, eth_price_formated, eth_timestamp_formated


def make_line_plots(df: pd.DataFrame,
                    y_col: str,
                    title: str,
                    multi_vars: list,
                    var_name: str,
                    value_name: str,
                    y_axis_title: str,
                    multicols: bool=False) -> px.line:
    """
    Makes a plotly line plot
    Params:
        df: pandas dataframe of pyusd
        y_col: str,
        title: str,
        multi_vars: list,
        var_name: str,
        value_name: str,
        multicols: bool=False
    Returns:
        Plotly object
    """
    # reset index to get timestamp
    if multicols:
        # melt cols
        df_melted = df.melt(id_vars='timestamp',
                            value_vars=multi_vars,
                            var_name=var_name,
                            value_name=value_name)
        # Create fig
        fig = px.line(
            data_frame=df_melted,
            x='timestamp',
            color=var_name,
            y=value_name,
            markers=True,
            color_discrete_sequence=['#10EEEE', '#ff6347'],
            title=title
        )
        
        # Fig layout
        fig.update_layout(
            xaxis_title='Date'
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
    else:
        # Create fig
        fig = px.line(
            data_frame=df,
            x='date',
            y=y_col,
            markers=True,
            title=title
        )
        
        # Fig layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title=y_axis_title
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
    return fig

def make_bar(df: pd.DataFrame, x_col: str,
             y_col: str,
             title: str,
             y_axis_title: str,
             x_axis_title: str,
             mode='v') -> px.bar:
    """
    Makes a simple bar plot
    Params:
        df: pd.DataFrame
        x_col: str
        y_col: str,
        title: str,
        y_axis_title: str,
        x_axis_title: str
    Returns:
        Plotly object
    """
    # Create fig
    fig = px.bar(
        data_frame=df,
        x=x_col,
        y=y_col,
        title=title,
        text_auto=True,
        orientation=mode
    )
    
    fig.update_layout(
        xaxis_title = x_axis_title,
        yaxis_title=y_axis_title
    )
    fig.update_traces(
        textposition='outside'
    )
    fig.update_xaxes(type='category',showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def upload_sheets(df: pd.DataFrame):
    """
    Uploads whole dataframe to google sheets
    Params:
        df: Dataframe containing pyusd data
    """
    # Clean df timestamp for sheets
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp'] = df['timestamp'].dt.date
    df.rename(columns={'timestamp': 'date'}, inplace=True)
    df['date'] = df['date'].astype(str)
    df.sort_values(by='date', ascending=True, inplace=True)

    # Open the Google Sheet
    SHEET_NAME = "PYUSD SHEETS"

    # Open spreadsheet
    try:
        sheet = gc.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f'Error: {e}')
        st.error('Failed to open sheet')

    # Upload Data to spreadsheet
    try:
        sheet.update(range_name='A2', values=df.values.tolist(), raw=False)
        print(f'\n {SHEET_NAME} successfully update')
        # Toast
        st.toast(f'{SHEET_NAME} successfully uploaded')
        # Url
        st.markdown("""
            [PYUSD SHEETS](https://docs.google.com/spreadsheets/d/1V84W8vQ1s0nzORT0RhopTT2VtqhvLUKmnUvpxMzN7Sw/edit?usp=sharing)""")
    except Exception as e:
        print(f'Error: {e}')


def append_sheets(df: pd.DataFrame):
    """
    Appends most recent rows to google sheets
    Params:
        df: Dataframe containing pyusd data
    """
    # Open the Google Sheet
    SHEET_NAME = "PYUSD SHEETS"
    
    # Open spreadsheet
    try:
        sheet = gc.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f'Error: {e}')

    # Get last row in sheets
    last_row = sheet.row_count
    # Get latest block
    latest_block = int(sheet.cell(last_row, 2).value)

    # check if latest block matches
    if df['block_number'].max() == latest_block:
        st.warning('Sheet is up-to-date')
    elif df['block_number'].max() > latest_block:
        # Subset most recent data
        df = df[df['block_number'] > latest_block]    
        # Append future data to sheets
        try:
            sheet.append_rows(df.values.tolist(), value_input_option='USER_ENTERED')
            st.toast(f'\n {SHEET_NAME} successfully appended')
            st.markdown("""
            [PYUSD SHEETS](https://docs.google.com/spreadsheets/d/1V84W8vQ1s0nzORT0RhopTT2VtqhvLUKmnUvpxMzN7Sw/edit?usp=sharing)""")
        except Exception as e:
            print(f'Error: {e}')
