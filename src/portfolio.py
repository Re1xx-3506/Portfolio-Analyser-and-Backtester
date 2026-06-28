import numpy as np
import pandas as pd


# ──────────────────────────────────────────────
# Weight Constructors
# ──────────────────────────────────────────────

def equal_weights(n_assets: int) -> np.ndarray:
    """
    Return an equal-weight array for n_assets.

    Example (n=3):  [0.3333, 0.3333, 0.3333]
    """
    if n_assets <= 0:
        raise ValueError("Number of assets must be positive")
    return np.repeat(1 / n_assets, n_assets)


def custom_weights(weights: list | np.ndarray) -> np.ndarray:
    """
    Validate and return a custom weight array.

    Rules
    -----
    - Not empty
    - No negative values
    - Must sum to 1.0  (within floating-point tolerance)

    Example:  [0.4, 0.4, 0.2]  →  40 % / 40 % / 20 %
    """
    weights = np.asarray(weights, dtype=float)

    if weights.size == 0:
        raise ValueError("Weights cannot be empty")

    if np.any(weights < 0):
        raise ValueError("Weights cannot be negative")

    if not np.isclose(weights.sum(), 1.0):
        raise ValueError(
            f"Weights must sum to 1.0 — got {weights.sum():.6f}"
        )

    return weights


# ──────────────────────────────────────────────
# Portfolio Returns & Equity Curve
# ──────────────────────────────────────────────

def portfolio_returns(
    returns: pd.DataFrame,
    weights: np.ndarray
) -> pd.Series:
    """
    Compute daily weighted portfolio returns.

    Formula:  R_p = Σ(w_i * R_i)   (dot product)

    Parameters
    ----------
    returns : pd.DataFrame  — daily asset returns, columns = tickers
    weights : np.ndarray    — weight per asset, must match column count

    Returns
    -------
    pd.Series  — daily portfolio returns, index = dates
    """
    if returns.shape[1] != len(weights):
        raise ValueError(
            f"Expected {returns.shape[1]} weights, got {len(weights)}"
        )

    result = returns.to_numpy().dot(weights)
    return pd.Series(result, index=returns.index, name="portfolio")


def portfolio_value(
    returns_series: pd.Series,
    initial_investment: float
) -> pd.Series:
    """
    Compound daily returns into a portfolio equity curve.

    Formula:  V_t = V_0 × Π(1 + R_t)

    Parameters
    ----------
    returns_series     : pd.Series  — daily portfolio returns
    initial_investment : float      — starting capital (e.g. 10 000)

    Returns
    -------
    pd.Series  — portfolio value over time, index = dates
    """
    growth = (1 + returns_series).cumprod()
    value = initial_investment * growth
    return pd.Series(value, index=returns_series.index, name="portfolio_value")


# ──────────────────────────────────────────────
# Benchmark Engine  (Phase 2.3)
# ──────────────────────────────────────────────

def benchmark_returns(
    returns: pd.DataFrame,
    benchmark_ticker: str = "SPY"
) -> pd.Series:
    """
    Extract the returns series for a benchmark ticker.

    The benchmark ticker must be a column in the `returns` DataFrame,
    meaning it should have been included in the original download.

    Parameters
    ----------
    returns          : pd.DataFrame  — returns including the benchmark
    benchmark_ticker : str           — column name, default "SPY"

    Returns
    -------
    pd.Series  — benchmark daily returns, index = dates
    """
    if benchmark_ticker not in returns.columns:
        raise ValueError(
            f"Benchmark ticker '{benchmark_ticker}' not found in returns. "
            f"Available columns: {list(returns.columns)}"
        )

    series = returns[benchmark_ticker].copy()
    series.name = benchmark_ticker
    return series


def benchmark_value(
    returns_series: pd.Series,
    initial_investment: float
) -> pd.Series:
    """
    Compound benchmark returns into a benchmark equity curve.

    Identical compounding logic to portfolio_value() so the two curves
    are directly comparable on the same chart.

    Parameters
    ----------
    returns_series     : pd.Series  — benchmark daily returns
    initial_investment : float      — same starting capital as portfolio

    Returns
    -------
    pd.Series  — benchmark value over time, index = dates
    """
    growth = (1 + returns_series).cumprod()
    value = initial_investment * growth
    return pd.Series(
        value,
        index=returns_series.index,
        name=f"{returns_series.name}_value"
    )


def compare_performance(
    port_curve: pd.Series,
    bench_curve: pd.Series,
    initial_investment: float
) -> dict:
    """
    Print and return a summary comparing portfolio vs benchmark.

    Metrics
    -------
    - Final portfolio value
    - Final benchmark value
    - Portfolio total return %
    - Benchmark total return %
    - Outperformance (alpha) %

    Parameters
    ----------
    port_curve         : pd.Series  — portfolio equity curve
    bench_curve        : pd.Series  — benchmark equity curve
    initial_investment : float

    Returns
    -------
    dict with keys: port_final, bench_final, port_return_pct,
                    bench_return_pct, outperformance_pct
    """
    port_final  = port_curve.iloc[-1]
    bench_final = bench_curve.iloc[-1]

    port_return_pct  = (port_final  / initial_investment - 1) * 100
    bench_return_pct = (bench_final / initial_investment - 1) * 100
    outperformance   = port_return_pct - bench_return_pct

    print("\n" + "=" * 45)
    print("  PERFORMANCE SUMMARY")
    print("=" * 45)
    print(f"  Initial Investment  : ${initial_investment:,.2f}")
    print(f"  Portfolio Final     : ${port_final:,.2f}")
    print(f"  Benchmark Final     : ${bench_final:,.2f}")
    print(f"  Portfolio Return    : {port_return_pct:+.2f}%")
    print(f"  Benchmark Return    : {bench_return_pct:+.2f}%")
    print(f"  Outperformance      : {outperformance:+.2f}%")
    print("=" * 45 + "\n")

    return {
        "port_final"         : port_final,
        "bench_final"        : bench_final,
        "port_return_pct"    : port_return_pct,
        "bench_return_pct"   : bench_return_pct,
        "outperformance_pct" : outperformance,
    }