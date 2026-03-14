"""
Logger - Centralized logging configuration for the Aether Trader platform.
Provides structured logging with file rotation, JSON formatting, and trade-specific loggers.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================
# Log Directories
# ============================================================

LOG_DIR = Path("logs")
TRADE_LOG_DIR = LOG_DIR / "trades"
PIPELINE_LOG_DIR = LOG_DIR / "pipeline"


def ensure_log_dirs() -> None:
    """Ensure all log directories exist."""
    for d in [LOG_DIR, TRADE_LOG_DIR, PIPELINE_LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


# ============================================================
# Custom Formatters
# ============================================================

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging and log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields
        for key in ["trade_id", "symbol", "strategy", "pnl", "action"]:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry)


class ColorFormatter(logging.Formatter):
    """Colored console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname:8s}{self.RESET}"
        return super().format(record)


# ============================================================
# Logger Setup
# ============================================================

def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure the root logger for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Use JSON format for file logs
        log_file: Path to log file (default: logs/aether_trader.log)
        max_bytes: Max size per log file before rotation
        backup_count: Number of rotated log files to keep

    Returns:
        Configured root logger
    """
    ensure_log_dirs()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if sys.stdout.isatty():
        console_fmt = ColorFormatter(
            "%(asctime)s %(levelname)s %(name)-30s %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_fmt)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file is None:
        log_file = str(LOG_DIR / "aether_trader.log")

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    if json_logs:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    for noisy in ["urllib3", "asyncio", "websockets", "ccxt"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root_logger.info("Logging system initialized (level=%s, json=%s)", level, json_logs)
    return root_logger


# ============================================================
# Specialized Loggers
# ============================================================

def get_trade_logger() -> logging.Logger:
    """
    Get a dedicated trade logger that writes to a separate trade log file.
    Logs every trade execution for audit and analysis.
    """
    logger = logging.getLogger("aether.trades")

    if not logger.handlers:
        ensure_log_dirs()

        handler = logging.handlers.RotatingFileHandler(
            str(TRADE_LOG_DIR / "trades.log"),
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=10,
            encoding="utf-8",
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def get_pipeline_logger() -> logging.Logger:
    """
    Get a dedicated pipeline logger for tracking pipeline iterations.
    """
    logger = logging.getLogger("aether.pipeline")

    if not logger.handlers:
        ensure_log_dirs()

        handler = logging.handlers.RotatingFileHandler(
            str(PIPELINE_LOG_DIR / "pipeline.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def get_pnl_logger() -> logging.Logger:
    """
    Get a dedicated PnL logger for tracking profit and loss.
    """
    logger = logging.getLogger("aether.pnl")

    if not logger.handlers:
        ensure_log_dirs()

        handler = logging.handlers.RotatingFileHandler(
            str(TRADE_LOG_DIR / "pnl.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


# ============================================================
# Trade Logging Helpers
# ============================================================

def log_trade(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    strategy: str = "",
    trade_id: str = "",
    pnl: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a trade execution with full details.

    Args:
        symbol: Trading symbol
        side: "buy" or "sell"
        quantity: Trade quantity
        price: Execution price
        strategy: Strategy name
        trade_id: Unique trade identifier
        pnl: Realized PnL (for closing trades)
        metadata: Additional trade metadata
    """
    trade_logger = get_trade_logger()

    trade_data = {
        "trade_id": trade_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "value": quantity * price,
        "strategy": strategy,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if pnl is not None:
        trade_data["pnl"] = pnl

    if metadata:
        trade_data.update(metadata)

    trade_logger.info(
        json.dumps(trade_data),
        extra={"trade_id": trade_id, "symbol": symbol, "strategy": strategy},
    )


def log_pnl(
    portfolio_value: float,
    cash: float,
    total_pnl: float,
    pnl_pct: float,
    positions: int = 0,
    drawdown: float = 0.0,
) -> None:
    """
    Log portfolio PnL snapshot.

    Args:
        portfolio_value: Total portfolio value
        cash: Available cash
        total_pnl: Total profit/loss
        pnl_pct: PnL as percentage
        positions: Number of open positions
        drawdown: Current drawdown percentage
    """
    pnl_logger = get_pnl_logger()

    pnl_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "portfolio_value": portfolio_value,
        "cash": cash,
        "total_pnl": total_pnl,
        "pnl_pct": pnl_pct,
        "positions": positions,
        "drawdown": drawdown,
    }

    pnl_logger.info(json.dumps(pnl_data), extra={"pnl": total_pnl, "action": "pnl_snapshot"})
