
from pathlib import Path
import pandas as pd
import pickle 
import yfinance as yf

# Paths

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"

# Index holdings from historical dataset

index_holdings = pd.read_csv(data_dir / "raw" / "sp500_historical.csv")

index_holdings["date"] = pd.to_datetime(index_holdings["date"])

# Monthly dates from hsitorical dataset

monthly_dates = (
    index_holdings
    .groupby(index_holdings["date"].dt.to_period("M"))["date"]
    .last()
    .dt.strftime("%Y-%m-%d")
    .tolist()
)

monthly_dates = pd.to_datetime(monthly_dates)

# Function 'cleaning' tickers to a more consistent format 

def clean_ticker (ticker):
    ticker = ticker.strip()

    if ticker == "-":
        return None
    
    ticker = ticker.replace("*", "")
    ticker = ticker.replace("/", "-")

    if "." in ticker:
        parts = ticker.split(".")
        if len(parts) == 2 and parts[1].isdigit():
            ticker = parts[0]

    if (
        ticker.endswith(" WI")
        or ticker.endswith(" WS")
        or ticker.endswith(" WS WI")
    ):
        return None

    if " " in ticker:
        return None

    return ticker

# Map of reformatted tickers or ticker changes 

ticker_map = {
    # Formatting for yfinance 
    "BF.B": "BF-B",
    "BFB": "BF-B",
    "BRKB": "BRK-B",
    "BRK.B": "BRK-B",
    "UAC/C": "UAC-C",

    # Ticker changes not including mergers
    "FB": "META",
    "WAG": "WBA",
    "HCP": "PEAK",
    "PCLN": "BKNG",
    "NLOK": "GEN",
    "VIAB": "PARA",
    "CBS": "PARA",
    "DTV": "T",
}

# Dataframe of the monthly holdings of the historical dataset

def create_monthly_holdings():
    monthly_holdings_df = (
    index_holdings[index_holdings["date"].isin(monthly_dates)]
    .groupby("date")["ticker"]
    .apply(list)
    .reset_index(name= "Holdings")
    )

    monthly_holdings_df["Holdings"] = monthly_holdings_df["Holdings"].apply(
    lambda holdings:[
        ticker_map.get(clean_ticker(ticker), clean_ticker(ticker))
        for ticker in holdings
        if clean_ticker(ticker) is not None
    ]
    )

    monthly_holdings_df = monthly_holdings_df.set_index("date")
    monthly_holdings_df.index = pd.to_datetime(monthly_holdings_df.index)

    # Dataframe of all the unique, valid holdings within the historical dataset 

    all_holdings_processed = sorted(set([
    ticker_map.get(ticker, ticker)
    for holdings in monthly_holdings_df["Holdings"]
    for ticker in holdings
    ]))

    return monthly_holdings_df, all_holdings_processed

def create_prices(all_holdings_processed):

    prices = {}

    for ticker in all_holdings_processed:
        try:
            history = yf.download(
            ticker,
            period = "max",
            interval="1d",
            progress=False
        )

            if not history.empty:
                prices[ticker] = history

        except Exception:
            continue

    for ticker in prices:
        prices[ticker].index = pd.to_datetime(prices[ticker].index)

    return prices 


def save_processed_data():

    monthly_holdings_df, all_holdings_processed = create_monthly_holdings()
    prices = create_prices(all_holdings_processed)

    # Saving dataframes 

    monthly_holdings_df.to_pickle(data_dir / "processed" / "monthly_holdings.pkl")

    with open(data_dir / "processed" / "all_holdings_processed.pkl", "wb") as f:
        pickle.dump(all_holdings_processed, f)

    with open(data_dir / "processed" / "prices.pkl", "wb") as f:
        pickle.dump(prices, f)


if __name__ == "__main__":
    save_processed_data()