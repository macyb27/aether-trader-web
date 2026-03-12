"""
Trading Pipeline - Main orchestration loop for the Aether Trader platform.

Implements the core trading loop:
    while True:
        data = load_market_data()
        features = build_features(data)
        strategies = generate_strategies(features)
        results = backtest_strategies(strategies)
        best = select_best(results)
        portfolio = optimize_portfolio(best)
        execute_paper_trades(portfolio)
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from ..data_ingestion import MarketDataLoader
from ..feature_engineering import FeaturePipeline
from ..strategy_generator import StrategyEngine
from ..backtesting import BacktestEngine
from ..portfolio_optimizer import PortfolioOptimizer
from ..execution import PaperTrader
from ..risk import RiskEngine
from ..monitoring import MetricsCollector

logger = logging.getLogger(__name__)


class TradingPipeline:
    """
    Main trading pipeline that orchestrates all modules.
    
    Runs the complete cycle:
    1. Data ingestion
    2. Feature engineering
    3. Strategy generation
    4. Backtesting
    5. Strategy selection
    6. Portfolio optimization
    7. Paper trade execution
    8. Risk monitoring
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.is_running = False
        self._iteration = 0

        # Initialize modules
        self.data_loader = MarketDataLoader(config.get("data", {}))
        self.feature_pipeline = FeaturePipeline(config.get("features", {}))
        self.strategy_engine = StrategyEngine(config.get("strategies", {}))
        self.backtest_engine = BacktestEngine()
        self.portfolio_optimizer = PortfolioOptimizer(config.get("portfolio", {}))
        self.paper_trader = PaperTrader(
            initial_capital=config.get("initial_capital", 100_000),
        )
        self.risk_engine = RiskEngine()
        self.metrics = MetricsCollector()

        logger.info("TradingPipeline initialized with all modules")

    def run(
        self,
        symbols: List[str],
        timeframe: str = "1d",
        interval_seconds: int = 3600,
        max_iterations: Optional[int] = None,
    ) -> None:
        """
        Run the trading pipeline in a continuous loop.

        Args:
            symbols: List of symbols to trade
            timeframe: Data timeframe
            interval_seconds: Seconds between iterations
            max_iterations: Maximum iterations (None = infinite)
        """
        self.is_running = True
        logger.info(
            f"Starting trading pipeline: {len(symbols)} symbols, "
            f"timeframe={timeframe}, interval={interval_seconds}s"
        )

        while self.is_running:
            try:
                self._iteration += 1
                start_time = time.time()

                logger.info(f"=== Pipeline Iteration {self._iteration} ===")

                # Step 1: Load market data
                data = self.load_market_data(symbols, timeframe)
                self.metrics.increment("pipeline_data_loads")

                # Step 2: Build features
                features = self.build_features(data)
                self.metrics.increment("pipeline_feature_builds")

                # Step 3: Generate strategies
                strategies = self.generate_strategies(features)
                self.metrics.increment("pipeline_strategy_generations")

                # Step 4: Backtest strategies
                results = self.backtest_strategies(strategies, data)
                self.metrics.increment("pipeline_backtests")

                # Step 5: Select best strategies
                best = self.select_best(results)
                self.metrics.increment("pipeline_selections")

                # Step 6: Optimize portfolio
                portfolio = self.optimize_portfolio(best, data)
                self.metrics.increment("pipeline_optimizations")

                # Step 7: Execute paper trades
                self.execute_paper_trades(portfolio)
                self.metrics.increment("pipeline_executions")

                # Step 8: Risk check
                self._risk_check()

                # Record iteration time
                elapsed = time.time() - start_time
                self.metrics.observe("pipeline_iteration_seconds", elapsed)
                self.metrics.set_gauge("pipeline_iteration", self._iteration)

                logger.info(f"Pipeline iteration {self._iteration} completed in {elapsed:.2f}s")

                # Check max iterations
                if max_iterations and self._iteration >= max_iterations:
                    logger.info(f"Max iterations ({max_iterations}) reached")
                    break

                # Wait for next iteration
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("Pipeline stopped by user")
                break
            except Exception as e:
                logger.error(f"Pipeline iteration {self._iteration} failed: {e}")
                self.metrics.increment("pipeline_errors")
                time.sleep(60)  # Wait before retry

        self.is_running = False
        logger.info("Trading pipeline stopped")

    def load_market_data(
        self, symbols: List[str], timeframe: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Step 1: Load market data from all sources."""
        logger.info(f"Loading market data for {len(symbols)} symbols")
        return self.data_loader.load_market_data(
            symbols=symbols,
            timeframe=timeframe,
            start=self.config.get("start_date"),
            end=self.config.get("end_date"),
        )

    def build_features(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Step 2: Build features from raw market data."""
        logger.info("Building features")
        return self.feature_pipeline.build_features(data)

    def generate_strategies(
        self, features: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, pd.Series]]:
        """Step 3: Generate trading strategies and signals."""
        logger.info("Generating strategies")
        all_signals = {}

        for symbol, feat_df in features.items():
            signals = self.strategy_engine.generate_all_signals(feat_df)
            all_signals[symbol] = signals

        return all_signals

    def backtest_strategies(
        self,
        strategies: Dict[str, Dict[str, pd.Series]],
        data: Dict[str, pd.DataFrame],
    ) -> Dict[str, Dict]:
        """Step 4: Backtest all strategies on all symbols."""
        logger.info("Backtesting strategies")
        all_results = {}

        for symbol, symbol_strategies in strategies.items():
            if symbol not in data or data[symbol].empty:
                continue

            results = self.backtest_engine.backtest_strategies(
                symbol_strategies, data[symbol]
            )
            all_results[symbol] = results

        return all_results

    def select_best(
        self, results: Dict[str, Dict]
    ) -> Dict[str, List]:
        """Step 5: Select best performing strategies."""
        logger.info("Selecting best strategies")
        best = {}

        for symbol, symbol_results in results.items():
            ranked = self.backtest_engine.select_best(
                symbol_results,
                metric="sharpe_ratio",
                min_trades=5,
            )
            best[symbol] = ranked[:3]  # Top 3 per symbol

        return best

    def optimize_portfolio(
        self, best: Dict[str, List], data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """Step 6: Optimize portfolio allocation."""
        logger.info("Optimizing portfolio")

        # Collect returns from best strategies
        strategy_returns = {}
        for symbol, ranked in best.items():
            for name, result in ranked:
                if hasattr(result, "returns") and len(result.returns) > 0:
                    strategy_returns[f"{symbol}_{name}"] = result.returns

        if not strategy_returns:
            return {}

        returns_df = pd.DataFrame(strategy_returns).dropna()

        if returns_df.empty or len(returns_df) < 10:
            # Equal weight fallback
            n = len(strategy_returns)
            return {name: 1.0 / n for name in strategy_returns}

        weights = self.portfolio_optimizer.optimize(
            returns_df,
            method=self.config.get("optimization_method", "max_sharpe"),
        )

        return weights

    def execute_paper_trades(self, portfolio: Dict[str, float]) -> None:
        """Step 7: Execute paper trades based on portfolio weights."""
        if not portfolio:
            return

        logger.info(f"Executing paper trades for {len(portfolio)} positions")
        self.paper_trader.execute_paper_trades(portfolio)
        self.paper_trader.snapshot()

        # Update metrics
        summary = self.paper_trader.get_portfolio_summary()
        self.metrics.set_gauge("portfolio_value", summary["total_value"])
        self.metrics.set_gauge("portfolio_pnl_pct", summary["pnl_pct"])
        self.metrics.set_gauge("portfolio_cash", summary["cash"])

    def _risk_check(self) -> None:
        """Step 8: Perform risk assessment."""
        summary = self.paper_trader.get_portfolio_summary()
        positions = self.paper_trader.engine.get_positions()

        # Simple returns history
        snapshots = self.paper_trader.portfolio_snapshots
        if len(snapshots) > 1:
            values = [s["total_value"] for s in snapshots]
            returns = pd.Series(values).pct_change().dropna()
        else:
            returns = pd.Series(dtype=float)

        report = self.risk_engine.assess_risk(
            portfolio_value=summary["total_value"],
            positions=positions,
            returns_history=returns,
        )

        self.metrics.set_gauge("risk_score", report.risk_score)
        self.metrics.set_gauge("risk_drawdown", report.current_drawdown)

        if report.violations:
            for v in report.violations:
                logger.warning(f"Risk violation: {v}")
                self.metrics.increment("risk_violations")

    def stop(self) -> None:
        """Stop the pipeline."""
        self.is_running = False
        logger.info("Pipeline stop requested")

    def get_status(self) -> Dict:
        """Get pipeline status."""
        return {
            "is_running": self.is_running,
            "iteration": self._iteration,
            "portfolio": self.paper_trader.get_portfolio_summary(),
            "metrics": self.metrics.get_metrics_json(),
        }
