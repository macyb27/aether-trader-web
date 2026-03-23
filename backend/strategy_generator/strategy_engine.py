"""
Strategy Engine - Orchestrates strategy generation, parameterization, and management.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .strategy_templates import StrategyTemplate

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Central engine for generating, managing, and evaluating trading strategies.
    Supports template-based generation and automatic parameter search.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.strategies: Dict[str, StrategyTemplate] = {}
        self._templates: Dict[str, type] = {}
        logger.info("StrategyEngine initialized")

    def register_template(self, name: str, template_class: type) -> None:
        """Register a strategy template class."""
        self._templates[name] = template_class
        logger.info(f"Strategy template registered: {name}")

    def generate_strategies(
        self,
        features: pd.DataFrame,
        templates: Optional[List[str]] = None,
        n_variants: int = 10,
        seed: Optional[int] = None,
    ) -> Dict[str, StrategyTemplate]:
        """
        Generate strategy variants from templates.

        Args:
            features: Feature matrix
            templates: Template names to use (None = all)
            n_variants: Number of parameter variants per template
            seed: Random seed

        Returns:
            Dictionary of generated strategies
        """
        if seed is not None:
            np.random.seed(seed)

        template_names = templates or list(self._templates.keys())
        generated = {}

        for template_name in template_names:
            if template_name not in self._templates:
                logger.warning(f"Template not found: {template_name}")
                continue

            template_class = self._templates[template_name]

            for i in range(n_variants):
                try:
                    # Generate random parameters within template bounds
                    params = template_class.random_params()
                    strategy = template_class(params=params)

                    name = f"{template_name}_v{i:03d}"
                    strategy.name = name
                    generated[name] = strategy
                    self.strategies[name] = strategy

                except Exception as e:
                    logger.error(f"Strategy generation failed: {e}")

        logger.info(f"Generated {len(generated)} strategies from {len(template_names)} templates")
        return generated

    def generate_signals(
        self,
        strategy_name: str,
        features: pd.DataFrame,
    ) -> pd.Series:
        """Generate trading signals from a strategy."""
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy not found: {strategy_name}")

        strategy = self.strategies[strategy_name]
        return strategy.generate_signals(features)

    def generate_all_signals(
        self,
        features: pd.DataFrame,
    ) -> Dict[str, pd.Series]:
        """Generate signals for all registered strategies."""
        results = {}
        for name, strategy in self.strategies.items():
            try:
                signals = strategy.generate_signals(features)
                results[name] = signals
            except Exception as e:
                logger.error(f"Signal generation failed for {name}: {e}")
        return results

    def get_strategy_params(self, name: str) -> Dict:
        """Get parameters for a specific strategy."""
        if name in self.strategies:
            return self.strategies[name].params
        return {}

    def update_strategy_params(self, name: str, params: Dict) -> None:
        """Update parameters for a specific strategy."""
        if name in self.strategies:
            self.strategies[name].params.update(params)
            logger.info(f"Updated params for {name}")

    def get_strategy_summary(self) -> pd.DataFrame:
        """Get summary of all strategies."""
        records = []
        for name, strategy in self.strategies.items():
            records.append({
                "name": name,
                "type": strategy.__class__.__name__,
                "params": str(strategy.params),
            })
        return pd.DataFrame(records)
