"""
Tests for the Storage module (SQLite and PostgreSQL support).
"""

import os
import tempfile

import pytest


class TestDatabase:
    """Test database layer with SQLite backend."""

    def test_sqlite_default(self):
        """Database should default to SQLite when no env var is set."""
        from backend.storage.database import Database

        # Remove env vars to force SQLite default
        old_val = os.environ.pop("AETHER_DATABASE_URL", None)
        old_val2 = os.environ.pop("DATABASE_URL", None)

        try:
            db = Database()
            assert db.is_sqlite is True
            assert "sqlite" in db.url
        finally:
            if old_val:
                os.environ["AETHER_DATABASE_URL"] = old_val
            if old_val2:
                os.environ["DATABASE_URL"] = old_val2

    def test_sqlite_create_tables(self):
        """Should create tables in SQLite database."""
        from backend.storage.database import Database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = Database(url=f"sqlite:///{db_path}")
            db.create_tables()
            assert db.health_check() is True
        finally:
            os.unlink(db_path)

    def test_sqlite_health_check(self):
        """Health check should pass for SQLite."""
        from backend.storage.database import Database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = Database(url=f"sqlite:///{db_path}")
            assert db.health_check() is True
        finally:
            os.unlink(db_path)

    def test_database_info(self):
        """Should return database info dict."""
        from backend.storage.database import Database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = Database(url=f"sqlite:///{db_path}")
            info = db.get_info()
            assert info["backend"] == "sqlite"
            assert info["healthy"] is True
        finally:
            os.unlink(db_path)

    def test_get_database_url_fallback(self):
        """Should fall back to SQLite URL when env vars are not set."""
        from backend.storage.database import get_database_url

        old_val = os.environ.pop("AETHER_DATABASE_URL", None)
        old_val2 = os.environ.pop("DATABASE_URL", None)

        try:
            url = get_database_url()
            assert "sqlite" in url
        finally:
            if old_val:
                os.environ["AETHER_DATABASE_URL"] = old_val
            if old_val2:
                os.environ["DATABASE_URL"] = old_val2


class TestModels:
    """Test SQLAlchemy models."""

    def test_models_importable(self):
        from backend.storage.models import (
            Base, OHLCVData, Strategy, BacktestResult, Trade
        )
        assert Base is not None
        assert OHLCVData is not None
        assert Strategy is not None
        assert BacktestResult is not None
        assert Trade is not None

    def test_model_table_names(self):
        from backend.storage.models import OHLCVData, Strategy, BacktestResult, Trade

        assert OHLCVData.__tablename__ == "ohlcv_data"
        assert Strategy.__tablename__ == "strategies"
        assert BacktestResult.__tablename__ == "backtest_results"
        assert Trade.__tablename__ == "trades"
