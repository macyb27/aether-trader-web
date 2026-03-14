"""
Tests for the centralized logging system.
"""

import logging
import os
import tempfile

import pytest


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging(self):
        from backend.utils.logger import setup_logging

        logger = setup_logging(level="DEBUG")
        assert logger is not None
        assert logger.level == logging.DEBUG

    def test_get_trade_logger(self):
        from backend.utils.logger import get_trade_logger

        logger = get_trade_logger()
        assert logger is not None
        assert logger.name == "aether.trades"

    def test_get_pipeline_logger(self):
        from backend.utils.logger import get_pipeline_logger

        logger = get_pipeline_logger()
        assert logger is not None
        assert logger.name == "aether.pipeline"

    def test_get_pnl_logger(self):
        from backend.utils.logger import get_pnl_logger

        logger = get_pnl_logger()
        assert logger is not None
        assert logger.name == "aether.pnl"

    def test_log_trade(self):
        from backend.utils.logger import log_trade

        # Should not raise
        log_trade(
            symbol="BTC/USDT",
            side="buy",
            quantity=0.5,
            price=50000.0,
            strategy="momentum",
            trade_id="test-001",
        )

    def test_log_pnl(self):
        from backend.utils.logger import log_pnl

        # Should not raise
        log_pnl(
            portfolio_value=105000.0,
            cash=50000.0,
            total_pnl=5000.0,
            pnl_pct=0.05,
            positions=3,
            drawdown=-0.02,
        )


class TestJSONFormatter:
    """Test JSON log formatting."""

    def test_json_format(self):
        import json
        from backend.utils.logger import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=None,
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
