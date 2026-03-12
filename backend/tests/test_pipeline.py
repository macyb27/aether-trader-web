"""
Tests for the Trading Pipeline and core modules.
"""

import numpy as np
import pandas as pd
import pytest


def create_sample_ohlcv(n: int = 200) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    close = np.maximum(close, 10)  # Prevent negative prices

    return pd.DataFrame(
        {
            "open": close + np.random.randn(n) * 0.5,
            "high": close + abs(np.random.randn(n)) * 2,
            "low": close - abs(np.random.randn(n)) * 2,
            "close": close,
            "volume": np.random.randint(1000, 100000, n).astype(float),
        },
        index=dates,
    )


class TestFeatureEngineering:
    """Test feature engineering pipeline."""

    def test_technical_features(self):
        from backend.feature_engineering.technical_features import TechnicalFeatures

        df = create_sample_ohlcv()
        tech = TechnicalFeatures()
        features = tech.compute(df)

        assert not features.empty
        assert "rsi_14" in features.columns
        assert "macd_line" in features.columns
        assert "bb_upper" in features.columns

    def test_statistical_features(self):
        from backend.feature_engineering.statistical_features import StatisticalFeatures

        df = create_sample_ohlcv()
        stat = StatisticalFeatures()
        features = stat.compute(df)

        assert not features.empty
        assert "realized_vol_20" in features.columns


class TestStrategyGenerator:
    """Test strategy generation."""

    def test_momentum_strategy(self):
        from backend.strategy_generator.strategy_templates import MomentumStrategy

        params = MomentumStrategy.random_params()
        strategy = MomentumStrategy(params=params)
        assert strategy.params is not None

    def test_mean_reversion_strategy(self):
        from backend.strategy_generator.strategy_templates import MeanReversionStrategy

        params = MeanReversionStrategy.random_params()
        strategy = MeanReversionStrategy(params=params)
        assert strategy.params is not None


class TestGeneticOptimizer:
    """Test genetic optimization."""

    def test_basic_optimization(self):
        from backend.genetic_optimizer.genetic_optimizer import GeneticOptimizer

        optimizer = GeneticOptimizer(
            population_size=20,
            generations=5,
            seed=42,
        )

        def fitness(params):
            return -(params["x"] ** 2 + params["y"] ** 2)

        result = optimizer.optimize(
            param_ranges={"x": (-10.0, 10.0), "y": (-10.0, 10.0)},
            fitness_function=fitness,
            maximize=True,
        )

        assert result.best_fitness > -100
        assert len(result.convergence_history) > 0


class TestRiskEngine:
    """Test risk management."""

    def test_risk_assessment(self):
        from backend.risk.risk_engine import RiskEngine

        engine = RiskEngine()
        engine.reset_daily(100_000)

        report = engine.assess_risk(
            portfolio_value=100_000,
            positions={"BTC": {"value": 10_000}},
            returns_history=pd.Series(np.random.randn(100) * 0.01),
        )

        assert report.risk_score >= 0
        assert report.risk_score <= 100

    def test_position_sizing(self):
        from backend.risk.risk_engine import RiskEngine

        engine = RiskEngine()
        size = engine.calculate_position_size(
            method="fixed_fractional",
            portfolio_value=100_000,
            entry_price=50_000,
            stop_loss_price=48_000,
        )

        assert size > 0


class TestPortfolioOptimizer:
    """Test portfolio optimization."""

    def test_equal_weight(self):
        from backend.portfolio_optimizer.portfolio_optimizer import PortfolioOptimizer

        optimizer = PortfolioOptimizer()
        returns = pd.DataFrame(
            np.random.randn(100, 3) * 0.01,
            columns=["A", "B", "C"],
        )

        weights = optimizer.optimize(returns, method="equal_weight")
        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.01
