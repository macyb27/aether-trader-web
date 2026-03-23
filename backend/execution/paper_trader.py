"""
Paper Trader - Simulated trading execution for strategy validation.
Maintains a virtual portfolio with realistic execution simulation.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .execution_engine import ExecutionEngine, Order, OrderSide, OrderType

logger = logging.getLogger(__name__)


class PaperTrader:
    """
    Paper trading system for validating strategies in real-time.
    
    Features:
    - Virtual portfolio management
    - Realistic order execution simulation
    - PnL tracking and reporting
    - Position management
    - Trade history logging
    """

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission
        self.slippage_rate = slippage

        self.engine = ExecutionEngine(
            mode="paper",
            config={"commission": commission, "slippage": slippage},
        )

        self.trade_history: List[Dict] = []
        self.portfolio_snapshots: List[Dict] = []
        self._current_prices: Dict[str, float] = {}

        logger.info(f"PaperTrader initialized: capital=${initial_capital:,.2f}")

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current market prices."""
        self._current_prices.update(prices)

    def execute_signals(
        self,
        signals: Dict[str, int],
        prices: Dict[str, float],
    ) -> List[Order]:
        """
        Execute trading signals.

        Args:
            signals: Symbol -> signal (-1, 0, 1)
            prices: Symbol -> current price

        Returns:
            List of executed orders
        """
        self.update_prices(prices)
        orders = []

        for symbol, signal in signals.items():
            price = prices.get(symbol, 0)
            if price <= 0:
                continue

            current_pos = self.engine.get_position(symbol)
            current_qty = current_pos.get("quantity", 0) if current_pos else 0

            if signal == 1 and current_qty <= 0:
                # Buy signal
                position_value = self.cash * 0.1  # 10% of cash per position
                quantity = position_value / price

                order = Order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=quantity,
                    price=price,
                )
                result = self.engine.submit_order(order)
                self.cash -= quantity * price * (1 + self.commission_rate + self.slippage_rate)
                orders.append(result)

                self.trade_history.append({
                    "timestamp": datetime.utcnow(),
                    "symbol": symbol,
                    "side": "buy",
                    "quantity": quantity,
                    "price": price,
                    "value": quantity * price,
                })

            elif signal == -1 and current_qty > 0:
                # Sell signal
                order = Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=current_qty,
                    price=price,
                )
                result = self.engine.submit_order(order)
                self.cash += current_qty * price * (1 - self.commission_rate - self.slippage_rate)
                orders.append(result)

                self.trade_history.append({
                    "timestamp": datetime.utcnow(),
                    "symbol": symbol,
                    "side": "sell",
                    "quantity": current_qty,
                    "price": price,
                    "value": current_qty * price,
                })

        return orders

    def execute_paper_trades(self, portfolio: Dict[str, float]) -> List[Order]:
        """
        Execute trades to match target portfolio weights.

        Args:
            portfolio: Symbol -> target weight

        Returns:
            List of executed orders
        """
        portfolio_value = self.get_portfolio_value()
        return self.engine.execute_portfolio(
            target_weights=portfolio,
            portfolio_value=portfolio_value,
            current_prices=self._current_prices,
        )

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(
            pos.get("quantity", 0) * self._current_prices.get(pos["symbol"], 0)
            for pos in self.engine.get_positions().values()
        )
        return self.cash + positions_value

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary."""
        portfolio_value = self.get_portfolio_value()
        pnl = portfolio_value - self.initial_capital
        pnl_pct = pnl / self.initial_capital

        return {
            "total_value": portfolio_value,
            "cash": self.cash,
            "positions_value": portfolio_value - self.cash,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "positions": self.engine.get_positions(),
            "total_trades": len(self.trade_history),
            "open_orders": len(self.engine.get_open_orders()),
        }

    def get_trade_history(self) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        if not self.trade_history:
            return pd.DataFrame()
        return pd.DataFrame(self.trade_history)

    def snapshot(self) -> Dict:
        """Take a portfolio snapshot."""
        snap = {
            "timestamp": datetime.utcnow(),
            **self.get_portfolio_summary(),
        }
        self.portfolio_snapshots.append(snap)
        return snap

    def reset(self) -> None:
        """Reset paper trader to initial state."""
        self.cash = self.initial_capital
        self.engine = ExecutionEngine(
            mode="paper",
            config={"commission": self.commission_rate, "slippage": self.slippage_rate},
        )
        self.trade_history.clear()
        self.portfolio_snapshots.clear()
        self._current_prices.clear()
        logger.info("PaperTrader reset")
