"""
Financial Risk & Performance Metrics Engine
Computes institutional-grade quantitative risk indicators:
Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Value at Risk (VaR),
Conditional VaR (CVaR), Annualized Volatility, CAGR, and Calmar Ratio.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RiskMetricsEngine:
    """
    Computes statistical and quantitative risk metrics from daily return series.
    """

    def __init__(self, risk_free_rate: float = 0.04):
        """
        :param risk_free_rate: Annualized risk-free rate (default 4.0% or 0.04)
        """
        self.rf = risk_free_rate

    def calculate_all_metrics(self, df: pd.DataFrame, price_col: str = "Close") -> Dict[str, Any]:
        """
        Extracts all standard risk and performance metrics from the price series.
        """
        if "Daily_Return" not in df.columns:
            returns = df[price_col].pct_change().dropna()
        else:
            returns = df["Daily_Return"].dropna()

        if len(returns) < 10:
            return {"error": "Insufficient data to compute statistical metrics"}

        prices = df[price_col].dropna()
        n_days = len(returns)
        trading_days_per_year = 252

        # 1. Total & Annualized Return (CAGR)
        total_return = (prices.iloc[-1] / prices.iloc[0]) - 1.0
        years = max(n_days / trading_days_per_year, 0.01)
        cagr = (1.0 + total_return) ** (1.0 / years) - 1.0

        # 2. Volatility
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(trading_days_per_year)

        # 3. Sharpe Ratio
        excess_return = cagr - self.rf
        sharpe_ratio = excess_return / (annualized_vol + 1e-10)

        # 4. Sortino Ratio (Penalizes only downside risk)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(trading_days_per_year)
        sortino_ratio = excess_return / (downside_std + 1e-10) if downside_std > 0 else 0.0

        # 5. Maximum Drawdown (MDD)
        rolling_max = prices.cummax()
        drawdowns = (prices - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()  # Negative value e.g. -0.22 for -22%

        # 6. Calmar Ratio
        calmar_ratio = cagr / (abs(max_drawdown) + 1e-10)

        # 7. Value at Risk (Historical 95% and 99%)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)

        # 8. Conditional Value at Risk (CVaR / Expected Shortfall 95%)
        cvar_95 = returns[returns <= var_95].mean()

        # 9. Win Rate & Daily Return Distribution Stats
        positive_days = (returns > 0).sum()
        negative_days = (returns < 0).sum()
        win_rate = positive_days / (positive_days + negative_days + 1e-10)

        skewness = float(returns.skew())
        kurtosis = float(returns.kurt())

        # 10. High / Low Statistics
        current_price = float(prices.iloc[-1])
        highest_price = float(prices.max())
        lowest_price = float(prices.min())
        distance_from_high = (current_price - highest_price) / highest_price
        distance_from_low = (current_price - lowest_price) / lowest_price

        # Pack into clean structured dictionary
        metrics = {
            "trading_days": int(n_days),
            "years_analyzed": round(float(years), 2),
            "current_price": round(current_price, 2),
            "highest_price": round(highest_price, 2),
            "lowest_price": round(lowest_price, 2),
            "distance_from_52w_high_pct": round(float(distance_from_high) * 100, 2),
            "distance_from_52w_low_pct": round(float(distance_from_low) * 100, 2),
            "total_return_pct": round(float(total_return) * 100, 2),
            "cagr_pct": round(float(cagr) * 100, 2),
            "annualized_volatility_pct": round(float(annualized_vol) * 100, 2),
            "sharpe_ratio": round(float(sharpe_ratio), 2),
            "sortino_ratio": round(float(sortino_ratio), 2),
            "max_drawdown_pct": round(float(max_drawdown) * 100, 2),
            "calmar_ratio": round(float(calmar_ratio), 2),
            "var_95_daily_pct": round(float(var_95) * 100, 2),
            "var_99_daily_pct": round(float(var_99) * 100, 2),
            "cvar_95_daily_pct": round(float(cvar_95) * 100, 2),
            "win_rate_pct": round(float(win_rate) * 100, 2),
            "skewness": round(skewness, 3),
            "kurtosis": round(kurtosis, 3),
            "risk_rating": self._assess_risk_rating(annualized_vol, max_drawdown)
        }

        return metrics

    @staticmethod
    def _assess_risk_rating(annualized_vol: float, max_drawdown: float) -> str:
        """Categorizes investment risk into Conservative, Moderate, High, or Speculative."""
        if annualized_vol < 0.18 and abs(max_drawdown) < 0.20:
            return "Low / Conservative"
        elif annualized_vol < 0.30 and abs(max_drawdown) < 0.35:
            return "Moderate"
        elif annualized_vol < 0.45:
            return "High Risk / Aggressive"
        else:
            return "Very High / Speculative"


if __name__ == "__main__":
    from data_fetcher import StockDataFetcher
    fetcher = StockDataFetcher()
    df_sample = fetcher.fetch_data("AAPL", period="1y")
    engine = RiskMetricsEngine(risk_free_rate=0.04)
    res = engine.calculate_all_metrics(df_sample)
    print("Computed Risk & Performance Metrics:")
    for k, v in res.items():
        print(f"  {k}: {v}")
