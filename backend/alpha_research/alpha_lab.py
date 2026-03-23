"""
Alpha Lab - Research environment for discovering and testing alpha signals.
Supports systematic alpha generation, testing, and combination.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AlphaSignal:
    """Represents a single alpha signal with metadata."""
    name: str
    signal: pd.Series
    ic: float = 0.0  # Information Coefficient
    ir: float = 0.0  # Information Ratio
    turnover: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    decay_halflife: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlphaLab:
    """
    Alpha research laboratory for systematic signal discovery.
    Provides tools for generating, testing, and combining alpha signals.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.alphas: Dict[str, AlphaSignal] = {}
        self._alpha_generators: Dict[str, Callable] = {}
        logger.info("AlphaLab initialized")

    def register_alpha(self, name: str, generator: Callable) -> None:
        """Register an alpha signal generator function."""
        self._alpha_generators[name] = generator
        logger.info(f"Alpha generator registered: {name}")

    def generate_alphas(
        self,
        features: pd.DataFrame,
        forward_returns: pd.Series,
        generators: Optional[List[str]] = None,
    ) -> Dict[str, AlphaSignal]:
        """
        Generate and evaluate alpha signals.

        Args:
            features: Feature matrix
            forward_returns: Forward-looking returns for evaluation
            generators: List of generator names to use (None = all)

        Returns:
            Dictionary of evaluated AlphaSignal objects
        """
        gen_names = generators or list(self._alpha_generators.keys())
        results = {}

        for name in gen_names:
            if name not in self._alpha_generators:
                logger.warning(f"Generator not found: {name}")
                continue

            try:
                signal = self._alpha_generators[name](features)
                alpha = self._evaluate_alpha(name, signal, forward_returns)
                results[name] = alpha
                self.alphas[name] = alpha
                logger.info(
                    f"Alpha '{name}': IC={alpha.ic:.4f}, IR={alpha.ir:.4f}, "
                    f"Sharpe={alpha.sharpe:.4f}"
                )
            except Exception as e:
                logger.error(f"Alpha generation failed for '{name}': {e}")

        return results

    def _evaluate_alpha(
        self, name: str, signal: pd.Series, forward_returns: pd.Series
    ) -> AlphaSignal:
        """Evaluate an alpha signal against forward returns."""
        # Align signal and returns
        common_idx = signal.dropna().index.intersection(forward_returns.dropna().index)
        sig = signal.loc[common_idx]
        ret = forward_returns.loc[common_idx]

        # Information Coefficient (rank correlation)
        ic = sig.corr(ret, method="spearman")

        # Rolling IC for Information Ratio
        rolling_ic = pd.Series(index=common_idx, dtype=float)
        window = min(60, len(common_idx) // 4)
        if window > 10:
            for i in range(window, len(common_idx)):
                idx = common_idx[i - window:i]
                rolling_ic.iloc[i] = sig.loc[idx].corr(ret.loc[idx], method="spearman")

        ir = rolling_ic.mean() / rolling_ic.std() if rolling_ic.std() > 0 else 0.0

        # Signal-weighted returns (proxy Sharpe)
        weighted_returns = sig * ret
        sharpe = (
            weighted_returns.mean() / weighted_returns.std() * np.sqrt(252)
            if weighted_returns.std() > 0 else 0.0
        )

        # Turnover
        turnover = sig.diff().abs().mean()

        # Max drawdown of cumulative signal returns
        cum_ret = (1 + weighted_returns).cumprod()
        rolling_max = cum_ret.cummax()
        drawdown = (cum_ret - rolling_max) / rolling_max
        max_dd = drawdown.min()

        # IC decay halflife
        decay_hl = self._compute_ic_decay(signal, forward_returns)

        return AlphaSignal(
            name=name,
            signal=signal,
            ic=ic,
            ir=ir,
            turnover=turnover,
            sharpe=sharpe,
            max_drawdown=max_dd,
            decay_halflife=decay_hl,
        )

    def _compute_ic_decay(
        self, signal: pd.Series, returns: pd.Series, max_lag: int = 20
    ) -> float:
        """Compute the halflife of IC decay across lags."""
        ics = []
        for lag in range(1, max_lag + 1):
            shifted_ret = returns.shift(-lag)
            common = signal.dropna().index.intersection(shifted_ret.dropna().index)
            if len(common) < 30:
                break
            ic = signal.loc[common].corr(shifted_ret.loc[common], method="spearman")
            ics.append(ic)

        if len(ics) < 3:
            return 0.0

        # Find where IC drops below half of initial
        initial_ic = abs(ics[0])
        for i, ic in enumerate(ics):
            if abs(ic) < initial_ic / 2:
                return float(i + 1)

        return float(len(ics))

    def combine_alphas(
        self,
        alpha_names: List[str],
        method: str = "equal_weight",
        forward_returns: Optional[pd.Series] = None,
    ) -> pd.Series:
        """
        Combine multiple alpha signals into a composite signal.

        Args:
            alpha_names: Names of alphas to combine
            method: Combination method ("equal_weight", "ic_weight", "ir_weight")
            forward_returns: Forward returns for IC/IR weighting

        Returns:
            Combined signal as pd.Series
        """
        signals = []
        weights = []

        for name in alpha_names:
            if name not in self.alphas:
                continue

            alpha = self.alphas[name]
            # Normalize signal to z-scores
            normalized = (alpha.signal - alpha.signal.mean()) / alpha.signal.std()
            signals.append(normalized)

            if method == "ic_weight":
                weights.append(abs(alpha.ic))
            elif method == "ir_weight":
                weights.append(abs(alpha.ir))
            else:
                weights.append(1.0)

        if not signals:
            return pd.Series(dtype=float)

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # Combine
        combined = sum(w * s for w, s in zip(weights, signals))
        return combined

    def get_alpha_report(self) -> pd.DataFrame:
        """Generate a summary report of all evaluated alphas."""
        records = []
        for name, alpha in self.alphas.items():
            records.append({
                "name": name,
                "ic": alpha.ic,
                "ir": alpha.ir,
                "sharpe": alpha.sharpe,
                "turnover": alpha.turnover,
                "max_drawdown": alpha.max_drawdown,
                "decay_halflife": alpha.decay_halflife,
                "created_at": alpha.created_at,
            })

        return pd.DataFrame(records).sort_values("ir", ascending=False)
