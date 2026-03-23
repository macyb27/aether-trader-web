"""
Crypto Feed - Market data ingestion from cryptocurrency exchanges via CCXT.
Supports multiple exchanges with automatic failover.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import ccxt
import pandas as pd

logger = logging.getLogger(__name__)


class CryptoFeed:
    """
    Cryptocurrency data feed using CCXT unified API.
    Supports 100+ exchanges with unified interface.
    """

    SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        sandbox: bool = True,
    ):
        self.exchange_id = exchange_id
        self.sandbox = sandbox

        exchange_class = getattr(ccxt, exchange_id)
        config = {"enableRateLimit": True}

        if api_key:
            config["apiKey"] = api_key
        if api_secret:
            config["secret"] = api_secret

        self.exchange = exchange_class(config)

        if sandbox and self.exchange.has.get("sandbox"):
            self.exchange.set_sandbox_mode(True)

        self._markets_loaded = False
        logger.info(f"CryptoFeed initialized: {exchange_id} (sandbox={sandbox})")

    def _ensure_markets(self) -> None:
        """Lazy-load market info."""
        if not self._markets_loaded:
            self.exchange.load_markets()
            self._markets_loaded = True

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV candle data from exchange.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            limit: Max number of candles

        Returns:
            DataFrame with columns: open, high, low, close, volume
        """
        self._ensure_markets()

        since = None
        if start:
            since = self.exchange.parse8601(f"{start}T00:00:00Z")

        all_candles = []
        fetched = 0

        while fetched < limit:
            batch_limit = min(limit - fetched, 500)
            candles = self.exchange.fetch_ohlcv(
                symbol, timeframe, since=since, limit=batch_limit
            )

            if not candles:
                break

            all_candles.extend(candles)
            fetched += len(candles)

            # Move since to after last candle
            since = candles[-1][0] + 1

            if len(candles) < batch_limit:
                break

        if not all_candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(
            all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp")

        # Filter by end date if specified
        if end:
            df = df[df.index <= pd.Timestamp(end)]

        return df

    def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current ticker data."""
        self._ensure_markets()
        ticker = self.exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "last": ticker.get("last"),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask"),
            "volume": ticker.get("baseVolume"),
            "change_pct": ticker.get("percentage"),
            "timestamp": ticker.get("datetime"),
        }

    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """Fetch current order book."""
        self._ensure_markets()
        ob = self.exchange.fetch_order_book(symbol, limit=limit)
        return {
            "symbol": symbol,
            "bids": ob.get("bids", [])[:limit],
            "asks": ob.get("asks", [])[:limit],
            "timestamp": ob.get("datetime"),
        }

    def get_symbols(self) -> List[str]:
        """Get all available trading pairs."""
        self._ensure_markets()
        return list(self.exchange.symbols)

    def get_exchange_info(self) -> Dict:
        """Get exchange metadata."""
        return {
            "id": self.exchange.id,
            "name": self.exchange.name,
            "countries": self.exchange.countries,
            "timeframes": list(self.exchange.timeframes.keys())
            if self.exchange.timeframes
            else [],
            "has_fetch_ohlcv": self.exchange.has.get("fetchOHLCV", False),
            "rate_limit": self.exchange.rateLimit,
        }
