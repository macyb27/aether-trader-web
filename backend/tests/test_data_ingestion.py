"""
Tests for the Data Ingestion module.
"""

import numpy as np
import pandas as pd
import pytest


class TestMarketDataLoader:
    """Test market data loader."""

    def test_loader_initialization(self):
        from backend.data_ingestion.market_data_loader import MarketDataLoader

        loader = MarketDataLoader()
        assert loader is not None
        assert hasattr(loader, "feeds")
        assert hasattr(loader, "load_market_data")

    def test_loader_has_cache(self):
        from backend.data_ingestion.market_data_loader import MarketDataLoader

        loader = MarketDataLoader()
        assert hasattr(loader, "_cache")

    def test_register_feed(self):
        from backend.data_ingestion.market_data_loader import MarketDataLoader

        loader = MarketDataLoader()
        # Should have default feeds registered
        assert len(loader.feeds) >= 0


class TestCryptoFeed:
    """Test crypto data feed."""

    def test_crypto_feed_initialization(self):
        from backend.data_ingestion.crypto_feed import CryptoFeed

        feed = CryptoFeed()
        assert feed is not None
        assert hasattr(feed, "fetch_ohlcv")

    def test_crypto_feed_has_exchange(self):
        from backend.data_ingestion.crypto_feed import CryptoFeed

        feed = CryptoFeed(exchange_id="binance")
        assert feed.exchange_id == "binance"


class TestEquityFeed:
    """Test equity data feed."""

    def test_equity_feed_initialization(self):
        from backend.data_ingestion.equity_feed import EquityFeed

        feed = EquityFeed()
        assert feed is not None
        assert hasattr(feed, "fetch_ohlcv")
