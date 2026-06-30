# Portfolio Analytics Engine 📈💼

A high-performance quantitative backtesting and optimization platform. This project features a robust **Python (Flask + Pandas + NumPy)** backend and an elegant, responsive **React 19 + TypeScript + Vite 8** dashboard running a default dark mode theme with zero charting library dependencies.

## Key Features
* **Dynamic Backtesting**: Input arbitrary stock ticker lists, custom weights, date ranges, and initial capital. Yahoo Finance data is retrieved and cleaned on-the-fly.
* **Dual Portfolio Evaluation**: Simultaneously models and compares a **Custom Weight Portfolio** against an **Equal Weight Portfolio** and a market **Benchmark** (e.g. SPY).
* **Comprehensive Quantitative Diagnostics**:
  * Total Cumulative Return & Compound Annual Growth Rate (CAGR).
  * Annualised Volatility & Risk-Adjusted Sharpe Ratio.
  * Max Drawdown Depth (Peak-to-Trough).
  * Systemic Risk Exposure (**Beta** vs benchmark) & Outperformance (**Jensen's Alpha**).
* **Advanced Visualizations**:
  * **Growth of Principal**: Equity curves comparing Custom Portfolio, Equal Weight Portfolio, and Benchmark.
  * **Rolling Metrics**: 63-day rolling volatility and 63-day rolling Sharpe ratio.
  * **Drawdown Depth**: Historical drawdown charts showing portfolio declines.
  * **Correlation Heatmap**: Inter-asset correlation matrix calculated from daily log returns.
  * **Weight Drift Diagnostics**: Shows how asset weights shift over time due to asset price movements with no rebalancing (stack area representation).
* **Static Reports Pipeline**: Generates clean CSV, Excel sheets, and professional PDF summary reports for offline access.

---

## Tech Stack
### Backend
* **Core**: Python 3.12+
* **Data & Science**: `pandas`, `numpy` for matrix algebra and returns series calculations
* **Feeds**: `yfinance` (Yahoo Finance API)
* **Web Services**: `Flask`, `Flask-CORS`
* **Static Exports**: `openpyxl` (Excel), `reportlab` (PDF generation)

### Frontend
* **Core**: React 19, TypeScript, Vite 8
* **Styling**: Pure CSS3 (custom CSS Variables design system optimized for dark mode)
* **Icons**: `lucide-react`
* **Visuals**: **Custom SVG Charts** (line, stacked area) built from scratch. Highly performant, fully responsive, and interactive (hover crosshair lines and floating tooltip readouts) with zero library dependency issues.

---

## Directory Structure
```
projects/pf/
├── server.py              # Flask API server entry point
├── main.py                # Standalone CLI backtester pipeline
├── requirements.txt       # Python virtual environment dependencies
├── src/                   # Python core modules
│   ├── data_loader.py     # YFinance prices retrieval
│   ├── data_cleaner.py    # Missing values removal and daily returns calculation
│   ├── portfolio.py       # Portfolio constructor and compounders
│   ├── metrics.py         # Sharpe, CAGR, Drawdowns, Alpha, and Beta calculations
│   ├── visualization.py   # Matplotlib standalone report charts
│   └── report.py          # CSV/Excel/PDF static generator
├── exports/               # Folder where main.py exports CSV/Excel sheets
├── reports/               # Folder where main.py exports PDF reports
└── frontend/              # React dashboard application
    ├── index.html         # Main app HTML layout (imports Google Fonts)
    ├── package.json       # Node package manager dependencies
    ├── vite.config.ts     # Vite compiler configuration
    └── src/
        ├── main.tsx       # React client entry point
        ├── App.tsx        # Dashboard shell and API client controller
        ├── App.css        # Local component level overrides
        ├── index.css      # Dark-mode design system & layout components
        └── components/
            ├── InteractiveChart.tsx  # Custom SVG line charts component
            └── StackedAreaChart.tsx  # Custom SVG stacked area drift chart
```

---

## Getting Started

### Prerequisites
* Python 3.12 or newer
* Node.js v24 or newer

### 1. Set Up and Launch Backend API
Navigate to the root directory and activate the virtual environment:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the Flask development API server
python server.py
```
The backend server will launch at **`http://localhost:5000`** with the POST `/api/backtest` endpoint active.

### 2. Set Up and Launch Frontend Dashboard
Open a new terminal window, navigate to the `frontend` folder, install dependencies, and start the Vite dev server:
```bash
# Go to frontend folder
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```
The frontend dev server will launch at **`http://localhost:5173`**. Open this URL in your web browser to access the dashboard.

---

## API Reference
### Backtest Portfolio
* **Endpoint**: `POST /api/backtest`
* **Content-Type**: `application/json`

#### Request Payload Example
```json
{
  "tickers": ["AAPL", "MSFT", "NVDA"],
  "weights": [0.4, 0.4, 0.2],
  "benchmark": "SPY",
  "start_date": "2020-01-16",
  "end_date": "2024-12-19",
  "initial_investment": 10000
}
```

#### Response Format Example (Successful 200 OK)
```json
{
  "benchmark": "SPY",
  "tickers": ["AAPL", "MSFT", "NVDA"],
  "weights": [0.4, 0.4, 0.2],
  "dates": ["2020-01-17", "2020-01-21", "..."],
  "equity_curves": [
    { "date": "2020-01-17", "custom": 10045.20, "equal": 10032.50, "benchmark": 10012.10 },
    "..."
  ],
  "drawdowns": [
    { "date": "2020-01-17", "custom": 0.0, "equal": 0.0, "benchmark": -0.15 },
    "..."
  ],
  "rolling_volatility": [
    { "date": "2020-04-17", "custom": 31.25, "equal": 32.10, "benchmark": 25.40 },
    "..."
  ],
  "rolling_sharpe": [
    { "date": "2020-04-17", "custom": 1.25, "equal": 1.15, "benchmark": 0.65 },
    "..."
  ],
  "weight_drift": [
    { "date": "2020-01-17", "AAPL": 40.10, "MSFT": 39.95, "NVDA": 19.95 },
    "..."
  ],
  "correlation_matrix": [
    { "ticker": "AAPL", "AAPL": 1.0, "MSFT": 0.748, "NVDA": 0.606 },
    { "ticker": "MSFT", "AAPL": 0.748, "MSFT": 1.0, "NVDA": 0.683 },
    { "ticker": "NVDA", "AAPL": 0.606, "MSFT": 0.683, "NVDA": 1.0 }
  ],
  "stock_performances": {
    "AAPL": { "ticker": "AAPL", "initial_price": 77.20, "final_price": 235.40, "total_return": 2.049, "cagr": 0.264, "sharpe_ratio": 0.985 },
    "..."
  },
  "metrics": {
    "custom": {
      "total_return": 3.909,
      "cagr": 0.382,
      "ann_volatility": 0.320,
      "sharpe_ratio": 1.109,
      "max_drawdown": -0.356,
      "beta": 1.310,
      "alpha": 0.180
    },
    "equal": { "..." },
    "benchmark": { "..." }
  }
}
```

---

## Quantitative Formulas Sourced
* **CAGR**: Estimating years $Y = \frac{N}{252}$ trading days:
  $$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{1/Y} - 1$$
* **Annualized Volatility**:
  $$\sigma_{\text{ann}} = \text{std}(R_{\text{daily}}) \times \sqrt{252}$$
* **Sharpe Ratio**:
  $$\text{Sharpe} = \frac{\overline{R_{\text{daily}}} \times 252 - R_f}{\sigma_{\text{ann}}}$$
* **Jensen's Alpha**:
  $$\alpha = (\overline{R_p} \times 252) - \left[R_f + \beta \times (\overline{R_b} \times 252 - R_f)\right]$$
* **Beta**:
  $$\beta = \frac{\text{Cov}(R_p, R_b)}{\text{Var}(R_b)}$$
* **Weight Drift**: For $n$ assets with initial weights $w_i$, asset value rels $V_{i,t} = \frac{P_{i,t}}{P_{i,0}}$:
  $$W_{i,t} = \frac{w_i V_{i,t}}{\sum_{j=1}^k w_j V_{j,t}} \times 100$$
