# 🔌 FastAPI REST API Specification
## Stock Market Data Analyzer Microservice

**Base URL:** `http://127.0.0.1:8000`  
**Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`  
**Alternative ReDoc:** `http://127.0.0.1:8000/redoc`

---

### Endpoint Catalog

#### 1. System Health & Metadata
- **Route:** `GET /`
- **Description:** Returns service status, version, and links to UI and documentation.
- **Sample Response:**
```json
{
  "status": "online",
  "service": "Stock Market Data Analyzer REST API",
  "version": "1.0.0",
  "docs_url": "/docs",
  "dashboard_ui": "/dashboard"
}
```

#### 2. FinTech Interactive Dashboard
- **Route:** `GET /dashboard`
- **Response:** HTML5/Tailwind/Chart.js interactive quantitative terminal.

#### 3. Ingest Stock Historical Data & Indicators
- **Route:** `GET /api/v1/stock/{ticker}`
- **Query Parameters:**
  - `period` (optional, default `"1y"`): `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`
  - `include_indicators` (optional, default `true`): Boolean
- **Sample Response:**
```json
{
  "ticker": "AAPL",
  "period": "1y",
  "data_points": 251,
  "latest": {
    "Close": 354.07,
    "SMA_20": 348.08,
    "SMA_50": 342.58,
    "SMA_200": 303.99,
    "RSI_14": 56.71,
    "MACD": 2.697,
    "Overall_Trend": "Neutral"
  },
  "risk_metrics": {
    "current_price": 354.07,
    "cagr_pct": 23.51,
    "annualized_volatility_pct": 29.06,
    "sharpe_ratio": 0.67,
    "max_drawdown_pct": -33.43,
    "var_95_daily_pct": -2.66
  },
  "historical": [ ... ]
}
```

#### 4. Risk Analysis Engine
- **Route:** `GET /api/v1/risk/{ticker}`
- **Query Parameters:** `period` (default `"2y"`)
- **Returns:** Sharpe, Sortino, Max Drawdown, Calmar Ratio, 95% and 99% VaR, CVaR.

#### 5. Quantitative Strategy Backtest
- **Route:** `POST /api/v1/backtest`
- **Request Body (JSON):**
```json
{
  "ticker": "AAPL",
  "strategy": "ma_cross",
  "period": "2y",
  "fast_period": 20,
  "slow_period": 50,
  "initial_capital": 10000.0
}
```
- **Sample Response:**
```json
{
  "ticker": "AAPL",
  "strategy": "MA_Cross_20_50",
  "summary": {
    "initial_capital": 10000.0,
    "final_strategy_equity": 10527.28,
    "final_benchmark_equity": 15204.62,
    "strategy_total_return_pct": 5.27,
    "benchmark_total_return_pct": 52.05,
    "alpha_pct": -46.77,
    "strategy_cagr_pct": 2.6,
    "strategy_max_drawdown_pct": -27.16,
    "total_trades": 7,
    "win_rate_pct": 28.57
  },
  "recent_trades": [ ... ],
  "equity_curve": [ ... ]
}
```

#### 6. Live Market Watchlist
- **Route:** `GET /api/v1/watchlist`
- **Returns:** Real-time pricing, daily percentage change, and volume for major benchmark equities.

#### 7. Export Cleaned Data as CSV
- **Route:** `GET /api/v1/export/{ticker}`
- **Response:** Downloadable CSV file containing complete historical time-series and computed indicators.
