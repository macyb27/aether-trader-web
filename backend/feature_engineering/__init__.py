"""
Aether Trader - Feature Engineering Module
Transforms raw market data into trading features and signals.
"""

from .feature_pipeline import FeaturePipeline
from .technical_features import TechnicalFeatures
from .statistical_features import StatisticalFeatures

__all__ = ["FeaturePipeline", "TechnicalFeatures", "StatisticalFeatures"]
