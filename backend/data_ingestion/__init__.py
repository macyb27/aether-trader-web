"""
Aether Trader - Data Ingestion Module
Handles market data collection from multiple sources.
"""

from .market_data_loader import MarketDataLoader
from .crypto_feed import CryptoFeed
from .equity_feed import EquityFeed
from .realtime_stream import RealtimeStream

__all__ = ["MarketDataLoader", "CryptoFeed", "EquityFeed", "RealtimeStream"]
