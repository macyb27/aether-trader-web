"""
Database - PostgreSQL interface using SQLAlchemy with async support.
Handles connection pooling, migrations, and CRUD operations.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)


class Database:
    """Synchronous database interface for PostgreSQL."""

    def __init__(self, url: str = "postgresql://localhost:5432/aether_trader"):
        self.url = url
        self.engine = create_engine(
            url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        logger.info("Database engine created")

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")

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


class AsyncDatabase:
    """Asynchronous database interface for PostgreSQL."""

    def __init__(self, url: str = "postgresql+asyncpg://localhost:5432/aether_trader"):
        self.url = url
        self.engine = create_async_engine(
            url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.AsyncSessionLocal = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Async database engine created")

    async def create_tables(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self):
        """Get an async database session."""
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
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Async database health check failed: {e}")
            return False
