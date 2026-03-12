"""
Database Models - SQLAlchemy ORM models for the Aether Trader platform.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class MarketData(Base):
    """Stored OHLCV market data."""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    source = Column(String(50), default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_market_data"),
        Index("ix_market_data_lookup", "symbol", "timeframe", "timestamp"),
    )


class Strategy(Base):
    """Trading strategy definitions and metadata."""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # momentum, mean_reversion, ml, rl
    parameters = Column(JSON, default={})
    code_hash = Column(String(64))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    backtest_results = relationship("BacktestResult", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")


class BacktestResult(Base):
    """Backtest results for strategies."""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Performance metrics
    total_return = Column(Float)
    annual_return = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    calmar_ratio = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    total_trades = Column(Integer)
    avg_trade_duration = Column(Float)  # in hours

    # Risk metrics
    volatility = Column(Float)
    var_95 = Column(Float)
    cvar_95 = Column(Float)
    beta = Column(Float)
    alpha = Column(Float)

    # Full results as JSON
    equity_curve = Column(JSON)
    trade_log = Column(JSON)
    metrics = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship("Strategy", back_populates="backtest_results")


class Trade(Base):
    """Individual trade records."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), default="market")
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    pnl = Column(Float)
    pnl_pct = Column(Float)
    is_paper = Column(Boolean, default=True)
    status = Column(String(20), default="filled")  # pending, filled, cancelled
    executed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship("Strategy", back_populates="trades")


class Portfolio(Base):
    """Portfolio state snapshots."""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    total_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions = Column(JSON, default={})
    weights = Column(JSON, default={})
    metrics = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    snapshot_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class GeneticRun(Base):
    """Genetic algorithm optimization run records."""
    __tablename__ = "genetic_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    population_size = Column(Integer, nullable=False)
    generations = Column(Integer, nullable=False)
    mutation_rate = Column(Float)
    crossover_rate = Column(Float)
    fitness_function = Column(String(100))
    best_fitness = Column(Float)
    best_params = Column(JSON)
    convergence_history = Column(JSON)
    status = Column(String(20), default="running")  # running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
