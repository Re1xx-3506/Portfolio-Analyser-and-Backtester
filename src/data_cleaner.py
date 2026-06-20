import pandas as pd


def clean_prices(prices):

    prices = prices.copy()

    prices = prices.dropna(how="all")

    prices = prices.ffill()

    prices = prices.dropna()

    return prices

def calculate_returns(prices):

    returns = prices.pct_change()

    returns = returns.dropna()

    return returns