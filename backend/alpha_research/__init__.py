"""
Aether Trader - Alpha Research Lab
Discover, test, and validate alpha signals and trading factors.
"""

from .alpha_lab import AlphaLab
from .signal_generator import SignalGenerator
from .factor_model import FactorModel

__all__ = ["AlphaLab", "SignalGenerator", "FactorModel"]
