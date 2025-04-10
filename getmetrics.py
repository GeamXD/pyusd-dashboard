import pandas as pd
import numpy as np
import plotly.express as px

def get_metrics(dataframe: pd.DataFrame)-> dict:
    """
    Gets dashboard metrics and values
    Params:
        dataframe: Dataframe containing the dataset
    Returns:
        Dictionary containing all dashboard metrics and values
    """
    # New dataframe and set time as index
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'])
    dataframe.set_index('timestamp', inplace=True)

    # Total transaction volume
    total_transaction_volume = dataframe['amount'].sum()

    # Unique senders and receivers
    unique_senders = dataframe['from_address'].nunique()
    unique_receivers = dataframe['to_address'].nunique()

    # Average transaction amount
    average_transaction_amount = dataframe['amount'].mean()

    # Daily reach
    daily_reach = dataframe.resample('d')['from_address','to_address'].nunique()

    # Total revenue
    total_revenue = dataframe['gas_fees_usd'].sum()

    # Average revenue per transaction
    average_revenue_per_transaction = dataframe['gas_fees_usd'].mean()

    # Active wallets
    active_wallets = dataframe[['from_address', 'to_address']].melt(value_name='wallet')['wallet'].nunique()

    # Active wallets -- daily -- weekly --monthly
    dataframe['date'] = dataframe.index.date
    active_wal = dataframe[['date', 'from_address', 'to_address']].melt(id_vars='date', value_name='active_wallet')
    active_wal['date'] = pd.to_datetime(active_wal['date'])
    active_wal.set_index('date', inplace=True)

    # -- daily
    active_wal_daily = active_wal.resample('D')['active_wallet'].nunique()

    # -- weekly
    active_wal_wkly = active_wal.resample('W')['active_wallet'].nunique()

    # --- monthly
    active_wal_montly = active_wal.resample('ME')['active_wallet'].nunique()

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
    retention_rate = retention.divide(retention[0], axis=0) * 100

    # long format
    retention_rate_reset = retention_rate.reset_index().melt(id_vars='cohort_week', var_name='Week', value_name='Retention Rate')

    # --- Plotly Heatmap ---
    reten_fig = px.imshow(
        retention_rate.values,
        labels=dict(x="Weeks Since First Seen", y="Cohort Week", color="Retention Rate"),
        x=retention_rate.columns,
        y=retention_rate.index.strftime('%Y-%m-%d'),
        color_continuous_scale='Blues',
        aspect='auto',
        text_auto=True
    )

    reten_fig.update_layout(title="Wallet Retention Heatmap", 
                      xaxis_title="Weeks Since First Seen",
                        yaxis_title="Cohort Week",
                        width=600,
                        height=500)
    
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
    top_holders = balances[balances['balance_usd'] > 0].sort_values(by='balance_usd', ascending=False)

    # Swap transactions
    dex_address = ['0x4a4d2410c3d4cfa8dd0d275bedefbd2f7b61ba2e', '0x13394005c1012e708fce1eb974f1130fdc73a5ce', '0xf313d711d71eb9a607b4a61a827a9e32a7846621']
    dex_names = ['uniswapv2', 'uniswapv3', 'uniswapv3']
    dex = dict(zip(dex_address, dex_names))
    swap_transactions = dataframe[dataframe['to_address'].isin(dex_address)]
    swap_transactions['dex'] = swap_transactions['to_address'].map(dex)

    # Daily swap transactions
    daily_swaps = swap_transactions.resample('D').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()

    # weekly swap transactions
    wkly_swaps = swap_transactions.resample('W').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()

    # monthly swap transactions
    monthly_swaps = swap_transactions.resample('ME').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()

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

    # weekly swap transactions
    uniswapv3_wkly_swaps = uniswapv3_swaps.resample('W').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()

    # monthly swap transactions
    uniswapv3_monthly_swaps = uniswapv3_swaps.resample('ME').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')
    ).reset_index()

    # By dex -- uniswapv3
    mask2 = swap_transactions['dex'] == 'uniswapv2'
    uniswapv2_swaps = swap_transactions[mask2]

    # Daily swap transactions
    uniswapv2_daily_swaps = uniswapv2_swaps.resample('D').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')).reset_index()

    # weekly swap transactions
    uniswapv2_wkly_swaps = uniswapv2_swaps.resample('W').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')).reset_index()

    # monthly swap transactions
    uniswapv2_monthly_swaps = uniswapv2_swaps.resample('ME').agg(
        total_volume=('amount', 'sum'),
        average_volume=('amount', 'mean'),
        transaction_count=('tx_hash', 'count'),
        total_fees=('gas_fees_usd', 'sum'),
        average_fees=('gas_fees_usd', 'mean')).reset_index()
    
    # Transaction volume over time
    # By hour
    transact_vol_by_hour = dataframe.resample('h')['amount'].count()
    # By day
    transact_vol_by_day = dataframe.resample('d')['amount'].count()
    # By week
    transact_vol_by_week = dataframe.resample('W')['amount'].count()
    # By month
    transact_vol_by_mnth = dataframe.resample('ME')['amount'].count()

    # Hourly amounts
    hr_amounts = dataframe.resample('h')['amount'].sum()
    # Hourly averages
    hr_avg = dataframe.resample('h')['amount'].mean()
    # daily amounts
    day_amounts = dataframe.resample('d')['amount'].sum()
    # daily averages
    day_avg = dataframe.resample('d')['amount'].mean()
    # weekly amounts
    week_amounts = dataframe.resample('W')['amount'].sum()
    # weekly averages
    week_avg = dataframe.resample('W')['amount'].mean()
    # monthly amounts
    mnth_amounts = dataframe.resample('ME')['amount'].sum()
    # monthly averages
    mnth_avg = dataframe.resample('ME')['amount'].mean()

    # Gas fee eth volume over time
    # By hour
    gas_fee_eth_by_hour = dataframe.resample('h')['gas_fees_eth'].count()
    # By day
    gas_fee_eth_by_day = dataframe.resample('d')['gas_fees_eth'].count()
    # By week
    gas_fee_eth_by_week = dataframe.resample('W')['gas_fees_eth'].count()
    # By month
    gas_fee_eth_by_mnth = dataframe.resample('ME')['gas_fees_eth'].count()

    # Hourly amounts
    hr_fee = new_df.resample('h')['gas_fees_eth'].sum()
    # Hourly averages
    hr_avg_fee = new_df.resample('h')['gas_fees_eth'].mean()
    # daily amounts
    day_fee = new_df.resample('d')['gas_fees_eth'].sum()
    # daily averages
    day_avg_fee = new_df.resample('d')['gas_fees_eth'].mean()
    # weekly amounts
    week_fee = new_df.resample('W')['gas_fees_eth'].sum()
    # weekly averages
    week_avg_fee = new_df.resample('W')['gas_fees_eth'].mean()
    # monthly amounts
    mnth_fee = new_df.resample('ME')['gas_fees_eth'].sum()
    # monthly averages
    mnth_avg_fee = new_df.resample('ME')['gas_fees_eth'].mean()

    # By block number
    block_fee = new_df.groupby('block_number')['gas_fees_eth'].sum()
    block_avg_fee = new_df.groupby('block_number')['gas_fees_eth'].mean()
    block_amt = new_df.groupby('block_number')['amount'].sum()
    block_avg_amt = new_df.groupby('block_number')['amount'].mean()
    block_trans_cnt = new_df.groupby('block_number')['tx_hash'].count()