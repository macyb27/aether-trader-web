"""
Settings - Central configuration management using Pydantic.
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Aether Trader"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str = "postgresql://aether:aether@localhost:5432/aether_trader"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300

    # Trading
    initial_capital: float = 100_000.0
    default_commission: float = 0.001
    default_slippage: float = 0.0005
    default_timeframe: str = "1d"
    default_symbols: List[str] = ["BTC/USDT", "ETH/USDT"]

    # Exchange (CCXT)
    exchange_id: str = "binance"
    exchange_api_key: Optional[str] = None
    exchange_api_secret: Optional[str] = None
    exchange_sandbox: bool = True

    # AI/RL
    rl_algorithm: str = "ppo"
    rl_total_timesteps: int = 100_000
    rl_device: str = "auto"
    model_dir: str = "models"

    # Genetic Optimizer
    ga_population_size: int = 100
    ga_generations: int = 50
    ga_mutation_rate: float = 0.1
    ga_crossover_rate: float = 0.8

    # Risk Management
    max_position_size: float = 0.10
    max_portfolio_leverage: float = 1.0
    max_daily_loss: float = 0.02
    max_drawdown: float = 0.10

    # Pipeline
    pipeline_interval: int = 3600
    pipeline_max_iterations: Optional[int] = None

    # Frontend
    frontend_url: str = "http://localhost:3000"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        env_prefix = "AETHER_"
        case_sensitive = False
