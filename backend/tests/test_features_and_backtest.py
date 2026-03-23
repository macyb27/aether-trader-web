"""
Tests for Feature Engineering and Backtesting modules.
"""

import numpy as np
import pandas as pd
import pytest


def create_ohlcv_data(n: int = 200) -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    close = np.maximum(close, 10)

    return pd.DataFrame({
        "open": close + np.random.randn(n) * 0.5,
        "high": close + abs(np.random.randn(n)) * 2,
        "low": close - abs(np.random.randn(n)) * 2,
        "close": close,
        "volume": np.random.randint(1000, 100000, n).astype(float),
    })


class TestTechnicalFeatures:
    """Test technical indicator computation."""

    def test_initialization(self):
        from backend.feature_engineering.technical_features import TechnicalFeatureBuilder

        builder = TechnicalFeatureBuilder()
        assert builder is not None

    def test_build_features(self):
        from backend.feature_engineering.technical_features import TechnicalFeatureBuilder

        df = create_ohlcv_data()
        builder = TechnicalFeatureBuilder()
        features = builder.build(df)

        assert isinstance(features, pd.DataFrame)
        assert len(features) == len(df)

    def test_rsi_computed(self):
        from backend.feature_engineering.technical_features import TechnicalFeatureBuilder

        df = create_ohlcv_data()
        builder = TechnicalFeatureBuilder()
        features = builder.build(df)

        rsi_cols = [c for c in features.columns if "rsi" in c.lower()]
        assert len(rsi_cols) > 0

    def test_momentum_computed(self):
        from backend.feature_engineering.technical_features import TechnicalFeatureBuilder

        df = create_ohlcv_data()
        builder = TechnicalFeatureBuilder()
        features = builder.build(df)

        momentum_cols = [c for c in features.columns if "momentum" in c.lower()]
        assert len(momentum_cols) > 0

    def test_moving_averages_computed(self):
        from backend.feature_engineering.technical_features import TechnicalFeatureBuilder

        df = create_ohlcv_data()
        builder = TechnicalFeatureBuilder()
        features = builder.build(df)

        ma_cols = [c for c in features.columns if "sma" in c.lower() or "ema" in c.lower()]
        assert len(ma_cols) > 0


class TestStatisticalFeatures:
    """Test statistical feature computation."""

    def test_initialization(self):
        from backend.feature_engineering.statistical_features import StatisticalFeatureBuilder

        builder = StatisticalFeatureBuilder()
        assert builder is not None

    def test_build_features(self):
        from backend.feature_engineering.statistical_features import StatisticalFeatureBuilder

        df = create_ohlcv_data()
        builder = StatisticalFeatureBuilder()
        features = builder.build(df)

        assert isinstance(features, pd.DataFrame)
        assert len(features) == len(df)

    def test_volatility_computed(self):
        from backend.feature_engineering.statistical_features import StatisticalFeatureBuilder

        df = create_ohlcv_data()
        builder = StatisticalFeatureBuilder()
        features = builder.build(df)

        vol_cols = [c for c in features.columns if "volatility" in c.lower() or "vol" in c.lower()]
        assert len(vol_cols) > 0

    def test_rolling_stats_computed(self):
        from backend.feature_engineering.statistical_features import StatisticalFeatureBuilder

        df = create_ohlcv_data()
        builder = StatisticalFeatureBuilder()
        features = builder.build(df)

        rolling_cols = [c for c in features.columns if "rolling" in c.lower() or "skew" in c.lower() or "kurt" in c.lower()]
        assert len(rolling_cols) > 0


class TestBacktestEngine:
    """Test backtesting engine."""

    def test_initialization(self):
        from backend.backtesting.backtest_engine import BacktestEngine

        engine = BacktestEngine()
        assert engine is not None

    def test_backtest_returns_results(self):
        from backend.backtesting.backtest_engine import BacktestEngine

        engine = BacktestEngine()
        df = create_ohlcv_data()

        # Create simple signals
        signals = pd.Series(np.random.choice([-1, 0, 1], len(df)), index=df.index)

        result = engine.run(
            data=df,
            signals=signals,
            initial_capital=100_000,
        )

        assert result is not None
        assert "total_return" in result or hasattr(result, "total_return")


class TestPerformanceMetrics:
    """Test performance metrics calculation."""

    def test_initialization(self):
        from backend.backtesting.performance_metrics import PerformanceCalculator

        calc = PerformanceCalculator()
        assert calc is not None

    def test_sharpe_ratio(self):
        from backend.backtesting.performance_metrics import PerformanceCalculator

        calc = PerformanceCalculator()
        returns = pd.Series(np.random.randn(252) * 0.01)
        sharpe = calc.sharpe_ratio(returns)

        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)

    def test_max_drawdown(self):
        from backend.backtesting.performance_metrics import PerformanceCalculator

        calc = PerformanceCalculator()
        equity = pd.Series([100, 110, 105, 115, 95, 120])
        dd = calc.max_drawdown(equity)

        assert isinstance(dd, float)
        assert dd <= 0  # Drawdown is negative

    def test_win_rate(self):
        from backend.backtesting.performance_metrics import PerformanceCalculator

        calc = PerformanceCalculator()
        returns = pd.Series([0.01, -0.005, 0.02, 0.01, -0.01, 0.005])
        wr = calc.win_rate(returns)

        assert 0 <= wr <= 1
        assert wr == pytest.approx(4 / 6, abs=0.01)


