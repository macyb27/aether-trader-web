"""
Live Risk Engine - Pre-trade risk checks for real-life trading.
Ensures every order is validated against strict risk limits before execution.
"""

import logging
from typing import Dict, Optional, Tuple

from .risk_engine import RiskEngine, RiskLimits

logger = logging.getLogger(__name__)


class LiveRiskEngine(RiskEngine):
    """
    Enhanced risk engine for live trading.
    Adds strict pre-trade checks and circuit breakers.
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        super().__init__(limits)
        self.circuit_breaker_active = False
        self.daily_loss_limit_reached = False

    def pre_trade_check(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        portfolio_value: float,
        current_positions: Dict[str, Dict],
        daily_pnl: float
    ) -> Tuple[bool, str]:
        """
        Perform all risk checks before sending an order to the exchange.
        Returns (is_allowed, reason).
        """
        # 1. Check Circuit Breaker
        if self.circuit_breaker_active:
            return False, "Circuit breaker is active. Trading halted."

        # 2. Check Daily Loss Limit
        if daily_pnl <= - (portfolio_value * self.limits.max_daily_loss):
            self.daily_loss_limit_reached = True
            return False, f"Daily loss limit reached: {daily_pnl:.2f}"

        # 3. Check Position Size Limit
        order_value = quantity * price
        if order_value > (portfolio_value * self.limits.max_position_size):
            return False, f"Order value {order_value:.2f} exceeds max position size."

        # 4. Check Portfolio Leverage
        current_exposure = sum(pos.get("value", 0) for pos in current_positions.values())
        new_exposure = current_exposure + order_value
        if new_exposure > (portfolio_value * self.limits.max_portfolio_leverage):
            return False, f"New exposure {new_exposure:.2f} exceeds max leverage."

        # 5. Check Symbol Concentration
        symbol_exposure = current_positions.get(symbol, {}).get("value", 0) + order_value
        if symbol_exposure > (portfolio_value * self.limits.max_position_size):
            return False, f"Symbol concentration for {symbol} too high."

        # 6. Check Minimum/Maximum Order Quantity (Exchange specific)
        if quantity <= 0:
            return False, "Order quantity must be positive."

        logger.info(f"Pre-trade check passed for {side} {quantity} {symbol} @ {price}")
        return True, "Check passed"

    def activate_kill_switch(self):
        """Emergency halt for all trading activities."""
        self.circuit_breaker_active = True
        logger.critical("KILL SWITCH ACTIVATED! All trading halted.")

    def reset_risk_limits(self):
        """Reset daily limits (usually at start of trading day)."""
        self.daily_loss_limit_reached = False
        self.circuit_breaker_active = False
        logger.info("Risk limits reset for new trading session.")


# Global instance
live_risk = LiveRiskEngine()
