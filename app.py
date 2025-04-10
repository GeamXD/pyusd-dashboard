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









# #
# # --- Feedback ---
# # Define the scope and authorize the service account
# SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# CREDS = Credentials.from_service_account_info(st.secrets['gcp_service_account'], scopes=SCOPES)
# gc = gspread.authorize(CREDS)


# # Open the Google Sheet
# SHEET_NAME = "Resume Feedback"

# # Open spreadsheet
# try:
#     sheet = gc.open(SHEET_NAME).sheet1
# except Exception as e:
#     print(f'Error: {e}')

# # Ensure the sheet has headers
# headers = ["Timestamp", "Name", "Email", "Message"]
# if not ensure_headers(sheet, headers):
#     raise ValueError("Sheet headers don't match expected format")

# st.write('\n')
# st.subheader(":material/contact_page: Contact Me")
# st.write('---')

# # Form container with custom styling
# with st.form("feedback_form", clear_on_submit=True):
#     # Input fields with placeholders and validation hints
#     name = st.text_input(
#         "Name *",
#         placeholder="Enter your full name",
#         help="Please enter your full name (minimum 2 characters)"
#     )
    
#     email = st.text_input(
#         "Email *",
#         placeholder="your.email@example.com",
#         help="Enter a valid email address"
#     )
    
#     message = st.text_area(
#         "Message *",
#         placeholder="Please share your thoughts...",
#         help="Minimum 10 characters",
#         height=150
#     )
    
#     # Submit button with custom styling
#     submitted = st.form_submit_button(
#         "Submit",
#         use_container_width=True,
#         type="primary"
#     )

# if submitted:
#     # Input validation
#     is_valid = True
#     validation_errors = []
    
#     # Name validation
#     if not name or len(name.strip()) < 2:
#         validation_errors.append("Please enter a valid name (minimum 2 characters)")
#         is_valid = False
    
#     # Email validation using regex
#     email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
#     if not email or not re.match(email_pattern, email):
#         validation_errors.append("Please enter a valid email address")
#         is_valid = False
    
#     # Message validation
#     if not message or len(message.strip()) < 10:
#         validation_errors.append("Please enter a message (minimum 10 characters)")
#         is_valid = False

#     if is_valid:
#         try:
#             with st.spinner("Submitting your message..."):
#                 timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 sheet.append_row([
#                     timestamp,
#                     name.strip(),
#                     email.lower().strip(),
#                     message.strip()
#                 ])
            
#             st.success("✨ Thank you for reaching out! I will get back to you shortly.")
#             st.balloons()
            
#         except Exception as e:
#             st.error("😟 We couldn't submit your message")
#             st.error(f"Error details: {str(e)}")
#             st.info("Please try again later later.")
#     else:
#         # Display all validation errors
#         for error in validation_errors:
#             st.warning(error)