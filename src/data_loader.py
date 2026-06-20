import yfinance as yf
import pandas as pd


def fetch_prices(
        tickers,
        start_date,
        end_date
):

    data = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False
    )

    if data is None:
        raise ValueError("Failed to download data")

    prices = data["Close"]

    return prices

