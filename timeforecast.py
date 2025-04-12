from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def prophet_forecast(df: pd.DataFrame, column: str, periods: int = 14)-> tuple:
    """
    Forecasts a column in a DataFrame using Prophet.
    Parameters:
        df (pd.DataFrame): DataFrame containing the data.
        column (str): Name of the column to forecast.
        periods (int): Number of periods to forecast into the future.
    Returns: Model and Forecast.
    """
    # Create custom dataframe
    df_prophet = df[['timestamp', column]].rename(columns={'timestamp': 'ds', column: 'y'})

    # Convert ds to datetime
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
    df_prophet.drop_duplicates(inplace=True)

    # Initialize and fit the Prophet model
    model = Prophet(weekly_seasonality=True, daily_seasonality=True)
    model.fit(df_prophet)

    # Make future dataframe
    future = model.make_future_dataframe(periods=periods)

    # Forecast
    forecast = model.predict(future)

    return model, forecast

def plot_forecast(model, forecast, column: str)-> tuple:
    """
    Plots the forecast using Plotly.
    Parameters:
        model: Prophet model.
        forecast: Forecast DataFrame.
        column (str): Name of the column forecasted.
    """
    fig1 = plot_plotly(model, forecast)
    fig1.update_layout(title=f"Prophet Forecast for {column}")

    fig2 = plot_components_plotly(model, forecast)
    fig2.update_layout(title=f"Prophet Forecast Components for {column}")
    return fig1, fig2
