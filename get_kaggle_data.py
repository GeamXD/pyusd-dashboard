import os
import kagglehub
from kagglehub import KaggleDatasetAdapter
import streamlit as st
import json

def get_kaggle_df():
    #Load key
    kaggle_secrets = st.secrets['kaggle_key']
    os.environ['KAGGLE_USERNAME'] = kaggle_secrets['username']
    os.environ['KAGGLE_KEY'] = kaggle_secrets['key']
    
    # Set the path to the file you'd like to load
    file_path = "pyusd.csv"

    # Load the latest version
    df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "musagodwin/pyusd-dataset",
    file_path,
  )
    # Save to disk
    df.to_csv('dataset/pyusd.csv', index=False)
