"""
Statistical Features - Advanced statistical and distributional features.
Includes rolling statistics, regime detection, and microstructure features.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


class StatisticalFeatures:
    """
    Computes statistical features from OHLCV data.
    Focuses on distributional properties, regime detection, and market microstructure.
    """

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all statistical features."""
        features = pd.DataFrame(index=df.index)

        features = pd.concat([features, self._rolling_statistics(df)], axis=1)
        features = pd.concat([features, self._volatility_features(df)], axis=1)
        features = pd.concat([features, self._regime_features(df)], axis=1)
        features = pd.concat([features, self._autocorrelation_features(df)], axis=1)
        features = pd.concat([features, self._entropy_features(df)], axis=1)

        return features

    def _rolling_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rolling distributional statistics."""
        result = pd.DataFrame(index=df.index)
        returns = df["close"].pct_change()

        for window in [10, 20, 50]:
            roll = returns.rolling(window)

            result[f"mean_{window}"] = roll.mean()
            result[f"std_{window}"] = roll.std()
            result[f"skew_{window}"] = roll.skew()
            result[f"kurt_{window}"] = roll.kurt()
            result[f"median_{window}"] = roll.median()

            # Z-score of current return
            result[f"zscore_{window}"] = (
                (returns - result[f"mean_{window}"]) / result[f"std_{window}"].replace(0, np.nan)
            )

            # Percentile rank
            result[f"pctrank_{window}"] = returns.rolling(window).apply(
                lambda x: scipy_stats.percentileofscore(x, x.iloc[-1]) / 100,
                raw=False,
            )

        return result

    def _volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced volatility features."""
        result = pd.DataFrame(index=df.index)
        returns = df["close"].pct_change()
        log_returns = np.log(df["close"] / df["close"].shift(1))

        # Realized volatility (annualized)
        for window in [5, 10, 20, 60]:
            result[f"realized_vol_{window}"] = log_returns.rolling(window).std() * np.sqrt(252)

        # Parkinson volatility (uses high-low range)
        hl_ratio = np.log(df["high"] / df["low"])
        for window in [10, 20]:
            result[f"parkinson_vol_{window}"] = (
                np.sqrt(hl_ratio.pow(2).rolling(window).mean() / (4 * np.log(2))) * np.sqrt(252)
            )

        # Garman-Klass volatility
        log_hl = np.log(df["high"] / df["low"]).pow(2)
        log_co = np.log(df["close"] / df["open"]).pow(2)
        gk = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
        result["garman_klass_vol_20"] = np.sqrt(gk.rolling(20).mean() * 252)

        # Volatility of volatility
        result["vol_of_vol_20"] = result["realized_vol_20"].rolling(20).std()

        # Volatility ratio (short-term vs long-term)
        result["vol_ratio_5_20"] = result["realized_vol_5"] / result["realized_vol_20"].replace(0, np.nan)
        result["vol_ratio_10_60"] = result["realized_vol_10"] / result["realized_vol_60"].replace(0, np.nan)

        return result

    def _regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Market regime detection features."""
        result = pd.DataFrame(index=df.index)
        close = df["close"]
        returns = close.pct_change()

        # Trend strength (ADX-like)
        up_moves = close.diff()
        down_moves = -close.diff()
        pos_dm = up_moves.where((up_moves > 0) & (up_moves > down_moves), 0)
        neg_dm = down_moves.where((down_moves > 0) & (down_moves > up_moves), 0)

        for window in [14, 28]:
            pos_di = pos_dm.rolling(window).mean()
            neg_di = neg_dm.rolling(window).mean()
            di_sum = pos_di + neg_di
            result[f"trend_strength_{window}"] = (
                (pos_di - neg_di).abs() / di_sum.replace(0, np.nan)
            )

        # Hurst exponent approximation (R/S method)
        result["hurst_50"] = returns.rolling(50).apply(
            self._hurst_rs, raw=True
        )

        # Mean reversion indicator
        sma_20 = close.rolling(20).mean()
        result["mean_rev_score"] = -(close - sma_20) / close.rolling(20).std().replace(0, np.nan)

        # Consecutive up/down days
        direction = np.sign(returns)
        result["consecutive_direction"] = direction.groupby(
            (direction != direction.shift()).cumsum()
        ).cumcount() + 1
        result["consecutive_direction"] *= direction

        return result

    def _autocorrelation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Autocorrelation and serial dependence features."""
        result = pd.DataFrame(index=df.index)
        returns = df["close"].pct_change()

        for lag in [1, 2, 5, 10]:
            result[f"autocorr_lag_{lag}"] = returns.rolling(50).apply(
                lambda x: x.autocorr(lag=lag) if len(x) > lag else np.nan,
                raw=False,
            )

        # Partial autocorrelation proxy
        result["return_lag_1"] = returns.shift(1)
        result["return_lag_2"] = returns.shift(2)
        result["return_lag_5"] = returns.shift(5)

        return result

    def _entropy_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Information-theoretic features."""
        result = pd.DataFrame(index=df.index)
        returns = df["close"].pct_change()

        # Approximate entropy using binned returns
        for window in [20, 50]:
            result[f"entropy_{window}"] = returns.rolling(window).apply(
                self._shannon_entropy, raw=True
            )

        return result

    @staticmethod
    def _hurst_rs(series: np.ndarray) -> float:
        """Estimate Hurst exponent using R/S method."""
        try:
            n = len(series)
            if n < 20:
                return np.nan

            series = series[~np.isnan(series)]
            if len(series) < 20:
                return np.nan

            mean = np.mean(series)
            deviations = np.cumsum(series - mean)
            R = np.max(deviations) - np.min(deviations)
            S = np.std(series, ddof=1)

            if S == 0:
                return np.nan

            return np.log(R / S) / np.log(n)
        except Exception:
            return np.nan

    @staticmethod
    def _shannon_entropy(series: np.ndarray) -> float:
        """Compute Shannon entropy of binned returns."""
        try:
            series = series[~np.isnan(series)]
            if len(series) < 5:
                return np.nan

            n_bins = max(5, int(np.sqrt(len(series))))
            counts, _ = np.histogram(series, bins=n_bins)
            probs = counts / counts.sum()
            probs = probs[probs > 0]

            return -np.sum(probs * np.log2(probs))
        except Exception:
            return np.nan
