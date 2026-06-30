import { useState, useEffect } from "react";
import {
  TrendingUp,
  Percent,
  Activity,
  Plus,
  Trash,
  AlertCircle,
  Calendar,
  DollarSign,
  Shield,
  Layers,
  ArrowRightLeft,
  RefreshCw,
} from "lucide-react";
import { InteractiveChart } from "./components/InteractiveChart";
import { StackedAreaChart } from "./components/StackedAreaChart";
import "./App.css";

// Color assignments for assets in individual charts
const ASSET_COLORS = [
  "#a855f7", // purple
  "#06b6d4", // cyan
  "#f97316", // orange
  "#ec4899", // pink
  "#14b8a6", // teal
  "#eab308", // yellow
  "#3b82f6", // blue
];

interface MetricSet {
  total_return: number;
  cagr: number;
  ann_volatility: number;
  sharpe_ratio: number | null;
  max_drawdown: number;
  beta: number | null;
  alpha: number | null;
}

interface StockPerformance {
  ticker: string;
  initial_price: number;
  final_price: number;
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
}

interface BacktestResponse {
  tickers: string[];
  weights: number[];
  benchmark: string;
  dates: string[];
  equity_curves: any[];
  drawdowns: any[];
  rolling_volatility: any[];
  rolling_sharpe: any[];
  weight_drift: any[];
  correlation_matrix: any[];
  stock_performances: { [ticker: string]: StockPerformance };
  metrics: {
    custom: MetricSet;
    equal: MetricSet;
    benchmark: MetricSet;
  };
}

