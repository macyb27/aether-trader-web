"""
Realtime Stream - WebSocket-based real-time market data streaming.
Supports multiple exchange connections with automatic reconnection.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RealtimeStream:
    """
    Real-time market data streaming via WebSocket connections.
    Supports pub/sub pattern for distributing data to multiple consumers.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._connections: Dict[str, object] = {}
        self._running = False
        self._buffer: Dict[str, list] = {}
        self._buffer_size = self.config.get("buffer_size", 1000)
        logger.info("RealtimeStream initialized")

    def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a data channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)
        logger.info(f"Subscriber added to channel: {channel}")

    def unsubscribe(self, channel: str, callback: Callable) -> None:
        """Unsubscribe from a data channel."""
        if channel in self._subscribers:
            self._subscribers[channel] = [
                cb for cb in self._subscribers[channel] if cb != callback
            ]

    async def start(self, channels: List[str]) -> None:
        """Start streaming data for given channels."""
        self._running = True
        logger.info(f"Starting realtime stream for {len(channels)} channels")

        tasks = [self._stream_channel(ch) for ch in channels]
        await asyncio.gather(*tasks)

    async def stop(self) -> None:
        """Stop all streams."""
        self._running = False
        for conn_id, conn in self._connections.items():
            try:
                await conn.close()
            except Exception:
                pass
        self._connections.clear()
        logger.info("Realtime stream stopped")

    async def _stream_channel(self, channel: str) -> None:
        """Stream data for a single channel with auto-reconnect."""
        retry_count = 0
        max_retries = self.config.get("max_retries", 10)
        retry_delay = self.config.get("retry_delay", 5)

        while self._running and retry_count < max_retries:
            try:
                # Placeholder for WebSocket connection
                # In production, connect to exchange WebSocket API
                logger.info(f"Connected to channel: {channel}")
                retry_count = 0

                while self._running:
                    # Simulate receiving data
                    await asyncio.sleep(1)
                    data = {
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "tick",
                    }
                    await self._dispatch(channel, data)

            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Stream error on {channel} (retry {retry_count}/{max_retries}): {e}"
                )
                await asyncio.sleep(retry_delay * retry_count)

    async def _dispatch(self, channel: str, data: Dict) -> None:
        """Dispatch data to all subscribers of a channel."""
        # Buffer data
        if channel not in self._buffer:
            self._buffer[channel] = []
        self._buffer[channel].append(data)
        if len(self._buffer[channel]) > self._buffer_size:
            self._buffer[channel] = self._buffer[channel][-self._buffer_size:]

        # Notify subscribers
        for callback in self._subscribers.get(channel, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")

    def get_buffer(self, channel: str) -> List[Dict]:
        """Get buffered data for a channel."""
        return self._buffer.get(channel, [])

    @property
    def is_running(self) -> bool:
        return self._running
