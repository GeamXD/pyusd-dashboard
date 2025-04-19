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
from myhelpers import make_line_plots, make_bar
from timeforecast import prophet_forecast, plot_forecast

##  Set page config
st.set_page_config(
    page_title='PYUSD Dashboard',
    layout='wide',
    page_icon=':material/developer_board:',
    initial_sidebar_state='collapsed',
)

#### TITLE
# st.markdown(
#     "<h1 style='text-align: center;'><span style='color: Orange;'>PYUSD</span> Dashboard</h1>",
#     unsafe_allow_html=True)
st.markdown(
    """
    <h1 style='text-align: center;'>
        PYUSD Dashboard
    </h1>
    """,
    unsafe_allow_html=True
)
st.write('')

# Get supply data and eth price
ethersn_data = get_and_format()
tkn_supply = ethersn_data[0]
eth_price = ethersn_data[1]
eth_price_timestamp = ethersn_data[2]

# update data source
update_data_cont = st.columns(8)
with update_data_cont[0]:
    st.markdown(f'ETH:${eth_price:.2f} {eth_price_timestamp}',
                help='Shows latest ETH Price applied to data')
with update_data_cont[-1]:
    update_data = st.button(label='**Latest**', 
                            help='Gets the latest pyusd data',
                            on_click=get_kaggle_df,
                            use_container_width=True,
                            icon='🚨')

# Load dataset
@st.cache_data
def get_df() -> pd.DataFrame:
    """
    Loads the csv
    """
    return pd.read_csv('dataset/pyusd.csv')

# if update data is clicked
if update_data:
    df = get_df()
    st.toast('Updating to latest dataset')
else:
    df = get_df()

### Sidebar
with st.sidebar:
    # Filter
    st.markdown('## **Select Filters**')
    # Date
    filter_date = st.date_input('Select date',
                                help='Filters by Selected date to Recent')
    # Confirm date
    confirm_date = st.checkbox('Confirm date',
                               help='Uncheck to return to default')

    # Forecast duration
    forecast_dur = int(st.text_input('Set duration of forecast', value='14'))

    ### Upload to sheets
    st.markdown('**Upload to Google Sheets**')
    upld_sheets = st.button('Upload Complete',
                                help='Uploads complete data to sheets',
                                on_click=upload_sheets,
                                args=(df,))
    appnd_sheets = st.button('Append Existing',
                             help='Appends most recent to sheets when new data is present',
                             on_click=append_sheets,
                             args=(df,))
    st.markdown("""
            [PYUSD SHEETS](https://docs.google.com/spreadsheets/d/1V84W8vQ1s0nzORT0RhopTT2VtqhvLUKmnUvpxMzN7Sw/edit?usp=sharing)""")

if confirm_date:
    df['date_filt'] = pd.to_datetime(df['timestamp']).dt.date
    df = df[df['date_filt'] >= filter_date]

# Lastest date
lt_date = pd.to_datetime(df['timestamp'].tail(1).values).strftime('%B %d, %Y')[0]


# Get metrics dict
metrics = get_metrics(df)

### PYUSD Dashboard
metrics_cols = st.columns(5)
with metrics_cols[0]:
    ui.metric_card(title="Total Supply",
                   content=f"${tkn_supply}M",
                   description="PYUSD Total Supply (millions)", key="card1")

with metrics_cols[1]:
    ui.metric_card(title="Total Transactions",
                   content=f"{metrics['total_transaction_cnt']}K",
                   description=f"17 March to {lt_date}", key="card2")

with metrics_cols[2]:
    ui.metric_card(title="Total Transaction Volume",
                   content=f"${metrics['total_transaction_volume']}B",
                   description=f"17 March to {lt_date}", key="card3")

with metrics_cols[3]:
    ui.metric_card(title="Active Wallets",
                   content=f"{metrics['active_wallets']}K",
                   description=f"17 March to {lt_date}", key="card4")

with metrics_cols[4]:
    ui.metric_card(title="Total Revenue",
                   content=f"${metrics['total_revenue']}K",
                   description=f"17 March to {lt_date}", key="card5")

