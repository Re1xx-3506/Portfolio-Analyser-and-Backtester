import traceback
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.data_loader import fetch_prices
from src.data_cleaner import clean_prices, calculate_returns
from src.portfolio import (
    custom_weights,
    equal_weights,
    portfolio_returns,
    portfolio_value,
    benchmark_returns,
    benchmark_value,
)
from src.metrics import performance_report

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

TRADING_DAYS = 252
RISK_FREE_RATE = 0.02
ROLLING_WINDOW = 63

def series_to_list(series):
    """Convert pandas series with datetime index to list of dicts with date and value."""
    return [{"date": str(date.date()), "value": float(val)} for date, val in series.items()]

def get_rolling_volatility(daily_returns, window=ROLLING_WINDOW):
    """Calculate rolling volatility as standard deviation multiplied by sqrt(252)."""
    roll_vol = daily_returns.rolling(window).std() * np.sqrt(TRADING_DAYS)
    # Replace NaNs (which occur at the beginning of the window) with None
    roll_vol = roll_vol.replace({np.nan: None})
    return [{"date": str(date.date()), "value": float(val) if val is not None else None} for date, val in roll_vol.items()]

def get_rolling_sharpe(daily_returns, window=ROLLING_WINDOW, rf=RISK_FREE_RATE):
    """Calculate rolling Sharpe ratio."""
    roll_mean = daily_returns.rolling(window).mean()
    roll_std = daily_returns.rolling(window).std()
    ann_ret = roll_mean * TRADING_DAYS
    ann_vol = roll_std * np.sqrt(TRADING_DAYS)
    roll_sharpe = (ann_ret - rf) / ann_vol
    roll_sharpe = roll_sharpe.replace({np.nan: None, np.inf: None, -np.inf: None})
    return [{"date": str(date.date()), "value": float(val) if val is not None else None} for date, val in roll_sharpe.items()]

def compute_drawdown_series(equity_curve):
    """Calculate drawdown percentage over time."""
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max * 100
    return [{"date": str(date.date()), "value": float(val)} for date, val in drawdown.items()]

def compute_weight_drift(prices, tickers, initial_weights):
    """Calculate the drifted weight of each asset over time."""
    subset = prices[tickers].copy()
    norm = subset / subset.iloc[0]
    holdings = norm * np.array(initial_weights)
    weights_over_time = holdings.div(holdings.sum(axis=1), axis=0) * 100
    
    drift_data = []
    for date, row in weights_over_time.iterrows():
        entry = {"date": str(date.date())}
        for ticker in tickers:
            entry[ticker] = float(row[ticker])
        drift_data.append(entry)
    return drift_data

