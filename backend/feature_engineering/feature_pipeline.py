"""
Feature Pipeline - Orchestrates feature computation from raw market data.
Supports chaining multiple feature generators with dependency resolution.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .technical_features import TechnicalFeatures
from .statistical_features import StatisticalFeatures

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    Feature engineering pipeline that transforms raw OHLCV data
    into a rich feature matrix for strategy generation and ML models.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.technical = TechnicalFeatures()
        self.statistical = StatisticalFeatures()
        self._feature_registry: Dict[str, callable] = {}
        self._computed_features: Dict[str, pd.DataFrame] = {}
        logger.info("FeaturePipeline initialized")

    def build_features(
        self,
        data: Dict[str, pd.DataFrame],
        feature_groups: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Build features for all symbols in the data dictionary.

        Args:
            data: Dictionary mapping symbol -> OHLCV DataFrame
            feature_groups: List of feature groups to compute
                           ("technical", "statistical", "all")

        Returns:
            Dictionary mapping symbol -> feature DataFrame
        """
        if feature_groups is None:
            feature_groups = ["technical", "statistical"]

        results = {}

        for symbol, df in data.items():
            if df.empty:
                logger.warning(f"Empty data for {symbol}, skipping")
                continue

            try:
                features = df.copy()

                if "technical" in feature_groups or "all" in feature_groups:
                    tech_features = self.technical.compute(df)
                    features = pd.concat([features, tech_features], axis=1)

                if "statistical" in feature_groups or "all" in feature_groups:
                    stat_features = self.statistical.compute(df)
                    features = pd.concat([features, stat_features], axis=1)

                # Apply custom registered features
                for name, func in self._feature_registry.items():
                    try:
                        custom_feat = func(df)
                        if isinstance(custom_feat, pd.Series):
                            features[name] = custom_feat
                        elif isinstance(custom_feat, pd.DataFrame):
                            features = pd.concat([features, custom_feat], axis=1)
                    except Exception as e:
                        logger.error(f"Custom feature '{name}' failed: {e}")

                # Clean up
                features = features.replace([np.inf, -np.inf], np.nan)
                features = features.dropna()

                results[symbol] = features
                logger.info(
                    f"Built {features.shape[1]} features for {symbol} "
                    f"({len(features)} rows)"
                )

            except Exception as e:
                logger.error(f"Feature building failed for {symbol}: {e}")
                results[symbol] = pd.DataFrame()

        self._computed_features = results
        return results

    def register_feature(self, name: str, func: callable) -> None:
        """Register a custom feature function."""
        self._feature_registry[name] = func
        logger.info(f"Custom feature registered: {name}")

    def get_feature_names(self, symbol: str) -> List[str]:
        """Get list of computed feature names for a symbol."""
        if symbol in self._computed_features:
            return list(self._computed_features[symbol].columns)
        return []

    def get_feature_importance(
        self, features: pd.DataFrame, target: pd.Series
    ) -> pd.Series:
        """
        Compute feature importance using mutual information.
        """
        from sklearn.feature_selection import mutual_info_regression

        # Align features and target
        common_idx = features.index.intersection(target.index)
        X = features.loc[common_idx].fillna(0)
        y = target.loc[common_idx]

        mi_scores = mutual_info_regression(X, y, random_state=42)
        importance = pd.Series(mi_scores, index=X.columns).sort_values(ascending=False)

        return importance
