"""
Stock Market Data Analyzer - Main CLI Application & Orchestrator
Integrates data ingestion, cleaning, technical analysis, risk modeling,
strategy backtesting, visual chart rendering, and automated report generation.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import pandas as pd

# Add root folder to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_fetcher import StockDataFetcher
from src.indicators import TechnicalIndicators
from src.risk_metrics import RiskMetricsEngine
from src.backtester import StrategyBacktester
from src.visualizer import FinancialVisualizer
from src.reporter import FinancialReporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def print_banner():
    banner = r"""
================================================================================
   ____ _____ ___   ____ _  __  __  __    _    ____  _  _______ _____ 
  / ___|_   _/ _ \ / ___| |/ / |  \/  |  / \  |  _ \| |/ / ____|_   _|
  \___ \ | || | | | |   | ' /  | |\/| | / _ \ | |_) | ' /|  _|   | |  
   ___) || || |_| | |___| . \  | |  | |/ ___ \|  _ <| . \| |___  | |  
  |____/ |_| \___/ \____|_|\_\ |_|  |_/_/   \_\_| \_\_|\_\_____| |_|  
                                                                       
        DATA ANALYZER & QUANTITATIVE STRATEGY BACKTESTING SYSTEM       
================================================================================
"""
    print(banner)


def analyze_stock(ticker: str = "AAPL", period: str = "2y", fast_ma: int = 20, slow_ma: int = 50):
    """
    Executes the end-to-end analytical pipeline for a single stock ticker.
    """
    ticker = ticker.upper().strip()
    print(f"\n[+] Starting Financial Quantitative Analysis for: {ticker} (Period: {period})")
    print("-" * 75)

    # 1. Data Ingestion
    print("  [Step 1/6] Ingesting market OHLCV data...")
    fetcher = StockDataFetcher()
    df_raw = fetcher.fetch_data(ticker=ticker, period=period)
    print(f"      -> Ingested {len(df_raw)} records from {str(df_raw.index[0])[:10]} to {str(df_raw.index[-1])[:10]}")

    # 2. Technical Indicators
    print("  [Step 2/6] Computing Technical Indicators & Momentum Oscillators...")
    df_ind = TechnicalIndicators.add_all_indicators(df_raw)
    latest = df_ind.iloc[-1].to_dict()
    print(f"      -> Current Close: ${latest['Close']:.2f}")
    print(f"      -> SMA 20: ${latest['SMA_20']:.2f} | SMA 50: ${latest['SMA_50']:.2f} | SMA 200: ${latest['SMA_200']:.2f}")
    print(f"      -> RSI (14): {latest['RSI_14']:.2f} | MACD: {latest['MACD']:.3f}")
    print(f"      -> Technical Consensus Bias: {latest['Overall_Trend']}")

    # 3. Quantitative Risk & Performance Metrics
    print("  [Step 3/6] Computing Statistical Risk & Performance Metrics...")
    risk_engine = RiskMetricsEngine(risk_free_rate=0.04)
    metrics = risk_engine.calculate_all_metrics(df_ind)
    print(f"      -> 52-Week Range: ${metrics['lowest_price']:.2f} - ${metrics['highest_price']:.2f}")
    print(f"      -> Annualized Return (CAGR): {metrics['cagr_pct']}%")
    print(f"      -> Annualized Volatility: {metrics['annualized_volatility_pct']}% (Rating: {metrics['risk_rating']})")
    print(f"      -> Sharpe Ratio: {metrics['sharpe_ratio']} | Sortino Ratio: {metrics['sortino_ratio']}")
    print(f"      -> Max Drawdown: {metrics['max_drawdown_pct']}%")
    print(f"      -> 95% Daily VaR: {metrics['var_95_daily_pct']}% | Daily Win Rate: {metrics['win_rate_pct']}%")

    # 4. Strategy Backtesting
    print("  [Step 4/6] Running Algorithmic Strategy Backtesting ($10,000 Portfolio)...")
    tester = StrategyBacktester(initial_capital=10000.0, commission_pct=0.001)
    bt_result = tester.backtest_ma_crossover(df_ind, fast_period=fast_ma, slow_period=slow_ma)
    print(f"      -> Strategy: {bt_result['strategy_name']}")
    print(f"      -> Final Strategy Capital: ${bt_result['final_strategy_equity']:,.2f} (Return: {bt_result['strategy_total_return_pct']}%)")
    print(f"      -> Buy & Hold Benchmark Capital: ${bt_result['final_benchmark_equity']:,.2f} (Return: {bt_result['benchmark_total_return_pct']}%)")
    print(f"      -> Alpha Generated: {bt_result['alpha_pct']}%")
    print(f"      -> Strategy Max Drawdown: {bt_result['strategy_max_drawdown_pct']}%")
    print(f"      -> Executed Trades: {bt_result['total_trades']} | Win Rate: {bt_result['win_rate_pct']}%")

    # 5. Visual Chart Rendering
    print("  [Step 5/6] Generating Publication-Quality Financial Visualizations...")
    vis = FinancialVisualizer()
    p1 = vis.plot_price_and_indicators(df_ind, ticker)
    p2 = vis.plot_returns_distribution(df_ind, ticker, metrics["var_95_daily_pct"])
    p3 = vis.plot_volatility_trend(df_ind, ticker)
    p4 = vis.plot_backtest_equity_curve(bt_result, ticker)
    print(f"      -> Saved: {os.path.basename(p1)}")
    print(f"      -> Saved: {os.path.basename(p2)}")
    print(f"      -> Saved: {os.path.basename(p3)}")
    print(f"      -> Saved: {os.path.basename(p4)}")

    # 6. Report Generation
    print("  [Step 6/6] Generating Structured Financial Research Reports...")
    reporter = FinancialReporter()
    rep_paths = reporter.generate_report(ticker, latest, metrics, bt_result)
    print(f"      -> JSON Report: {os.path.basename(rep_paths['json_path'])}")
    print(f"      -> Executive Markdown: {os.path.basename(rep_paths['md_path'])}")

    print("-" * 75)
    print(f"[✓] Analysis Completed Successfully for {ticker}!\n")
    return {"df": df_ind, "metrics": metrics, "backtest": bt_result, "reports": rep_paths}


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Stock Market Data Analyzer & Quant Backtester")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Stock ticker symbol (e.g. AAPL, NVDA, TSLA, MSFT)")
    parser.add_argument("--period", type=str, default="2y", help="Timeframe period: 3mo, 6mo, 1y, 2y, 5y")
    parser.add_argument("--fast", type=int, default=20, help="Fast Moving Average period (default 20)")
    parser.add_argument("--slow", type=int, default=50, help="Slow Moving Average period (default 50)")
    parser.add_argument("--serve", action="store_true", help="Launch FastAPI web server and interactive web dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port for web server (default 8000)")
    parser.add_argument("--all", action="store_true", help="Analyze top benchmark portfolio basket (AAPL, NVDA, MSFT, TSLA, SPY)")

    args = parser.parse_args()

    if args.serve:
        print(f"\n[🚀] Starting FastAPI Server & FinTech Interactive Dashboard on http://127.0.0.1:{args.port}...")
        print(f"     -> Web Dashboard:  http://127.0.0.1:{args.port}/dashboard")
        print(f"     -> Swagger API:    http://127.0.0.1:{args.port}/docs\n")
        import uvicorn
        uvicorn.run("api.main_api:app", host="127.0.0.1", port=args.port, reload=True)
    elif args.all:
        basket = ["AAPL", "NVDA", "MSFT", "TSLA", "SPY"]
        print(f"\n[*] Running Portfolio Batch Analysis across {len(basket)} tickers: {basket}")
        for t in basket:
            analyze_stock(ticker=t, period=args.period, fast_ma=args.fast, slow_ma=args.slow)
        print("\n[✓] All tickers in basket analyzed successfully.")
    else:
        analyze_stock(ticker=args.ticker, period=args.period, fast_ma=args.fast, slow_ma=args.slow)


if __name__ == "__main__":
    main()
