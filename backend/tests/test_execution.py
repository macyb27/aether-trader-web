"""
Tests for the Execution Engine and Paper Trader.
"""

import pytest


class TestExecutionEngine:
    """Test order management and execution."""

    def test_engine_initialization(self):
        from backend.execution.execution_engine import ExecutionEngine

        engine = ExecutionEngine(mode="paper")
        assert engine.mode == "paper"
        assert len(engine.orders) == 0
        assert len(engine.positions) == 0

    def test_submit_order(self):
        from backend.execution.execution_engine import (
            ExecutionEngine, Order, OrderSide, OrderType, OrderStatus,
        )

        engine = ExecutionEngine(mode="paper")
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1,
            price=50000.0,
        )

        result = engine.submit_order(order)
        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 0.1

    def test_cancel_order(self):
        from backend.execution.execution_engine import (
            ExecutionEngine, Order, OrderSide, OrderType, OrderStatus,
        )

        engine = ExecutionEngine(mode="paper")
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=45000.0,
        )

        # Limit orders don't auto-fill in paper mode
        engine.orders[order.id] = order
        order.status = OrderStatus.SUBMITTED

        result = engine.cancel_order(order.id)
        assert result is True

    def test_reject_invalid_order(self):
        from backend.execution.execution_engine import (
            ExecutionEngine, Order, OrderSide, OrderType, OrderStatus,
        )

        engine = ExecutionEngine(mode="paper")
        order = Order(
            symbol="",  # Invalid: no symbol
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1,
        )

        result = engine.submit_order(order)
        assert result.status == OrderStatus.REJECTED

    def test_position_tracking(self):
        from backend.execution.execution_engine import (
            ExecutionEngine, Order, OrderSide, OrderType,
        )

        engine = ExecutionEngine(mode="paper")

        # Buy order
        buy_order = Order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10.0,
            price=3000.0,
        )
        engine.submit_order(buy_order)

        positions = engine.get_positions()
        assert "ETH/USDT" in positions

    def test_get_open_orders(self):
        from backend.execution.execution_engine import ExecutionEngine

        engine = ExecutionEngine(mode="paper")
        open_orders = engine.get_open_orders()
        assert isinstance(open_orders, list)


class TestPaperTrader:
    """Test paper trading system."""

    def test_paper_trader_initialization(self):
        from backend.execution.paper_trader import PaperTrader

        trader = PaperTrader(initial_capital=100_000)
        assert trader.cash == 100_000
        assert trader.initial_capital == 100_000

    def test_portfolio_value(self):
        from backend.execution.paper_trader import PaperTrader

        trader = PaperTrader(initial_capital=50_000)
        value = trader.get_portfolio_value()
        assert value == 50_000

    def test_portfolio_summary(self):
        from backend.execution.paper_trader import PaperTrader

        trader = PaperTrader()
        summary = trader.get_portfolio_summary()

        assert "total_value" in summary
        assert "cash" in summary
        assert "pnl" in summary
        assert "pnl_pct" in summary
        assert "total_trades" in summary

    def test_snapshot(self):
        from backend.execution.paper_trader import PaperTrader

        trader = PaperTrader()
        snap = trader.snapshot()

        assert "timestamp" in snap
        assert "total_value" in snap

    def test_reset(self):
        from backend.execution.paper_trader import PaperTrader

        trader = PaperTrader(initial_capital=100_000)
        trader.cash = 50_000  # Simulate some spending
        trader.reset()
        assert trader.cash == 100_000

    def test_trade_history_empty(self):
        from backend.execution.paper_trader import PaperTrader

        trader = PaperTrader()
        history = trader.get_trade_history()
        assert history.empty


class TestMetricsCollector:
    """Test monitoring metrics."""

    def test_collector_initialization(self):
        from backend.monitoring.metrics_collector import MetricsCollector

        collector = MetricsCollector()
        assert collector is not None

    def test_increment_counter(self):
        from backend.monitoring.metrics_collector import MetricsCollector

        collector = MetricsCollector()
        collector.increment("test_counter")
        collector.increment("test_counter")

        metrics = collector.get_metrics_json()
        assert metrics["counters"]["aether_test_counter"] == 2

    def test_set_gauge(self):
        from backend.monitoring.metrics_collector import MetricsCollector

        collector = MetricsCollector()
        collector.set_gauge("portfolio_value", 105000.0)

        metrics = collector.get_metrics_json()
        assert metrics["gauges"]["aether_portfolio_value"] == 105000.0

    def test_prometheus_format(self):
        from backend.monitoring.metrics_collector import MetricsCollector

        collector = MetricsCollector()
        collector.increment("trades_total", 5)
        collector.set_gauge("risk_score", 42.0)

        text = collector.get_metrics_text()
        assert "aether_trades_total" in text
        assert "aether_risk_score" in text
        assert "aether_uptime_seconds" in text
