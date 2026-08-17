
import pickle
from pathlib import Path
import pandas as pd

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"

# Load prices dataset

with open(data_dir / "processed" / "prices.pkl", "rb") as f:
    prices = pickle.load(f)


# Function for getting the prices of a specific holding

def get_price(ticker, target_date, prices):

    df = prices[ticker]

    available = df.loc[:target_date]

    if available.empty:
         return None

    return available.iloc[-1][("Close", ticker)]

# Function which calculates the 3,6, 12-month momentum scores of a holding

def momentum_cal(date, ticker, prices):

    date = pd.Timestamp(date)

    df = prices[ticker].copy()
    df.index = pd.to_datetime(df.index)

    # make sure dates are sorted
    df = df.sort_index()

    previous_month = date - pd.DateOffset(months=1)
    previous_3_month = date - pd.DateOffset(months=3)
    previous_6_month = date - pd.DateOffset(months=6)
    previous_12_month = date - pd.DateOffset(months=12)

    price_1m = get_price(ticker, previous_month, prices)
    price_3m = get_price(ticker, previous_3_month, prices)
    price_6m = get_price(ticker, previous_6_month, prices)
    price_12m = get_price(ticker, previous_12_month, prices)


    momentum_3_mo = None
    momentum_6_mo = None
    momentum_12_mo = None


    if price_1m is not None and price_3m is not None:
        momentum_3_mo = price_1m / price_3m

    if price_1m is not None and price_6m is not None:
        momentum_6_mo = price_1m / price_6m

    if price_1m is not None and price_12m is not None:
        momentum_12_mo = price_1m / price_12m


    return momentum_3_mo, momentum_6_mo, momentum_12_mo

