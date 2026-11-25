"""
Quantitative Strategy Backtesting Engine
Vectorized and event-driven backtesting for systematic algorithmic trading strategies:
- Dual Moving Average Crossover (Golden Cross / Death Cross)
- RSI Mean-Reversion Strategy
- MACD Momentum Strategy
- Buy & Hold Benchmark Comparison
Calculates equity curves, trade logs, win rate, profit factor, and CAGR.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class StrategyBacktester:
    """
    Backtests trading strategies against historical time-series data.
    """

    def __init__(self, initial_capital: float = 10000.0, commission_pct: float = 0.001):
        """
        :param initial_capital: Starting capital (e.g., $10,000)
        :param commission_pct: Transaction cost per trade (e.g., 0.1% = 0.001)
        """
        self.initial_capital = initial_capital
        self.commission = commission_pct

    def backtest_ma_crossover(
        self,
        df: pd.DataFrame,
        fast_period: int = 50,
        slow_period: int = 200
    ) -> Dict[str, Any]:
        """
        Dual Moving Average Crossover:
        Long when Fast MA > Slow MA; Flat (Cash) otherwise.
        """
        data = df.copy()

        fast_col = f"SMA_{fast_period}"
        slow_col = f"SMA_{slow_period}"

        if fast_col not in data.columns:
            data[fast_col] = data["Close"].rolling(window=fast_period, min_periods=1).mean()
        if slow_col not in data.columns:
            data[slow_col] = data["Close"].rolling(window=slow_period, min_periods=1).mean()

        # Signal: 1 for Long, 0 for Cash
        data["Signal"] = np.where(data[fast_col] > data[slow_col], 1, 0)
        # Shift signal by 1 day to prevent lookahead bias (execute on next open/close)
        data["Position"] = data["Signal"].shift(1).fillna(0)

        return self._evaluate_strategy(data, strategy_name=f"MA_Cross_{fast_period}_{slow_period}")

    def backtest_rsi_mean_reversion(
        self,
        df: pd.DataFrame,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0
    ) -> Dict[str, Any]:
        """
        RSI Mean-Reversion:
        Buy when RSI < oversold (30); Exit when RSI > overbought (70).
        """
        data = df.copy()
        rsi_col = f"RSI_{rsi_period}"
        if rsi_col not in data.columns:
            from indicators import TechnicalIndicators
            data = TechnicalIndicators.add_rsi(data, period=rsi_period)

        # Iterative position state machine
        positions = np.zeros(len(data))
        current_pos = 0

        for i in range(1, len(data)):
            rsi_val = data[rsi_col].iloc[i - 1]
            if pd.isna(rsi_val):
                continue

            if current_pos == 0 and rsi_val < oversold:
                current_pos = 1  # Enter Long
            elif current_pos == 1 and rsi_val > overbought:
                current_pos = 0  # Exit to Cash
            positions[i] = current_pos

        data["Position"] = positions
        return self._evaluate_strategy(data, strategy_name="RSI_Mean_Reversion")

    def _evaluate_strategy(self, data: pd.DataFrame, strategy_name: str) -> Dict[str, Any]:
        """
        Vectorized evaluation of returns, transaction costs, equity curve, and trade log.
        """
        df = data.copy()
        if "Daily_Return" not in df.columns:
            df["Daily_Return"] = df["Close"].pct_change().fillna(0)
        else:
            df["Daily_Return"] = df["Daily_Return"].fillna(0)

        # Strategy Return = Position * Asset Return
        df["Raw_Strategy_Return"] = df["Position"] * df["Daily_Return"]

        # Transaction costs: detect position changes
        df["Trades"] = df["Position"].diff().abs().fillna(0)
        df["Cost"] = df["Trades"] * self.commission
        df["Strategy_Return"] = df["Raw_Strategy_Return"] - df["Cost"]

        # Cumulative Equity Curves
        df["Strategy_Equity"] = self.initial_capital * (1 + df["Strategy_Return"]).cumprod()
        df["Benchmark_Equity"] = self.initial_capital * (1 + df["Daily_Return"]).cumprod()

        # Performance summary
        strat_final = float(df["Strategy_Equity"].iloc[-1])
        bench_final = float(df["Benchmark_Equity"].iloc[-1])

        strat_total_return = (strat_final - self.initial_capital) / self.initial_capital
        bench_total_return = (bench_final - self.initial_capital) / self.initial_capital

        n_days = len(df)
        years = max(n_days / 252.0, 0.01)
        strat_cagr = (strat_final / self.initial_capital) ** (1.0 / years) - 1.0
        bench_cagr = (bench_final / self.initial_capital) ** (1.0 / years) - 1.0

        # Drawdowns
        strat_rolling_max = df["Strategy_Equity"].cummax()
        strat_drawdown = (df["Strategy_Equity"] - strat_rolling_max) / strat_rolling_max
        max_drawdown = float(strat_drawdown.min())

        bench_rolling_max = df["Benchmark_Equity"].cummax()
        bench_drawdown = (df["Benchmark_Equity"] - bench_rolling_max) / bench_rolling_max
        bench_max_dd = float(bench_drawdown.min())

        # Trades details
        total_trades = int(df["Trades"].sum() / 2)  # Entry + Exit = 1 trade
        trade_logs = self._generate_trade_log(df)

        profitable_trades = [t for t in trade_logs if t["return_pct"] > 0]
        win_rate = (len(profitable_trades) / len(trade_logs) * 100) if trade_logs else 0.0

        return {
            "strategy_name": strategy_name,
            "initial_capital": self.initial_capital,
            "final_strategy_equity": round(strat_final, 2),
            "final_benchmark_equity": round(bench_final, 2),
            "strategy_total_return_pct": round(strat_total_return * 100, 2),
            "benchmark_total_return_pct": round(bench_total_return * 100, 2),
            "strategy_cagr_pct": round(strat_cagr * 100, 2),
            "benchmark_cagr_pct": round(bench_cagr * 100, 2),
            "alpha_pct": round((strat_total_return - bench_total_return) * 100, 2),
            "strategy_max_drawdown_pct": round(max_drawdown * 100, 2),
            "benchmark_max_drawdown_pct": round(bench_max_dd * 100, 2),
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate, 2),
            "trades": trade_logs[-10:],  # Return recent 10 trades
            "equity_df": df[["Close", "Position", "Strategy_Equity", "Benchmark_Equity"]]
        }

    def _generate_trade_log(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extracts individual trade executions, holding periods, and returns."""
        trades = []
        in_trade = False
        entry_date = None
        entry_price = 0.0

        for date, row in df.iterrows():
            pos = row["Position"]
            price = row["Close"]

            if not in_trade and pos == 1:
                in_trade = True
                entry_date = date
                entry_price = price
            elif in_trade and pos == 0:
                in_trade = False
                exit_date = date
                exit_price = price
                ret = (exit_price - entry_price) / (entry_price + 1e-10)
                trades.append({
                    "entry_date": str(entry_date)[:10],
                    "exit_date": str(exit_date)[:10],
                    "entry_price": round(float(entry_price), 2),
                    "exit_price": round(float(exit_price), 2),
                    "return_pct": round(float(ret) * 100, 2)
                })

        return trades


if __name__ == "__main__":
    from data_fetcher import StockDataFetcher
    from indicators import TechnicalIndicators

    fetcher = StockDataFetcher()
    df_raw = fetcher.fetch_data("AAPL", period="2y")
    df_ind = TechnicalIndicators.add_all_indicators(df_raw)

    backtester = StrategyBacktester(initial_capital=10000)
    result = backtester.backtest_ma_crossover(df_ind, fast_period=20, slow_period=50)

    print("Backtest Result Summary:")
    for k, v in result.items():
        if k not in ["trades", "equity_df"]:
            print(f"  {k}: {v}")
    print(f"Recent Trades: {result['trades']}")
