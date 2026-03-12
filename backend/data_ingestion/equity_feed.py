"""
Equity Feed - Stock and ETF data ingestion via yfinance.
Supports historical OHLCV, fundamentals, and real-time quotes.
"""

import logging
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class EquityFeed:
    """
    Equity market data feed using yfinance.
    Supports stocks, ETFs, indices, and futures.
    """

    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "1h",  # yfinance doesn't support 4h natively
        "1d": "1d",
        "1w": "1wk",
    }

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._ticker_cache: Dict[str, yf.Ticker] = {}
        logger.info("EquityFeed initialized")

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get or create a yfinance Ticker object."""
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for an equity symbol.

        Args:
            symbol: Ticker symbol (e.g., "AAPL", "SPY")
            timeframe: Candle timeframe
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)

        Returns:
            DataFrame with columns: open, high, low, close, volume
        """
        yf_interval = self.TIMEFRAME_MAP.get(timeframe, "1d")

        try:
            ticker = self._get_ticker(symbol)
            df = ticker.history(
                interval=yf_interval,
                start=start,
                end=end,
                auto_adjust=True,
            )

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

            # Standardize column names
            df.columns = [c.lower() for c in df.columns]

            # Keep only OHLCV
            ohlcv_cols = ["open", "high", "low", "close", "volume"]
            available = [c for c in ohlcv_cols if c in df.columns]
            df = df[available]

            # Handle 4h by resampling from 1h
            if timeframe == "4h" and yf_interval == "1h":
                df = self._resample_to_4h(df)

            logger.info(f"Loaded {len(df)} bars for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch equity data for {symbol}: {e}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current quote data."""
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "last": info.get("regularMarketPrice"),
                "bid": info.get("bid"),
                "ask": info.get("ask"),
                "volume": info.get("regularMarketVolume"),
                "change_pct": info.get("regularMarketChangePercent"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
            }
        except Exception as e:
            logger.error(f"Ticker fetch failed for {symbol}: {e}")
            return {"symbol": symbol}

    def fetch_fundamentals(self, symbol: str) -> Dict:
        """Fetch fundamental data for a symbol."""
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"),
                "profit_margin": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
            }
        except Exception as e:
            logger.error(f"Fundamentals fetch failed for {symbol}: {e}")
            return {"symbol": symbol}

    def get_symbols(self) -> List[str]:
        """Return common equity symbols (placeholder)."""
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
            "SPY", "QQQ", "IWM", "DIA", "VTI",
        ]

    def _resample_to_4h(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample 1h data to 4h candles."""
        return df.resample("4h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna()
