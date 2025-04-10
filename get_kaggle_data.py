import kagglehub
from kagglehub import KaggleDatasetAdapter

# Set the path to the file you'd like to load
file_path = "pyusd.csv"

# Load the latest version
df = kagglehub.load_dataset(
  KaggleDatasetAdapter.PANDAS,
  "musagodwin/pyusd-dataset",
  file_path,
)
# Save to disk
df.to_csv('dataset/pyusd.csv')