import json
import requests
from web3 import Web3
import gspread
import numpy as np
from google.oauth2.service_account import Credentials
import time
import pandas as pd
from datetime import datetime
from prophet.plot import plot_plotly, plot_components_plotly
from prophet import Prophet
import plotly.express as px
import streamlit as st

# User defined imports
from getdata import get_data as gd

# Get latest blocks:
c_a = '0x6c3ea9036406852006290770BEdFcAbA0e23A0e8'
df_new = gd(num_blocks=100, contract_address=c_a)