@app.route("/api/backtest", methods=["POST"])
def backtest():
    try:
        data = request.get_json() or {}
        
        tickers = data.get("tickers", ["AAPL", "MSFT", "NVDA"])
        benchmark = data.get("benchmark", "SPY")
        start_date = data.get("start_date", "2020-01-01")
        end_date = data.get("end_date", "2024-12-31")
        initial_investment = float(data.get("initial_investment", 10000))
        weights = data.get("weights", [0.4, 0.4, 0.2])
        
        # Ensure distinct tickers and validate inputs
        if not tickers:
            return jsonify({"error": "At least one ticker must be provided."}), 400
        
        if len(tickers) != len(weights):
            return jsonify({"error": f"Number of tickers ({len(tickers)}) does not match number of weights ({len(weights)})."}), 400
            
        try:
            # Validate custom weights (sums to 1, no negative numbers)
            validated_weights = custom_weights(weights)
        except Exception as e:
            return jsonify({"error": f"Invalid weights: {str(e)}"}), 400

        # Include benchmark in download list
        all_tickers = tickers.copy()
        if benchmark not in all_tickers:
            all_tickers.append(benchmark)
            
        print(f"Running backtest for {tickers} vs {benchmark} ({start_date} to {end_date})")
        
        # Fetch and clean price data
        raw_prices = fetch_prices(all_tickers, start_date, end_date)
        clean = clean_prices(raw_prices)
        all_returns = calculate_returns(clean)
        
        # Prepare returns and equity curves
        bench_ret = benchmark_returns(all_returns, benchmark)
        bench_val = benchmark_value(bench_ret, initial_investment)
        
        # 1. Custom weights portfolio
        port_ret_cust = portfolio_returns(all_returns[tickers], validated_weights)
        port_val_cust = portfolio_value(port_ret_cust, initial_investment)
        
        # 2. Equal weights portfolio
        eq_w = equal_weights(len(tickers))
        port_ret_eq = portfolio_returns(all_returns[tickers], eq_w)
        port_val_eq = portfolio_value(port_ret_eq, initial_investment)
        
        # Compute performance metrics
        bench_metrics = performance_report(
            label="Benchmark",
            equity_curve=bench_val,
            daily_returns=bench_ret,
            initial_investment=initial_investment,
            bench_returns=None
        )
        
        cust_metrics = performance_report(
            label="Custom Weights Portfolio",
            equity_curve=port_val_cust,
            daily_returns=port_ret_cust,
            initial_investment=initial_investment,
            bench_returns=bench_ret
        )
        
        eq_metrics = performance_report(
            label="Equal Weights Portfolio",
            equity_curve=port_val_eq,
            daily_returns=port_ret_eq,
            initial_investment=initial_investment,
            bench_returns=bench_ret
        )
        
        # Individual stock details (total returns, final value of $100, etc.)
        stock_performances = {}
        for t in tickers:
            stock_prices = clean[t]
            start_price = float(stock_prices.iloc[0])
            end_price = float(stock_prices.iloc[-1])
            tot_ret = (end_price / start_price - 1)
            stock_performances[t] = {
                "ticker": t,
                "initial_price": start_price,
                "final_price": end_price,
                "total_return": tot_ret,
                "cagr": float((end_price / start_price) ** (1 / (len(clean) / TRADING_DAYS)) - 1),
                "sharpe_ratio": float(sharpe_ratio_for_stock(all_returns[t]))
            }
            
        # Correlation matrix
        corr = all_returns[tickers].corr()
        corr_matrix = []
        for t1 in tickers:
            row = {"ticker": t1}
            for t2 in tickers:
                row[t2] = float(corr.loc[t1, t2])
            corr_matrix.append(row)
            
        # Response object
        dates = [str(d.date()) for d in all_returns.index]
        
        # Construct curves data in a format suitable for charting (aligned by date)
        equity_curves = []
        for d in all_returns.index:
            date_str = str(d.date())
            equity_curves.append({
                "date": date_str,
                "custom": float(port_val_cust.loc[d]),
                "equal": float(port_val_eq.loc[d]),
                "benchmark": float(bench_val.loc[d])
            })
            
        # Drawdowns series
        drawdowns = []
        dd_cust = (port_val_cust - port_val_cust.cummax()) / port_val_cust.cummax() * 100
        dd_eq = (port_val_eq - port_val_eq.cummax()) / port_val_eq.cummax() * 100
        dd_bench = (bench_val - bench_val.cummax()) / bench_val.cummax() * 100
        for d in all_returns.index:
            drawdowns.append({
                "date": str(d.date()),
                "custom": float(dd_cust.loc[d]),
                "equal": float(dd_eq.loc[d]),
                "benchmark": float(dd_bench.loc[d])
            })
            
        # Rolling Volatility & Sharpe
        rolling_vol = []
        rolling_sharpe = []
        roll_vol_cust = port_ret_cust.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS) * 100
        roll_vol_eq = port_ret_eq.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS) * 100
        roll_vol_bench = bench_ret.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS) * 100
        
        roll_sharpe_cust = (port_ret_cust.rolling(ROLLING_WINDOW).mean() * TRADING_DAYS - RISK_FREE_RATE) / (port_ret_cust.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS))
        roll_sharpe_eq = (port_ret_eq.rolling(ROLLING_WINDOW).mean() * TRADING_DAYS - RISK_FREE_RATE) / (port_ret_eq.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS))
        roll_sharpe_bench = (bench_ret.rolling(ROLLING_WINDOW).mean() * TRADING_DAYS - RISK_FREE_RATE) / (bench_ret.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS))

        for d in all_returns.index[ROLLING_WINDOW-1:]:
            date_str = str(d.date())
            rolling_vol.append({
                "date": date_str,
                "custom": float(roll_vol_cust.loc[d]) if not np.isnan(roll_vol_cust.loc[d]) else None,
                "equal": float(roll_vol_eq.loc[d]) if not np.isnan(roll_vol_eq.loc[d]) else None,
                "benchmark": float(roll_vol_bench.loc[d]) if not np.isnan(roll_vol_bench.loc[d]) else None
            })
            rolling_sharpe.append({
                "date": date_str,
                "custom": float(roll_sharpe_cust.loc[d]) if not np.isnan(roll_sharpe_cust.loc[d]) and not np.isinf(roll_sharpe_cust.loc[d]) else None,
                "equal": float(roll_sharpe_eq.loc[d]) if not np.isnan(roll_sharpe_eq.loc[d]) and not np.isinf(roll_sharpe_eq.loc[d]) else None,
                "benchmark": float(roll_sharpe_bench.loc[d]) if not np.isnan(roll_sharpe_bench.loc[d]) and not np.isinf(roll_sharpe_bench.loc[d]) else None
            })

        response = {
            "tickers": tickers,
            "weights": weights,
            "benchmark": benchmark,
            "dates": dates,
            "equity_curves": equity_curves,
            "drawdowns": drawdowns,
            "rolling_volatility": rolling_vol,
            "rolling_sharpe": rolling_sharpe,
            "weight_drift": compute_weight_drift(clean.loc[all_returns.index], tickers, validated_weights),
            "correlation_matrix": corr_matrix,
            "stock_performances": stock_performances,
            "metrics": {
                "custom": clean_metrics(cust_metrics),
                "equal": clean_metrics(eq_metrics),
                "benchmark": clean_metrics(bench_metrics)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

def sharpe_ratio_for_stock(stock_returns, rf=RISK_FREE_RATE):
    ann_return = stock_returns.mean() * TRADING_DAYS
    ann_vol = stock_returns.std() * np.sqrt(TRADING_DAYS)
    if ann_vol == 0 or np.isnan(ann_vol):
        return 0.0
    return (ann_return - rf) / ann_vol

def clean_metrics(metrics):
    cleaned = {}
    for k, v in metrics.items():
        if v is None:
            cleaned[k] = None
        elif np.isnan(v):
            cleaned[k] = None
        elif np.isinf(v):
            cleaned[k] = None
        else:
            cleaned[k] = float(v)
    return cleaned

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
