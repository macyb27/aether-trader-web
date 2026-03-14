"""
Tests for the FastAPI REST API.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from backend.server import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "timestamp" in data

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Aether Trader"
        assert data["version"] == "2.0.0"


class TestStatusEndpoint:
    """Test system status endpoint."""

    def test_status(self, client):
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "modules" in data
        assert len(data["modules"]) >= 9


class TestStrategyEndpoints:
    """Test strategy-related endpoints."""

    def test_list_strategies(self, client):
        response = client.get("/api/v1/strategies")
        assert response.status_code == 200

    def test_generate_strategies(self, client):
        response = client.post("/api/v1/strategies/generate", json={
            "n_variants": 10,
            "symbol": "BTC/USDT",
        })
        assert response.status_code == 200


class TestBacktestEndpoints:
    """Test backtesting endpoints."""

    def test_run_backtest(self, client):
        response = client.post("/api/v1/backtest/run", json={
            "strategy_name": "momentum",
            "symbol": "BTC/USDT",
        })
        assert response.status_code == 200

    def test_get_results(self, client):
        response = client.get("/api/v1/backtest/results")
        assert response.status_code == 200


class TestPortfolioEndpoints:
    """Test portfolio endpoints."""

    def test_optimize_portfolio(self, client):
        response = client.post("/api/v1/portfolio/optimize", json={
            "method": "max_sharpe",
            "symbols": ["BTC/USDT", "ETH/USDT"],
        })
        assert response.status_code == 200

    def test_current_portfolio(self, client):
        response = client.get("/api/v1/portfolio/current")
        assert response.status_code == 200


class TestRiskEndpoints:
    """Test risk management endpoints."""

    def test_risk_report(self, client):
        response = client.get("/api/v1/risk/report")
        assert response.status_code == 200

    def test_risk_limits(self, client):
        response = client.get("/api/v1/risk/limits")
        assert response.status_code == 200
        data = response.json()
        assert "max_position_size" in data
        assert "max_drawdown" in data


class TestPipelineEndpoints:
    """Test pipeline endpoints."""

    def test_pipeline_status(self, client):
        response = client.get("/api/v1/pipeline/status")
        assert response.status_code == 200

    def test_start_pipeline(self, client):
        response = client.post("/api/v1/pipeline/start", json={
            "symbols": ["BTC/USDT"],
            "timeframe": "1d",
        })
        assert response.status_code == 200


class TestDashboardEndpoints:
    """Test dashboard endpoints."""

    def test_dashboard_overview(self, client):
        response = client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert "system_status" in data
