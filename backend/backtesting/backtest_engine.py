"""
Backtest Engine - High-performance backtesting using vectorbt.
Supports vectorized and event-driven backtesting with realistic execution simulation.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import vectorbt as vbt

from .performance_metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""
    initial_capital: float = 100_000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    size_type: str = "percent"  # "percent", "fixed", "target"
    size: float = 1.0  # 100% of available capital
    freq: str = "1d"
    allow_short: bool = True
    max_leverage: float = 1.0
    risk_free_rate: float = 0.02


@dataclass
class BacktestResult:
    """Complete backtest result with metrics and trade log."""
    strategy_name: str
    symbol: str
    config: BacktestConfig
    metrics: Dict[str, float]
    equity_curve: pd.Series
    returns: pd.Series
    positions: pd.Series
    trade_log: pd.DataFrame
    drawdown_series: pd.Series
    start_date: datetime = None
    end_date: datetime = None


class BacktestEngine:
    """
    High-performance backtesting engine built on vectorbt.
    
    Features:
    - Vectorized backtesting for speed
    - Realistic commission and slippage modeling
    - Walk-forward analysis
    - Monte Carlo simulation
    - Multi-asset portfolio backtesting
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        self.metrics_calculator = PerformanceMetrics()
        logger.info("BacktestEngine initialized")

    def backtest(
        self,
        signals: pd.Series,
        price_data: pd.DataFrame,
        strategy_name: str = "unnamed",
        config: Optional[BacktestConfig] = None,
    ) -> BacktestResult:
        """
        Run a backtest on a single asset.

        Args:
            signals: Trading signals (-1, 0, 1)
            price_data: OHLCV DataFrame
            strategy_name: Name identifier
            config: Optional override config

        Returns:
            BacktestResult with full metrics and trade log
        """
        cfg = config or self.config
        close = price_data["close"]

        # Align signals with price data
        common_idx = signals.index.intersection(close.index)
        signals = signals.loc[common_idx]
        close = close.loc[common_idx]

        try:
            # Create entries and exits from signals
            entries = (signals > 0) & (signals.shift(1) <= 0)
            exits = (signals <= 0) & (signals.shift(1) > 0)

            short_entries = (signals < 0) & (signals.shift(1) >= 0) if cfg.allow_short else pd.Series(False, index=common_idx)
            short_exits = (signals >= 0) & (signals.shift(1) < 0) if cfg.allow_short else pd.Series(False, index=common_idx)

            # Run vectorbt portfolio simulation
            portfolio = vbt.Portfolio.from_signals(
                close=close,
                entries=entries,
                exits=exits,
                short_entries=short_entries,
                short_exits=short_exits,
                init_cash=cfg.initial_capital,
                fees=cfg.commission,
                slippage=cfg.slippage,
                freq=cfg.freq,
            )

            # Extract results
            equity_curve = portfolio.value()
            returns = portfolio.returns()
            positions = portfolio.position_mask().astype(int)

            # Build trade log
            trades = portfolio.trades.records_readable
            trade_log = self._build_trade_log(trades) if len(trades) > 0 else pd.DataFrame()

            # Calculate comprehensive metrics
            metrics = self.metrics_calculator.calculate_all(
                returns=returns,
                equity_curve=equity_curve,
                trade_log=trade_log,
                risk_free_rate=cfg.risk_free_rate,
            )

            # Drawdown series
            drawdown_series = portfolio.drawdown()

            result = BacktestResult(
                strategy_name=strategy_name,
                symbol=price_data.get("symbol", "unknown") if isinstance(price_data, dict) else "unknown",
                config=cfg,
                metrics=metrics,
                equity_curve=equity_curve,
                returns=returns,
                positions=positions,
                trade_log=trade_log,
                drawdown_series=drawdown_series,
                start_date=common_idx[0],
                end_date=common_idx[-1],
            )

            logger.info(
                f"Backtest '{strategy_name}': "
                f"Return={metrics.get('total_return', 0):.2%}, "
                f"Sharpe={metrics.get('sharpe_ratio', 0):.2f}, "
                f"MaxDD={metrics.get('max_drawdown', 0):.2%}"
            )

            return result

        except Exception as e:
            logger.error(f"Backtest failed for '{strategy_name}': {e}")
            return BacktestResult(
                strategy_name=strategy_name,
                symbol="error",
                config=cfg,
                metrics={},
                equity_curve=pd.Series(dtype=float),
                returns=pd.Series(dtype=float),
                positions=pd.Series(dtype=int),
                trade_log=pd.DataFrame(),
                drawdown_series=pd.Series(dtype=float),
            )

    def backtest_strategies(
        self,
        strategies: Dict[str, pd.Series],
        price_data: pd.DataFrame,
    ) -> Dict[str, BacktestResult]:
        """Backtest multiple strategies on the same data."""
        results = {}
        for name, signals in strategies.items():
            results[name] = self.backtest(signals, price_data, strategy_name=name)
        return results

    def walk_forward(
        self,
        signals_func,
        price_data: pd.DataFrame,
        features: pd.DataFrame,
        n_splits: int = 5,
        train_ratio: float = 0.7,
    ) -> List[BacktestResult]:
        """
        Walk-forward analysis with rolling train/test splits.

        Args:
            signals_func: Function that takes features and returns signals
            price_data: OHLCV data
            features: Feature matrix
            n_splits: Number of walk-forward periods
            train_ratio: Ratio of training data in each split

        Returns:
            List of BacktestResult for each test period
        """
        n = len(price_data)
        split_size = n // n_splits
        results = []

        for i in range(n_splits):
            start = i * split_size
            end = min((i + 2) * split_size, n)
            train_end = start + int((end - start) * train_ratio)

            # Train period
            train_features = features.iloc[start:train_end]
            # Test period
            test_features = features.iloc[train_end:end]
            test_prices = price_data.iloc[train_end:end]

            try:
                # Generate signals on test data (model fitted on train)
                signals = signals_func(train_features, test_features)
                result = self.backtest(signals, test_prices, f"wf_split_{i}")
                results.append(result)
            except Exception as e:
                logger.error(f"Walk-forward split {i} failed: {e}")

        return results

    def monte_carlo(
        self,
        returns: pd.Series,
        n_simulations: int = 1000,
        n_periods: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Monte Carlo simulation by bootstrapping returns.

        Returns distribution of key metrics across simulations.
        """
        if n_periods is None:
            n_periods = len(returns)

        simulated_metrics = []

        for _ in range(n_simulations):
            # Bootstrap returns with replacement
            sampled = returns.sample(n=n_periods, replace=True).values
            cum_returns = (1 + sampled).cumprod()

            total_return = cum_returns[-1] - 1
            sharpe = np.mean(sampled) / np.std(sampled) * np.sqrt(252) if np.std(sampled) > 0 else 0
            max_dd = (cum_returns / np.maximum.accumulate(cum_returns) - 1).min()

            simulated_metrics.append({
                "total_return": total_return,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
            })

        df = pd.DataFrame(simulated_metrics)
        return {
            "mean": df.mean().to_dict(),
            "std": df.std().to_dict(),
            "percentile_5": df.quantile(0.05).to_dict(),
            "percentile_25": df.quantile(0.25).to_dict(),
            "percentile_50": df.quantile(0.50).to_dict(),
            "percentile_75": df.quantile(0.75).to_dict(),
            "percentile_95": df.quantile(0.95).to_dict(),
        }

    def _build_trade_log(self, trades) -> pd.DataFrame:
        """Build a clean trade log from vectorbt trades."""
        try:
            if hasattr(trades, "to_dict"):
                return pd.DataFrame(trades.to_dict())
            return pd.DataFrame(trades)
        except Exception:
            return pd.DataFrame()

    def select_best(
        self,
        results: Dict[str, BacktestResult],
        metric: str = "sharpe_ratio",
        min_trades: int = 10,
    ) -> List[Tuple[str, BacktestResult]]:
        """
        Select best strategies based on a metric.

        Args:
            results: Dictionary of backtest results
            metric: Metric to rank by
            min_trades: Minimum number of trades required

        Returns:
            Sorted list of (name, result) tuples
        """
        valid = [
            (name, r)
            for name, r in results.items()
            if r.metrics.get("total_trades", 0) >= min_trades
        ]

        valid.sort(key=lambda x: x[1].metrics.get(metric, float("-inf")), reverse=True)
        return valid
