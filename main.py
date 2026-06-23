from src.data_loader import fetch_prices
from src.data_cleaner import (
    clean_prices,
    calculate_returns
)

from src.portfolio import (
    equal_weights,
    portfolio_returns,
    portfolio_value
)

tickers = [
    "AAPL",
    "MSFT",
    "NVDA"
]

prices = fetch_prices(
    tickers,
    start_date="2020-01-01",
    end_date="2025-01-01"
)

prices = clean_prices(prices)

returns = calculate_returns(prices)

weights = equal_weights(
    len(tickers)
)

port_ret = portfolio_returns(
    returns,
    weights
)

equity_curve = portfolio_value(
    port_ret,
    initial_investment=10000
)

print(equity_curve.head())
print(equity_curve.tail())