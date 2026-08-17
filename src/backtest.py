import pandas as pd
from pathlib import Path
import pickle 

from src.portfolio import normalised_weightings

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"

with open(data_dir / "processed" / "prices.pkl", "rb") as f:
    prices = pickle.load(f)

with open(data_dir / "processed" / "monthly_portfolios.pkl", "rb") as f:
    monthly_portfolios = pickle.load(f)

with open(data_dir / "processed" / "monthly_holdings.pkl", "rb") as f:
    monthly_holdings_df = pickle.load(f)


def monthly_portfolio_return(previous_date, current_date, portfolio,):

    previous_date = pd.Timestamp(previous_date)
    current_date = pd.Timestamp(current_date)

    old_weights = portfolio

    available_dates = [
        date for date in monthly_portfolios
        if date <= current_date
    ]

    if not available_dates:
        return None

    portfolio_date = max(available_dates)
    new_weights = monthly_portfolios[portfolio_date]

    gross_return = 0.0
    turnover = 0.0

    all_tickers = set(old_weights.index).union(new_weights.index)

    for ticker in all_tickers:

        if ticker not in prices:
            continue

        prices_df = prices[ticker].copy()
        prices_df.index = pd.to_datetime(prices_df.index)

        previous_prices = prices_df.loc[:previous_date]
        current_prices = prices_df.loc[:current_date]

        if previous_prices.empty or current_prices.empty:
            continue

        previous_price = previous_prices.iloc[-1][("Close", ticker)]
        current_price = current_prices.iloc[-1][("Close", ticker)]

        asset_return = current_price / previous_price - 1

        old_weight = old_weights.get(ticker, 0.0)
        new_weight = new_weights.get(ticker, 0.0)

        gross_return += old_weight * asset_return
        turnover += abs(new_weight - old_weight)

    # Converts absolute turnover into one-way turnover
    turnover /= 2

    return gross_return, turnover, new_weights

def periodic_momentum_returns(start_date, end_date, transaction_cost_rate = None):

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    monthly_holdings_df.index = pd.to_datetime(monthly_holdings_df.index)

    if not (monthly_holdings_df.index[0] <= start_date <= monthly_holdings_df.index[-1]):
        return "Invalid start date"

    if not (monthly_holdings_df.index[0] <= end_date <= monthly_holdings_df.index[-1]):
        return "Invalid end date"

    rebalance_dates = monthly_holdings_df.index[
        (monthly_holdings_df.index >= start_date) &
        (monthly_holdings_df.index <= end_date)
    ]

    if len(rebalance_dates) < 2:
        return "Need at least two rebalance dates."

    current_portfolio = normalised_weightings(
        str(rebalance_dates[0]), prices
    )["Weights"]

    total_gross_return = 1.0
    total_net_return = 1.0
    total_turnover = 0.0

    for i in range(1, len(rebalance_dates)):

        previous_date = rebalance_dates[i - 1]
        current_date = rebalance_dates[i]

        month_gross_return, month_turnover, current_portfolio = (
            monthly_portfolio_return(
                previous_date,
                current_date,
                current_portfolio, 
            )
        )

        total_gross_return *= (1 + month_gross_return)
        total_turnover += month_turnover

        if transaction_cost_rate is not None:
            month_transaction_cost = month_turnover * transaction_cost_rate

            month_net_return = month_gross_return - month_transaction_cost

            total_net_return *= 1 + month_net_return

    total_gross_return -= 1

    if transaction_cost_rate is not None:
        total_net_return -= 1
    else:
        total_net_return = None

    return total_gross_return, total_net_return, total_turnover

def saved_monthly_transaction_cost_df():

    monthly_transaction_cost_df = pd.DataFrame()

    transaction_cost_rates = {
        "bp_0" : 0.0,
        "bp_5" : 0.0005,
        "bp_10" : 0.001,
        "bp_25" : 0.0025,
        "bp_50" : 0.005
        }

    previous_date = monthly_holdings_df.index[0]

    portfolio = normalised_weightings(str(previous_date), prices)["Weights"]

    rows = []

    for date in monthly_holdings_df.index[1:]:

        gross_return, turnover, portfolio = monthly_portfolio_return(previous_date, date, portfolio)

        row = {
            "Date" : date,
            "Gross Return" : gross_return,
            "Turnover" : turnover
        }

        for name, rate in transaction_cost_rates.items():

            row[f"Transaction Cost {name}"] = (
                            turnover * rate
                        )

            row[f"Net Return {name}"] = (
                gross_return - turnover * rate
            )

        rows.append(row)

        previous_date = date

    monthly_transaction_cost_df = pd.DataFrame(rows)

    return monthly_transaction_cost_df

if __name__ == "__main__":

    monthly_transaction_cost_df = saved_monthly_transaction_cost_df()

    output_path = data_dir / "processed" / "monthly_transaction_cost_df.pkl"

    with open(output_path, "wb") as f:
        pickle.dump(monthly_transaction_cost_df, f)

    print(f"Saved to {output_path}")


