"""
src/visualization.py
====================
Phase 4 — Visualization & Diagnostics

All functions accept the pd.Series / pd.DataFrame outputs produced by
the existing pipeline and render matplotlib figures.

Call plot_all() from main.py to generate every chart in one go, or
call individual functions for specific charts.

Assumptions
-----------
- 252 trading days / year for annualisation.
- Rolling window: 63 trading days  (~1 quarter).
- Risk-free rate sourced from src.metrics.RISK_FREE_RATE so it stays
  in sync with Phase 3.
- plt.show() is called once at the end of plot_all() so figures render
  together rather than blocking execution one by one.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from src.metrics import RISK_FREE_RATE

TRADING_DAYS   = 252
ROLLING_WINDOW = 63          # ~1 quarter

# ── Shared style ──────────────────────────────────────────────────────

COLORS = {
    "eq_weight"   : "#2196F3",   # blue
    "cust_weight" : "#4CAF50",   # green
    "benchmark"   : "#FF5722",   # deep orange
    "aapl"        : "#9C27B0",   # purple
    "msft"        : "#00BCD4",   # cyan
    "nvda"        : "#FF9800",   # amber
    "neutral"     : "#607D8B",   # blue-grey
}

def _pct_formatter(x, _):
    return f"{x:.0f}%"

def _style_ax(ax, title, xlabel="Date", ylabel=""):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.tick_params(axis="x", rotation=30)


# ──────────────────────────────────────────────────────────────────────
# Chart 1 — Equity Curves
# ──────────────────────────────────────────────────────────────────────

def plot_equity_curves(
    port_val_eq:   pd.Series,
    port_val_cust: pd.Series,
    bench_val:     pd.Series,
    initial_investment: float,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Plot equal-weight, custom-weight, and SPY equity curves on one axis.
    All three start from the same initial_investment so the scale is
    directly comparable.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 5))

    ax.plot(port_val_eq.index,   port_val_eq,   color=COLORS["eq_weight"],
            label="Equal Weight",   linewidth=1.8)
    ax.plot(port_val_cust.index, port_val_cust, color=COLORS["cust_weight"],
            label="Custom Weight (40/40/20)", linewidth=1.8)
    ax.plot(bench_val.index,     bench_val,     color=COLORS["benchmark"],
            label="SPY Benchmark", linewidth=1.8, linestyle="--")

    ax.axhline(initial_investment, color="grey", linewidth=0.8,
               linestyle=":", label=f"Initial ${initial_investment:,.0f}")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x:,.0f}"
    ))
    _style_ax(ax, "Portfolio Equity Curves", ylabel="Portfolio Value ($)")
    return ax


# ──────────────────────────────────────────────────────────────────────
# Chart 2 — Drawdown
# ──────────────────────────────────────────────────────────────────────

def _compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return (equity_curve - running_max) / running_max * 100   # as %


def plot_drawdown(
    port_val:  pd.Series,
    bench_val: pd.Series,
    port_label: str = "Portfolio",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Plot drawdown (%) for the portfolio and SPY benchmark.
    Shaded fill makes the depth visually obvious.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    dd_port  = _compute_drawdown(port_val)
    dd_bench = _compute_drawdown(bench_val)

    ax.fill_between(dd_port.index,  dd_port,  0,
                    alpha=0.3, color=COLORS["eq_weight"])
    ax.fill_between(dd_bench.index, dd_bench, 0,
                    alpha=0.3, color=COLORS["benchmark"])

    ax.plot(dd_port.index,  dd_port,  color=COLORS["eq_weight"],
            linewidth=1.4, label=port_label)
    ax.plot(dd_bench.index, dd_bench, color=COLORS["benchmark"],
            linewidth=1.4, linestyle="--", label="SPY")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:.0f}%"
    ))
    _style_ax(ax, "Drawdown (%)", ylabel="Drawdown (%)")
    return ax


# ──────────────────────────────────────────────────────────────────────
# Chart 3 — Rolling Volatility
# ──────────────────────────────────────────────────────────────────────

def plot_rolling_volatility(
    port_returns:  pd.Series,
    bench_returns: pd.Series,
    port_label: str = "Portfolio",
    window: int = ROLLING_WINDOW,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Plot 63-day rolling annualised volatility for portfolio and SPY.
    Annualised as:  rolling_std * sqrt(252)
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    roll_vol_port  = port_returns.rolling(window).std()  * np.sqrt(TRADING_DAYS) * 100
    roll_vol_bench = bench_returns.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100

    ax.plot(roll_vol_port.index,  roll_vol_port,  color=COLORS["eq_weight"],
            linewidth=1.4, label=port_label)
    ax.plot(roll_vol_bench.index, roll_vol_bench, color=COLORS["benchmark"],
            linewidth=1.4, linestyle="--", label="SPY")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pct_formatter))
    _style_ax(
        ax,
        f"{window}-Day Rolling Annualised Volatility (%)",
        ylabel="Volatility (%)"
    )
    return ax


# ──────────────────────────────────────────────────────────────────────
# Chart 4 — Rolling Sharpe
# ──────────────────────────────────────────────────────────────────────

def plot_rolling_sharpe(
    port_returns:  pd.Series,
    bench_returns: pd.Series,
    port_label: str = "Portfolio",
    window: int = ROLLING_WINDOW,
    rf: float = RISK_FREE_RATE,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Plot 63-day rolling Sharpe ratio.

    Rolling Sharpe = (mean(r) * 252 - rf) / (std(r) * sqrt(252))
    computed over a rolling window.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    daily_rf = rf / TRADING_DAYS

    def _rolling_sharpe(returns: pd.Series) -> pd.Series:
        roll_mean = returns.rolling(window).mean()
        roll_std  = returns.rolling(window).std()
        ann_ret   = roll_mean * TRADING_DAYS
        ann_vol   = roll_std  * np.sqrt(TRADING_DAYS)
        return (ann_ret - rf) / ann_vol

    ax.plot(_rolling_sharpe(port_returns).index,
            _rolling_sharpe(port_returns),
            color=COLORS["eq_weight"], linewidth=1.4, label=port_label)
    ax.plot(_rolling_sharpe(bench_returns).index,
            _rolling_sharpe(bench_returns),
            color=COLORS["benchmark"], linewidth=1.4,
            linestyle="--", label="SPY")

    ax.axhline(0, color="grey", linewidth=0.8, linestyle=":")
    ax.axhline(1, color="grey", linewidth=0.8, linestyle=":",
               label="Sharpe = 1")
    _style_ax(
        ax,
        f"{window}-Day Rolling Sharpe Ratio (rf={rf*100:.1f}%)",
        ylabel="Sharpe Ratio"
    )
    return ax


# ──────────────────────────────────────────────────────────────────────
# Chart 5 — Asset Growth (Normalised)
# ──────────────────────────────────────────────────────────────────────

def plot_asset_growth(
    prices: pd.DataFrame,
    tickers: list[str],
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Normalise each asset to 100 at the start date so growth can be
    compared on a common scale regardless of absolute price differences.

    Normalised value = price / price[0] * 100
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    color_map = {
        tickers[0]: COLORS["aapl"],
        tickers[1]: COLORS["msft"],
        tickers[2]: COLORS["nvda"],
    }

    for ticker in tickers:
        if ticker not in prices.columns:
            continue
        normalised = prices[ticker] / prices[ticker].iloc[0] * 100
        ax.plot(normalised.index, normalised,
                color=color_map.get(ticker, COLORS["neutral"]),
                linewidth=1.6, label=ticker)

    ax.axhline(100, color="grey", linewidth=0.8, linestyle=":",
               label="Starting value = 100")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:.0f}"
    ))
    _style_ax(ax, "Individual Asset Growth (Normalised to 100)",
              ylabel="Growth Index")
    return ax


# ──────────────────────────────────────────────────────────────────────
# Chart 6 — Weight Drift
# ──────────────────────────────────────────────────────────────────────

def plot_weight_drift(
    prices: pd.DataFrame,
    tickers: list[str],
    initial_weights: list[float],
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Show how portfolio weights drift over time with NO rebalancing.

    Method
    ------
    1. Normalise each asset price to 1.0 at start.
    2. Multiply each by its initial weight to get the dollar value of
       each holding as if we invested $1 total at day 0.
    3. At each date, express each holding as a fraction of total value.

    This correctly captures how a buy-and-hold portfolio drifts from
    its target weights over time.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    subset = prices[tickers].copy()
    # normalised price relatives
    norm   = subset / subset.iloc[0]
    # dollar value of each holding (initial_weights sum to 1)
    holdings = norm * np.array(initial_weights)
    # weight = holding value / total portfolio value
    weights_over_time = holdings.div(holdings.sum(axis=1), axis=0) * 100

    color_map = {
        tickers[0]: COLORS["aapl"],
        tickers[1]: COLORS["msft"],
        tickers[2]: COLORS["nvda"],
    }

    ax.stackplot(
        weights_over_time.index,
        *[weights_over_time[t] for t in tickers],
        labels=tickers,
        colors=[color_map.get(t, COLORS["neutral"]) for t in tickers],
        alpha=0.75,
    )

    # target weight reference lines
    cumulative = 0
    for w in initial_weights[:-1]:
        cumulative += w * 100
        ax.axhline(cumulative, color="white", linewidth=0.8,
                   linestyle="--", alpha=0.6)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pct_formatter))
    ax.set_ylim(0, 100)
    _style_ax(ax, "Portfolio Weight Drift Over Time (No Rebalancing)",
              ylabel="Weight (%)")
    return ax


# ──────────────────────────────────────────────────────────────────────
# Chart 7 — Daily Return Distribution
# ──────────────────────────────────────────────────────────────────────

def plot_return_distribution(
    port_returns:  pd.Series,
    bench_returns: pd.Series,
    port_label: str = "Portfolio",
    bins: int = 80,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Histogram of daily returns for portfolio and benchmark.
    Overlaid so tail behaviour can be compared directly.

    Mean and ±2σ lines are drawn to highlight the distribution shape.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    ax.hist(port_returns  * 100, bins=bins, alpha=0.55,
            color=COLORS["eq_weight"],  label=port_label, density=True)
    ax.hist(bench_returns * 100, bins=bins, alpha=0.55,
            color=COLORS["benchmark"], label="SPY", density=True)

    for series, color in [
        (port_returns,  COLORS["eq_weight"]),
        (bench_returns, COLORS["benchmark"]),
    ]:
        mu  = series.mean() * 100
        sig = series.std()  * 100
        ax.axvline(mu,           color=color, linewidth=1.2, linestyle="-")
        ax.axvline(mu + 2 * sig, color=color, linewidth=0.9, linestyle="--",
                   alpha=0.7)
        ax.axvline(mu - 2 * sig, color=color, linewidth=0.9, linestyle="--",
                   alpha=0.7)

    ax.axvline(0, color="grey", linewidth=0.8, linestyle=":")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_pct_formatter))
    _style_ax(ax, "Daily Return Distribution  (solid=mean, dashed=±2σ)",
              xlabel="Daily Return (%)", ylabel="Density")
    return ax


# ──────────────────────────────────────────────────────────────────────
# Master function — render all 7 charts
# ──────────────────────────────────────────────────────────────────────

def plot_all(
    port_val_eq:    pd.Series,
    port_val_cust:  pd.Series,
    bench_val:      pd.Series,
    port_ret_eq:    pd.Series,
    port_ret_cust:  pd.Series,
    bench_ret:      pd.Series,
    prices:         pd.DataFrame,
    tickers:        list[str],
    initial_weights: list[float],
    initial_investment: float,
) -> None:
    """
    Render all Phase 4 charts.

    Layout
    ------
    Figure 1 (3-row):  Equity curves / Drawdown / Rolling Volatility
    Figure 2 (2-row):  Rolling Sharpe / Asset Growth
    Figure 3 (2-row):  Weight Drift / Return Distribution

    Calling plt.show() once at the end avoids blocking between figures.
    """
    # ── Figure 1 ──────────────────────────────
    fig1, axes1 = plt.subplots(3, 1, figsize=(13, 14))
    fig1.suptitle("Portfolio Analytics Report — Part 1",
                  fontsize=15, fontweight="bold", y=1.01)

    plot_equity_curves(port_val_eq, port_val_cust, bench_val,
                       initial_investment, ax=axes1[0])

    plot_drawdown(port_val_eq, bench_val,
                  port_label="Equal Weight", ax=axes1[1])

    plot_rolling_volatility(port_ret_eq, bench_ret,
                            port_label="Equal Weight", ax=axes1[2])

    fig1.tight_layout()

    # ── Figure 2 ──────────────────────────────
    fig2, axes2 = plt.subplots(2, 1, figsize=(13, 9))
    fig2.suptitle("Portfolio Analytics Report — Part 2",
                  fontsize=15, fontweight="bold", y=1.01)

    plot_rolling_sharpe(port_ret_eq, bench_ret,
                        port_label="Equal Weight", ax=axes2[0])

    plot_asset_growth(prices, tickers, ax=axes2[1])

    fig2.tight_layout()

    # ── Figure 3 ──────────────────────────────
    fig3, axes3 = plt.subplots(2, 1, figsize=(13, 9))
    fig3.suptitle("Portfolio Analytics Report — Part 3",
                  fontsize=15, fontweight="bold", y=1.01)

    plot_weight_drift(prices, tickers, initial_weights, ax=axes3[0])

    plot_return_distribution(port_ret_eq, bench_ret,
                             port_label="Equal Weight", ax=axes3[1])

    fig3.tight_layout()

    plt.show()