# Custom CSS to style tab buttons
st.markdown("""
    <style>
        button[data-baseweb="tab"] {
            font-size: 24px;
            margin: 0;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["### **Reach**", "### **Retention**", "### **Revenue**", "### **Swaps [dex]**", '### **Forecast**','### **Health Score**'])


# Reach
with tab1:
    # Top Senders
    # 3 Columns
    ts_cols = st.columns(3)
    ## - bar plot: total_amount sent
    tp_snd = metrics['top_senders']
    tp_snd['from_address'] = tp_snd['from_address'].astype(str)
    with ts_cols[0]:
        ts_ta_con = st.container(border=True)
        ts_ta_con.plotly_chart(make_bar(df=tp_snd,
            x_col='from_address',
            y_col='total_amount',
            title='Top Senders vs Amount Sent (PYUSD)',
            y_axis_title='Total Amount (PYUSD)',
            x_axis_title='Addresses',
            ), use_container_width=True)
    ## - bar plot: total_fees_usd
    with ts_cols[1]:
        ts_tf_con = st.container(border=True)
        ts_tf_con.plotly_chart(make_bar(df=tp_snd,
            x_col='from_address',
            y_col='total_fees_usd',
            title='Top Senders vs Gas Fees',
            y_axis_title='Gas Fees (USD)',
            x_axis_title='Addresses',
            ), use_container_width=True)
    ## - bar plot: total_transaction 
    with ts_cols[2]:
        ts_tc_con = st.container(border=True)
        ts_tc_con.plotly_chart(make_bar(df=tp_snd,
            x_col='from_address',
            y_col='transaction_count',
            title='Top Senders vs Transaction Count',
            y_axis_title='Count',
            x_axis_title='Addresses',
            ), use_container_width=True)
    # Top Receivers
    tr_cols = st.columns(3)
    tp_rc = metrics['top_receivers']
    tp_rc['to_address'] = tp_rc['to_address'].astype(str)
    with tr_cols[0]:
        tr_ta_con = st.container(border=True)
        tr_ta_con.plotly_chart(make_bar(df=tp_rc,
            x_col='to_address',
            y_col='total_amount',
            title='Top Receivers vs Amount Received (PYUSD)',
            y_axis_title='Total Amount (PYUSD)',
            x_axis_title='Addresses',
            ), use_container_width=True)
    ## - bar plot: total_fees_usd
    with tr_cols[1]:
        tr_tf_con = st.container(border=True)
        tr_tf_con.plotly_chart(make_bar(df=tp_rc,
            x_col='to_address',
            y_col='total_fees_usd',
            title='Top Receivers vs Gas Fees',
            y_axis_title='Gas Fees (USD)',
            x_axis_title='Addresses',
            ), use_container_width=True)
    ## - bar plot: total_transaction 
    with tr_cols[2]:
        tr_tc_con = st.container(border=True)
        tr_tc_con.plotly_chart(make_bar(df=tp_rc,
            x_col='to_address',
            y_col='transaction_count',
            title='Top Receivers vs Transaction Count',
            y_axis_title='Count',
            x_axis_title='Addresses',
            ), use_container_width=True)
    
    # Wallet activity
    # columns
    w_act = st.columns(3)
    with w_act[0]:
        w_ak_daily_con = st.container(border=True)
        w_ak_daily = metrics['active_wal_daily']
        w_ak_daily_con.plotly_chart(make_line_plots(
            df=w_ak_daily,
            y_col='active_wallet',
            title='Daily Wallet Activity',
            y_axis_title='Number of Wallets',
            multi_vars=[],
            var_name='',
            value_name='',
            multicols=False
        ))
    with w_act[1]:
        w_ak_wkly_con = st.container(border=True)
        w_ak_wkly = metrics['active_wal_wkly']
        w_ak_wkly_con.plotly_chart(make_line_plots(
            df=w_ak_wkly,
            y_col='active_wallet',
            title='Weekly Wallet Activity',
            y_axis_title='Number of Wallets',
            multi_vars=[],
            var_name='',
            value_name='',
            multicols=False
        ))
    with w_act[2]:
        w_ak_monthly_con = st.container(border=True)
        w_ak_monthly = metrics['active_wal_montly']
        w_ak_monthly_con.plotly_chart(make_line_plots(
            df=w_ak_monthly,
            y_col='active_wallet',
            title='Monthly Wallets Activity',
            y_axis_title='Number of Wallets',
            multi_vars=[],
            var_name='',
            value_name='',
            multicols=False
        ))
    dr_cols = st.columns(1)
    with dr_cols[0]:
        daily_reach = metrics['daily_reach']
        daily_rh_con = st.container(border=True)
        daily_rh_con.plotly_chart(make_line_plots(
        df=daily_reach,
        y_col='',
        title='Daily reach: Senders vs Receivers',
        y_axis_title='',
        multi_vars=["from_address", "to_address"],
        var_name='Address Type',
        value_name='Count',
        multicols=True
        ))

# Retention
with tab2:
    # Retention Table
    top_holders = metrics['top_holders']
    # Retention heatmap
    rent_hmp = metrics['reten_fig']
    # cols
    rent_col = st.columns(2)
    with rent_col[0]:
        # Top holders
        tp_hld = st.container(border=True)
        tp_hld.plotly_chart(make_bar(
            df=top_holders,
            x_col='address',
            y_col='balance_usd',
            title='Top holders',
            y_axis_title='Balances (USD)',
            x_axis_title='Address'
        ), use_container_width=True)
        
    with rent_col[1]:
        # heatmap
        rent_col_hmp = st.container(border=True)
        rent_col_hmp.plotly_chart(rent_hmp, use_container_width=True)

# Revenue
with tab3:
    # cols
    tv_col = st.columns(3)
    rv_fee_col = st.columns(3)
    blocks_cols = st.columns(3)
    
    # TV
    with tv_col[0]:
        # TV by hour
        tvhr_con = st.container(border=True)
        tvhr_con.plotly_chart(make_line_plots(
            df=metrics['transact_vol_by_hour'],
            y_col='amount',
            title='Transaction Volume Per Hour',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)    
    with tv_col[1]:
        # Daily TV
        tvd_con = st.container(border=True)
        tvd_con.plotly_chart(make_line_plots(
            df=metrics['transact_vol_by_day'],
            y_col='amount',
            title='Transaction Volume Per Day',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    with tv_col[2]:
        # Weekly TV
        tvwk_swaps_con = st.container(border=True)
        tvwk_swaps_con.plotly_chart(make_line_plots(
            df=metrics['transact_vol_by_week'],
            y_col='amount',
            title='Transaction Volume Per Week',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    # Average Fees
    with rv_fee_col[0]:
        # Average fees by hr
        avg_fee_hr_con = st.container(border=True)
        avg_fee_hr_con.plotly_chart(make_line_plots(
            df=metrics['hr_avg_fee'],
            y_col='gas_fees_usd',
            title='Hourly Gas Fees',
            y_axis_title='Gas Fees (USD)',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)    
    with rv_fee_col[1]:
        # Average fees by day
        wkly_swaps_con = st.container(border=True)
        wkly_swaps_con.plotly_chart(make_line_plots(
            df=metrics['day_avg_fee'],
            y_col='gas_fees_usd',
            title='Daily Gas Fees',
            y_axis_title='Gas Fees (USD)',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    with rv_fee_col[2]:
        # Average fees by week
        monthly_swaps_con = st.container(border=True)
        monthly_swaps_con.plotly_chart(make_line_plots(
            df=metrics['week_avg_fee'],
            y_col='gas_fees_usd',
            title='Weekly Gas Fees',
            y_axis_title='Gas Fees (USD)',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    # Block Average Fees
    with blocks_cols[0]:
        # Blocks Per Gas Fees (USD)
        blks_gf_con = st.container(border=True)
        blks_gf_con.plotly_chart(make_bar(
            df=metrics['block_avg_fee'],
            x_col='block_number',
            y_col='gas_fees_usd',
            title='Blocks Per Gas Fees (USD)',
            y_axis_title='Gas Fees (USD)',
            x_axis_title='Block Number',
            mode='v'
        ), use_container_width=True)    
    with blocks_cols[1]:
        # Blocks Per Amount (PYUSD)'
        bls_amnt_con = st.container(border=True)
        bls_amnt_con.plotly_chart(make_bar(
            df=metrics['block_avg_amt'],
            x_col='block_number',
            y_col='amount',
            title='Blocks Per Amount (PYUSD)',
            y_axis_title='Amount (PYUSD)',
            x_axis_title='Block Number',
            mode='v'
        ), use_container_width=True)
    with blocks_cols[2]:
        # Blocks Per Transaction Count
        blks_tc_con = st.container(border=True)
        blks_tc_con.plotly_chart(make_bar(
            df=metrics['block_trans_cnt'],
            x_col='block_number',
            y_col='tx_hash',
            title='Blocks Per Transaction Count',
            y_axis_title='Count',
            x_axis_title='Block Number',
            mode='v'
        ), use_container_width=True)


# Swaps
with tab4:
    # cols
    swaps_col = st.columns(3)
    swaps_dex_col = st.columns(3)
    swap_fig_col = st.columns(1)
    
    # Swap fig col
    with swap_fig_col[0]:
        swap_fig_con = st.container(border=True)
        swap_fig_con.plotly_chart(metrics['dex_swaps_figs'],
                                  use_container_width=True)
    # Swaps --daily, --weekly, --monthly
    with swaps_col[0]:
        # Daily Swaps
        daily_swaps_con = st.container(border=True)
        daily_swaps_con.plotly_chart(make_line_plots(
            df=metrics['daily_swaps'],
            y_col='transaction_count',
            title='Daily Dex Swaps',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)    
    with swaps_col[1]:
        # Weekly Swaps
        wkly_swaps_con = st.container(border=True)
        wkly_swaps_con.plotly_chart(make_line_plots(
            df=metrics['wkly_swaps'],
            y_col='transaction_count',
            title='Weekly Dex Swaps',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    with swaps_col[2]:
        # MOnthyl Swaps
        monthly_swaps_con = st.container(border=True)
        monthly_swaps_con.plotly_chart(make_line_plots(
            df=metrics['monthly_swaps'],
            y_col='transaction_count',
            title='Monthly Dex Swaps',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    #Dex Swaps --daily, --weekly, --monthly
    with swaps_dex_col[0]:
        # Daily Dex Swaps
        daily_swaps_con = st.container(border=True)
        daily_swaps_con.plotly_chart(make_line_plots(
            df=metrics['uniswapv3_daily_swaps'],
            y_col='transaction_count',
            title='Unisawpv3 Daily Swaps',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)    
    with swaps_dex_col[1]:
        # Weekly Dex Swaps
        wkly_swaps_con = st.container(border=True)
        wkly_swaps_con.plotly_chart(make_line_plots(
            df=metrics['uniswapv3_wkly_swaps'],
            y_col='transaction_count',
            title='Uniswapv3 Weekly Swaps',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    with swaps_dex_col[2]:
        # MOnthly Dex Swaps
        monthly_swaps_con = st.container(border=True)
        monthly_swaps_con.plotly_chart(make_line_plots(
            df=metrics['uniswapv3_monthly_swaps'],
            y_col='transaction_count',
            title='Uniswapv3 Monthly Swaps',
            y_axis_title='Count',
            multi_vars=[],
            value_name='',
            var_name=''
        ), use_container_width=True)
    
# Forecast
with tab5:
    fore_cast_btn = st.columns(2)
    with fore_cast_btn[0]:
        # Forecast button
        fore_cast_amnt = st.checkbox('Forecast (Amount  (PYUSD))')
    with fore_cast_btn[1]:
        # Forecast button
        fore_cast_gf = st.checkbox('Forecast (Gas Fee USD)')

    fore_cast_cols = st.columns(1)
    fore_cast_cols2 = st.columns(1)
    with fore_cast_cols[0]:

        if forecast_dur and fore_cast_amnt:
            # Forecast values - Amount
            amnt_model, amnt_forecast = prophet_forecast(df, column='amount', periods=forecast_dur)
            amnt_fig1, amnt_fig2 = plot_forecast(amnt_model, amnt_forecast, 'Amount (PYUSD)')
            fc_amnt_con = st.container(border=True)
            fc_amnt_con.plotly_chart(amnt_fig1)
            fc_amnt_con.plotly_chart(amnt_fig2)
    with fore_cast_cols2[0]:
        if fore_cast_gf and forecast_dur: 
            # Forecast values - gas fee usd
            gf_model, gf_forecast = prophet_forecast(df, column='gas_fees_usd', periods=forecast_dur)
            gf_fig1, gf_fig2 = plot_forecast(amnt_model, amnt_forecast, 'Gas Fees')
            fc_gf_con = st.container(border=True)
            fc_gf_con.plotly_chart(gf_fig1 )
            fc_gf_con.plotly_chart(gf_fig2)
 
# Health score
with tab6:
    # Health score label column and container
    health_score_col = st.columns(1)
    health_score_con = st.container(border=True)
    with health_score_col[0]:
        health_score_con.plotly_chart(make_bar(
            df=metrics['transaction_health_score_label'],
            x_col='transaction_health_score_label',
            y_col='count',
            title='Transaction Health Score',
            x_axis_title='Health Label',
            y_axis_title='Count',
            mode='v'
        ))

