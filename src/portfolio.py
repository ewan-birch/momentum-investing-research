
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"

import pandas as pd
import numpy as np
import pickle 
from pathlib import Path

from .momentum import momentum_cal
from .data_processing import create_monthly_holdings

monthly_holdings_df, all_holdings_processed = create_monthly_holdings()

with open(data_dir / "processed" / "prices.pkl", "rb") as f:
    prices = pickle.load(f)


def comp_score (date, ticker, prices):
    month_3, month_6, month_12 =  momentum_cal(date, ticker, prices)

    if None in (month_3, month_6, month_12):
        return np.nan
    
    score = (0.5 * month_3) + (0.3 * month_6) + (0.2 * month_12)

    return score


def rank_comp_scores (date, prices):

    date = pd.Timestamp(date)

    holdings = monthly_holdings_df.loc[:date, "Holdings"].iloc[-1]

    scores = {}

    for ticker in holdings:
        if ticker in prices:
            scores[ticker] = comp_score(date, ticker, prices)

    df = (
        pd.DataFrame.from_dict(scores, orient = "index", columns = ["Score"])
        .dropna()
        .sort_values("Score", ascending = False)
    )

    return (df)


def normalised_weightings(date, prices):
    df = rank_comp_scores(date, prices)

    top_25 = df.iloc[:25]

    summed_scores = top_25["Score"].sum()

    holdings = {
        ticker: float(f"{score / summed_scores :.6g}")
        for ticker, score in top_25["Score"].items()
    }

    weightings_df = (
        pd.DataFrame.from_dict(holdings, orient = "index", columns = ["Weights"])
        .sort_values("Weights", ascending = False)
    )

    return (weightings_df)

# Loading monthly portfolios to ease computing time  

if __name__ == "__main__":
    monthly_portfolios = {}

    for date in monthly_holdings_df.index:
        try:
            monthly_portfolios[date] = normalised_weightings(str(date), prices)["Weights"]
            print(f"{date} done")
        except Exception:
            continue


    with open("../data/processed/monthly_portfolios.pkl", "wb") as f:
        pickle.dump(monthly_portfolios, f)

