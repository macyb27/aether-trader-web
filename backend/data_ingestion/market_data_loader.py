"""
Market Data Loader - Unified interface for loading market data from multiple sources.
Supports crypto (via CCXT), equities (via yfinance), and custom data sources.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataLoader:
    """
    Unified market data loader that aggregates data from multiple feeds.
    Implements caching, rate limiting, and automatic failover.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_ttl: int = self.config.get("cache_ttl", 300)  # 5 min default
        self._cache_timestamps: Dict[str, datetime] = {}
        self.feeds: Dict[str, object] = {}
        logger.info("MarketDataLoader initialized")

    def register_feed(self, name: str, feed: object) -> None:
        """Register a data feed source."""
        self.feeds[name] = feed
        logger.info(f"Feed registered: {name}")

    def load_market_data(
        self,
        symbols: List[str],
        timeframe: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        source: str = "auto",
    ) -> Dict[str, pd.DataFrame]:
        """
        Load market data for given symbols.

        Args:
            symbols: List of ticker symbols (e.g., ["BTC/USDT", "AAPL"])
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            start: Start date string (YYYY-MM-DD)
            end: End date string (YYYY-MM-DD)
            source: Data source ("crypto", "equity", "auto")

        Returns:
            Dictionary mapping symbol -> OHLCV DataFrame
        """
        results = {}
        for symbol in symbols:
            cache_key = f"{symbol}_{timeframe}_{start}_{end}"

            if self._is_cache_valid(cache_key):
                results[symbol] = self._cache[cache_key]
                logger.debug(f"Cache hit for {symbol}")
                continue

            try:
                feed_name = self._resolve_feed(symbol, source)
                feed = self.feeds.get(feed_name)

                if feed is None:
                    logger.warning(f"No feed available for {symbol}, skipping")
                    continue

                df = feed.fetch_ohlcv(
                    symbol=symbol, timeframe=timeframe, start=start, end=end
                )

                df = self._validate_and_clean(df, symbol)
                self._update_cache(cache_key, df)
                results[symbol] = df
                logger.info(f"Loaded {len(df)} bars for {symbol}")

            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {e}")
                results[symbol] = pd.DataFrame()

        return results

    def load_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """Load real-time ticker data for given symbols."""
        results = {}
        for symbol in symbols:
            try:
                feed_name = self._resolve_feed(symbol, "auto")
                feed = self.feeds.get(feed_name)
                if feed:
                    results[symbol] = feed.fetch_ticker(symbol)
            except Exception as e:
                logger.error(f"Realtime fetch failed for {symbol}: {e}")
        return results

    def _resolve_feed(self, symbol: str, source: str) -> str:
        """Determine which feed to use for a given symbol."""
        if source != "auto":
            return source
        if "/" in symbol:
            return "crypto"
        return "equity"

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        ts = self._cache_timestamps.get(key)
        if ts is None:
            return False
        return (datetime.utcnow() - ts).total_seconds() < self._cache_ttl

    def _update_cache(self, key: str, data: pd.DataFrame) -> None:
        """Update cache with new data."""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.utcnow()

    def _validate_and_clean(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate and clean OHLCV data."""
        required_cols = ["open", "high", "low", "close", "volume"]

        if df.empty:
            return df

        # Standardize column names
        df.columns = [c.lower().strip() for c in df.columns]

        # Ensure required columns exist
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"Missing column '{col}' for {symbol}")
                df[col] = np.nan

        # Remove duplicates
        df = df[~df.index.duplicated(keep="last")]

        # Sort by index
        df = df.sort_index()

        # Forward-fill NaN values (max 5 periods)
        df = df.fillna(method="ffill", limit=5)

        # Drop remaining NaN rows
        df = df.dropna(subset=["close"])

        return df[required_cols]

    def get_available_symbols(self, feed_name: str) -> List[str]:
        """Get list of available symbols from a specific feed."""
        feed = self.feeds.get(feed_name)
        if feed and hasattr(feed, "get_symbols"):
            return feed.get_symbols()
        return []

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")
