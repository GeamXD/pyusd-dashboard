import kagglehub
from kagglehub import KaggleDatasetAdapter
import streamlit as st
import json

def get_kaggle_df():
  # Save secret as json
    with open('.kaggle/kaggle.json', 'w') as f:
      kg = st.secrets['kaggle_key']
      json.dump(dict(kg), f)

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
