from src.data_loader import fetch_prices
from src.data_cleaner import (
    clean_prices,
    calculate_returns
)

tickers = [
    "AAPL",
    "MSFT",
    "NVDA"
]

prices = fetch_prices(
    tickers=tickers,
    start_date="2020-01-01",
    end_date="2025-01-01"
)

prices = clean_prices(prices)

returns = calculate_returns(prices)

print(prices.head())
print()

print(returns.head())

prices.to_csv("data/prices.csv")
returns.to_csv("data/returns.csv")