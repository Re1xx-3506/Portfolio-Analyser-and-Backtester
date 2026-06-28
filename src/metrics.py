"""
src/metrics.py
==============
Phase 3 — Performance Metrics

All functions accept pd.Series inputs so they slot cleanly into the
existing pipeline.  Each function is self-contained and independently
testable.

Assumptions
-----------
- 252 trading days per year for annualisation.
- Risk-free rate defaults to RISK_FREE_RATE (2 % annualised).
  Change the constant below or pass rf= explicitly to any function.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE_RATE = 0.02          # 2 % annualised — change here to update everywhere


# ──────────────────────────────────────────────
# Individual Metrics
# ──────────────────────────────────────────────

def total_return(equity_curve: pd.Series, initial_investment: float) -> float:
    """
    Total Return = (final_value / initial_value) - 1

    Example: 10 000 → 18 000  =>  0.80  (80 %)
    """
    return equity_curve.iloc[-1] / initial_investment - 1


def cagr(equity_curve: pd.Series, initial_investment: float) -> float:
    """
    Compound Annual Growth Rate.

    Formula: (final / initial) ** (1 / years) - 1

    Years is estimated from the number of trading-day rows / 252,
    so no calendar maths is needed.
    """
    years = len(equity_curve) / TRADING_DAYS
    return (equity_curve.iloc[-1] / initial_investment) ** (1 / years) - 1


def annualized_volatility(daily_returns: pd.Series) -> float:
    """
    Annualised Volatility = std(daily_returns) * sqrt(252)

    Uses the sample standard deviation (ddof=1, pandas default).
    """
    return daily_returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(
    daily_returns: pd.Series,
    rf: float = RISK_FREE_RATE
) -> float:
    """
    Sharpe Ratio = (annualised_return - rf) / annualised_volatility

    Annualised return is computed from the mean daily return * 252,
    which is the standard approximation used in practice.
    """
    ann_return = daily_returns.mean() * TRADING_DAYS
    ann_vol    = annualized_volatility(daily_returns)
    if ann_vol == 0:
        return np.nan
    return (ann_return - rf) / ann_vol


def max_drawdown(equity_curve: pd.Series) -> float:
    """
    Max Drawdown = min( (curve - running_max) / running_max )

    Returns a negative number, e.g. -0.34 means a 34 % peak-to-trough
    decline was the worst observed drawdown.
    """
    running_max = equity_curve.cummax()
    drawdown    = (equity_curve - running_max) / running_max
    return drawdown.min()


def beta(
    port_returns: pd.Series,
    bench_returns: pd.Series
) -> float:
    """
    Beta = Cov(portfolio, benchmark) / Var(benchmark)

    Measures how much the portfolio moves relative to the benchmark.
    Beta > 1 means more volatile than the market.
    """
    cov_matrix = np.cov(port_returns, bench_returns)
    return cov_matrix[0, 1] / cov_matrix[1, 1]


def alpha(
    port_returns: pd.Series,
    bench_returns: pd.Series,
    rf: float = RISK_FREE_RATE
) -> float:
    """
    Jensen's Alpha (annualised).

    Alpha = ann_port_return - [ rf + beta * (ann_bench_return - rf) ]

    Positive alpha means the portfolio outperformed what its market
    exposure alone would predict.
    """
    ann_port  = port_returns.mean()  * TRADING_DAYS
    ann_bench = bench_returns.mean() * TRADING_DAYS
    b         = beta(port_returns, bench_returns)
    return ann_port - (rf + b * (ann_bench - rf))


def outperformance(
    port_total_return: float,
    bench_total_return: float
) -> float:
    """
    Outperformance % = portfolio total return - benchmark total return

    Both inputs should already be decimal fractions (e.g. 0.80, not 80).
    """
    return port_total_return - bench_total_return


# ──────────────────────────────────────────────
# Report Builder
# ──────────────────────────────────────────────

def performance_report(
    label: str,
    equity_curve: pd.Series,
    daily_returns: pd.Series,
    initial_investment: float,
    bench_returns: pd.Series | None = None,
    rf: float = RISK_FREE_RATE,
) -> dict:
    """
    Compute all Phase 3 metrics for one portfolio or benchmark.

    Parameters
    ----------
    label              : display name, e.g. "Custom Weight Portfolio"
    equity_curve       : pd.Series from portfolio_value() or benchmark_value()
    daily_returns      : pd.Series from portfolio_returns() or benchmark_returns()
    initial_investment : starting capital
    bench_returns      : pd.Series — required to compute Beta and Alpha;
                         pass None for the benchmark itself
    rf                 : annualised risk-free rate (default RISK_FREE_RATE)

    Returns
    -------
    dict of metric name → value
    """
    tr   = total_return(equity_curve, initial_investment)
    c    = cagr(equity_curve, initial_investment)
    vol  = annualized_volatility(daily_returns)
    sr   = sharpe_ratio(daily_returns, rf)
    mdd  = max_drawdown(equity_curve)

    b    = beta(daily_returns, bench_returns)  if bench_returns is not None else None
    a    = alpha(daily_returns, bench_returns, rf) if bench_returns is not None else None

    # ── Print ──────────────────────────────────
    w = 44
    print("\n" + "=" * w)
    print(f"  {label}")
    print("=" * w)
    print(f"  Total Return        : {tr * 100:+.2f}%")
    print(f"  CAGR                : {c  * 100:+.2f}%")
    print(f"  Ann. Volatility     : {vol* 100:.2f}%")
    print(f"  Sharpe Ratio        : {sr:.3f}")
    print(f"  Max Drawdown        : {mdd* 100:.2f}%")
    if b is not None:
        print(f"  Beta (vs benchmark) : {b:.3f}")
    if a is not None:
        print(f"  Alpha (annualised)  : {a * 100:+.2f}%")
    print("=" * w)

    return {
        "total_return"  : tr,
        "cagr"          : c,
        "ann_volatility": vol,
        "sharpe_ratio"  : sr,
        "max_drawdown"  : mdd,
        "beta"          : b,
        "alpha"         : a,
    }


def comparison_summary(
    port_metrics: dict,
    bench_metrics: dict,
    port_label: str = "Portfolio",
    bench_label: str = "SPY",
) -> None:
    """
    Print a side-by-side outperformance summary after both reports.
    """
    op = outperformance(
        port_metrics["total_return"],
        bench_metrics["total_return"]
    )
    w = 44
    print("\n" + "=" * w)
    print(f"  {port_label} vs {bench_label}")
    print("=" * w)
    print(f"  {port_label} Total Return  : {port_metrics['total_return']  * 100:+.2f}%")
    print(f"  {bench_label} Total Return : {bench_metrics['total_return'] * 100:+.2f}%")
    print(f"  Outperformance        : {op * 100:+.2f}%")
    print("=" * w + "\n")