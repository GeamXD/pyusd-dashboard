import pandas as pd
import numpy as np
import plotly.express as px
from myhelpers import get_and_format
import streamlit as st


@st.cache_data
def get_metrics(dataframe: pd.DataFrame)-> dict:
    """
    Gets dashboard metrics and values
    Params:
        dataframe: Dataframe containing the dataset
    Returns:
        Dictionary containing all dashboard metrics and values
    """
    # Eth price
    eth_price = get_and_format()[1]
    
    # Format amount
    dataframe['amount'] = round(dataframe['amount'], 3)
    # Add gas fee usd
    dataframe['gas_fees_usd'] = dataframe['gas_fees_eth'].apply(lambda x: round(x * float(eth_price), 3))

    # New dataframe and set time as index
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'])
    dataframe.set_index('timestamp', inplace=True)

    # Total transaction volume
    total_transaction_volume = round(dataframe['amount'].sum() / 10**9, 2)
    
    # Total transaction count
    total_transaction_cnt = round(dataframe['tx_hash'].nunique() / 10**3, 2)
    
    # # Unique senders and receivers
    # unique_senders = dataframe['from_address'].nunique()
    # unique_receivers = dataframe['to_address'].nunique()

    # Average transaction amount
    # average_transaction_amount = dataframe['amount'].mean()

    # Daily reach
    daily_reach = dataframe.resample('d')['from_address','to_address'].nunique().reset_index()

    # Total revenue
    total_revenue = round(dataframe['gas_fees_usd'].sum() / 10**3, 2)

    # Average revenue per transaction
    # average_revenue_per_transaction = dataframe['gas_fees_usd'].mean()

    # Active wallets
    active_wallets = dataframe[['from_address', 'to_address']].melt(value_name='wallet')['wallet'].nunique()
    active_wallets = round(active_wallets / 10**3, 2)

    # Active wallets -- daily -- weekly --monthly
    dataframe['date'] = dataframe.index.date
    active_wal = dataframe[['date', 'from_address', 'to_address']].melt(id_vars='date', value_name='active_wallet')
    active_wal['date'] = pd.to_datetime(active_wal['date'])
    active_wal.set_index('date', inplace=True)

    # -- daily
    active_wal_daily = active_wal.resample('D')['active_wallet'].nunique().to_frame().reset_index()

    # -- weekly
    active_wal_wkly = active_wal.resample('W')['active_wallet'].nunique().to_frame().reset_index()

    # # --- monthly
    active_wal_montly = active_wal.resample('ME')['active_wallet'].nunique().to_frame().reset_index()

    # Convert to datetime
    dataframe['date'] = pd.to_datetime(dataframe['date'])
    dataframe['week'] = dataframe['date'].dt.to_period('W').apply(lambda r: r.start_time)

    # Determine first seen week (cohort) for each wallet
    wallet_activity = pd.concat([
        dataframe[['from_address', 'week']].rename(columns={'from_address': 'wallet'}),
        dataframe[['to_address', 'week']].rename(columns={'to_address': 'wallet'})
    ])
    wallet_cohort = wallet_activity.groupby('wallet')['week'].min().reset_index()
    wallet_cohort.columns = ['wallet', 'cohort_week']

    # Merge to track activity over time
    wallet_activity = wallet_activity.merge(wallet_cohort, on='wallet')
    wallet_activity['weeks_since_cohort'] = ((wallet_activity['week'] -
                                            wallet_activity['cohort_week']) /
                                            np.timedelta64(1, 'W')).astype(int)

    # Retention Table
    retention = (
        wallet_activity.groupby(['cohort_week', 'weeks_since_cohort'])['wallet']
        .nunique()
        .unstack(fill_value=0)
    )

    # Retention Rate
    retention_rate = round(retention.divide(retention[0], axis=0) * 100, 2)

    # long format
    # retention_rate_reset = retention_rate.reset_index().melt(id_vars='cohort_week', var_name='Week', value_name='Retention Rate')

    # --- Plotly Heatmap ---
    reten_fig = px.imshow(
        retention_rate.values,
        labels=dict(x="Weeks Since First Seen", y="Cohort Week", color="Retention Rate"),
        x=retention_rate.columns,
        y=retention_rate.index.strftime('%B %d, %Y'),
        color_continuous_scale='Blues',
        aspect='auto',
        text_auto=True
    )

    reten_fig.update_layout(title="Wallet Retention Heatmap",
                      xaxis_title="Weeks Since First Seen",
                        yaxis_title="Cohort Week"
                        )    
    # Top holders
    balances_a = dataframe.groupby('from_address')['amount'].sum().reset_index(name='sent')
    balances_a.rename(columns={'from_address':'address'}, inplace=True)
    balances_a['received'] = 0
    balances_b = dataframe.groupby('to_address')['amount'].sum().reset_index(name='received')
    balances_b.rename(columns={'to_address':'address'}, inplace=True)
    balances_b['sent'] = 0

    # Join
    balances = pd.concat([balances_a, balances_b])
    balances['balance_usd'] = balances['received'] - balances['sent']
    balances = balances.groupby('address')['balance_usd'].sum().reset_index()
    top_holders = balances[balances['balance_usd'] > 0].sort_values(by='balance_usd', ascending=False).head(5)

    # Swap transactions
    dex_address = ['0x4a4d2410c3d4cfa8dd0d275bedefbd2f7b61ba2e', '0x13394005c1012e708fce1eb974f1130fdc73a5ce', '0xf313d711d71eb9a607b4a61a827a9e32a7846621']
    dex_names = ['uniswapv2', 'uniswapv3', 'uniswapv3']
    dex = dict(zip(dex_address, dex_names))
    swap_transactions = dataframe[dataframe['to_address'].isin(dex_address)]
    swap_transactions['dex'] = swap_transactions['to_address'].map(dex)

    # Swap pie chart
    swap_fig = px.pie(
            data_frame=swap_transactions,
            names='dex',
            hole=.6,
            title='Dex Swaps',
            color_discrete_sequence=['#10EEEE', '#ff6347']
            )

    # Daily swap transactions
    daily_swaps = swap_transactions.resample('D').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()
    daily_swaps.rename(columns={'timestamp':'date'}, inplace=True)
    

    # weekly swap transactions
    wkly_swaps = swap_transactions.resample('W').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()
    wkly_swaps.rename(columns={'timestamp':'date'}, inplace=True)

    # monthly swap transactions
    monthly_swaps = swap_transactions.resample('ME').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()
    monthly_swaps.rename(columns={'timestamp':'date'}, inplace=True)
    

    # By dex -- uniswapv3
    mask = swap_transactions['dex'] == 'uniswapv3'
    uniswapv3_swaps = swap_transactions[mask]

    # Daily swap transactions
    uniswapv3_daily_swaps = uniswapv3_swaps.resample('D').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()
    uniswapv3_daily_swaps.rename(columns={'timestamp':'date'}, inplace=True)

    # weekly swap transactions
    uniswapv3_wkly_swaps = uniswapv3_swaps.resample('W').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()
    uniswapv3_wkly_swaps.rename(columns={'timestamp':'date'}, inplace=True)

    # monthly swap transactions
    uniswapv3_monthly_swaps = uniswapv3_swaps.resample('ME').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()
    uniswapv3_monthly_swaps.rename(columns={'timestamp':'date'}, inplace=True)
    
    # # By dex -- uniswapv3
    # mask2 = swap_transactions['dex'] == 'uniswapv2'
    # uniswapv2_swaps = swap_transactions[mask2]

    # # Daily swap transactions
    # uniswapv2_daily_swaps = uniswapv2_swaps.resample('D').agg(
    #     total_volume=('amount', 'sum'),
    #     average_volume=('amount', 'mean'),
    #     transaction_count=('tx_hash', 'count'),
    #     total_fees=('gas_fees_usd', 'sum'),
    #     average_fees=('gas_fees_usd', 'mean')).reset_index()

    # # weekly swap transactions
    # uniswapv2_wkly_swaps = uniswapv2_swaps.resample('W').agg(
    #     total_volume=('amount', 'sum'),
    #     average_volume=('amount', 'mean'),
    #     transaction_count=('tx_hash', 'count'),
    #     total_fees=('gas_fees_usd', 'sum'),
    #     average_fees=('gas_fees_usd', 'mean')).reset_index()

    # # monthly swap transactions
    # uniswapv2_monthly_swaps = uniswapv2_swaps.resample('ME').agg(
    #     total_volume=('amount', 'sum'),
    #     average_volume=('amount', 'mean'),
    #     transaction_count=('tx_hash', 'count'),
    #     total_fees=('gas_fees_usd', 'sum'),
    #     average_fees=('gas_fees_usd', 'mean')).reset_index()
    
    # Transaction volume over time
    # By hour
    transact_vol_by_hour = dataframe.resample('h')['amount'].count().reset_index()
    transact_vol_by_hour.rename(columns={'timestamp': 'date'}, inplace=True)
    # By day
    transact_vol_by_day = dataframe.resample('d')['amount'].count().reset_index()
    transact_vol_by_day.rename(columns={'timestamp': 'date'}, inplace=True)
    # By week
    transact_vol_by_week = dataframe.resample('W')['amount'].count().reset_index()
    transact_vol_by_week.rename(columns={'timestamp': 'date'}, inplace=True)
    # By month
    # transact_vol_by_mnth = dataframe.resample('ME')['amount'].count()

    # Hourly amounts
    # hr_amounts = dataframe.resample('h')['amount'].sum()
    # # Hourly averages
    # hr_avg = dataframe.resample('h')['amount'].mean()
    # # daily amounts
    # day_amounts = dataframe.resample('d')['amount'].sum()
    # # daily averages
    # day_avg = dataframe.resample('d')['amount'].mean()
    # # weekly amounts
    # week_amounts = dataframe.resample('W')['amount'].sum()
    # # weekly averages
    # week_avg = dataframe.resample('W')['amount'].mean()
    # monthly amounts
    # mnth_amounts = dataframe.resample('ME')['amount'].sum()
    # # monthly averages
    # mnth_avg = dataframe.resample('ME')['amount'].mean()

    # Hourly amounts
    # hr_fee = dataframe.resample('h')['gas_fees_usd'].sum()
    # Hourly averages
    hr_avg_fee = dataframe.resample('h')['gas_fees_usd'].mean().reset_index()
    hr_avg_fee.rename(columns={'timestamp': 'date'}, inplace=True)
    # daily amounts
    # day_fee = dataframe.resample('d')['gas_fees_usd'].sum()
    # daily averages
    day_avg_fee = dataframe.resample('d')['gas_fees_usd'].mean().reset_index()
    day_avg_fee.rename(columns={'timestamp': 'date'}, inplace=True)
    
    # weekly amounts
    # week_fee = dataframe.resample('W')['gas_fees_usd'].sum()
    # weekly averages
    week_avg_fee = dataframe.resample('W')['gas_fees_usd'].mean().reset_index()
    week_avg_fee.rename(columns={'timestamp': 'date'}, inplace=True)
    # monthly amounts
    # mnth_fee = dataframe.resample('ME')['gas_fees_eth'].sum()
    # monthly averages
    # mnth_avg_fee = dataframe.resample('ME')['gas_fees_eth'].mean()

    # By block number
    # block_fee = dataframe.groupby('block_number')['gas_fees_usd'].sum().reset_index().sort_values('gas_fees_usd', ascending=False).head(5)
    block_avg_fee = dataframe.groupby('block_number')['gas_fees_usd'].mean().reset_index().sort_values('gas_fees_usd', ascending=False).head(5)
    # block_amt = dataframe.groupby('block_number')['amount'].sum().reset_index()
    block_avg_amt = dataframe.groupby('block_number')['amount'].mean().reset_index().sort_values('amount', ascending=False).head(5)
    block_trans_cnt = dataframe.groupby('block_number')['tx_hash'].count().reset_index().sort_values('tx_hash', ascending=False).head(5)

    # top senders, amount and fees
    top_senders = dataframe.groupby('from_address').agg(
        total_amount=('amount', 'sum'),
        total_fees_usd=('gas_fees_usd', 'sum'),
        total_fees_eth=('gas_fees_eth', 'sum'),
        transaction_count=('tx_hash', 'count')
    ).reset_index().sort_values('transaction_count', ascending=False).head(6)
    # top receivers, , amount and fees
    top_receivers = dataframe.groupby('to_address').agg(
        total_amount=('amount', 'sum'),
        total_fees_usd=('gas_fees_usd', 'sum'),
        total_fees_eth=('gas_fees_eth', 'sum'),
        transaction_count=('tx_hash', 'count')
    ).reset_index().sort_values('transaction_count', ascending=False).head(6)

    # Transaction health score
    dataframe['transaction_health_score'] = dataframe['gas_fees_usd'] * 100 / dataframe['amount']
    dataframe['transaction_health_score'] = dataframe['transaction_health_score'].replace([np.inf, -np.inf], -9999)

    # Score label
    def score_label(score):
        if score <= 0:
            return 'Extremely bad'
        elif score > 0 and score < 10:
            return 'Excellent'
        elif score >= 10 and score < 20:
            return 'Good'
        elif score >= 20 and score < 30:
            return 'Fair'
        else:
            return 'Poor'
    dataframe['transaction_health_score_label'] = dataframe['transaction_health_score'].apply(score_label)
    ths_label = dataframe['transaction_health_score_label'].value_counts().reset_index()
    
    # to be updated
    metrics_dict = {
        'total_transaction_volume': total_transaction_volume,
        'total_transaction_cnt': total_transaction_cnt,
        # 'unique_senders': unique_senders,
        # 'unique_receivers': unique_receivers,
        # 'average_transaction_amount': average_transaction_amount,
        'daily_reach': daily_reach,
        'total_revenue': total_revenue,
        # 'average_revenue_per_transaction': average_revenue_per_transaction,
        'active_wallets': active_wallets,
        'active_wal_daily': active_wal_daily,
        'active_wal_wkly': active_wal_wkly,
        'active_wal_montly': active_wal_montly,
        'retention_rate': retention_rate,
        'reten_fig': reten_fig,
        'top_holders': top_holders,
        'daily_swaps': daily_swaps,
        'wkly_swaps': wkly_swaps,
        'monthly_swaps': monthly_swaps,
        'uniswapv3_daily_swaps': uniswapv3_daily_swaps,
        'uniswapv3_wkly_swaps': uniswapv3_wkly_swaps,
        'uniswapv3_monthly_swaps': uniswapv3_monthly_swaps,
        # 'uniswapv2_daily_swaps': uniswapv2_daily_swaps,
        # 'uniswapv2_wkly_swaps': uniswapv2_wkly_swaps,
        # 'uniswapv2_monthly_swaps': uniswapv2_monthly_swaps,
        'transact_vol_by_hour': transact_vol_by_hour,
        'transact_vol_by_day': transact_vol_by_day,
        'transact_vol_by_week': transact_vol_by_week,
        # 'transact_vol_by_mnth': transact_vol_by_mnth,
        # 'hr_amounts': hr_amounts,
        # 'hr_avg': hr_avg,
        # 'day_amounts': day_amounts,
        # 'day_avg': day_avg,
        # 'week_amounts': week_amounts,
        # 'week_avg': week_avg,
        # 'mnth_amounts': mnth_amounts,
        # 'mnth_avg': mnth_avg,
        # 'hr_fee': hr_fee,
        'hr_avg_fee': hr_avg_fee,
        # 'day_fee': day_fee,
        'day_avg_fee': day_avg_fee,
        # 'week_fee': week_fee,
        'week_avg_fee': week_avg_fee,
        # 'mnth_fee': mnth_fee,
        # 'mnth_avg_fee': mnth_avg_fee,
        # 'block_fee': block_fee,
        'block_avg_fee': block_avg_fee,
        # 'block_amt': block_amt,
        'block_avg_amt': block_avg_amt,
        'block_trans_cnt': block_trans_cnt,
        'top_senders': top_senders,
        'top_receivers': top_receivers,
        'dex_swaps_figs': swap_fig,
        'transaction_health_score_label': ths_label
    }
    return metrics_dict