function App() {
  // Input parameters
  const [tickerInputs, setTickerInputs] = useState<{ ticker: string; weight: string }[]>([
    { ticker: "AAPL", weight: "40" },
    { ticker: "MSFT", weight: "40" },
    { ticker: "NVDA", weight: "20" },
  ]);
  const [benchmark, setBenchmark] = useState("SPY");
  const [startDate, setStartDate] = useState("2020-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [initialInvestment, setInitialInvestment] = useState("10000");

  // API states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BacktestResponse | null>(null);

  // UI state
  const [activeTab, setActiveTab] = useState<"overview" | "risk" | "drift" | "assets">("overview");
  const [metricsFocus, setMetricsFocus] = useState<"custom" | "equal" | "benchmark">("custom");

  // Calculate sum of weights
  const weightSum = tickerInputs.reduce((sum, item) => sum + (parseFloat(item.weight) || 0), 0);
  const isWeightValid = Math.abs(weightSum - 100) < 0.01;

  // Run backtest request
  const runBacktest = async () => {
    setLoading(true);
    setError(null);

    const tickers = tickerInputs.map((t) => t.ticker.trim().toUpperCase()).filter((t) => t !== "");
    const weights = tickerInputs.map((t) => (parseFloat(t.weight) || 0) / 100);

    try {
      const response = await fetch("http://localhost:5000/api/backtest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tickers,
          benchmark: benchmark.trim().toUpperCase(),
          start_date: startDate,
          end_date: endDate,
          initial_investment: initialInvestment,
          weights,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Failed to execute backtest");
      }

      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Run initial backtest on load
  useEffect(() => {
    runBacktest();
  }, []);

  const handleAddTicker = () => {
    setTickerInputs([...tickerInputs, { ticker: "", weight: "0" }]);
  };

  const handleRemoveTicker = (index: number) => {
    const updated = [...tickerInputs];
    updated.splice(index, 1);
    setTickerInputs(updated);
  };

  const handleTickerChange = (index: number, field: "ticker" | "weight", value: string) => {
    const updated = [...tickerInputs];
    updated[index][field] = value;
    setTickerInputs(updated);
  };

  // Colors mapping for weights stack and stock performances
  const getAssetColors = () => {
    const map: { [ticker: string]: string } = {};
    tickerInputs.forEach((item, idx) => {
      if (item.ticker) {
        map[item.ticker.toUpperCase()] = ASSET_COLORS[idx % ASSET_COLORS.length];
      }
    });
    return map;
  };

  // Formatting helpers
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(val);
  };

  const formatPercent = (val: number | null) => {
    if (val === null || val === undefined) return "N/A";
    const sign = val >= 0 ? "+" : "";
    return `${sign}${(val * 100).toFixed(2)}%`;
  };

  const formatSimplePercent = (val: number) => {
    return `${val.toFixed(1)}%`;
  };

  const formatNumber = (val: number | null, decimals = 3) => {
    if (val === null || val === undefined) return "N/A";
    return val.toFixed(decimals);
  };

  const selectedMetrics = result ? result.metrics[metricsFocus] : null;
  const assetColors = getAssetColors();

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="dashboard-header">
        <div className="dashboard-title-group">
          <h1>Portfolio Analytics Engine</h1>
          <p>
            Systematic Backtester & Portfolio Optimization • Static-free Performance Reports
          </p>
        </div>
        <div className="mono" style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "flex", gap: "1rem" }}>
          <span>API Status: <span style={{ color: "var(--color-equal)" }}>● ONLINE</span></span>
          <span>Port: 5000</span>
        </div>
      </header>

      {/* Main Grid */}
      <div className="dashboard-container">
        {/* Left Control Column */}
        <aside className="config-panel">
          <div className="config-section-title">Backtest Parameters</div>

          {/* Date range */}
          <div className="form-group">
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Calendar size={14} /> Start Date
            </label>
            <input
              type="date"
              className="form-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Calendar size={14} /> End Date
            </label>
            <input
              type="date"
              className="form-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          {/* Capital */}
          <div className="form-group">
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <DollarSign size={14} /> Initial Principal
            </label>
            <input
              type="number"
              className="form-input"
              value={initialInvestment}
              onChange={(e) => setInitialInvestment(e.target.value)}
            />
          </div>

          {/* Benchmark */}
          <div className="form-group">
            <label>Benchmark Ticker</label>
            <input
              type="text"
              className="form-input code"
              value={benchmark}
              onChange={(e) => setBenchmark(e.target.value)}
            />
          </div>

          <div className="config-section-title" style={{ marginTop: "0.5rem" }}>
            Portfolio Assets & Weights
          </div>

          <div className="weights-grid">
            {tickerInputs.map((item, idx) => (
              <div key={idx} className="weight-row">
                <input
                  type="text"
                  placeholder="Ticker"
                  className="form-input code"
                  value={item.ticker}
                  onChange={(e) => handleTickerChange(idx, "ticker", e.target.value)}
                  style={{ textTransform: "uppercase" }}
                />
                <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <input
                    type="number"
                    placeholder="%"
                    className="form-input code"
                    value={item.weight}
                    onChange={(e) => handleTickerChange(idx, "weight", e.target.value)}
                    style={{ textAlign: "right" }}
                  />
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>%</span>
                </div>
                {tickerInputs.length > 1 ? (
                  <button className="btn-remove" onClick={() => handleRemoveTicker(idx)}>
                    <Trash size={14} />
                  </button>
                ) : (
                  <div />
                )}
              </div>
            ))}
          </div>

          <button className="btn-add" onClick={handleAddTicker}>
            <Plus size={14} /> Add Asset
          </button>

          {/* Weight Validation Message */}
          <div
            style={{
              padding: "0.75rem",
              borderRadius: "var(--radius-md)",
              backgroundColor: isWeightValid ? "rgba(16, 185, 129, 0.08)" : "rgba(245, 158, 11, 0.08)",
              border: `1px solid ${isWeightValid ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)"}`,
              fontSize: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <AlertCircle size={14} className={isWeightValid ? "text-success" : "text-benchmark"} />
            <div>
              Total Allocation: <span className="mono font-bold">{weightSum.toFixed(1)}%</span>
              {!isWeightValid && <div style={{ color: "var(--text-secondary)", marginTop: "0.1rem" }}>Allocation must sum to 100%</div>}
            </div>
          </div>

          <button className="btn-submit" onClick={runBacktest} disabled={loading || !isWeightValid}>
            {loading ? (
              <>
                <RefreshCw size={16} className="spinner" /> Backtesting...
              </>
            ) : (
              "Run Backtest Analytics"
            )}
          </button>
        </aside>

        {/* Right Main Panel */}
        <main className="dashboard-main">
          {error && (
            <div className="error-container">
              <Shield size={18} />
              <div>
                <strong>Error running backtester:</strong> {error}
              </div>
            </div>
          )}

          {/* Tab Selection */}
          <div className="tabs-header">
            <button
              className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              <TrendingUp size={16} style={{ display: "inline", marginRight: "0.5rem", verticalAlign: "middle" }} />
              Performance & Curves
            </button>
            <button
              className={`tab-btn ${activeTab === "risk" ? "active" : ""}`}
              onClick={() => setActiveTab("risk")}
            >
              <Activity size={16} style={{ display: "inline", marginRight: "0.5rem", verticalAlign: "middle" }} />
              Risk & Volatility
            </button>
            <button
              className={`tab-btn ${activeTab === "drift" ? "active" : ""}`}
              onClick={() => setActiveTab("drift")}
            >
              <Layers size={16} style={{ display: "inline", marginRight: "0.5rem", verticalAlign: "middle" }} />
              Drift & Correlation
            </button>
            <button
              className={`tab-btn ${activeTab === "assets" ? "active" : ""}`}
              onClick={() => setActiveTab("assets")}
            >
              <ArrowRightLeft size={16} style={{ display: "inline", marginRight: "0.5rem", verticalAlign: "middle" }} />
              Asset Performance
            </button>
          </div>

          {loading && !result && (
            <div className="loading-container">
              <RefreshCw size={36} className="spinner" />
              <h3>Fetching Historical Market Data...</h3>
              <p style={{ color: "var(--text-secondary)" }}>Connecting to Yahoo Finance to fetch prices and evaluate returns.</p>
            </div>
          )}

          {/* Dashboard Data Views */}
          {result && (
            <>
              {/* Target Portfolio metrics switcher */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  backgroundColor: "var(--bg-secondary)",
                  padding: "0.75rem 1.25rem",
                  borderRadius: "var(--radius-lg)",
                  border: "1px solid var(--border-color)",
                }}
              >
                <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Display Focus:</span>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    className={`tab-btn ${metricsFocus === "custom" ? "active" : ""}`}
                    onClick={() => setMetricsFocus("custom")}
                    style={{ padding: "0.35rem 0.75rem", borderBottomWidth: "1px", borderRadius: "var(--radius-sm)" }}
                  >
                    Custom Weights Portfolio
                  </button>
                  <button
                    className={`tab-btn ${metricsFocus === "equal" ? "active" : ""}`}
                    onClick={() => setMetricsFocus("equal")}
                    style={{ padding: "0.35rem 0.75rem", borderBottomWidth: "1px", borderRadius: "var(--radius-sm)" }}
                  >
                    Equal Weights Portfolio
                  </button>
                  <button
                    className={`tab-btn ${metricsFocus === "benchmark" ? "active" : ""}`}
                    onClick={() => setMetricsFocus("benchmark")}
                    style={{ padding: "0.35rem 0.75rem", borderBottomWidth: "1px", borderRadius: "var(--radius-sm)" }}
                  >
                    Benchmark ({result.benchmark || "SPY"})
                  </button>
                </div>
              </div>

              {/* Metrics Grid Cards */}
              {selectedMetrics && (
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-card-title">
                      Total Cumulative Return <TrendingUp size={14} className="text-accent" />
                    </div>
                    <div className="metric-card-value mono" style={{ color: selectedMetrics.total_return >= 0 ? "var(--color-equal)" : "var(--color-danger)" }}>
                      {formatPercent(selectedMetrics.total_return)}
                    </div>
                    <div className="metric-card-footer">Over full backtest period</div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-card-title">
                      Compound Annual Growth (CAGR) <Percent size={14} className="text-accent" />
                    </div>
                    <div className="metric-card-value mono" style={{ color: selectedMetrics.cagr >= 0 ? "var(--color-equal)" : "var(--color-danger)" }}>
                      {formatPercent(selectedMetrics.cagr)}
                    </div>
                    <div className="metric-card-footer">Annualized geometric return</div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-card-title">
                      Risk-Adjusted (Sharpe Ratio) <Activity size={14} className="text-accent" />
                    </div>
                    <div className="metric-card-value mono">
                      {formatNumber(selectedMetrics.sharpe_ratio)}
                    </div>
                    <div className="metric-card-footer">Risk-Free Rate: 2.0%</div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-card-title">
                      Max Drawdown Peak-to-Trough <Shield size={14} className="text-danger" />
                    </div>
                    <div className="metric-card-value mono text-danger">
                      {formatPercent(selectedMetrics.max_drawdown)}
                    </div>
                    <div className="metric-card-footer">Worst peak-to-trough decline</div>
                  </div>
                </div>
              )}

              {/* Tab 1: Performance Overview */}
              {activeTab === "overview" && (
                <>
                  <div className="chart-card">
                    <div className="chart-card-header">
                      <div className="chart-card-title">Growth of Principal (${initialInvestment})</div>
                      <div className="chart-legend">
                        <div className="legend-item">
                          <span className="legend-dot bg-custom" />
                          <span>Custom Portfolio</span>
                        </div>
                        <div className="legend-item">
                          <span className="legend-dot bg-equal" />
                          <span>Equal Weight Portfolio</span>
                        </div>
                        <div className="legend-item">
                          <span className="legend-dot bg-benchmark" />
                          <span>Benchmark ({result.benchmark || "SPY"})</span>
                        </div>
                      </div>
                    </div>
                    <InteractiveChart
                      data={result.equity_curves}
                      keys={["custom", "equal", "benchmark"]}
                      colors={{ custom: "var(--color-custom)", equal: "var(--color-equal)", benchmark: "var(--color-benchmark)" }}
                      labels={{ custom: "Custom Weight", equal: "Equal Weight", benchmark: "Benchmark SPY" }}
                      formatY={formatCurrency}
                    />
                  </div>

                  <div className="chart-card" style={{ padding: "1.25rem" }}>
                    <div className="chart-card-title" style={{ marginBottom: "0.5rem" }}>Comparative Performance Matrix</div>
                    <div className="table-wrapper">
                      <table className="dashboard-table">
                        <thead>
                          <tr>
                            <th>Performance Metric</th>
                            <th className="text-custom">Custom Weights</th>
                            <th className="text-equal">Equal Weights</th>
                            <th className="text-benchmark">Benchmark (SPY)</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>Total Return</td>
                            <td className="mono font-semibold text-custom">{formatPercent(result.metrics.custom.total_return)}</td>
                            <td className="mono font-semibold text-equal">{formatPercent(result.metrics.equal.total_return)}</td>
                            <td className="mono font-semibold text-benchmark">{formatPercent(result.metrics.benchmark.total_return)}</td>
                          </tr>
                          <tr>
                            <td>CAGR</td>
                            <td className="mono text-custom">{formatPercent(result.metrics.custom.cagr)}</td>
                            <td className="mono text-equal">{formatPercent(result.metrics.equal.cagr)}</td>
                            <td className="mono text-benchmark">{formatPercent(result.metrics.benchmark.cagr)}</td>
                          </tr>
                          <tr>
                            <td>Annual Volatility</td>
                            <td className="mono">{formatSimplePercent(result.metrics.custom.ann_volatility * 100)}</td>
                            <td className="mono">{formatSimplePercent(result.metrics.equal.ann_volatility * 100)}</td>
                            <td className="mono">{formatSimplePercent(result.metrics.benchmark.ann_volatility * 100)}</td>
                          </tr>
                          <tr>
                            <td>Sharpe Ratio</td>
                            <td className="mono font-semibold">{formatNumber(result.metrics.custom.sharpe_ratio)}</td>
                            <td className="mono font-semibold">{formatNumber(result.metrics.equal.sharpe_ratio)}</td>
                            <td className="mono font-semibold">{formatNumber(result.metrics.benchmark.sharpe_ratio)}</td>
                          </tr>
                          <tr>
                            <td>Max Drawdown</td>
                            <td className="mono text-danger">{formatPercent(result.metrics.custom.max_drawdown)}</td>
                            <td className="mono text-danger">{formatPercent(result.metrics.equal.max_drawdown)}</td>
                            <td className="mono text-danger">{formatPercent(result.metrics.benchmark.max_drawdown)}</td>
                          </tr>
                          <tr>
                            <td>Portfolio Beta</td>
                            <td className="mono">{formatNumber(result.metrics.custom.beta)}</td>
                            <td className="mono">{formatNumber(result.metrics.equal.beta)}</td>
                            <td className="mono">1.000</td>
                          </tr>
                          <tr>
                            <td>Jensen's Alpha (Ann.)</td>
                            <td className="mono font-semibold text-custom">{formatPercent(result.metrics.custom.alpha)}</td>
                            <td className="mono font-semibold text-equal">{formatPercent(result.metrics.equal.alpha)}</td>
                            <td className="mono">0.00%</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}

              {/* Tab 2: Risk & Drawdown */}
              {activeTab === "risk" && (
                <>
                  <div className="chart-card">
                    <div className="chart-card-header">
                      <div className="chart-card-title">Peak-to-Trough Drawdown Depth (%)</div>
                      <div className="chart-legend">
                        <div className="legend-item"><span className="legend-dot bg-custom" /><span>Custom</span></div>
                        <div className="legend-item"><span className="legend-dot bg-equal" /><span>Equal</span></div>
                        <div className="legend-item"><span className="legend-dot bg-benchmark" /><span>Benchmark</span></div>
                      </div>
                    </div>
                    <InteractiveChart
                      data={result.drawdowns}
                      keys={["custom", "equal", "benchmark"]}
                      colors={{ custom: "var(--color-custom)", equal: "var(--color-equal)", benchmark: "var(--color-benchmark)" }}
                      labels={{ custom: "Custom DD", equal: "Equal DD", benchmark: "Benchmark DD" }}
                      formatY={formatSimplePercent}
                    />
                  </div>

                  <div className="chart-card">
                    <div className="chart-card-header">
                      <div className="chart-card-title">63-Day Rolling Annualised Volatility (%)</div>
                      <div className="chart-legend">
                        <div className="legend-item"><span className="legend-dot bg-custom" /><span>Custom</span></div>
                        <div className="legend-item"><span className="legend-dot bg-equal" /><span>Equal</span></div>
                        <div className="legend-item"><span className="legend-dot bg-benchmark" /><span>Benchmark</span></div>
                      </div>
                    </div>
                    <InteractiveChart
                      data={result.rolling_volatility}
                      keys={["custom", "equal", "benchmark"]}
                      colors={{ custom: "var(--color-custom)", equal: "var(--color-equal)", benchmark: "var(--color-benchmark)" }}
                      labels={{ custom: "Custom Vol", equal: "Equal Vol", benchmark: "Benchmark Vol" }}
                      formatY={formatSimplePercent}
                    />
                  </div>

                  <div className="chart-card">
                    <div className="chart-card-header">
                      <div className="chart-card-title">63-Day Rolling Sharpe Ratio</div>
                      <div className="chart-legend">
                        <div className="legend-item"><span className="legend-dot bg-custom" /><span>Custom</span></div>
                        <div className="legend-item"><span className="legend-dot bg-equal" /><span>Equal</span></div>
                        <div className="legend-item"><span className="legend-dot bg-benchmark" /><span>Benchmark</span></div>
                      </div>
                    </div>
                    <InteractiveChart
                      data={result.rolling_sharpe}
                      keys={["custom", "equal", "benchmark"]}
                      colors={{ custom: "var(--color-custom)", equal: "var(--color-equal)", benchmark: "var(--color-benchmark)" }}
                      labels={{ custom: "Custom Sharpe", equal: "Equal Sharpe", benchmark: "Benchmark Sharpe" }}
                      formatY={(v) => v.toFixed(2)}
                    />
                  </div>
                </>
              )}

              {/* Tab 3: Drift & Correlation */}
              {activeTab === "drift" && (
                <>
                  <div className="chart-card">
                    <div className="chart-card-header">
                      <div className="chart-card-title">Portfolio Weight Drift Over Time (No Rebalancing)</div>
                      <div className="chart-legend">
                        {tickerInputs.map((item, idx) => (
                          <div key={idx} className="legend-item">
                            <span className="legend-dot" style={{ backgroundColor: assetColors[item.ticker.toUpperCase()] }} />
                            <span>{item.ticker.toUpperCase()}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <StackedAreaChart
                      data={result.weight_drift}
                      tickers={result.tickers}
                      colors={assetColors}
                    />
                  </div>

                  <div className="chart-card" style={{ padding: "1.25rem" }}>
                    <div className="chart-card-title" style={{ marginBottom: "0.25rem" }}>Asset Correlation Matrix (Daily Returns)</div>
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
                      Correlation coefficients range between -1 and +1. Lighter shades represent higher correlation.
                    </p>
                    <div className="table-wrapper">
                      <table className="heatmap-table">
                        <thead>
                          <tr>
                            <th>Ticker</th>
                            {result.tickers.map((t) => (
                              <th key={t}>{t}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {result.correlation_matrix.map((row) => (
                            <tr key={row.ticker}>
                              <td style={{ fontWeight: 600, backgroundColor: "var(--bg-tertiary)" }}>{row.ticker}</td>
                              {result.tickers.map((colTicker) => {
                                const corrVal = row[colTicker];
                                // Interpolate color dynamically: 0 correlation is transparent/dark blue, 1 correlation is bright accent bg
                                const alphaVal = Math.abs(corrVal).toFixed(2);
                                return (
                                  <td
                                    key={colTicker}
                                    className="heatmap-cell"
                                    style={{
                                      backgroundColor: `rgba(99, 102, 241, ${0.1 + parseFloat(alphaVal) * 0.45})`,
                                      border: "1px solid var(--border-color)",
                                    }}
                                  >
                                    {corrVal.toFixed(3)}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}

              {/* Tab 4: Asset Performances */}
              {activeTab === "assets" && (
                <div className="chart-card" style={{ padding: "1.25rem" }}>
                  <div className="chart-card-title" style={{ marginBottom: "1rem" }}>Individual Asset Diagnostics</div>
                  <div className="table-wrapper">
                    <table className="dashboard-table">
                      <thead>
                        <tr>
                          <th>Asset Ticker</th>
                          <th>Allocation Weight</th>
                          <th>Initial Price (Start Date)</th>
                          <th>Final Price (End Date)</th>
                          <th>Cumulative Return</th>
                          <th>Annualized CAGR</th>
                          <th>Sharpe Ratio</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.tickers.map((ticker, idx) => {
                          const perf = result.stock_performances[ticker];
                          const weightVal = result.weights[idx];
                          return (
                            <tr key={ticker}>
                              <td style={{ fontWeight: 700, color: assetColors[ticker] }}>{ticker}</td>
                              <td className="mono font-semibold">{(weightVal * 100).toFixed(1)}%</td>
                              <td className="mono">{perf ? `$${perf.initial_price.toFixed(2)}` : "N/A"}</td>
                              <td className="mono">{perf ? `$${perf.final_price.toFixed(2)}` : "N/A"}</td>
                              <td className="mono font-semibold" style={{ color: perf && perf.total_return >= 0 ? "var(--color-equal)" : "var(--color-danger)" }}>
                                {perf ? formatPercent(perf.total_return) : "N/A"}
                              </td>
                              <td className="mono" style={{ color: perf && perf.cagr >= 0 ? "var(--color-equal)" : "var(--color-danger)" }}>
                                {perf ? formatPercent(perf.cagr) : "N/A"}
                              </td>
                              <td className="mono font-semibold">
                                {perf ? formatNumber(perf.sharpe_ratio) : "N/A"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
