"""
Monitoring - Sentry integration and health checks for production.
Ensures errors are tracked and system health is visible.
"""

import logging
import os
from typing import Dict, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


def setup_monitoring(dsn: Optional[str] = None, environment: str = "production"):
    """
    Initialize Sentry for error tracking and performance monitoring.
    """
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not set. Error tracking disabled.")
        return

    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(),
            sentry_logging,
        ],
        environment=environment,
        traces_sample_rate=1.0,      # Capture 100% of transactions for performance monitoring
        profiles_sample_rate=1.0,    # Capture 100% of profiles
    )
    logger.info(f"Sentry monitoring initialized in {environment} mode.")


class HealthMonitor:
    """
    System health monitor for Kubernetes liveness/readiness probes.
    """

    def __init__(self, db_instance, redis_instance):
        self.db = db_instance
        self.redis = redis_instance

    async def check_health(self) -> Dict[str, bool]:
        """Check health of all critical components."""
        health = {
            "database": await self.db.health_check(),
            "redis": await self.redis.health_check(),
            "api": True
        }
        return health


# Global instance
health_monitor = None # Initialized in server.py
