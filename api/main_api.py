"""
FastAPI Financial Analytics Engine & REST Microservice
Exposes high-performance asynchronous endpoints for market data,
technical indicators, risk metrics, strategy backtesting, and dashboard rendering.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_fetcher import StockDataFetcher
from src.indicators import TechnicalIndicators
from src.risk_metrics import RiskMetricsEngine
from src.backtester import StrategyBacktester
from src.visualizer import FinancialVisualizer
from src.reporter import FinancialReporter

app = FastAPI(
    title="Stock Market Data Analyzer API",
    description="Quantitative Financial Analytics, Technical Indicators, and Backtesting REST Microservice.",
    version="1.0.0"
)

# Enable CORS for Next.js / frontend client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and template directories for web dashboard
WEB_DIR = os.path.join(PROJECT_ROOT, "web")
STATIC_DIR = os.path.join(WEB_DIR, "static")
TEMPLATES_DIR = os.path.join(WEB_DIR, "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize engines
fetcher = StockDataFetcher()
risk_engine = RiskMetricsEngine(risk_free_rate=0.04)
backtester = StrategyBacktester(initial_capital=10000.0, commission_pct=0.001)
visualizer = FinancialVisualizer()
reporter = FinancialReporter()


# Pydantic Request Models
class BacktestRequest(BaseModel):
    ticker: str = Field(default="AAPL", example="AAPL")
    strategy: str = Field(default="ma_cross", example="ma_cross")
    period: str = Field(default="2y", example="2y")
    fast_period: int = Field(default=20, example=20)
    slow_period: int = Field(default=50, example=50)
    rsi_oversold: float = Field(default=30.0, example=30.0)
    rsi_overbought: float = Field(default=70.0, example=70.0)
    initial_capital: float = Field(default=10000.0, example=10000.0)


@app.get("/", tags=["General"])
async def root():
    return {
        "status": "online",
        "service": "Stock Market Data Analyzer REST API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "dashboard_ui": "/dashboard"
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard UI"])
async def get_dashboard(request: Request):
    """
    Renders the modern interactive FinTech Web Dashboard.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/v1/stock/{ticker}", tags=["Market Data"])
