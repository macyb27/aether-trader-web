"""
Signal Generator - Automatic generation of trading signals from features.
Uses expression trees and genetic programming for signal discovery.
"""

import logging
import random
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates trading signals by combining features using mathematical operations.
    Supports both predefined signal templates and automatic discovery.
    """

    OPERATORS = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b.replace(0, np.nan),
        "max": lambda a, b: np.maximum(a, b),
        "min": lambda a, b: np.minimum(a, b),
    }

    UNARY_OPS = {
        "neg": lambda a: -a,
        "abs": lambda a: a.abs(),
        "sign": lambda a: np.sign(a),
        "rank": lambda a: a.rank(pct=True),
        "zscore": lambda a: (a - a.mean()) / a.std() if a.std() > 0 else a * 0,
        "delay": lambda a: a.shift(1),
        "delta": lambda a: a.diff(1),
        "ts_mean_5": lambda a: a.rolling(5).mean(),
        "ts_mean_20": lambda a: a.rolling(20).mean(),
        "ts_std_20": lambda a: a.rolling(20).std(),
        "ts_rank_20": lambda a: a.rolling(20).apply(
            lambda x: pd.Series(x).rank().iloc[-1] / len(x), raw=True
        ),
    }

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.generated_signals: Dict[str, pd.Series] = {}
        logger.info("SignalGenerator initialized")

    def generate_predefined(self, features: pd.DataFrame) -> Dict[str, pd.Series]:
        """Generate signals from predefined templates."""
        signals = {}

        # Momentum signals
        if "rsi_14" in features.columns:
            signals["rsi_mean_reversion"] = -(features["rsi_14"] - 50) / 50

        if "macd_histogram" in features.columns:
            signals["macd_momentum"] = self.UNARY_OPS["rank"](features["macd_histogram"])

        # Volatility signals
        if "bb_position" in features.columns:
            signals["bb_mean_reversion"] = -(features["bb_position"] - 0.5)

        # Volume signals
        if "vol_ratio_5_20" in features.columns:
            signals["volume_breakout"] = features["vol_ratio_5_20"] - 1

        # Trend signals
        if "sma_cross_20_50" in features.columns:
            signals["trend_following"] = self.UNARY_OPS["sign"](features["sma_cross_20_50"])

        # Statistical signals
        if "zscore_20" in features.columns:
            signals["stat_mean_reversion"] = -features["zscore_20"]

        if "hurst_50" in features.columns:
            # Trade mean reversion when Hurst < 0.5, trend when > 0.5
            hurst = features["hurst_50"]
            signals["regime_adaptive"] = np.where(
                hurst < 0.5,
                -features.get("zscore_20", pd.Series(0, index=features.index)),
                features.get("momentum_20", pd.Series(0, index=features.index)),
            )
            signals["regime_adaptive"] = pd.Series(
                signals["regime_adaptive"], index=features.index
            )

        self.generated_signals.update(signals)
        logger.info(f"Generated {len(signals)} predefined signals")
        return signals

    def generate_random(
        self,
        features: pd.DataFrame,
        n_signals: int = 50,
        max_depth: int = 3,
        seed: Optional[int] = None,
    ) -> Dict[str, pd.Series]:
        """
        Generate random signals by combining features with operators.

        Args:
            features: Feature matrix
            n_signals: Number of random signals to generate
            max_depth: Maximum expression tree depth
            seed: Random seed for reproducibility

        Returns:
            Dictionary of generated signals
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        signals = {}
        feature_cols = [c for c in features.columns if features[c].std() > 0]

        for i in range(n_signals):
            try:
                signal = self._random_expression(features, feature_cols, max_depth)
                if signal is not None and signal.std() > 0:
                    name = f"random_alpha_{i:04d}"
                    signals[name] = signal
            except Exception:
                continue

        self.generated_signals.update(signals)
        logger.info(f"Generated {len(signals)} random signals")
        return signals

    def _random_expression(
        self,
        features: pd.DataFrame,
        feature_cols: List[str],
        depth: int,
    ) -> Optional[pd.Series]:
        """Build a random expression tree and evaluate it."""
        if depth <= 0 or random.random() < 0.3:
            # Terminal: pick a random feature
            col = random.choice(feature_cols)
            return features[col].copy()

        # Apply unary or binary operator
        if random.random() < 0.4:
            # Unary operation
            op_name = random.choice(list(self.UNARY_OPS.keys()))
            operand = self._random_expression(features, feature_cols, depth - 1)
            if operand is None:
                return None
            return self.UNARY_OPS[op_name](operand)
        else:
            # Binary operation
            op_name = random.choice(list(self.OPERATORS.keys()))
            left = self._random_expression(features, feature_cols, depth - 1)
            right = self._random_expression(features, feature_cols, depth - 1)
            if left is None or right is None:
                return None
            result = self.OPERATORS[op_name](left, right)
            return result.replace([np.inf, -np.inf], np.nan)
