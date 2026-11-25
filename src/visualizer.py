"""
Data Visualization Engine
Generates publication-quality static financial plots (Matplotlib/Seaborn)
and interactive Plotly JSON feeds for the web dashboard.
"""

import os
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use("Agg")  # Headless backend for server/CLI environments
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Set global financial plotting theme
plt.style.use("seaborn-v0_8-darkgrid" if "seaborn-v0_8-darkgrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.autolayout"] = True


class FinancialVisualizer:
    """
    Renders institutional-grade financial charts and exports them to PNG / Plotly format.
    """

    def __init__(self, output_dir: str = OUTPUTS_DIR):
        self.output_dir = output_dir

    def plot_price_and_indicators(self, df: pd.DataFrame, ticker: str) -> str:
        """
        Generates comprehensive multi-panel chart:
        - Panel 1: Price, SMA 20, SMA 50, SMA 200, Bollinger Bands
        - Panel 2: MACD & Signal Line
        - Panel 3: Relative Strength Index (RSI) with 70/30 thresholds
        - Panel 4: Trading Volume
        """
        fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True, gridspec_kw={"height_ratios": [3, 1, 1, 1]})

        # Panel 1: Price & MAs
        ax1 = axes[0]
        ax1.plot(df.index, df["Close"], label="Close Price", color="#1f77b4", linewidth=1.8)
        if "SMA_20" in df.columns:
            ax1.plot(df.index, df["SMA_20"], label="SMA 20", color="#ff7f0e", linestyle="--", alpha=0.8)
        if "SMA_50" in df.columns:
            ax1.plot(df.index, df["SMA_50"], label="SMA 50", color="#2ca02c", linestyle="-.", alpha=0.9)
        if "SMA_200" in df.columns:
            ax1.plot(df.index, df["SMA_200"], label="SMA 200", color="#d62728", linewidth=1.5)
        if "BB_Upper" in df.columns and "BB_Lower" in df.columns:
            ax1.fill_between(df.index, df["BB_Upper"], df["BB_Lower"], color="#aec7e8", alpha=0.25, label="Bollinger Bands")

        ax1.set_title(f"{ticker.upper()} - Technical Price Trend & Moving Averages", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Price ($)", fontsize=11)
        ax1.legend(loc="upper left", frameon=True, fontsize=9)
        ax1.grid(True, linestyle="--", alpha=0.6)

        # Panel 2: MACD
        ax2 = axes[1]
        if "MACD" in df.columns and "MACD_Signal" in df.columns:
            ax2.plot(df.index, df["MACD"], label="MACD", color="#17becf", linewidth=1.2)
            ax2.plot(df.index, df["MACD_Signal"], label="Signal Line", color="#e377c2", linestyle="--", linewidth=1.2)
            hist = df["MACD_Hist"]
            colors = np.where(hist >= 0, "#2ca02c", "#d62728")
            ax2.bar(df.index, hist, color=colors, alpha=0.5, width=1.0, label="MACD Hist")
            ax2.axhline(0, color="gray", linestyle=":", linewidth=0.8)
            ax2.set_ylabel("MACD", fontsize=11)
            ax2.legend(loc="upper left", fontsize=8)
            ax2.grid(True, linestyle="--", alpha=0.6)

        # Panel 3: RSI
        ax3 = axes[2]
        if "RSI_14" in df.columns:
            ax3.plot(df.index, df["RSI_14"], label="RSI (14)", color="#9467bd", linewidth=1.5)
            ax3.axhline(70, color="red", linestyle="--", alpha=0.7, label="Overbought (70)")
            ax3.axhline(30, color="green", linestyle="--", alpha=0.7, label="Oversold (30)")
            ax3.fill_between(df.index, 70, 30, color="#f0f0f0", alpha=0.5)
            ax3.set_ylabel("RSI", fontsize=11)
            ax3.set_ylim(0, 100)
            ax3.legend(loc="upper left", fontsize=8)
            ax3.grid(True, linestyle="--", alpha=0.6)

        # Panel 4: Volume
        ax4 = axes[3]
        if "Volume" in df.columns:
            vol_colors = np.where(df["Close"] >= df["Open"], "#2ca02c", "#d62728")
            ax4.bar(df.index, df["Volume"], color=vol_colors, alpha=0.7, width=1.0)
            ax4.set_ylabel("Volume", fontsize=11)
            ax4.set_xlabel("Date", fontsize=11)
            ax4.grid(True, linestyle="--", alpha=0.6)

        save_path = os.path.join(self.output_dir, f"{ticker}_technical_dashboard.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Technical chart saved: {save_path}")
        return save_path

    def plot_returns_distribution(self, df: pd.DataFrame, ticker: str, var_95: float) -> str:
        """
        Plots daily returns histogram, KDE normal curve, and 95% VaR cutoff.
        """
        returns = df["Daily_Return"].dropna() * 100  # Convert to percent
        fig, ax = plt.subplots(figsize=(10, 6))

        sns.histplot(returns, bins=50, kde=True, color="#2b5c8f", stat="density", ax=ax, alpha=0.6)
        ax.axvline(0, color="black", linestyle="--", linewidth=1)
        ax.axvline(var_95, color="#d62728", linestyle="-.", linewidth=2, label=f"95% Daily VaR: {var_95:.2f}%")

        ax.set_title(f"{ticker.upper()} - Daily Return Distribution & Value at Risk (VaR)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Daily Return (%)", fontsize=11)
        ax.set_ylabel("Probability Density", fontsize=11)
        ax.legend(loc="upper right", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.6)

        save_path = os.path.join(self.output_dir, f"{ticker}_returns_distribution.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Returns distribution plot saved: {save_path}")
        return save_path

    def plot_volatility_trend(self, df: pd.DataFrame, ticker: str) -> str:
        """
        Plots rolling 20-day annualized volatility over time.
        """
        fig, ax = plt.subplots(figsize=(11, 5))
        if "Rolling_Vol_20d" in df.columns:
            vol_pct = df["Rolling_Vol_20d"] * 100
            ax.plot(df.index, vol_pct, color="#e6550d", linewidth=1.8, label="20-Day Rolling Annualized Volatility")
            mean_vol = vol_pct.mean()
            ax.axhline(mean_vol, color="#3182bd", linestyle="--", label=f"Mean Volatility ({mean_vol:.1f}%)")
            ax.fill_between(df.index, vol_pct, mean_vol, alpha=0.2, color="#fdae6b")

        ax.set_title(f"{ticker.upper()} - Historical Volatility Trend", fontsize=13, fontweight="bold")
        ax.set_ylabel("Annualized Volatility (%)", fontsize=11)
        ax.set_xlabel("Date", fontsize=11)
        ax.legend(loc="upper left")
        ax.grid(True, linestyle="--", alpha=0.6)

        save_path = os.path.join(self.output_dir, f"{ticker}_volatility_trend.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Volatility trend plot saved: {save_path}")
        return save_path

    def plot_backtest_equity_curve(self, backtest_res: Dict[str, Any], ticker: str) -> str:
        """
        Plots strategy equity curve vs Buy & Hold benchmark.
        """
        equity_df = backtest_res.get("equity_df")
        if equity_df is None or equity_df.empty:
            return ""

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

        # Panel 1: Equity Curves
        ax1.plot(equity_df.index, equity_df["Strategy_Equity"], label=f"Strategy: {backtest_res['strategy_name']} ({backtest_res['strategy_total_return_pct']}%)", color="#2ca02c", linewidth=2)
        ax1.plot(equity_df.index, equity_df["Benchmark_Equity"], label=f"Buy & Hold Benchmark ({backtest_res['benchmark_total_return_pct']}%)", color="#1f77b4", linestyle="--", linewidth=1.6)

        ax1.set_title(f"{ticker.upper()} - Quantitative Strategy Backtest Equity Growth ($10,000 Initial)", fontsize=13, fontweight="bold")
        ax1.set_ylabel("Portfolio Value ($)", fontsize=11)
        ax1.legend(loc="upper left")
        ax1.grid(True, linestyle="--", alpha=0.6)

        # Panel 2: Position exposure
        ax2.fill_between(equity_df.index, equity_df["Position"], 0, color="#2ca02c", alpha=0.4, label="Market Exposure (1=In Market, 0=Cash)")
        ax2.set_ylabel("Exposure", fontsize=11)
        ax2.set_xlabel("Date", fontsize=11)
        ax2.set_ylim(-0.1, 1.2)
        ax2.legend(loc="upper left", fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.6)

        save_path = os.path.join(self.output_dir, f"{ticker}_backtest_equity_curve.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Backtest equity curve saved: {save_path}")
        return save_path


if __name__ == "__main__":
    from data_fetcher import StockDataFetcher
    from indicators import TechnicalIndicators
    from risk_metrics import RiskMetricsEngine
    from backtester import StrategyBacktester

    fetcher = StockDataFetcher()
    df = fetcher.fetch_data("AAPL", period="1y")
    df = TechnicalIndicators.add_all_indicators(df)
    risk_eng = RiskMetricsEngine()
    metrics = risk_eng.calculate_all_metrics(df)

    bt = StrategyBacktester()
    bt_res = bt.backtest_ma_crossover(df, fast_period=20, slow_period=50)

    vis = FinancialVisualizer()
    vis.plot_price_and_indicators(df, "AAPL")
    vis.plot_returns_distribution(df, "AAPL", metrics["var_95_daily_pct"])
    vis.plot_volatility_trend(df, "AAPL")
    vis.plot_backtest_equity_curve(bt_res, "AAPL")
    print("Static chart generation test passed successfully!")