async def get_stock_data(
    ticker: str,
    period: str = Query("1y", description="Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y"),
    include_indicators: bool = Query(True, description="Compute technical indicators")
):
    """
    Ingests and returns cleaned OHLCV data with technical indicators and summary metrics.
    """
    try:
        df = fetcher.fetch_data(ticker=ticker, period=period)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for ticker {ticker}")

        if include_indicators:
            df = TechnicalIndicators.add_all_indicators(df)

        risk_metrics = risk_engine.calculate_all_metrics(df)

        # Prepare records for chart plotting
        records = []
        for dt, row in df.iterrows():
            rec = {
                "date": str(dt)[:10],
                "open": round(float(row.get("Open", 0)), 2),
                "high": round(float(row.get("High", 0)), 2),
                "low": round(float(row.get("Low", 0)), 2),
                "close": round(float(row.get("Close", 0)), 2),
                "volume": int(row.get("Volume", 0)),
                "sma_20": round(float(row.get("SMA_20", 0)), 2) if not pd.isna(row.get("SMA_20")) else None,
                "sma_50": round(float(row.get("SMA_50", 0)), 2) if not pd.isna(row.get("SMA_50")) else None,
                "sma_200": round(float(row.get("SMA_200", 0)), 2) if not pd.isna(row.get("SMA_200")) else None,
                "rsi_14": round(float(row.get("RSI_14", 50)), 2) if not pd.isna(row.get("RSI_14")) else None,
                "macd": round(float(row.get("MACD", 0)), 3) if not pd.isna(row.get("MACD")) else None,
                "macd_signal": round(float(row.get("MACD_Signal", 0)), 3) if not pd.isna(row.get("MACD_Signal")) else None,
                "macd_hist": round(float(row.get("MACD_Hist", 0)), 3) if not pd.isna(row.get("MACD_Hist")) else None,
                "bb_upper": round(float(row.get("BB_Upper", 0)), 2) if not pd.isna(row.get("BB_Upper")) else None,
                "bb_lower": round(float(row.get("BB_Lower", 0)), 2) if not pd.isna(row.get("BB_Lower")) else None,
            }
            records.append(rec)

        latest_row = df.iloc[-1].to_dict()
        latest_clean = {
            k: (round(float(v), 2) if isinstance(v, (int, float)) and not pd.isna(v) else str(v))
            for k, v in latest_row.items()
        }

        return {
            "ticker": ticker.upper(),
            "period": period,
            "data_points": len(records),
            "latest": latest_clean,
            "risk_metrics": risk_metrics,
            "historical": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/risk/{ticker}", tags=["Risk Analysis"])
async def get_risk_analysis(ticker: str, period: str = Query("2y")):
    """
    Computes Sharpe, Sortino, Max Drawdown, VaR 95%, CVaR, and Volatility metrics.
    """
    df = fetcher.fetch_data(ticker=ticker, period=period)
    df = TechnicalIndicators.add_all_indicators(df)
    metrics = risk_engine.calculate_all_metrics(df)
    return {"ticker": ticker.upper(), "metrics": metrics}


@app.post("/api/v1/backtest", tags=["Algorithmic Backtesting"])
async def run_backtest(req: BacktestRequest):
    """
    Executes algorithmic strategy backtest and returns equity growth curves and trade history.
    """
    try:
        df = fetcher.fetch_data(ticker=req.ticker, period=req.period)
        df = TechnicalIndicators.add_all_indicators(df)

        tester = StrategyBacktester(initial_capital=req.initial_capital)

        if req.strategy == "rsi":
            result = tester.backtest_rsi_mean_reversion(
                df, oversold=req.rsi_oversold, overbought=req.rsi_overbought
            )
        else:
            result = tester.backtest_ma_crossover(
                df, fast_period=req.fast_period, slow_period=req.slow_period
            )

        # Format equity curve for chart rendering
        equity_df = result["equity_df"]
        equity_series = []
        for dt, row in equity_df.iterrows():
            equity_series.append({
                "date": str(dt)[:10],
                "strategy": round(float(row["Strategy_Equity"]), 2),
                "benchmark": round(float(row["Benchmark_Equity"]), 2),
                "position": int(row["Position"])
            })

        return {
            "ticker": req.ticker.upper(),
            "strategy": result["strategy_name"],
            "summary": {
                "initial_capital": result["initial_capital"],
                "final_strategy_equity": result["final_strategy_equity"],
                "final_benchmark_equity": result["final_benchmark_equity"],
                "strategy_total_return_pct": result["strategy_total_return_pct"],
                "benchmark_total_return_pct": result["benchmark_total_return_pct"],
                "alpha_pct": result["alpha_pct"],
                "strategy_cagr_pct": result["strategy_cagr_pct"],
                "strategy_max_drawdown_pct": result["strategy_max_drawdown_pct"],
                "total_trades": result["total_trades"],
                "win_rate_pct": result["win_rate_pct"],
            },
            "recent_trades": result["trades"],
            "equity_curve": equity_series
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/watchlist", tags=["Watchlist"])
async def get_watchlist():
    """
    Returns curated watchlist prices, daily changes, and RSI momentum.
    """
    tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "SPY"]
    watchlist = []

    for t in tickers:
        try:
            df = fetcher.fetch_data(t, period="3mo")
            if df is not None and not df.empty:
                last_price = float(df["Close"].iloc[-1])
                prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else last_price
                chg_pct = ((last_price - prev_price) / prev_price) * 100
                vol = int(df["Volume"].iloc[-1])

                watchlist.append({
                    "ticker": t,
                    "price": round(last_price, 2),
                    "change_pct": round(chg_pct, 2),
                    "volume": vol
                })
        except Exception:
            pass

    return {"watchlist": watchlist}


@app.get("/api/v1/export/{ticker}", tags=["Export"])
async def export_csv(ticker: str, period: str = "2y"):
    """
    Downloads full cleaned dataset with indicators as CSV.
    """
    df = fetcher.fetch_data(ticker=ticker, period=period)
    df = TechnicalIndicators.add_all_indicators(df)
    csv_path = os.path.join(PROJECT_ROOT, "data", f"{ticker.upper()}_export.csv")
    df.to_csv(csv_path)
    return FileResponse(csv_path, media_type="text/csv", filename=f"{ticker.upper()}_data.csv")


if __name__ == "__main__":
    import uvicorn
    import pandas as pd
    uvicorn.run("main_api:app", host="127.0.0.1", port=8000, reload=True)
else:
    import pandas as pd
