import pandas as pd


def clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw price DataFrame.

    Steps
    -----
    1. Drop rows where every asset is NaN  (e.g. market holidays
       that slipped through).
    2. Forward-fill isolated missing values within a column
       (e.g. one ticker not trading on a given day).
    3. Drop any remaining NaN rows so downstream maths never sees
       a NaN.

    Parameters
    ----------
    prices : pd.DataFrame  — raw Close prices, columns = tickers

    Returns
    -------
    pd.DataFrame  — cleaned prices
    """
    prices = prices.copy()
    prices = prices.dropna(how="all")
    prices = prices.ffill()
    prices = prices.dropna()
    return prices


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a price DataFrame into simple daily returns.

    Formula:  R_t = (P_t - P_{t-1}) / P_{t-1}

    Parameters
    ----------
    prices : pd.DataFrame  — cleaned Close prices

    Returns
    -------
    pd.DataFrame  — daily returns (first row dropped)
    """
    returns = prices.pct_change()
    returns = returns.dropna()
    return returns