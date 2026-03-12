"""
Fitness Functions - Objective functions for genetic optimization.
Supports single and multi-objective fitness evaluation.
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FitnessFunctions:
    """
    Collection of fitness functions for evaluating trading strategies.
    Each function takes backtest metrics and returns a scalar fitness score.
    """

    @staticmethod
    def sharpe_ratio(metrics: Dict[str, float]) -> float:
        """Maximize Sharpe ratio."""
        return metrics.get("sharpe_ratio", -np.inf)

    @staticmethod
    def sortino_ratio(metrics: Dict[str, float]) -> float:
        """Maximize Sortino ratio."""
        return metrics.get("sortino_ratio", -np.inf)

    @staticmethod
    def calmar_ratio(metrics: Dict[str, float]) -> float:
        """Maximize Calmar ratio (return / max drawdown)."""
        return metrics.get("calmar_ratio", -np.inf)

    @staticmethod
    def profit_factor(metrics: Dict[str, float]) -> float:
        """Maximize profit factor."""
        return metrics.get("profit_factor", -np.inf)

    @staticmethod
    def risk_adjusted_return(metrics: Dict[str, float]) -> float:
        """
        Composite fitness: weighted combination of multiple metrics.
        Balances return, risk, and consistency.
        """
        sharpe = metrics.get("sharpe_ratio", 0)
        sortino = metrics.get("sortino_ratio", 0)
        max_dd = abs(metrics.get("max_drawdown", -1))
        win_rate = metrics.get("win_rate", 0)
        profit_factor = metrics.get("profit_factor", 0)
        total_trades = metrics.get("total_trades", 0)

        # Penalize too few trades
        trade_penalty = 1.0 if total_trades >= 30 else total_trades / 30

        # Penalize extreme drawdowns
        dd_penalty = max(0, 1 - max_dd * 2)

        fitness = (
            0.30 * sharpe
            + 0.20 * sortino
            + 0.15 * profit_factor
            + 0.15 * win_rate
            + 0.10 * dd_penalty
            + 0.10 * trade_penalty
        )

        return fitness

    @staticmethod
    def minimum_drawdown(metrics: Dict[str, float]) -> float:
        """Minimize maximum drawdown (returns negative for maximization)."""
        max_dd = metrics.get("max_drawdown", -1)
        return max_dd  # Already negative, so maximizing this minimizes drawdown

    @staticmethod
    def multi_objective(
        metrics: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Multi-objective fitness with configurable weights.

        Default weights balance return, risk, and stability.
        """
        if weights is None:
            weights = {
                "annual_return": 0.25,
                "sharpe_ratio": 0.25,
                "max_drawdown": 0.20,  # Penalty
                "win_rate": 0.15,
                "profit_factor": 0.15,
            }

        score = 0.0
        for metric, weight in weights.items():
            value = metrics.get(metric, 0)

            # Normalize metrics to comparable scales
            if metric == "annual_return":
                normalized = np.clip(value, -1, 5)
            elif metric == "sharpe_ratio":
                normalized = np.clip(value, -3, 5)
            elif metric == "max_drawdown":
                normalized = 1 + value  # Convert negative DD to positive score
            elif metric == "win_rate":
                normalized = value  # Already 0-1
            elif metric == "profit_factor":
                normalized = np.clip(value / 3, 0, 1)  # Normalize to 0-1
            else:
                normalized = value

            score += weight * normalized

        return score
