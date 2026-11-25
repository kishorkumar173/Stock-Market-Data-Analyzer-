"""
Technical Indicators & Signal Generation Module
Computes financial market technical indicators: Moving Averages (SMA/EMA),
RSI, MACD, Bollinger Bands, ATR, Volatility, and Quantitative Signal triggers.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Computes industry-standard technical indicators and quantitative trading signals.
    """

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies a full suite of technical indicators to the input OHLCV DataFrame.
        """
        data = df.copy()

        # 1. Price Returns
        data = TechnicalIndicators.add_returns(data)

        # 2. Moving Averages (Trend)
        data = TechnicalIndicators.add_moving_averages(data)

        # 3. Momentum: Relative Strength Index (RSI)
        data = TechnicalIndicators.add_rsi(data, period=14)

        # 4. Momentum / Trend: MACD
        data = TechnicalIndicators.add_macd(data)

        # 5. Volatility: Bollinger Bands
        data = TechnicalIndicators.add_bollinger_bands(data, period=20, std_dev=2.0)

        # 6. Volatility: Average True Range (ATR)
        data = TechnicalIndicators.add_atr(data, period=14)

        # 7. Rolling Annualized Volatility (20-day)
        data = TechnicalIndicators.add_rolling_volatility(data, window=20)

        # 8. Trend & Momentum Signals
        data = TechnicalIndicators.generate_signals(data)

        return data

    @staticmethod
    def add_returns(df: pd.DataFrame) -> pd.DataFrame:
        """Computes daily percentage returns, log returns, and cumulative returns."""
        data = df.copy()
        data["Daily_Return"] = data["Close"].pct_change()
        data["Log_Return"] = np.log(data["Close"] / data["Close"].shift(1))
        data["Cumulative_Return"] = (1 + data["Daily_Return"]).cumprod() - 1
        return data

    @staticmethod
    def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """Computes short-term, medium-term, and long-term SMAs and EMAs."""
        data = df.copy()
        data["SMA_20"] = data["Close"].rolling(window=20, min_periods=1).mean()
        data["SMA_50"] = data["Close"].rolling(window=50, min_periods=1).mean()
        data["SMA_200"] = data["Close"].rolling(window=200, min_periods=1).mean()

        data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
        data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()
        return data

    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Relative Strength Index (RSI) using exponential moving average of gains/losses.
        """
        data = df.copy()
        delta = data["Close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        rs = avg_gain / (avg_loss + 1e-10)
        data[f"RSI_{period}"] = 100 - (100 / (1 + rs))
        return data

    @staticmethod
    def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Moving Average Convergence Divergence (MACD), Signal line, and Histogram.
        """
        data = df.copy()
        ema_fast = data["Close"].ewm(span=fast, adjust=False).mean()
        ema_slow = data["Close"].ewm(span=slow, adjust=False).mean()

        data["MACD"] = ema_fast - ema_slow
        data["MACD_Signal"] = data["MACD"].ewm(span=signal, adjust=False).mean()
        data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]
        return data

    @staticmethod
    def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        Bollinger Bands: Middle (SMA), Upper, Lower bands, and Bandwidth.
        """
        data = df.copy()
        middle = data["Close"].rolling(window=period, min_periods=1).mean()
        std = data["Close"].rolling(window=period, min_periods=1).std()

        data["BB_Middle"] = middle
        data["BB_Upper"] = middle + (std_dev * std)
        data["BB_Lower"] = middle - (std_dev * std)
        data["BB_Bandwidth"] = (data["BB_Upper"] - data["BB_Lower"]) / (data["BB_Middle"] + 1e-10)
        return data

    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Average True Range (ATR) measuring market volatility.
        """
        data = df.copy()
        high_low = data["High"] - data["Low"]
        high_prev_close = (data["High"] - data["Close"].shift(1)).abs()
        low_prev_close = (data["Low"] - data["Close"].shift(1)).abs()

        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        data["ATR_14"] = tr.rolling(window=period, min_periods=1).mean()
        return data

    @staticmethod
    def add_rolling_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        Annualized rolling volatility: standard deviation of daily returns * sqrt(252).
        """
        data = df.copy()
        if "Daily_Return" not in data.columns:
            data["Daily_Return"] = data["Close"].pct_change()
        data[f"Rolling_Vol_{window}d"] = data["Daily_Return"].rolling(window=window, min_periods=5).std() * np.sqrt(252)
        return data

    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates binary and discrete trading signals:
        - SMA Golden Cross (1) / Death Cross (-1)
        - RSI Overbought (-1) / Oversold (1) / Neutral (0)
        - MACD Crossover (1: Bullish, -1: Bearish)
        - Combined Signal Consensus
        """
        data = df.copy()

        # 1. SMA Trend Cross (50 vs 200)
        data["Signal_SMA_Cross"] = 0
        if "SMA_50" in data.columns and "SMA_200" in data.columns:
            condition_bullish = data["SMA_50"] > data["SMA_200"]
            data.loc[condition_bullish, "Signal_SMA_Cross"] = 1
            data.loc[~condition_bullish, "Signal_SMA_Cross"] = -1

        # 2. RSI Signals (Threshold 70 / 30)
        data["Signal_RSI"] = 0
        if "RSI_14" in data.columns:
            data.loc[data["RSI_14"] < 30, "Signal_RSI"] = 1   # Oversold -> Buy Signal
            data.loc[data["RSI_14"] > 70, "Signal_RSI"] = -1  # Overbought -> Sell Signal

        # 3. MACD Cross
        data["Signal_MACD"] = 0
        if "MACD" in data.columns and "MACD_Signal" in data.columns:
            data.loc[data["MACD"] > data["MACD_Signal"], "Signal_MACD"] = 1
            data.loc[data["MACD"] < data["MACD_Signal"], "Signal_MACD"] = -1

        # 4. Overall Consensus Score (-3 strong sell to +3 strong buy)
        data["Consensus_Score"] = data["Signal_SMA_Cross"] + data["Signal_RSI"] + data["Signal_MACD"]
        data["Overall_Trend"] = "Neutral"
        data.loc[data["Consensus_Score"] >= 2, "Overall_Trend"] = "Strongly Bullish"
        data.loc[data["Consensus_Score"] == 1, "Overall_Trend"] = "Mildly Bullish"
        data.loc[data["Consensus_Score"] == -1, "Overall_Trend"] = "Mildly Bearish"
        data.loc[data["Consensus_Score"] <= -2, "Overall_Trend"] = "Strongly Bearish"

        return data


if __name__ == "__main__":
    from data_fetcher import StockDataFetcher
    fetcher = StockDataFetcher()
    df_raw = fetcher.fetch_data("AAPL", period="1y")
    df_ind = TechnicalIndicators.add_all_indicators(df_raw)
    print(f"Computed Indicators Columns:\n{df_ind.columns.tolist()}")
    print(f"Latest Technical Summary:\n{df_ind[['Close', 'SMA_50', 'SMA_200', 'RSI_14', 'MACD', 'Overall_Trend']].tail(3)}")
