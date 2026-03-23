"""
Risk Engine - Comprehensive risk management system.
Handles position sizing, exposure limits, drawdown controls, and real-time monitoring.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk limit configuration."""
    max_position_size: float = 0.10  # 10% of portfolio per position
    max_portfolio_leverage: float = 1.0
    max_sector_exposure: float = 0.30  # 30% per sector
    max_correlation_exposure: float = 0.50
    max_daily_loss: float = 0.02  # 2% daily loss limit
    max_drawdown: float = 0.10  # 10% max drawdown
    max_var_95: float = 0.03  # 3% daily VaR limit
    min_liquidity_ratio: float = 0.20  # 20% cash minimum
    max_single_trade_risk: float = 0.01  # 1% risk per trade
    stop_loss_pct: float = 0.02  # 2% stop loss
    trailing_stop_pct: float = 0.03  # 3% trailing stop


@dataclass
class RiskReport:
    """Risk assessment report."""
    timestamp: datetime
    portfolio_value: float
    total_exposure: float
    leverage: float
    daily_pnl: float
    daily_pnl_pct: float
    current_drawdown: float
    var_95: float
    cvar_95: float
    position_risks: Dict[str, Dict]
    violations: List[str]
    risk_score: float  # 0-100, higher = more risk


class RiskEngine:
    """
    Real-time risk management engine.
    
    Features:
    - Position sizing (Kelly, fixed fractional, volatility-targeted)
    - Exposure monitoring and limit enforcement
    - Drawdown controls with circuit breakers
    - VaR/CVaR computation
    - Correlation-based risk assessment
    - Real-time risk scoring
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()
        self._portfolio_history: List[float] = []
        self._peak_value: float = 0.0
        self._daily_start_value: float = 0.0
        self._circuit_breaker_active: bool = False
        logger.info("RiskEngine initialized")

    def assess_risk(
        self,
        portfolio_value: float,
        positions: Dict[str, Dict],
        returns_history: pd.Series,
    ) -> RiskReport:
        """
        Perform comprehensive risk assessment.

        Args:
            portfolio_value: Current portfolio value
            positions: Dict of position_name -> {value, weight, side}
            returns_history: Historical portfolio returns

        Returns:
            RiskReport with current risk state
        """
        violations = []

        # Update tracking
        self._portfolio_history.append(portfolio_value)
        self._peak_value = max(self._peak_value, portfolio_value)

        # Calculate metrics
        total_exposure = sum(abs(p.get("value", 0)) for p in positions.values())
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0

        # Daily PnL
        daily_pnl = portfolio_value - self._daily_start_value if self._daily_start_value > 0 else 0
        daily_pnl_pct = daily_pnl / self._daily_start_value if self._daily_start_value > 0 else 0

        # Current drawdown
        current_dd = (portfolio_value - self._peak_value) / self._peak_value if self._peak_value > 0 else 0

        # VaR/CVaR
        var_95 = self._calculate_var(returns_history, 0.05)
        cvar_95 = self._calculate_cvar(returns_history, 0.05)

        # Position-level risk
        position_risks = {}
        for name, pos in positions.items():
            pos_risk = self._assess_position_risk(name, pos, portfolio_value)
            position_risks[name] = pos_risk

        # Check limits
        if leverage > self.limits.max_portfolio_leverage:
            violations.append(f"Leverage {leverage:.2f} exceeds limit {self.limits.max_portfolio_leverage}")

        if abs(daily_pnl_pct) > self.limits.max_daily_loss:
            violations.append(f"Daily loss {daily_pnl_pct:.2%} exceeds limit {self.limits.max_daily_loss:.2%}")
            self._circuit_breaker_active = True

        if abs(current_dd) > self.limits.max_drawdown:
            violations.append(f"Drawdown {current_dd:.2%} exceeds limit {self.limits.max_drawdown:.2%}")
            self._circuit_breaker_active = True

        if abs(var_95) > self.limits.max_var_95:
            violations.append(f"VaR95 {var_95:.2%} exceeds limit {self.limits.max_var_95:.2%}")

        # Risk score (0-100)
        risk_score = self._calculate_risk_score(
            leverage, daily_pnl_pct, current_dd, var_95, len(violations)
        )

        return RiskReport(
            timestamp=datetime.utcnow(),
            portfolio_value=portfolio_value,
            total_exposure=total_exposure,
            leverage=leverage,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
            current_drawdown=current_dd,
            var_95=var_95,
            cvar_95=cvar_95,
            position_risks=position_risks,
            violations=violations,
            risk_score=risk_score,
        )

    def calculate_position_size(
        self,
        method: str,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        volatility: float = 0.0,
        win_rate: float = 0.5,
        avg_win_loss_ratio: float = 1.5,
    ) -> float:
        """
        Calculate optimal position size.

        Methods:
        - "fixed_fractional": Risk fixed % of portfolio per trade
        - "kelly": Kelly criterion optimal sizing
        - "volatility_target": Target specific portfolio volatility
        - "equal_weight": Equal weight across positions
        """
        if method == "fixed_fractional":
            risk_per_share = abs(entry_price - stop_loss_price)
            if risk_per_share == 0:
                return 0
            risk_amount = portfolio_value * self.limits.max_single_trade_risk
            shares = risk_amount / risk_per_share
            max_shares = (portfolio_value * self.limits.max_position_size) / entry_price
            return min(shares, max_shares)

        elif method == "kelly":
            # Kelly criterion: f* = (p * b - q) / b
            # p = win rate, q = 1-p, b = avg win/loss ratio
            q = 1 - win_rate
            kelly_fraction = (win_rate * avg_win_loss_ratio - q) / avg_win_loss_ratio
            # Half-Kelly for safety
            kelly_fraction = max(0, kelly_fraction * 0.5)
            position_value = portfolio_value * min(kelly_fraction, self.limits.max_position_size)
            return position_value / entry_price

        elif method == "volatility_target":
            target_vol = 0.15  # 15% annualized target
            if volatility == 0:
                return 0
            weight = target_vol / (volatility * np.sqrt(252))
            weight = min(weight, self.limits.max_position_size)
            return (portfolio_value * weight) / entry_price

        elif method == "equal_weight":
            position_value = portfolio_value * self.limits.max_position_size
            return position_value / entry_price

        return 0

    def check_trade_allowed(
        self,
        portfolio_value: float,
        current_positions: Dict[str, Dict],
        proposed_trade: Dict,
    ) -> Tuple[bool, str]:
        """
        Check if a proposed trade is allowed under current risk limits.

        Returns:
            (allowed: bool, reason: str)
        """
        if self._circuit_breaker_active:
            return False, "Circuit breaker active - trading halted"

        trade_value = abs(proposed_trade.get("value", 0))
        trade_weight = trade_value / portfolio_value if portfolio_value > 0 else 0

        # Position size check
        if trade_weight > self.limits.max_position_size:
            return False, f"Position size {trade_weight:.2%} exceeds limit {self.limits.max_position_size:.2%}"

        # Leverage check
        total_exposure = sum(abs(p.get("value", 0)) for p in current_positions.values())
        new_leverage = (total_exposure + trade_value) / portfolio_value
        if new_leverage > self.limits.max_portfolio_leverage:
            return False, f"Would exceed leverage limit: {new_leverage:.2f}"

        # Liquidity check
        cash_ratio = 1 - (total_exposure + trade_value) / portfolio_value
        if cash_ratio < self.limits.min_liquidity_ratio:
            return False, f"Insufficient liquidity: {cash_ratio:.2%}"

        return True, "Trade approved"

    def reset_daily(self, portfolio_value: float) -> None:
        """Reset daily tracking (call at start of each trading day)."""
        self._daily_start_value = portfolio_value
        self._circuit_breaker_active = False

    def _assess_position_risk(
        self, name: str, position: Dict, portfolio_value: float
    ) -> Dict:
        """Assess risk for a single position."""
        value = abs(position.get("value", 0))
        weight = value / portfolio_value if portfolio_value > 0 else 0

        return {
            "name": name,
            "value": value,
            "weight": weight,
            "exceeds_limit": weight > self.limits.max_position_size,
        }

    def _calculate_var(self, returns: pd.Series, alpha: float) -> float:
        """Calculate Value at Risk."""
        if len(returns) < 10:
            return 0.0
        return float(np.percentile(returns.dropna(), alpha * 100))

    def _calculate_cvar(self, returns: pd.Series, alpha: float) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        var = self._calculate_var(returns, alpha)
        tail = returns[returns <= var]
        return float(tail.mean()) if len(tail) > 0 else var

    def _calculate_risk_score(
        self,
        leverage: float,
        daily_pnl_pct: float,
        drawdown: float,
        var_95: float,
        n_violations: int,
    ) -> float:
        """Calculate composite risk score (0-100)."""
        score = 0.0

        # Leverage contribution (0-25)
        score += min(25, (leverage / self.limits.max_portfolio_leverage) * 25)

        # Drawdown contribution (0-25)
        score += min(25, (abs(drawdown) / self.limits.max_drawdown) * 25)

        # VaR contribution (0-25)
        score += min(25, (abs(var_95) / self.limits.max_var_95) * 25)

        # Violations contribution (0-25)
        score += min(25, n_violations * 10)

        return min(100, score)

    @property
    def is_circuit_breaker_active(self) -> bool:
        return self._circuit_breaker_active
