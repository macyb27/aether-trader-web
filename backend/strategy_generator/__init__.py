"""
Aether Trader - Strategy Generator Module
Automatic generation and management of trading strategies.
"""

from .strategy_engine import StrategyEngine
from .strategy_templates import StrategyTemplate, MomentumStrategy, MeanReversionStrategy, MLStrategy

__all__ = [
    "StrategyEngine", "StrategyTemplate",
    "MomentumStrategy", "MeanReversionStrategy", "MLStrategy",
]
