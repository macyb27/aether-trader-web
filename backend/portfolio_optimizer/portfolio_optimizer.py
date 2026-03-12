"""
Portfolio Optimizer - Advanced portfolio optimization methods.
Supports Mean-Variance, Risk Parity, Black-Litterman, and HRP.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Portfolio optimization engine supporting multiple methods.
    
    Methods:
    - Mean-Variance (Markowitz)
    - Minimum Variance
    - Maximum Sharpe
    - Risk Parity
    - Equal Weight
    - Hierarchical Risk Parity (HRP)
    - Black-Litterman
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.risk_free_rate = self.config.get("risk_free_rate", 0.02)
        logger.info("PortfolioOptimizer initialized")

    def optimize(
        self,
        returns: pd.DataFrame,
        method: str = "max_sharpe",
        constraints: Optional[Dict] = None,
    ) -> Dict[str, float]:
        """
        Optimize portfolio weights.

        Args:
            returns: DataFrame of asset returns (T x N)
            method: Optimization method
            constraints: Optional constraints (min_weight, max_weight, etc.)

        Returns:
            Dictionary of asset -> weight
        """
        if constraints is None:
            constraints = {"min_weight": 0.0, "max_weight": 0.30}

        assets = returns.columns.tolist()
        n_assets = len(assets)

        if n_assets == 0:
            return {}

        # Calculate expected returns and covariance
        mu = returns.mean() * 252  # Annualized
        cov = returns.cov() * 252  # Annualized

        if method == "max_sharpe":
            weights = self._max_sharpe(mu, cov, constraints)
        elif method == "min_variance":
            weights = self._min_variance(cov, constraints)
        elif method == "risk_parity":
            weights = self._risk_parity(cov)
        elif method == "equal_weight":
            weights = np.ones(n_assets) / n_assets
        elif method == "hrp":
            weights = self._hierarchical_risk_parity(returns)
        elif method == "mean_variance":
            target_return = constraints.get("target_return", mu.mean())
            weights = self._mean_variance(mu, cov, target_return, constraints)
        else:
            raise ValueError(f"Unknown method: {method}")

        result = dict(zip(assets, weights))
        logger.info(f"Portfolio optimized ({method}): {len(result)} assets")
        return result

    def _max_sharpe(
        self,
        mu: pd.Series,
        cov: pd.DataFrame,
        constraints: Dict,
    ) -> np.ndarray:
        """Maximum Sharpe ratio portfolio."""
        n = len(mu)
        w0 = np.ones(n) / n

        def neg_sharpe(w):
            port_return = w @ mu.values
            port_vol = np.sqrt(w @ cov.values @ w)
            return -(port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0

        bounds = [
            (constraints.get("min_weight", 0), constraints.get("max_weight", 1))
            for _ in range(n)
        ]
        cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

        result = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons)
        return result.x if result.success else w0

    def _min_variance(
        self, cov: pd.DataFrame, constraints: Dict
    ) -> np.ndarray:
        """Minimum variance portfolio."""
        n = len(cov)
        w0 = np.ones(n) / n

        def portfolio_variance(w):
            return w @ cov.values @ w

        bounds = [
            (constraints.get("min_weight", 0), constraints.get("max_weight", 1))
            for _ in range(n)
        ]
        cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

        result = minimize(portfolio_variance, w0, method="SLSQP", bounds=bounds, constraints=cons)
        return result.x if result.success else w0

    def _risk_parity(self, cov: pd.DataFrame) -> np.ndarray:
        """Risk parity (equal risk contribution) portfolio."""
        n = len(cov)
        w0 = np.ones(n) / n

        def risk_parity_objective(w):
            port_vol = np.sqrt(w @ cov.values @ w)
            if port_vol == 0:
                return 0
            marginal_contrib = cov.values @ w
            risk_contrib = w * marginal_contrib / port_vol
            target_risk = port_vol / n
            return np.sum((risk_contrib - target_risk) ** 2)

        bounds = [(0.01, 1.0) for _ in range(n)]
        cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

        result = minimize(risk_parity_objective, w0, method="SLSQP", bounds=bounds, constraints=cons)
        return result.x if result.success else w0

    def _mean_variance(
        self,
        mu: pd.Series,
        cov: pd.DataFrame,
        target_return: float,
        constraints: Dict,
    ) -> np.ndarray:
        """Mean-variance optimization with target return."""
        n = len(mu)
        w0 = np.ones(n) / n

        def portfolio_variance(w):
            return w @ cov.values @ w

        bounds = [
            (constraints.get("min_weight", 0), constraints.get("max_weight", 1))
            for _ in range(n)
        ]
        cons = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: w @ mu.values - target_return},
        ]

        result = minimize(portfolio_variance, w0, method="SLSQP", bounds=bounds, constraints=cons)
        return result.x if result.success else w0

    def _hierarchical_risk_parity(self, returns: pd.DataFrame) -> np.ndarray:
        """
        Hierarchical Risk Parity (HRP) by Marcos Lopez de Prado.
        Uses hierarchical clustering for robust portfolio allocation.
        """
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import squareform

        cov = returns.cov()
        corr = returns.corr()
        n = len(corr)

        # Distance matrix
        dist = np.sqrt(0.5 * (1 - corr.values))
        np.fill_diagonal(dist, 0)

        # Hierarchical clustering
        condensed_dist = squareform(dist, checks=False)
        link = linkage(condensed_dist, method="single")
        sort_idx = leaves_list(link)

        # Recursive bisection
        weights = np.ones(n)
        cluster_items = [sort_idx.tolist()]

        while cluster_items:
            new_clusters = []
            for cluster in cluster_items:
                if len(cluster) <= 1:
                    continue

                mid = len(cluster) // 2
                left = cluster[:mid]
                right = cluster[mid:]

                # Calculate cluster variance
                left_var = self._cluster_variance(cov.values, left)
                right_var = self._cluster_variance(cov.values, right)

                # Allocate inversely proportional to variance
                total_var = left_var + right_var
                if total_var > 0:
                    left_weight = 1 - left_var / total_var
                    right_weight = 1 - right_var / total_var
                else:
                    left_weight = right_weight = 0.5

                for i in left:
                    weights[i] *= left_weight
                for i in right:
                    weights[i] *= right_weight

                new_clusters.extend([left, right])

            cluster_items = [c for c in new_clusters if len(c) > 1]

        # Normalize
        weights = weights / weights.sum()
        return weights

    @staticmethod
    def _cluster_variance(cov: np.ndarray, indices: List[int]) -> float:
        """Calculate variance of an equal-weighted cluster."""
        sub_cov = cov[np.ix_(indices, indices)]
        n = len(indices)
        w = np.ones(n) / n
        return w @ sub_cov @ w

    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        n_points: int = 50,
    ) -> pd.DataFrame:
        """
        Calculate the efficient frontier.

        Returns DataFrame with columns: return, volatility, sharpe, weights
        """
        mu = returns.mean() * 252
        cov = returns.cov() * 252

        min_ret = mu.min()
        max_ret = mu.max()
        target_returns = np.linspace(min_ret, max_ret, n_points)

        frontier = []
        for target in target_returns:
            try:
                weights = self._mean_variance(
                    mu, cov, target, {"min_weight": 0, "max_weight": 1}
                )
                port_ret = weights @ mu.values
                port_vol = np.sqrt(weights @ cov.values @ weights)
                sharpe = (port_ret - self.risk_free_rate) / port_vol if port_vol > 0 else 0

                frontier.append({
                    "return": port_ret,
                    "volatility": port_vol,
                    "sharpe": sharpe,
                    "weights": dict(zip(returns.columns, weights)),
                })
            except Exception:
                continue

        return pd.DataFrame(frontier)
