"""
Aether Trader - Main Entry Point
Runnable server with CLI configuration.

Usage:
    python -m backend.main                    # Start API server
    python -m backend.main --pipeline         # Start trading pipeline
    python -m backend.main --port 9000        # Custom port
    python -m backend.main --reload           # Development mode
"""

import argparse
import logging
import os
import sys

import uvicorn


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/aether_trader.log", mode="a"),
        ],
    )


def ensure_directories() -> None:
    """Ensure required directories exist."""
    for directory in ["logs", "models", "models/rl", "data"]:
        os.makedirs(directory, exist_ok=True)


def run_server(host: str, port: int, workers: int, reload: bool) -> None:
    """Start the FastAPI server."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Aether Trader API on {host}:{port}")

    uvicorn.run(
        "backend.server:app",
        host=host,
        port=port,
        workers=1 if reload else workers,
        reload=reload,
        log_level="info",
    )


def run_pipeline(symbols: list, timeframe: str, interval: int) -> None:
    """Start the trading pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting Aether Trader Pipeline")

    from backend.core.trading_pipeline import TradingPipeline

    config = {
        "initial_capital": float(os.getenv("AETHER_INITIAL_CAPITAL", 100_000)),
        "optimization_method": "max_sharpe",
    }

    pipeline = TradingPipeline(config)
    pipeline.run(
        symbols=symbols,
        timeframe=timeframe,
        interval_seconds=interval,
    )


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Aether Trader - AI Quantitative Trading Research Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.main                          Start API server (default)
  python -m backend.main --port 9000              Custom port
  python -m backend.main --reload                 Development mode with auto-reload
  python -m backend.main --pipeline               Start trading pipeline
  python -m backend.main --pipeline --symbols BTC/USDT ETH/USDT
        """,
    )

    # Server options
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers (default: 4)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="INFO", help="Log level (default: INFO)")

    # Pipeline options
    parser.add_argument("--pipeline", action="store_true", help="Run trading pipeline instead of API server")
    parser.add_argument("--symbols", nargs="+", default=["BTC/USDT", "ETH/USDT"], help="Trading symbols")
    parser.add_argument("--timeframe", default="1d", help="Data timeframe (default: 1d)")
    parser.add_argument("--interval", type=int, default=3600, help="Pipeline interval in seconds (default: 3600)")

    args = parser.parse_args()

    # Setup
    ensure_directories()
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("  Aether Trader v2.0 - AI Quantitative Trading Platform")
    logger.info("=" * 60)

    if args.pipeline:
        run_pipeline(args.symbols, args.timeframe, args.interval)
    else:
        run_server(args.host, args.port, args.workers, args.reload)


if __name__ == "__main__":
    main()
