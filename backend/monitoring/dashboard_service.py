"""
Dashboard Service - Backend service for the monitoring dashboard.
Aggregates data from all modules for visualization.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Aggregation service for the monitoring dashboard.
    Collects and formats data from all platform modules.
    """

    def __init__(self):
        self._data_sources: Dict[str, Any] = {}
        logger.info("DashboardService initialized")

    def register_source(self, name: str, source: Any) -> None:
        """Register a data source module."""
        self._data_sources[name] = source

    def get_overview(self) -> Dict:
        """Get platform overview metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": "running",
            "registered_modules": list(self._data_sources.keys()),
            "uptime": self._get_uptime(),
        }

    def get_portfolio_dashboard(self) -> Dict:
        """Get portfolio dashboard data."""
        paper_trader = self._data_sources.get("paper_trader")
        if paper_trader is None:
            return {"error": "Paper trader not registered"}

        summary = paper_trader.get_portfolio_summary()
        snapshots = paper_trader.portfolio_snapshots

        return {
            "summary": summary,
            "equity_curve": [
                {"timestamp": s["timestamp"].isoformat(), "value": s["total_value"]}
                for s in snapshots
            ],
            "recent_trades": paper_trader.trade_history[-20:],
        }

    def get_strategy_dashboard(self) -> Dict:
        """Get strategy performance dashboard data."""
        strategy_engine = self._data_sources.get("strategy_engine")
        backtest_engine = self._data_sources.get("backtest_engine")

        data = {"strategies": [], "backtest_results": []}

        if strategy_engine:
            data["strategies"] = strategy_engine.get_strategy_summary().to_dict("records")

        return data

    def get_risk_dashboard(self) -> Dict:
        """Get risk monitoring dashboard data."""
        risk_engine = self._data_sources.get("risk_engine")
        if risk_engine is None:
            return {"error": "Risk engine not registered"}

        return {
            "circuit_breaker_active": risk_engine.is_circuit_breaker_active,
            "limits": {
                "max_position_size": risk_engine.limits.max_position_size,
                "max_drawdown": risk_engine.limits.max_drawdown,
                "max_daily_loss": risk_engine.limits.max_daily_loss,
                "max_leverage": risk_engine.limits.max_portfolio_leverage,
            },
        }

    def get_ai_dashboard(self) -> Dict:
        """Get AI/RL training dashboard data."""
        rl_trainer = self._data_sources.get("rl_trainer")
        if rl_trainer is None:
            return {"error": "RL trainer not registered"}

        return {
            "training_history": rl_trainer.get_training_history(),
            "algorithm": rl_trainer.algorithm,
        }

    def get_market_data_dashboard(self) -> Dict:
        """Get market data status dashboard."""
        data_loader = self._data_sources.get("data_loader")
        if data_loader is None:
            return {"error": "Data loader not registered"}

        return {
            "feeds": list(data_loader.feeds.keys()),
            "cache_size": len(data_loader._cache),
        }

    def _get_uptime(self) -> str:
        """Get system uptime string."""
        return "running"
