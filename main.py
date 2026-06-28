"""
Portfolio Backtester — main.py
==============================
Phases completed:
  ✅ Phase 1   — Data Pipeline
  ✅ Phase 2.1 — Equal Weight Portfolio
  ✅ Phase 2.2 — Custom Weight Portfolio
  ✅ Phase 2.3 — Benchmark Engine (SPY)
  ✅ Phase 3   — Performance Metrics
  ✅ Phase 4   — Visualization & Diagnostics
  ✅ Phase 5   — Reporting (CSV / Excel / PDF / Grade / Narrative)

Run:
  python main.py
"""

from src.data_loader    import fetch_prices
from src.data_cleaner   import clean_prices, calculate_returns
from src.portfolio      import (
    custom_weights,
    equal_weights,
    portfolio_returns,
    portfolio_value,
    benchmark_returns,
    benchmark_value,
)
from src.metrics        import performance_report, comparison_summary
from src.visualization  import plot_all
from src.report         import generate_all_reports   # ← Phase 5

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

PORTFOLIO_TICKERS  = ["AAPL", "MSFT", "NVDA"]
BENCHMARK_TICKER   = "SPY"
START_DATE         = "2020-01-01"
END_DATE           = "2024-12-31"
INITIAL_INVESTMENT = 10_000
CUSTOM_WEIGHTS     = [0.4, 0.4, 0.2]

ALL_TICKERS = PORTFOLIO_TICKERS + [BENCHMARK_TICKER]

# ──────────────────────────────────────────────
# Phase 1 — Data Pipeline
# ──────────────────────────────────────────────

print("Downloading price data...")
raw_prices  = fetch_prices(ALL_TICKERS, START_DATE, END_DATE)
clean       = clean_prices(raw_prices)
all_returns = calculate_returns(clean)

print(f"Price data shape : {clean.shape}")
print(f"Returns shape    : {all_returns.shape}")

# ──────────────────────────────────────────────
# Phase 2 — Portfolios + Benchmark
# ──────────────────────────────────────────────

bench_ret = benchmark_returns(all_returns, BENCHMARK_TICKER)
bench_val = benchmark_value(bench_ret, INITIAL_INVESTMENT)

port_ret_eq = portfolio_returns(
    all_returns[PORTFOLIO_TICKERS],
    equal_weights(len(PORTFOLIO_TICKERS))
)
port_val_eq = portfolio_value(port_ret_eq, INITIAL_INVESTMENT)

port_ret_cust = portfolio_returns(
    all_returns[PORTFOLIO_TICKERS],
    custom_weights(CUSTOM_WEIGHTS)
)
port_val_cust = portfolio_value(port_ret_cust, INITIAL_INVESTMENT)

# ──────────────────────────────────────────────
# Phase 3 — Performance Reports
# ──────────────────────────────────────────────

bench_metrics = performance_report(
    label              = "Benchmark — SPY",
    equity_curve       = bench_val,
    daily_returns      = bench_ret,
    initial_investment = INITIAL_INVESTMENT,
    bench_returns      = None,
)

eq_metrics = performance_report(
    label              = "Equal Weight Portfolio (AAPL 33 / MSFT 33 / NVDA 33)",
    equity_curve       = port_val_eq,
    daily_returns      = port_ret_eq,
    initial_investment = INITIAL_INVESTMENT,
    bench_returns      = bench_ret,
)

cust_metrics = performance_report(
    label              = "Custom Weight Portfolio (AAPL 40 / MSFT 40 / NVDA 20)",
    equity_curve       = port_val_cust,
    daily_returns      = port_ret_cust,
    initial_investment = INITIAL_INVESTMENT,
    bench_returns      = bench_ret,
)

comparison_summary(eq_metrics,   bench_metrics, "Equal Weight",  "SPY")
comparison_summary(cust_metrics, bench_metrics, "Custom Weight", "SPY")

# ──────────────────────────────────────────────
# Phase 4 — Visualization
# ──────────────────────────────────────────────

plot_all(
    port_val_eq        = port_val_eq,
    port_val_cust      = port_val_cust,
    bench_val          = bench_val,
    port_ret_eq        = port_ret_eq,
    port_ret_cust      = port_ret_cust,
    bench_ret          = bench_ret,
    prices             = clean[PORTFOLIO_TICKERS],
    tickers            = PORTFOLIO_TICKERS,
    initial_weights    = CUSTOM_WEIGHTS,
    initial_investment = INITIAL_INVESTMENT,
)

# ──────────────────────────────────────────────
# Phase 5 — Reporting
# ──────────────────────────────────────────────
# We pass eq_metrics as the "primary" portfolio metrics for the PDF
# cover page and summary. The Excel and CSV files include both portfolios.

generate_all_reports(
    port_label         = "Equal Weight Portfolio (AAPL / MSFT / NVDA)",
    port_metrics       = eq_metrics,
    bench_metrics      = bench_metrics,
    eq_metrics         = eq_metrics,
    cust_metrics       = cust_metrics,
    port_val_eq        = port_val_eq,
    port_val_cust      = port_val_cust,
    bench_val          = bench_val,
    port_ret_eq        = port_ret_eq,
    port_ret_cust      = port_ret_cust,
    bench_ret          = bench_ret,
    bench_label        = "SPY",
    initial_investment = INITIAL_INVESTMENT,
    start_date         = START_DATE,
    end_date           = END_DATE,
)