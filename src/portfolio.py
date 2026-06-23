import numpy as np
import pandas as pd


def equal_weights(n_assets):

    if n_assets <= 0:
        raise ValueError("Number of assets must be positive")

    weights = np.repeat(
        1 / n_assets,
        n_assets
    )

    return weights

def portfolio_returns(
    returns,
    weights
):

    if len(weights) != returns.shape[1]:
        raise ValueError(
            "Weights must match number of assets"
        )

    portfolio_ret = returns.dot(weights)

    return portfolio_ret

def portfolio_value(
    portfolio_returns,
    initial_investment
):

    growth = (
        1 + portfolio_returns
    ).cumprod()

    return (
        initial_investment
        * growth
    )