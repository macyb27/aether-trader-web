"""
Performance Metrics - Comprehensive trading performance metrics calculation.
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Calculates comprehensive performance metrics for backtested strategies.
    Includes return, risk, risk-adjusted, and trade-level metrics.
    """

    def calculate_all(
        self,
        returns: pd.Series,
        equity_curve: pd.Series,
        trade_log: pd.DataFrame,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252,
    ) -> Dict[str, float]:
        """Calculate all performance metrics."""
        metrics = {}

        # Return metrics
        metrics.update(self._return_metrics(returns, equity_curve, periods_per_year))

        # Risk metrics
        metrics.update(self._risk_metrics(returns, equity_curve, periods_per_year))

        # Risk-adjusted metrics
        metrics.update(
            self._risk_adjusted_metrics(returns, risk_free_rate, periods_per_year)
        )

        # Drawdown metrics
        metrics.update(self._drawdown_metrics(equity_curve))

        # Trade metrics
        if not trade_log.empty:
            metrics.update(self._trade_metrics(trade_log))

        return metrics

    def _return_metrics(
        self, returns: pd.Series, equity_curve: pd.Series, periods: int
    ) -> Dict[str, float]:
        """Calculate return-based metrics."""
        if len(returns) == 0:
            return {}

        total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1 if len(equity_curve) > 0 else 0
        n_years = len(returns) / periods
        annual_return = (1 + total_return) ** (1 / max(n_years, 0.01)) - 1 if total_return > -1 else -1

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "cumulative_return": total_return,
            "avg_daily_return": returns.mean(),
            "best_day": returns.max(),
            "worst_day": returns.min(),
            "positive_days": (returns > 0).sum() / len(returns),
        }

    def _risk_metrics(
        self, returns: pd.Series, equity_curve: pd.Series, periods: int
    ) -> Dict[str, float]:
        """Calculate risk metrics."""
        if len(returns) == 0:
            return {}

        volatility = returns.std() * np.sqrt(periods)
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(periods) if len(downside_returns) > 0 else 0

        # Value at Risk
        var_95 = np.percentile(returns.dropna(), 5)
        var_99 = np.percentile(returns.dropna(), 1)

        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95

        return {
            "volatility": volatility,
            "downside_volatility": downside_vol,
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "skewness": returns.skew(),
            "kurtosis": returns.kurt(),
        }

    def _risk_adjusted_metrics(
        self, returns: pd.Series, risk_free_rate: float, periods: int
    ) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics."""
        if len(returns) == 0:
            return {}

        daily_rf = risk_free_rate / periods
        excess_returns = returns - daily_rf

        # Sharpe Ratio
        sharpe = (
            excess_returns.mean() / excess_returns.std() * np.sqrt(periods)
            if excess_returns.std() > 0 else 0
        )

        # Sortino Ratio
        downside = excess_returns[excess_returns < 0]
        sortino = (
            excess_returns.mean() / downside.std() * np.sqrt(periods)
            if len(downside) > 0 and downside.std() > 0 else 0
        )

        # Calmar Ratio
        equity = (1 + returns).cumprod()
        max_dd = ((equity / equity.cummax()) - 1).min()
        annual_return = (equity.iloc[-1]) ** (periods / len(returns)) - 1 if len(returns) > 0 else 0
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0

        # Omega Ratio
        threshold = daily_rf
        gains = excess_returns[excess_returns > threshold].sum()
        losses = abs(excess_returns[excess_returns <= threshold].sum())
        omega = gains / losses if losses > 0 else float("inf")

        return {
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "omega_ratio": omega,
        }

    def _drawdown_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """Calculate drawdown metrics."""
        if len(equity_curve) == 0:
            return {}

        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve - rolling_max) / rolling_max

        max_dd = drawdown.min()
        avg_dd = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0

        # Max drawdown duration
        is_underwater = drawdown < 0
        underwater_periods = is_underwater.astype(int)
        groups = (underwater_periods != underwater_periods.shift()).cumsum()
        dd_durations = underwater_periods.groupby(groups).sum()
        max_dd_duration = dd_durations.max() if len(dd_durations) > 0 else 0

        return {
            "max_drawdown": max_dd,
            "avg_drawdown": avg_dd,
            "max_drawdown_duration": int(max_dd_duration),
        }

    def _trade_metrics(self, trade_log: pd.DataFrame) -> Dict[str, float]:
        """Calculate trade-level metrics."""
        total_trades = len(trade_log)
        if total_trades == 0:
            return {"total_trades": 0}

        # Try to extract PnL from trade log
        pnl_col = None
        for col in ["pnl", "PnL", "profit", "return", "pnl_pct"]:
            if col in trade_log.columns:
                pnl_col = col
                break

        if pnl_col is None:
            return {"total_trades": total_trades}

        pnl = trade_log[pnl_col]
        winners = pnl[pnl > 0]
        losers = pnl[pnl < 0]

        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        avg_win = winners.mean() if len(winners) > 0 else 0
        avg_loss = losers.mean() if len(losers) > 0 else 0
        profit_factor = abs(winners.sum() / losers.sum()) if losers.sum() != 0 else float("inf")

        # Expectancy
        expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "largest_win": winners.max() if len(winners) > 0 else 0,
            "largest_loss": losers.min() if len(losers) > 0 else 0,
        }
