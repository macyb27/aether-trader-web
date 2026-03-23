"""
Tests for the AI/RL module.
"""

import numpy as np
import pandas as pd
import pytest


def create_sample_data(n: int = 200):
    """Create sample OHLCV data and features for testing."""
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    close = np.maximum(close, 10)

    df = pd.DataFrame({
        "open": close + np.random.randn(n) * 0.5,
        "high": close + abs(np.random.randn(n)) * 2,
        "low": close - abs(np.random.randn(n)) * 2,
        "close": close,
        "volume": np.random.randint(1000, 100000, n).astype(float),
    })

    features = pd.DataFrame({
        "rsi": np.random.uniform(20, 80, n),
        "macd": np.random.randn(n) * 5,
        "bb_width": np.random.uniform(0.01, 0.05, n),
        "momentum": np.random.randn(n) * 0.02,
        "volatility": np.random.uniform(0.01, 0.05, n),
    })

    return df, features


class TestTradingEnvironment:
    """Test the RL trading environment."""

    def test_env_creation(self):
        from backend.ai.rl_env import TradingEnvironment

        df, features = create_sample_data()
        env = TradingEnvironment(df=df, features=features, window_size=10)
        assert env is not None
        assert env.observation_space is not None
        assert env.action_space is not None

    def test_env_reset(self):
        from backend.ai.rl_env import TradingEnvironment

        df, features = create_sample_data()
        env = TradingEnvironment(df=df, features=features, window_size=10)
        obs, info = env.reset()

        assert obs is not None
        assert len(obs.shape) == 1
        assert info is not None
        assert "portfolio_value" in info

    def test_env_step(self):
        from backend.ai.rl_env import TradingEnvironment

        df, features = create_sample_data()
        env = TradingEnvironment(df=df, features=features, window_size=10)
        obs, info = env.reset()

        action = env.action_space.sample()
        obs2, reward, terminated, truncated, info2 = env.step(action)

        assert obs2 is not None
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)

    def test_env_discrete_actions(self):
        from backend.ai.rl_env import TradingEnvironment

        df, features = create_sample_data()
        env = TradingEnvironment(
            df=df, features=features, window_size=10, action_type="discrete"
        )
        obs, _ = env.reset()

        # Test all discrete actions
        for action in [0, 1, 2]:
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break

    def test_env_full_episode(self):
        from backend.ai.rl_env import TradingEnvironment

        df, features = create_sample_data(100)
        env = TradingEnvironment(df=df, features=features, window_size=5)
        obs, _ = env.reset()

        total_reward = 0
        steps = 0
        done = False

        while not done:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

        assert steps > 0
        assert "portfolio_value" in info


class TestRLTrainer:
    """Test the RL trainer."""

    def test_trainer_initialization(self):
        from backend.ai.rl_trainer import RLTrainer

        trainer = RLTrainer(algorithm="ppo")
        assert trainer.algorithm == "ppo"
        assert trainer.model is None

    def test_trainer_supported_algorithms(self):
        from backend.ai.rl_trainer import RLTrainer

        for algo in ["ppo", "a2c", "sac", "td3", "dqn"]:
            trainer = RLTrainer(algorithm=algo)
            assert trainer.algorithm == algo

    def test_trainer_default_hyperparams(self):
        from backend.ai.rl_trainer import RLTrainer

        trainer = RLTrainer(algorithm="ppo")
        assert "ppo" in trainer.DEFAULT_HYPERPARAMS
        assert "learning_rate" in trainer.DEFAULT_HYPERPARAMS["ppo"]

    def test_training_history(self):
        from backend.ai.rl_trainer import RLTrainer

        trainer = RLTrainer(algorithm="ppo")
        history = trainer.get_training_history()
        assert isinstance(history, list)
        assert len(history) == 0
