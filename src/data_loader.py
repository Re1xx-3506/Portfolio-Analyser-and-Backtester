import yfinance as yf
import pandas as pd


def fetch_prices(
    tickers: list[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame | pd.Series:
    """
    Download adjusted close prices for a list of tickers.

    Parameters
    ----------
    tickers     : list of ticker symbols, e.g. ["AAPL", "MSFT"]
    start_date  : "YYYY-MM-DD"
    end_date    : "YYYY-MM-DD"

    Returns
    -------
    pd.DataFrame | pd.Series  — columns = tickers, index = dates
    """
    raw = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False
    )

    if raw is None or raw.empty:
        raise ValueError(
            f"No price data returned for tickers: {tickers}"
        )

    # yfinance returns multi-level columns when >1 ticker is requested
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        # single ticker — raw itself is the Close series
        prices = raw[["Close"]]
        prices.columns = tickers

    # enforce consistent column ordering
    prices = prices[tickers]

    return prices