class TestStrategyTemplates:
    """Test strategy templates."""

    def test_momentum_strategy(self):
        from backend.strategy_generator.strategy_templates import MomentumStrategy

        strategy = MomentumStrategy(name="test_momentum")
        assert strategy is not None

    def test_random_params(self):
        from backend.strategy_generator.strategy_templates import MomentumStrategy

        params = MomentumStrategy.random_params()
        assert isinstance(params, dict)
        assert "fast_period" in params
        assert "slow_period" in params

    def test_mean_reversion_strategy(self):
        from backend.strategy_generator.strategy_templates import MeanReversionStrategy

        strategy = MeanReversionStrategy(name="test_mr")
        assert strategy is not None

    def test_breakout_strategy(self):
        from backend.strategy_generator.strategy_templates import BreakoutStrategy

        strategy = BreakoutStrategy(name="test_breakout")
        assert strategy is not None


class TestGeneticOptimizer:
    """Test genetic optimization."""

    def test_initialization(self):
        from backend.genetic_optimizer.genetic_optimizer import GeneticOptimizer

        optimizer = GeneticOptimizer(population_size=20, generations=5)
        assert optimizer is not None
        assert optimizer.population_size == 20
        assert optimizer.generations == 5

    def test_mutation(self):
        from backend.genetic_optimizer.genetic_optimizer import GeneticOptimizer

        optimizer = GeneticOptimizer(mutation_rate=1.0)  # Force mutation
        individual = {"fast_period": 10, "slow_period": 50, "rsi_period": 14}
        param_ranges = {
            "fast_period": (5, 30),
            "slow_period": (20, 100),
            "rsi_period": (7, 21),
        }

        mutated = optimizer.mutate(individual, param_ranges)
        assert isinstance(mutated, dict)
        assert "fast_period" in mutated

    def test_crossover(self):
        from backend.genetic_optimizer.genetic_optimizer import GeneticOptimizer

        optimizer = GeneticOptimizer()
        parent1 = {"fast_period": 10, "slow_period": 50}
        parent2 = {"fast_period": 20, "slow_period": 80}

        child = optimizer.crossover(parent1, parent2)
        assert isinstance(child, dict)
        assert "fast_period" in child
        assert "slow_period" in child


class TestFitnessFunctions:
    """Test fitness evaluation functions."""

    def test_sharpe_fitness(self):
        from backend.genetic_optimizer.fitness_functions import sharpe_fitness

        returns = pd.Series(np.random.randn(252) * 0.01 + 0.0005)
        score = sharpe_fitness(returns)
        assert isinstance(score, float)

    def test_sortino_fitness(self):
        from backend.genetic_optimizer.fitness_functions import sortino_fitness

        returns = pd.Series(np.random.randn(252) * 0.01 + 0.0005)
        score = sortino_fitness(returns)
        assert isinstance(score, float)


class TestRiskEngine:
    """Test risk management."""

    def test_initialization(self):
        from backend.risk.risk_engine import RiskEngine

        engine = RiskEngine()
        assert engine is not None

    def test_position_sizing(self):
        from backend.risk.risk_engine import RiskEngine

        engine = RiskEngine()
        size = engine.calculate_position_size(
            portfolio_value=100_000,
            entry_price=50_000,
            stop_loss_price=48_000,
            method="fixed_fractional",
        )

        assert isinstance(size, float)
        assert size >= 0

    def test_volatility_targeting(self):
        from backend.risk.risk_engine import RiskEngine

        engine = RiskEngine()
        size = engine.calculate_position_size(
            portfolio_value=100_000,
            entry_price=50_000,
            stop_loss_price=48_000,
            method="volatility_target",
            volatility=0.03,
        )

        assert isinstance(size, float)
        assert size >= 0


class TestPortfolioOptimizer:
    """Test portfolio optimization."""

    def test_initialization(self):
        from backend.portfolio_optimizer.portfolio_optimizer import PortfolioOptimizer

        optimizer = PortfolioOptimizer()
        assert optimizer is not None

    def test_risk_parity(self):
        from backend.portfolio_optimizer.portfolio_optimizer import PortfolioOptimizer

        optimizer = PortfolioOptimizer()
        returns = pd.DataFrame({
            "BTC": np.random.randn(100) * 0.02,
            "ETH": np.random.randn(100) * 0.03,
            "SOL": np.random.randn(100) * 0.04,
        })

        weights = optimizer.optimize(returns, method="risk_parity")
        assert isinstance(weights, dict)
        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.01

    def test_mean_variance(self):
        from backend.portfolio_optimizer.portfolio_optimizer import PortfolioOptimizer

        optimizer = PortfolioOptimizer()
        returns = pd.DataFrame({
            "BTC": np.random.randn(100) * 0.02 + 0.001,
            "ETH": np.random.randn(100) * 0.03 + 0.0005,
        })

        weights = optimizer.optimize(returns, method="max_sharpe")
        assert isinstance(weights, dict)
        assert len(weights) == 2
