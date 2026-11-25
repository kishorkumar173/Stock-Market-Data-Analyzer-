# 🏛️ Architecture & System Design Document
## Stock Market Data Analyzer (Institutional Quantitative Framework)

### 1. High-Level Architecture Diagram
```
+-----------------------------------------------------------------------------------+
|                            EXTERNAL DATA FEEDS & STREAMS                         |
|   +--------------------------+    +-----------------------+    +---------------+  |
|   | Yahoo Finance (yfinance) |    | Local CSV Data Cache  |    | Synthetic GBM |  |
|   +------------+-------------+    +-----------+-----------+    +-------+-------+  |
+----------------\------------------------------|------------------------/----------+
                  \                             |                       /
                   \                            v                      /
+-----------------------------------------------------------------------------------+
|                        INGESTION & CLEANING LAYER (`src/data_fetcher.py`)         |
|  * Multi-index column flattening         * Forward/Backward fill missing values  |
|  * Deduplication & date sorting          * Validation & sanitize OHLCV arrays    |
+-----------------------------------------------+-----------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------+
|                     ANALYTICAL & INDICATOR ENGINE (`src/indicators.py`)           |
|  * Trend: SMA (20, 50, 200), EMA (12, 26)     * Volatility: Bollinger Bands, ATR  |
|  * Momentum: RSI (14), MACD (12/26/9)         * Returns: Daily, Log, Cumulative   |
|  * Signal Triggers: Golden Cross, Death Cross, RSI Oversold/Overbought Consensus   |
+-----------------------+---------------------------------------+-------------------+
                        |                                       |
                        v                                       v
+---------------------------------------+   +---------------------------------------+
|  RISK METRICS ENGINE                  |   |  STRATEGY BACKTESTING ENGINE          |
|  (`src/risk_metrics.py`)              |   |  (`src/backtester.py`)                |
|  * Annualized Volatility (σ * √252)   |   |  * Dual Moving Average Cross Strategy |
|  * CAGR (Compound Annual Growth)      |   |  * RSI Mean-Reversion Strategy        |
|  * Sharpe Ratio (Rf = 4.0%)           |   |  * Buy & Hold Benchmark Equity Curve  |
|  * Sortino Ratio (Downside Deviation) |   |  * Trade Log & Execution State        |
|  * Max Drawdown (Peak-to-Trough)      |   |  * Alpha Outperformance Calculation   |
|  * Value at Risk (VaR 95% & 99%)      |   |  * Win Rate % & Profit Factor         |
|  * Expected Shortfall (CVaR 95%)      |   |  * Vectorized Returns with 0.1% Costs |
+-----------------------+---------------+   +-------------------+-------------------+
                        |                                       |
                        +-------------------+-------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                 PRESENTATION, SERVING & AUTOMATION LAYERS                         |
|                                                                                   |
|  +---------------------------+  +-------------------------+  +------------------+ |
|  | CLI Runner (`main.py`)    |  | REST API (`FastAPI`)    |  | Web UI Dashboard | |
|  | - Direct terminal output  |  | - `/api/v1/stock/{sym}` |  | - Modern Tailwind| |
|  | - Batch portfolio run     |  | - `/api/v1/risk/{sym}`  |  | - Chart.js Plots | |
|  | - Instant chart export    |  | - `/api/v1/backtest`    |  | - Live Watchlist | |
|  +-------------+-------------+  +------------+------------+  +--------+---------+ |
|                |                             |                        |           |
|                v                             v                        v           |
|  +---------------------------+  +-------------------------+  +------------------+ |
|  | Visualizer & Reporter     |  | Interactive Docs        |  | Client Browser   | |
|  | `outputs/*.png` (4 plots) |  | `/docs` (Swagger UI)    |  | Live Interactivity| |
|  | `reports/*.json` & `*.md` |  | OpenAPI Schema v3.1     |  | One-click export | |
|  +---------------------------+  +-------------------------+  +------------------+ |
+-----------------------------------------------------------------------------------+
```

---

### 2. Quantitative Formula Reference

1. **Daily Percentage Return:**
   $$r_t = \frac{P_t - P_{t-1}}{P_{t-1}}$$

2. **Annualized Volatility:**
   $$\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{252}$$

3. **Compound Annual Growth Rate (CAGR):**
   $$\text{CAGR} = \left( \frac{P_{\text{end}}}{P_{\text{start}}} \right)^{\frac{252}{N}} - 1$$

4. **Sharpe Ratio:**
   $$\text{Sharpe} = \frac{\text{CAGR} - R_f}{\sigma_{\text{ann}}}$$

5. **Sortino Ratio:**
   $$\text{Sortino} = \frac{\text{CAGR} - R_f}{\sigma_{\text{downside}} \times \sqrt{252}}$$

6. **Maximum Drawdown (MDD):**
   $$\text{DD}_t = \frac{P_t - \max_{\tau \le t}(P_\tau)}{\max_{\tau \le t}(P_\tau)}, \quad \text{MDD} = \min_t(\text{DD}_t)$$

7. **Historical Value at Risk (VaR 95%):**
   $$\text{VaR}_{0.95} = \text{Percentile}(r, 5\%)$$

8. **Conditional Value at Risk (CVaR / Expected Shortfall 95%):**
   $$\text{CVaR}_{0.95} = \mathbb{E}[r \mid r \le \text{VaR}_{0.95}]$$

---

### 3. Data Flow Step-by-Step
1. **User Request / CLI Trigger:** User triggers `main.py` with ticker and period parameters, or accesses the FastAPI web endpoint `/dashboard`.
2. **Ingestion & Fallback Engine:** `StockDataFetcher` attempts live yfinance API fetch. If internet or API is unreachable, it checks the local cache (`data/{ticker}_historical.csv`), or automatically synthesizes a Geometric Brownian Motion market price path.
3. **Indicator Calculation:** `TechnicalIndicators` computes vectorized rolling windows for SMA (20/50/200), EMA (12/26), RSI (14), MACD, Bollinger Bands, and consensus trading signals.
4. **Risk Quantification:** `RiskMetricsEngine` generates annualized return, volatility, Sharpe, Sortino, Drawdown, VaR, and tail risk metrics.
5. **Backtesting Pipeline:** `StrategyBacktester` simulates trading signals shifted by 1 period to prevent lookahead bias, factors in 0.1% transaction costs, and computes equity curves against the buy-and-hold benchmark.
6. **Visualization & Report Assembly:** Matplotlib and Seaborn generate high-resolution PNG plots saved to `outputs/` and `images/`. `FinancialReporter` outputs a structured JSON report and executive Markdown audit to `reports/`.
7. **Interactive Web Dashboard:** The FastAPI backend serves the dark-mode dashboard on `http://127.0.0.1:8000/dashboard`, rendering responsive Chart.js price action, RSI, MACD, and backtest equity curves with real-time controls.
