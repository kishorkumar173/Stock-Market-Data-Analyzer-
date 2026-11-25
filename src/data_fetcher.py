"""
Data Ingestion and Preprocessing Module
Fetches real-time and historical financial market data via Yahoo Finance (yfinance),
with robust offline fallback, automated data validation, and data cleaning.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class StockDataFetcher:
    """
    Handles robust ingestion of stock market data with caching and offline fallback.
    """

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        save_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical stock data.
        Tries online via yfinance first; falls back to cached CSV or simulated realistic market data.

        :param ticker: Stock ticker symbol (e.g. 'AAPL', 'NVDA', 'TSLA', 'MSFT', 'INFY.NS')
        :param start_date: Start date string 'YYYY-MM-DD'
        :param end_date: End date string 'YYYY-MM-DD'
        :param period: yfinance period string like '1y', '2y', '5y', 'max' (default '2y' if dates not given)
        :param save_cache: Whether to persist ingested data to disk in data/
        :return: Cleaned pandas DataFrame indexed by Date with Open, High, Low, Close, Adj Close, Volume.
        """
        ticker = ticker.strip().upper()
        cache_path = os.path.join(self.data_dir, f"{ticker}_historical.csv")

        # Set default dates if not provided
        if not start_date and not period:
            period = "2y"

        df = None

        # 1. Attempt yfinance ingestion
        try:
            import yfinance as yf
            logger.info(f"Connecting to market feed for ticker: {ticker}...")
            
            if period:
                raw_df = yf.download(ticker, period=period, progress=False, auto_adjust=False)
            else:
                raw_df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)

            if raw_df is not None and not raw_df.empty:
                df = self._clean_raw_dataframe(raw_df, ticker)
                logger.info(f"Successfully ingested {len(df)} market records for {ticker} via yfinance.")
        except Exception as e:
            logger.warning(f"Live market ingestion failed for {ticker}: {e}. Checking local cache...")

        # 2. Attempt Local CSV Cache Fallback
        if df is None or df.empty:
            if os.path.exists(cache_path):
                logger.info(f"Loading cached historical data from {cache_path}")
                try:
                    df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    df = self._validate_and_sanitize(df)
                except Exception as e:
                    logger.error(f"Error reading cached CSV: {e}")
                    df = None

        # 3. Fallback: Generate Realistic Historical Market Data (Geometric Brownian Motion)
        if df is None or df.empty:
            logger.warning(f"No live feed or local CSV for {ticker}. Generating high-fidelity synthetic market dataset...")
            df = self._generate_synthetic_market_data(ticker, start_date, end_date)

        # 4. Save to cache
        if save_cache and df is not None and not df.empty:
            df.to_csv(cache_path)
            logger.info(f"Market data cached to {cache_path}")

        return df

    def _clean_raw_dataframe(self, raw_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Flattens multi-level index columns returned by yfinance v0.2.36+,
        standardizes column names, removes NaNs, and ensures proper datetime index.
        """
        df = raw_df.copy()

        # Handle MultiIndex columns (e.g. ('Close', 'AAPL'))
        if isinstance(df.columns, pd.MultiIndex):
            new_cols = []
            for col in df.columns:
                if isinstance(col, tuple):
                    new_cols.append(col[0])
                else:
                    new_cols.append(str(col))
            df.columns = new_cols

        # Standardize column naming
        df.columns = [col.strip().title() for col in df.columns]
        
        # Ensure necessary columns exist
        required = ["Open", "High", "Low", "Close", "Volume"]
        for col in required:
            if col not in df.columns:
                if col == "Volume":
                    df["Volume"] = 1000000
                elif "Adj Close" in df.columns and col == "Close":
                    df["Close"] = df["Adj Close"]
                else:
                    df[col] = df.get("Close", 100.0)

        if "Adj Close" not in df.columns:
            df["Adj Close"] = df["Close"]

        return self._validate_and_sanitize(df)

    def _validate_and_sanitize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensures chronological order, deduplication, datetime index, and forward-fills gaps.
        """
        # Ensure index is DatetimeIndex
        df.index = pd.to_datetime(df.index)
        df.index.name = "Date"

        # Sort chronologically & drop duplicates
        df = df[~df.index.duplicated(keep="last")]
        df = df.sort_index()

        # Fill missing values (forward fill then backward fill)
        numeric_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        df = df.ffill().bfill()
        return df

    def _generate_synthetic_market_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generates realistic stock market daily data using Geometric Brownian Motion (GBM).
        Includes realistic volatility, drift, OHLC spread, and volume surges.
        """
        np.random.seed(abs(hash(ticker)) % (2**32))

        if not end_date:
            end_dt = datetime.now()
        else:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if not start_date:
            start_dt = end_dt - timedelta(days=730)  # 2 years
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        dates = pd.date_range(start=start_dt, end=end_dt, freq="B")  # Business days
        n_days = len(dates)

        # Baseline stock price based on ticker name
        base_price = 150.0
        if "NVDA" in ticker:
            base_price = 120.0
        elif "TSLA" in ticker:
            base_price = 220.0
        elif "MSFT" in ticker:
            base_price = 420.0
        elif "AAPL" in ticker:
            base_price = 180.0

        # Annualized drift (mu) and volatility (sigma)
        mu = 0.12   # 12% annual return trend
        sigma = 0.28  # 28% annualized volatility
        dt = 1 / 252

        # Daily returns via GBM
        daily_returns = np.random.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), n_days)
        price_multipliers = np.exp(daily_returns)
        close_prices = base_price * np.cumprod(price_multipliers)

        # Generate realistic intraday Open, High, Low
        intraday_volatility = np.random.uniform(0.005, 0.025, n_days)
        opens = close_prices * (1 + np.random.normal(0, 0.005, n_days))
        highs = np.maximum(opens, close_prices) * (1 + intraday_volatility)
        lows = np.minimum(opens, close_prices) * (1 - intraday_volatility)
        volumes = np.random.lognormal(mean=16.5, sigma=0.5, size=n_days).astype(int)

        df = pd.DataFrame(
            {
                "Open": np.round(opens, 2),
                "High": np.round(highs, 2),
                "Low": np.round(lows, 2),
                "Close": np.round(close_prices, 2),
                "Adj Close": np.round(close_prices, 2),
                "Volume": volumes
            },
            index=dates
        )
        df.index.name = "Date"
        return df


if __name__ == "__main__":
    fetcher = StockDataFetcher()
    test_df = fetcher.fetch_data("AAPL", period="1y")
    print(f"Sample Fetched Data for AAPL:\n{test_df.tail()}")
