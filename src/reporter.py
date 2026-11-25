"""
Automated Financial Report Generator
Synthesizes market data, technical indicator signals, risk analysis,
and backtest performance into structured JSON and executive Markdown reports.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class FinancialReporter:
    """
    Assembles comprehensive equity research summaries and risk audits.
    """

    def __init__(self, reports_dir: str = REPORTS_DIR):
        self.reports_dir = reports_dir

    def generate_report(
        self,
        ticker: str,
        df_latest: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Creates both Markdown and JSON reports on disk and returns paths.
        """
        ticker = ticker.upper()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Build structured JSON payload
        report_data = {
            "metadata": {
                "ticker": ticker,
                "generated_at": now_str,
                "project": "Stock Market Data Analyzer",
                "analyst_role": "Quantitative & Financial Data Analyst"
            },
            "technical_snapshot": df_latest,
            "risk_and_performance": risk_metrics,
            "quantitative_backtest": {
                k: v for k, v in backtest_results.items() if k not in ["equity_df"]
            },
            "disclaimer": "This report is generated strictly for academic, educational, and research evaluation purposes. It does not constitute financial or investment advice."
        }

        json_path = os.path.join(self.reports_dir, f"{ticker}_analysis_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4)

        # 2. Build Markdown Executive Report
        md_content = f"""# 📈 EQUITY RESEARCH & QUANTITATIVE AUDIT REPORT: {ticker}
**Generated Date:** `{now_str}`  
**Project:** Stock Market Data Analyzer (Python Quantitative Framework)  
**Target Roles:** Financial Analyst | Quantitative Analyst | Data Analyst | Python Developer  

---

## 1. Executive Summary & Market Snapshot
| Metric | Value |
| :--- | :--- |
| **Ticker Symbol** | **{ticker}** |
| **Current Market Price** | **${risk_metrics.get('current_price', 'N/A')}** |
| **52-Week High** | ${risk_metrics.get('highest_price', 'N/A')} ({risk_metrics.get('distance_from_52w_high_pct', 'N/A')}% away) |
| **52-Week Low** | ${risk_metrics.get('lowest_price', 'N/A')} (+{risk_metrics.get('distance_from_52w_low_pct', 'N/A')}% from bottom) |
| **Overall Technical Bias** | **{df_latest.get('Overall_Trend', 'Neutral')}** |
| **Risk Rating** | **{risk_metrics.get('risk_rating', 'Moderate')}** |

---

## 2. Technical Indicator Status
- **20-Day SMA:** ${df_latest.get('SMA_20', 'N/A'):.2f} (Short-Term Trend)
- **50-Day SMA:** ${df_latest.get('SMA_50', 'N/A'):.2f} (Medium-Term Baseline)
- **200-Day SMA:** ${df_latest.get('SMA_200', 'N/A'):.2f} (Long-Term Institutional Line)
- **RSI (14-period):** **{df_latest.get('RSI_14', 'N/A'):.2f}** ({'Oversold (<30)' if df_latest.get('RSI_14', 50) < 30 else 'Overbought (>70)' if df_latest.get('RSI_14', 50) > 70 else 'Neutral Momentum (30-70)'})
- **MACD Value:** {df_latest.get('MACD', 'N/A'):.3f} vs Signal: {df_latest.get('MACD_Signal', 'N/A'):.3f}
- **Bollinger Bands:** Upper ${df_latest.get('BB_Upper', 'N/A'):.2f} | Lower ${df_latest.get('BB_Lower', 'N/A'):.2f}

---

## 3. Quantitative Risk & Volatility Analysis
| Risk Metric | Value | Industry Interpretation |
| :--- | :--- | :--- |
| **CAGR (Annual Return)** | **{risk_metrics.get('cagr_pct', 'N/A')}%** | Compound annualized compounding rate |
| **Annualized Volatility** | **{risk_metrics.get('annualized_volatility_pct', 'N/A')}%** | Standard deviation of annualized daily swings |
| **Sharpe Ratio (Rf=4%)** | **{risk_metrics.get('sharpe_ratio', 'N/A')}** | Risk-adjusted excess return per unit of volatility (>1.0 is healthy) |
| **Sortino Ratio** | **{risk_metrics.get('sortino_ratio', 'N/A')}** | Downside-adjusted return (>1.5 is strong) |
| **Maximum Drawdown** | **{risk_metrics.get('max_drawdown_pct', 'N/A')}%** | Worst peak-to-trough paper loss observed |
| **95% Daily VaR** | **{risk_metrics.get('var_95_daily_pct', 'N/A')}%** | Maximum expected daily loss at 95% confidence |
| **95% Expected Shortfall (CVaR)** | **{risk_metrics.get('cvar_95_daily_pct', 'N/A')}%** | Average tail loss when VaR threshold is breached |
| **Win Rate (Daily)** | **{risk_metrics.get('win_rate_pct', 'N/A')}%** | Proportion of positive closing days |

---

## 4. Quantitative Strategy Backtest Efficacy
**Strategy Evaluated:** `{backtest_results.get('strategy_name', 'Moving Average Cross')}`  
**Initial Capital:** `$10,000` (Simulated Portfolio)  

- **Strategy Final Equity:** `${backtest_results.get('final_strategy_equity', 'N/A')}`
- **Strategy Total Return:** **{backtest_results.get('strategy_total_return_pct', 'N/A')}%**
- **Buy & Hold Benchmark Return:** {backtest_results.get('benchmark_total_return_pct', 'N/A')}%
- **Generated Alpha (Outperformance):** **{backtest_results.get('alpha_pct', 'N/A')}%**
- **Strategy Max Drawdown:** {backtest_results.get('strategy_max_drawdown_pct', 'N/A')}% vs Benchmark: {backtest_results.get('benchmark_max_drawdown_pct', 'N/A')}%
- **Completed Trades:** {backtest_results.get('total_trades', 0)} round-trips
- **Trade Win Rate:** {backtest_results.get('win_rate_pct', 'N/A')}%

---

## 5. Strategic Analyst Recommendations & Action Plan
1. **Trend Orientation:** The asset is currently expressing a `{df_latest.get('Overall_Trend', 'Neutral')}` bias. Watch for golden cross or MACD convergence confirmations.
2. **Capital Preservation:** Ensure stop losses align within the 95% Daily VaR boundary ({abs(risk_metrics.get('var_95_daily_pct', 2.0)):.2f}%).
3. **Execution Guardrails:** In high-volatility regimes (>30% annualized vol), reduce position sizing to maintain portfolio-level risk limits.

---
*⚠️ **Disclaimer:** This project and research report is developed for academic, educational demonstration, and proof-of-work purposes. It does NOT constitute financial advisory, investment recommendation, or financial solicitation.*
"""

        md_path = os.path.join(self.reports_dir, f"{ticker}_executive_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Generated JSON report: {json_path}")
        logger.info(f"Generated Markdown report: {md_path}")

        return {"json_path": json_path, "md_path": md_path}


if __name__ == "__main__":
    from data_fetcher import StockDataFetcher
    from indicators import TechnicalIndicators
    from risk_metrics import RiskMetricsEngine
    from backtester import StrategyBacktester

    fetcher = StockDataFetcher()
    df = fetcher.fetch_data("AAPL", period="1y")
    df = TechnicalIndicators.add_all_indicators(df)
    latest = df.iloc[-1].to_dict()

    risk_eng = RiskMetricsEngine()
    metrics = risk_eng.calculate_all_metrics(df)

    bt = StrategyBacktester()
    bt_res = bt.backtest_ma_crossover(df, fast_period=20, slow_period=50)

    reporter = FinancialReporter()
    paths = reporter.generate_report("AAPL", latest, metrics, bt_res)
    print("Report generation test passed:")
    print(paths)
