"""
Data loader for Hotel Booking Demand dataset.
Source: Antonio, Almeida & Nunes (2019), via TidyTuesday.
"""
import os
import pandas as pd

DATA_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/"
    "master/data/2020/2020-02-11/hotels.csv"
)
DEFAULT_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "hotels_raw.csv"
)


def load_data(cache_path=None):
    """
    Load hotel booking dataset, caching locally after first download.

    Args:
        cache_path: Path to cache the CSV. Defaults to training/data/hotels_raw.csv.

    Returns:
        pd.DataFrame with raw hotel booking data.
    """
    if cache_path is None:
        cache_path = DEFAULT_CACHE_PATH

    if os.path.exists(cache_path):
        print(f"[data_loader] Loading cached data from {cache_path}")
        return pd.read_csv(cache_path)

    print(f"[data_loader] Downloading data from {DATA_URL} ...")
    df = pd.read_csv(DATA_URL)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_csv(cache_path, index=False)
    print(f"[data_loader] Data cached to {cache_path}  ({len(df):,} rows)")

    return df
