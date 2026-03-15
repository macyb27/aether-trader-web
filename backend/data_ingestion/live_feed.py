"""
Live Feed - Real-time market data ingestion via WebSockets.
Supports multiple exchanges via CCXT Pro or direct WebSocket connections.
"""

import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional

import websockets
from .market_data_loader import MarketDataLoader

logger = logging.getLogger(__name__)


class LiveMarketFeed:
    """
    Handles real-time market data streams.
    In production, this should use CCXT Pro for unified WebSocket access.
    """

    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.callbacks: List[Callable] = []
        self.is_running = False

    def register_callback(self, callback: Callable[[Dict], None]):
        """Register a function to be called on every new market update."""
        self.callbacks.append(callback)

    async def start_stream(self, symbols: List[str]):
        """Start streaming real-time data for the given symbols."""
        self.is_running = True
        tasks = []
        for symbol in symbols:
            if symbol not in self.active_streams:
                task = asyncio.create_task(self._stream_symbol(symbol))
                self.active_streams[symbol] = task
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks)

    async def stop_stream(self, symbol: Optional[str] = None):
        """Stop streaming for a specific symbol or all symbols."""
        if symbol:
            if symbol in self.active_streams:
                self.active_streams[symbol].cancel()
                del self.active_streams[symbol]
        else:
            for task in self.active_streams.values():
                task.cancel()
            self.active_streams.clear()
            self.is_running = False

    async def _stream_symbol(self, symbol: str):
        """
        Internal stream handler for a single symbol.
        Example implementation for Binance WebSocket.
        """
        # Convert symbol to Binance format (e.g., BTC/USDT -> btcusdt)
        formatted_symbol = symbol.replace("/", "").lower()
        url = f"wss://stream.binance.com:9443/ws/{formatted_symbol}@kline_1m"

        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info(f"Connected to live stream for {symbol}")
                    async for message in ws:
                        data = json.loads(message)
                        processed_data = self._process_message(data, symbol)
                        
                        # Notify all registered callbacks
                        for callback in self.callbacks:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(processed_data)
                            else:
                                callback(processed_data)
            except Exception as e:
                logger.error(f"Stream error for {symbol}: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    def _process_message(self, data: Dict, symbol: str) -> Dict:
        """Normalize exchange-specific message to Aether format."""
        # Example for Binance Kline stream
        k = data.get("k", {})
        return {
            "symbol": symbol,
            "timestamp": data.get("E"),
            "open": float(k.get("o", 0)),
            "high": float(k.get("h", 0)),
            "low": float(k.get("l", 0)),
            "close": float(k.get("c", 0)),
            "volume": float(k.get("v", 0)),
            "is_final": k.get("x", False)
        }


# Global instance for the platform
live_feed = LiveMarketFeed()
