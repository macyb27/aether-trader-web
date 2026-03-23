"""
Execution Engine - Order management and execution routing.
Supports paper trading and live execution via CCXT.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Represents a trading order."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: float = 0.0
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    strategy_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


class ExecutionEngine:
    """
    Central execution engine that routes orders to appropriate executors.
    Manages order lifecycle, position tracking, and execution reporting.
    """

    def __init__(self, mode: str = "paper", config: Optional[Dict] = None):
        """
        Args:
            mode: "paper" for paper trading, "live" for real execution
            config: Execution configuration
        """
        self.mode = mode
        self.config = config or {}
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Dict] = {}
        self._order_callbacks: List = []
        logger.info(f"ExecutionEngine initialized: mode={mode}")

    def submit_order(self, order: Order) -> Order:
        """
        Submit an order for execution.

        Args:
            order: Order to submit

        Returns:
            Updated order with status
        """
        # Validate order
        if not self._validate_order(order):
            order.status = OrderStatus.REJECTED
            self.orders[order.id] = order
            return order

        order.status = OrderStatus.SUBMITTED
        self.orders[order.id] = order

        logger.info(
            f"Order submitted: {order.id} {order.side.value} "
            f"{order.quantity} {order.symbol} @ {order.order_type.value}"
        )

        # Execute based on mode
        if self.mode == "paper":
            self._paper_execute(order)
        elif self.mode == "live":
            self._live_execute(order)

        # Notify callbacks
        for callback in self._order_callbacks:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"Order callback error: {e}")

        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        order = self.orders.get(order_id)
        if order and order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            logger.info(f"Order cancelled: {order_id}")
            return True
        return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)

    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        return [
            o for o in self.orders.values()
            if o.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL]
        ]

    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions."""
        return self.positions.copy()

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a specific symbol."""
        return self.positions.get(symbol)

    def register_callback(self, callback) -> None:
        """Register an order update callback."""
        self._order_callbacks.append(callback)

    def execute_portfolio(
        self,
        target_weights: Dict[str, float],
        portfolio_value: float,
        current_prices: Dict[str, float],
    ) -> List[Order]:
        """
        Execute trades to reach target portfolio weights.

        Args:
            target_weights: Symbol -> target weight
            portfolio_value: Total portfolio value
            current_prices: Symbol -> current price

        Returns:
            List of submitted orders
        """
        orders = []

        for symbol, target_weight in target_weights.items():
            current_pos = self.positions.get(symbol, {})
            current_value = current_pos.get("value", 0)
            current_weight = current_value / portfolio_value if portfolio_value > 0 else 0

            weight_diff = target_weight - current_weight
            trade_value = weight_diff * portfolio_value

            if abs(trade_value) < 10:  # Skip tiny trades
                continue

            price = current_prices.get(symbol, 0)
            if price <= 0:
                continue

            quantity = abs(trade_value) / price
            side = OrderSide.BUY if trade_value > 0 else OrderSide.SELL

            order = Order(
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=quantity,
                metadata={"target_weight": target_weight, "rebalance": True},
            )

            submitted = self.submit_order(order)
            orders.append(submitted)

        return orders

    def _validate_order(self, order: Order) -> bool:
        """Validate order parameters."""
        if order.quantity <= 0:
            logger.warning(f"Invalid quantity: {order.quantity}")
            return False
        if not order.symbol:
            logger.warning("Missing symbol")
            return False
        if order.order_type == OrderType.LIMIT and order.price is None:
            logger.warning("Limit order requires price")
            return False
        return True

    def _paper_execute(self, order: Order) -> None:
        """Execute order in paper trading mode."""
        # Simulate immediate fill for market orders
        if order.order_type == OrderType.MARKET:
            commission_rate = self.config.get("commission", 0.001)
            slippage_rate = self.config.get("slippage", 0.0005)

            # Use last known price or order price
            fill_price = order.price or 0
            order.filled_quantity = order.quantity
            order.filled_price = fill_price
            order.commission = order.quantity * fill_price * commission_rate
            order.slippage = order.quantity * fill_price * slippage_rate
            order.status = OrderStatus.FILLED
            order.updated_at = datetime.utcnow()

            # Update position
            self._update_position(order)

    def _live_execute(self, order: Order) -> None:
        """Execute order via live exchange (CCXT)."""
        logger.warning("Live execution not yet implemented - falling back to paper")
        self._paper_execute(order)

    def _update_position(self, order: Order) -> None:
        """Update position tracking after a fill."""
        symbol = order.symbol
        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "quantity": 0,
                "avg_price": 0,
                "value": 0,
                "unrealized_pnl": 0,
                "realized_pnl": 0,
            }

        pos = self.positions[symbol]

        if order.side == OrderSide.BUY:
            # Average up
            total_qty = pos["quantity"] + order.filled_quantity
            if total_qty > 0:
                pos["avg_price"] = (
                    (pos["quantity"] * pos["avg_price"] + order.filled_quantity * order.filled_price)
                    / total_qty
                )
            pos["quantity"] = total_qty
        else:
            # Realize PnL on sell
            pnl = (order.filled_price - pos["avg_price"]) * order.filled_quantity
            pos["realized_pnl"] += pnl - order.commission
            pos["quantity"] -= order.filled_quantity

        pos["value"] = pos["quantity"] * order.filled_price

        # Remove closed positions
        if abs(pos["quantity"]) < 1e-10:
            del self.positions[symbol]
