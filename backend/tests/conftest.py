"""
Pytest configuration and shared fixtures.
"""

import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def sample_ohlcv():
    """Generate sample OHLCV data."""
    np.random.seed(42)
    n = 200
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    close = np.maximum(close, 10)

    return pd.DataFrame({
        "open": close + np.random.randn(n) * 0.5,
        "high": close + abs(np.random.randn(n)) * 2,
        "low": close - abs(np.random.randn(n)) * 2,
        "close": close,
        "volume": np.random.randint(1000, 100000, n).astype(float),
    })


@pytest.fixture
def sample_returns():
    """Generate sample return series."""
    np.random.seed(42)
    return pd.Series(np.random.randn(252) * 0.01 + 0.0003)


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)
