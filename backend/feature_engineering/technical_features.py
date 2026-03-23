"""
Technical Features - Comprehensive technical indicator computation.
Includes trend, momentum, volatility, and volume indicators.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalFeatures:
    """
    Computes technical analysis features from OHLCV data.
    All indicators are computed using vectorized operations for performance.
    """

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all technical features."""
        features = pd.DataFrame(index=df.index)

        # Trend indicators
        features = pd.concat([features, self._moving_averages(df)], axis=1)
        features = pd.concat([features, self._macd(df)], axis=1)

        # Momentum indicators
        features = pd.concat([features, self._rsi(df)], axis=1)
        features = pd.concat([features, self._stochastic(df)], axis=1)
        features = pd.concat([features, self._momentum(df)], axis=1)

        # Volatility indicators
        features = pd.concat([features, self._bollinger_bands(df)], axis=1)
        features = pd.concat([features, self._atr(df)], axis=1)

        # Volume indicators
        features = pd.concat([features, self._volume_features(df)], axis=1)

        # Price action
        features = pd.concat([features, self._price_action(df)], axis=1)

        return features

    def _moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Simple and Exponential Moving Averages."""
        close = df["close"]
        result = pd.DataFrame(index=df.index)

        for period in [5, 10, 20, 50, 100, 200]:
            result[f"sma_{period}"] = close.rolling(period).mean()
            result[f"ema_{period}"] = close.ewm(span=period, adjust=False).mean()

        # MA crossover signals
        result["sma_cross_20_50"] = (result["sma_20"] - result["sma_50"]) / result["sma_50"]
        result["sma_cross_50_200"] = (result["sma_50"] - result["sma_200"]) / result["sma_200"]
        result["ema_cross_10_20"] = (result["ema_10"] - result["ema_20"]) / result["ema_20"]

        # Price relative to MAs
        for period in [20, 50, 200]:
            result[f"price_vs_sma_{period}"] = (close - result[f"sma_{period}"]) / result[f"sma_{period}"]

        return result

    def _macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD indicator."""
        close = df["close"]
        result = pd.DataFrame(index=df.index)

        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()

        result["macd_line"] = ema_fast - ema_slow
        result["macd_signal"] = result["macd_line"].ewm(span=signal, adjust=False).mean()
        result["macd_histogram"] = result["macd_line"] - result["macd_signal"]
        result["macd_cross"] = np.sign(result["macd_histogram"])

        return result

    def _rsi(self, df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """Relative Strength Index."""
        if periods is None:
            periods = [7, 14, 21]

        close = df["close"]
        result = pd.DataFrame(index=df.index)

        for period in periods:
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)

            avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

            rs = avg_gain / avg_loss.replace(0, np.nan)
            result[f"rsi_{period}"] = 100 - (100 / (1 + rs))

        return result

    def _stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Stochastic Oscillator."""
        result = pd.DataFrame(index=df.index)

        low_min = df["low"].rolling(k_period).min()
        high_max = df["high"].rolling(k_period).max()

        result["stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        result["stoch_d"] = result["stoch_k"].rolling(d_period).mean()

        return result

    def _momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Momentum and Rate of Change indicators."""
        close = df["close"]
        result = pd.DataFrame(index=df.index)

        for period in [5, 10, 20]:
            result[f"momentum_{period}"] = close / close.shift(period) - 1
            result[f"roc_{period}"] = close.pct_change(period)

        # Williams %R
        high_14 = df["high"].rolling(14).max()
        low_14 = df["low"].rolling(14).min()
        result["williams_r"] = -100 * (high_14 - close) / (high_14 - low_14).replace(0, np.nan)

        return result

    def _bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """Bollinger Bands."""
        close = df["close"]
        result = pd.DataFrame(index=df.index)

        sma = close.rolling(period).mean()
        std = close.rolling(period).std()

        result["bb_upper"] = sma + std_dev * std
        result["bb_middle"] = sma
        result["bb_lower"] = sma - std_dev * std
        result["bb_width"] = (result["bb_upper"] - result["bb_lower"]) / result["bb_middle"]
        result["bb_position"] = (close - result["bb_lower"]) / (result["bb_upper"] - result["bb_lower"]).replace(0, np.nan)

        return result

    def _atr(self, df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """Average True Range."""
        if periods is None:
            periods = [7, 14, 21]

        result = pd.DataFrame(index=df.index)

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)

        for period in periods:
            result[f"atr_{period}"] = tr.rolling(period).mean()
            result[f"atr_pct_{period}"] = result[f"atr_{period}"] / close

        return result

    def _volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volume-based features."""
        result = pd.DataFrame(index=df.index)
        volume = df["volume"]
        close = df["close"]

        # Volume moving averages
        for period in [5, 10, 20]:
            result[f"vol_sma_{period}"] = volume.rolling(period).mean()

        # Volume ratio
        result["vol_ratio_5_20"] = result["vol_sma_5"] / result["vol_sma_20"].replace(0, np.nan)

        # On-Balance Volume
        obv = (np.sign(close.diff()) * volume).cumsum()
        result["obv"] = obv
        result["obv_sma_20"] = obv.rolling(20).mean()

        # Volume-Price Trend
        result["vpt"] = (volume * close.pct_change()).cumsum()

        # Money Flow Index
        typical_price = (df["high"] + df["low"] + close) / 3
        money_flow = typical_price * volume
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0)

        pos_sum = positive_flow.rolling(14).sum()
        neg_sum = negative_flow.rolling(14).sum()
        mfi_ratio = pos_sum / neg_sum.replace(0, np.nan)
        result["mfi"] = 100 - (100 / (1 + mfi_ratio))

        return result

    def _price_action(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price action features."""
        result = pd.DataFrame(index=df.index)

        # Returns
        result["return_1d"] = df["close"].pct_change(1)
        result["return_5d"] = df["close"].pct_change(5)
        result["return_20d"] = df["close"].pct_change(20)

        # Log returns
        result["log_return"] = np.log(df["close"] / df["close"].shift(1))

        # Candle body and shadows
        body = df["close"] - df["open"]
        full_range = df["high"] - df["low"]
        result["candle_body_pct"] = body / full_range.replace(0, np.nan)
        result["upper_shadow_pct"] = (df["high"] - df[["close", "open"]].max(axis=1)) / full_range.replace(0, np.nan)
        result["lower_shadow_pct"] = (df[["close", "open"]].min(axis=1) - df["low"]) / full_range.replace(0, np.nan)

        # Gap
        result["gap"] = df["open"] / df["close"].shift(1) - 1

        # High-Low range
        result["hl_range_pct"] = full_range / df["close"]

        return result
