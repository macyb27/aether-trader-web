"""
Strategy Templates - Base class and predefined strategy templates.
Each template defines parameter ranges and signal generation logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class StrategyTemplate(ABC):
    """Abstract base class for trading strategies."""

    PARAM_RANGES: Dict[str, tuple] = {}

    def __init__(self, params: Optional[Dict] = None, name: str = ""):
        self.params = params or {}
        self.name = name

    @abstractmethod
    def generate_signals(self, features: pd.DataFrame) -> pd.Series:
        """Generate trading signals from features. Returns series of -1, 0, 1."""
        pass

    @classmethod
    def random_params(cls) -> Dict:
        """Generate random parameters within defined ranges."""
        params = {}
        for key, (low, high) in cls.PARAM_RANGES.items():
            if isinstance(low, int) and isinstance(high, int):
                params[key] = np.random.randint(low, high + 1)
            else:
                params[key] = np.random.uniform(low, high)
        return params

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', params={self.params})"


class MomentumStrategy(StrategyTemplate):
    """
    Momentum/trend-following strategy.
    Buys when short MA > long MA and RSI confirms.
    """

    PARAM_RANGES = {
        "fast_period": (5, 30),
        "slow_period": (20, 100),
        "rsi_period": (7, 21),
        "rsi_upper": (60, 80),
        "rsi_lower": (20, 40),
        "atr_multiplier": (1.0, 3.0),
    }

    def generate_signals(self, features: pd.DataFrame) -> pd.Series:
        fast = self.params.get("fast_period", 10)
        slow = self.params.get("slow_period", 50)
        rsi_upper = self.params.get("rsi_upper", 70)
        rsi_lower = self.params.get("rsi_lower", 30)

        close = features["close"]
        fast_ma = close.rolling(fast).mean()
        slow_ma = close.rolling(slow).mean()

        # Trend direction
        trend = np.sign(fast_ma - slow_ma)

        # RSI filter
        rsi_col = f"rsi_{self.params.get('rsi_period', 14)}"
        if rsi_col in features.columns:
            rsi = features[rsi_col]
            # Don't buy overbought, don't sell oversold
            trend = trend.where(~((trend > 0) & (rsi > rsi_upper)), 0)
            trend = trend.where(~((trend < 0) & (rsi < rsi_lower)), 0)

        return trend.fillna(0).astype(int)


class MeanReversionStrategy(StrategyTemplate):
    """
    Mean reversion strategy.
    Trades against extreme deviations from the mean.
    """

    PARAM_RANGES = {
        "lookback": (10, 50),
        "entry_zscore": (1.5, 3.0),
        "exit_zscore": (0.0, 0.5),
        "max_holding": (5, 30),
    }

    def generate_signals(self, features: pd.DataFrame) -> pd.Series:
        lookback = self.params.get("lookback", 20)
        entry_z = self.params.get("entry_zscore", 2.0)
        exit_z = self.params.get("exit_zscore", 0.25)

        close = features["close"]
        mean = close.rolling(lookback).mean()
        std = close.rolling(lookback).std()
        zscore = (close - mean) / std.replace(0, np.nan)

        signals = pd.Series(0, index=features.index)

        # Short when z-score is too high
        signals = signals.where(zscore <= entry_z, -1)
        # Long when z-score is too low
        signals = signals.where(zscore >= -entry_z, 1)
        # Exit when z-score reverts
        signals = signals.where(zscore.abs() >= exit_z, 0)

        return signals.fillna(0).astype(int)


class MLStrategy(StrategyTemplate):
    """
    Machine Learning strategy.
    Uses a trained model to predict return direction.
    """

    PARAM_RANGES = {
        "threshold": (0.0, 0.02),
        "lookback": (20, 100),
        "retrain_interval": (20, 60),
    }

    def __init__(self, params: Optional[Dict] = None, name: str = "", model=None):
        super().__init__(params, name)
        self.model = model
        self._is_fitted = False

    def generate_signals(self, features: pd.DataFrame) -> pd.Series:
        threshold = self.params.get("threshold", 0.005)

        if self.model is None:
            # Fallback: use simple feature combination
            return self._fallback_signals(features, threshold)

        try:
            # Use ML model predictions
            feature_cols = [c for c in features.columns if c not in ["open", "high", "low", "close", "volume"]]
            X = features[feature_cols].fillna(0)

            if not self._is_fitted:
                # Train on available data
                y = features["close"].pct_change().shift(-1).fillna(0)
                self.model.fit(X.iloc[:-1], np.sign(y.iloc[:-1]))
                self._is_fitted = True

            predictions = self.model.predict(X)
            signals = pd.Series(predictions, index=features.index)
            return signals.fillna(0).astype(int)

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._fallback_signals(features, threshold)

    def _fallback_signals(self, features: pd.DataFrame, threshold: float) -> pd.Series:
        """Fallback signal generation without ML model."""
        returns = features["close"].pct_change()
        signals = pd.Series(0, index=features.index)
        signals = signals.where(returns <= threshold, 1)
        signals = signals.where(returns >= -threshold, -1)
        return signals.fillna(0).astype(int)


class BreakoutStrategy(StrategyTemplate):
    """
    Breakout strategy.
    Trades breakouts from price channels with volume confirmation.
    """

    PARAM_RANGES = {
        "channel_period": (10, 50),
        "volume_multiplier": (1.2, 3.0),
        "atr_stop_multiplier": (1.5, 4.0),
    }

    def generate_signals(self, features: pd.DataFrame) -> pd.Series:
        period = self.params.get("channel_period", 20)
        vol_mult = self.params.get("volume_multiplier", 1.5)

        high_channel = features["high"].rolling(period).max()
        low_channel = features["low"].rolling(period).min()
        vol_avg = features["volume"].rolling(period).mean()

        close = features["close"]
        volume = features["volume"]

        # Breakout signals with volume confirmation
        long_signal = (close > high_channel.shift(1)) & (volume > vol_avg * vol_mult)
        short_signal = (close < low_channel.shift(1)) & (volume > vol_avg * vol_mult)

        signals = pd.Series(0, index=features.index)
        signals[long_signal] = 1
        signals[short_signal] = -1

        return signals
