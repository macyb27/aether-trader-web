"""
Factor Model - Multi-factor model for alpha combination and risk decomposition.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FactorModel:
    """
    Multi-factor model for combining alpha signals and decomposing risk.
    Supports cross-sectional and time-series factor analysis.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.factor_returns: Optional[pd.DataFrame] = None
        self.factor_loadings: Optional[pd.DataFrame] = None
        self.residuals: Optional[pd.Series] = None
        logger.info("FactorModel initialized")

    def fit(
        self,
        factors: pd.DataFrame,
        returns: pd.Series,
        method: str = "ols",
    ) -> Dict[str, float]:
        """
        Fit the factor model.

        Args:
            factors: Factor exposure matrix (T x K)
            returns: Asset returns (T,)
            method: Fitting method ("ols", "ridge", "lasso")

        Returns:
            Dictionary of factor coefficients
        """
        common_idx = factors.index.intersection(returns.index)
        X = factors.loc[common_idx].fillna(0)
        y = returns.loc[common_idx].fillna(0)

        if method == "ols":
            coeffs = self._fit_ols(X, y)
        elif method == "ridge":
            coeffs = self._fit_ridge(X, y)
        elif method == "lasso":
            coeffs = self._fit_lasso(X, y)
        else:
            raise ValueError(f"Unknown method: {method}")

        self.factor_loadings = pd.Series(coeffs, index=X.columns)
        self.residuals = y - X @ coeffs

        # Factor returns attribution
        self.factor_returns = X.multiply(coeffs, axis=1)

        result = dict(zip(X.columns, coeffs))
        logger.info(f"Factor model fitted with {len(result)} factors")
        return result

    def _fit_ols(self, X: pd.DataFrame, y: pd.Series) -> np.ndarray:
        """Ordinary Least Squares."""
        X_np = X.values
        y_np = y.values
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(len(X_np)), X_np])
        coeffs = np.linalg.lstsq(X_with_intercept, y_np, rcond=None)[0]
        return coeffs[1:]  # Exclude intercept

    def _fit_ridge(self, X: pd.DataFrame, y: pd.Series, alpha: float = 1.0) -> np.ndarray:
        """Ridge regression."""
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(X.values, y.values)
        return model.coef_

    def _fit_lasso(self, X: pd.DataFrame, y: pd.Series, alpha: float = 0.01) -> np.ndarray:
        """Lasso regression."""
        from sklearn.linear_model import Lasso
        model = Lasso(alpha=alpha, fit_intercept=True, max_iter=10000)
        model.fit(X.values, y.values)
        return model.coef_

    def get_factor_attribution(self) -> pd.DataFrame:
        """Get factor return attribution."""
        if self.factor_returns is None:
            return pd.DataFrame()
        return self.factor_returns

    def get_r_squared(self) -> float:
        """Get model R-squared."""
        if self.residuals is None or self.factor_returns is None:
            return 0.0

        total_var = (self.residuals + self.factor_returns.sum(axis=1)).var()
        residual_var = self.residuals.var()

        if total_var == 0:
            return 0.0
        return 1 - residual_var / total_var

    def predict(self, factors: pd.DataFrame) -> pd.Series:
        """Predict returns using fitted factor model."""
        if self.factor_loadings is None:
            raise ValueError("Model not fitted yet")

        common_factors = [f for f in self.factor_loadings.index if f in factors.columns]
        return factors[common_factors] @ self.factor_loadings[common_factors]
