"""
Database - Multi-backend interface using SQLAlchemy.
Supports SQLite (default/development) and PostgreSQL (production).
Handles connection pooling, migrations, and CRUD operations.
"""

import logging
import os
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

# Default to SQLite for zero-config development
DEFAULT_SQLITE_PATH = Path("data/aether_trader.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"
DEFAULT_POSTGRES_URL = "postgresql://aether:aether@localhost:5432/aether_trader"


def get_database_url() -> str:
    """
    Resolve database URL from environment.
    Falls back to SQLite if no PostgreSQL is configured.
    """
    url = os.getenv("AETHER_DATABASE_URL") or os.getenv("DATABASE_URL")
    if url:
        return url
    return DEFAULT_SQLITE_URL


class Database:
    """
    Synchronous database interface.
    Supports SQLite (development) and PostgreSQL (production).
    """

    def __init__(self, url: Optional[str] = None):
        self.url = url or get_database_url()
        self.is_sqlite = self.url.startswith("sqlite")

        # Configure engine based on backend
        engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}

        if self.is_sqlite:
            # SQLite-specific configuration
            self._ensure_sqlite_dir()
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # PostgreSQL-specific configuration
            engine_kwargs["pool_size"] = 20
            engine_kwargs["max_overflow"] = 10
            engine_kwargs["pool_recycle"] = 3600

        self.engine = create_engine(self.url, **engine_kwargs)

        # Enable WAL mode for SQLite (better concurrent read performance)
        if self.is_sqlite:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        backend_name = "SQLite" if self.is_sqlite else "PostgreSQL"
        logger.info(f"Database engine created ({backend_name}): {self._safe_url()}")

    def _ensure_sqlite_dir(self) -> None:
        """Ensure the directory for the SQLite database file exists."""
        if self.url.startswith("sqlite:///"):
            db_path = Path(self.url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

    def _safe_url(self) -> str:
        """Return URL with password masked for logging."""
        if "@" in self.url:
            parts = self.url.split("@")
            return "***@" + parts[-1]
        return self.url

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")

    def drop_tables(self) -> None:
        """Drop all tables. Use with caution."""
        Base.metadata.drop_all(self.engine)
        logger.info("Database tables dropped")

    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def insert(self, obj: Any) -> Any:
        """Insert a single object."""
        with self.get_session() as session:
            session.add(obj)
            session.flush()
            return obj

    def insert_many(self, objects: List[Any]) -> List[Any]:
        """Insert multiple objects."""
        with self.get_session() as session:
            session.add_all(objects)
            session.flush()
            return objects

    def query(self, model: Type, filters: Optional[Dict] = None, limit: int = 100) -> List:
        """Query objects with optional filters."""
        with self.get_session() as session:
            q = session.query(model)
            if filters:
                for key, value in filters.items():
                    q = q.filter(getattr(model, key) == value)
            return q.limit(limit).all()

    def delete(self, model: Type, filters: Dict) -> int:
        """Delete objects matching filters. Returns count of deleted rows."""
        with self.get_session() as session:
            q = session.query(model)
            for key, value in filters.items():
                q = q.filter(getattr(model, key) == value)
            count = q.delete(synchronize_session="fetch")
            return count

    def count(self, model: Type, filters: Optional[Dict] = None) -> int:
        """Count objects matching optional filters."""
        with self.get_session() as session:
            q = session.query(model)
            if filters:
                for key, value in filters.items():
                    q = q.filter(getattr(model, key) == value)
            return q.count()

    def execute_raw(self, sql: str, params: Optional[Dict] = None) -> Any:
        """Execute raw SQL."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            conn.commit()
            return result

    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get database information."""
        return {
            "backend": "sqlite" if self.is_sqlite else "postgresql",
            "url": self._safe_url(),
            "healthy": self.health_check(),
        }


class AsyncDatabase:
    """
    Asynchronous database interface.
    Supports PostgreSQL with asyncpg and SQLite with aiosqlite.
    """

    def __init__(self, url: Optional[str] = None):
        self.url = url or get_database_url()
        self.is_sqlite = self.url.startswith("sqlite")

        # Convert URL for async drivers
        if self.is_sqlite:
            async_url = self.url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            async_url = self.url.replace("postgresql://", "postgresql+asyncpg://")

        try:
            from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

            engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}
            if not self.is_sqlite:
                engine_kwargs["pool_size"] = 20
                engine_kwargs["max_overflow"] = 10
                engine_kwargs["pool_recycle"] = 3600

            self.engine = create_async_engine(async_url, **engine_kwargs)
            self.AsyncSessionLocal = sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info(f"Async database engine created")
        except ImportError:
            logger.warning(
                "Async database driver not available. "
                "Install asyncpg (PostgreSQL) or aiosqlite (SQLite)."
            )
            self.engine = None
            self.AsyncSessionLocal = None

    async def create_tables(self) -> None:
        """Create all tables."""
        if self.engine is None:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self):
        """Get an async database session."""
        if self.AsyncSessionLocal is None:
            raise RuntimeError("Async database not initialized")
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if self.engine is None:
            return False
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Async database health check failed: {e}")
            return False
