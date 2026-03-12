"""
Metrics Collector - Prometheus-compatible metrics collection.
Exposes trading platform metrics for monitoring and alerting.
"""

import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and exposes metrics in Prometheus format.
    Tracks system health, trading performance, and operational metrics.
    """

    def __init__(self):
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}
        self._start_time = time.time()
        logger.info("MetricsCollector initialized")

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None) -> None:
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def observe(self, name: str, value: float, labels: Optional[Dict] = None) -> None:
        """Record an observation for a histogram metric."""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def get_metrics_text(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        # Counters
        for key, value in self._counters.items():
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {value}")

        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key} gauge")
            lines.append(f"{key} {value}")

        # Histograms (simplified)
        for key, values in self._histograms.items():
            if values:
                import numpy as np
                lines.append(f"# TYPE {key} summary")
                lines.append(f'{key}{{quantile="0.5"}} {np.percentile(values, 50):.6f}')
                lines.append(f'{key}{{quantile="0.9"}} {np.percentile(values, 90):.6f}')
                lines.append(f'{key}{{quantile="0.99"}} {np.percentile(values, 99):.6f}')
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values):.6f}")

        # System metrics
        lines.append("# TYPE aether_uptime_seconds gauge")
        lines.append(f"aether_uptime_seconds {time.time() - self._start_time:.0f}")

        return "\n".join(lines) + "\n"

    def get_metrics_json(self) -> Dict:
        """Export metrics as JSON."""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "uptime_seconds": time.time() - self._start_time,
        }

    def _make_key(self, name: str, labels: Optional[Dict] = None) -> str:
        """Create a metric key with optional labels."""
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"aether_{name}{{{label_str}}}"
        return f"aether_{name}"

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._start_time = time.time()
