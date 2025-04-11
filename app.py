import json
from web3 import Web3
import gspread
import numpy as np
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import streamlit_shadcn_ui as ui

# User defined imports
from get_kaggle_data import get_kaggle_df # tie to a condition or button
from getmetrics import get_metrics
from myhelpers import get_and_format
from myhelpers import upload_sheets, append_sheets

##  Set page config
st.set_page_config(
    page_title='PYUSD Dashboard',
    layout='wide',
    page_icon=':material/developer_board:',
    initial_sidebar_state='collapsed',
)

#### TITLE
st.markdown(
    "<h1 style='text-align: center;'><span style='color: blue;'>PYUSD</span> Dashboard</h1>",
    unsafe_allow_html=True)
st.write('')

# Get supply data and eth price
# ethersn_data = get_and_format()
ethersn_data = 'M k p'
tkn_supply = ethersn_data[0]
eth_price = ethersn_data[1]
eth_price_timestamp = ethersn_data[2]

# Get metrics dict


# update data source
update_data_cont = st.columns(8)
with update_data_cont[0]:
    st.markdown(f'ETH:${eth_price} {eth_price_timestamp}',
                help='Shows latest ETH Price applied to data')
with update_data_cont[-1]:
    update_data = st.button(label='**Latest**', 
                            help='Gets the latest pyusd data',
                            on_click=get_kaggle_df,
                            use_container_width=True,
                            icon='🚨')


### Sidebar
with st.sidebar:
    st.subheader('Navigation')
    st.write(':material/home: [Home](#pyusd-dashboard-interactive-app)')
    st.write(':material/contact_page: [Contact Me](#contact-page-contact-me)')
    # Filters
    st.subheader('Filter', divider=True)
    # Date
    filter_date = st.date_input('Select date')

### PYUSD Dashboard
metrics_cols = st.columns(5)
with metrics_cols[0]:
    ui.metric_card(title="Total Supply",
                   content=f"${tkn_supply} M",
                   description="PYUSD Total Supply (millions)", key="card1")
with metrics_cols[1]:
    ui.metric_card(title="Total Transactions",
                   content="567",
                   description="+10.5% from last month", key="card2")
with metrics_cols[2]:
    ui.metric_card(title="Total Transaction Volume",
                   content="$123,456.78",
                   description="+15.3% from last month", key="card3")
with metrics_cols[3]:
    ui.metric_card(title="Active Wallets",
                   content="$1,234.56",
                   description="+8.7% from last month", key="card4")
with metrics_cols[4]:
    ui.metric_card(title="Total Revenue",
                   content="$45,231.89",
                   description="+20.1% from last month", key="card5")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["**Reach**", "**Retention**", "**Revenue**", "**Swaps [dex]**", '**Health Score**'])


# Reach
with tab1:
    st.write('news')


# Retention
with tab2:
    st.write('reten')

# Revenue
with tab3:
    st.write('retention')

# Swaps
with tab4:
    st.write('swaps')

# Health score
with tab5:
    st.write('score')



#### Upload to sheets
# upld_sheets = st.button('Upload to Google Sheets',
#                         help='Uploads complete data to sheets',
#                         on_click='',
#                         args=(df,))
# appnd_sheets = st.button('Append latest to Google Sheets',
#                          help='Appends most recent to sheets',
#                          on_click='',
#                          args=(df,))


# # First row of visuals
# first_col = st.columns(3)
# with first_col[0]:
#     # Bar chart
#     st_slope_con = st.container(border=True)
#     st_slope_con.plotly_chart([], use_container_width=True)
#     # Pie chart
#     diesase_stat_con = st.container(border=True)
#     diesase_stat_con.plotly_chart([], use_container_width=True)
# with first_col[1]:
#     # Histogram
#     mx_hr = st.container(border=True)
#     mx_hr.plotly_chart([], use_container_width=True)
# with first_col[2]:
#     # bar chart
#     chst_con = st.container(border=True)
#     chst_con.plotly_chart([], use_container_width=True)
#     # bar chart
#     rest_con = st.container(border=True)
#     rest_con.plotly_chart([], use_container_width=True)

# # Second row of visuals
# second_col = st.columns(3)
# with second_col[0]:
#     # Bar chart
#     age_con = st.container(border=True)
#     age_con.plotly_chart([], use_container_width=True)
# with second_col[1]:
#     # bar chart
#     fbs_con = st.container(border=True)
#     fbs_con.plotly_chart([], use_container_width=True)
# with second_col[2]:
#     # bar chart
#     chol_con = st.container(border=True)
#     chol_con.plotly_chart([], use_container_width=True)


# # Final Row
# final_row = st.columns(2)
# with final_row[0]:
#     # Histogram
#     age_h_con = st.container(border=True)
#     age_h_con.plotly_chart([], use_container_width=True)
# with final_row[1]:
#     # Histogram
#     chol_hst_con = st.container(border=True)
#     chol_hst_con.plotly_chart([], use_container_width=True)








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
