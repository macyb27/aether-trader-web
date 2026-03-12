# Aether Trader - Architecture Documentation

## AI Quantitative Trading Research Platform v2.0

---

## System Overview

Aether Trader is a fully modular, scalable AI-powered quantitative trading research platform. It combines classical quantitative finance methods with modern machine learning and reinforcement learning to discover, optimize, and execute trading strategies.

---

## Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │           Frontend (Next.js)             │
                    │         Analytics Dashboard              │
                    └──────────────────┬──────────────────────┘
                                       │ REST API
                    ┌──────────────────▼──────────────────────┐
                    │         FastAPI Server (server.py)       │
                    │              REST API v1                  │
                    └──────────────────┬──────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
    ┌─────▼─────┐              ┌──────▼──────┐             ┌──────▼──────┐
    │   Data     │              │   Trading   │             │  Monitoring │
    │  Ingestion │              │  Pipeline   │             │  Dashboard  │
    └─────┬─────┘              └──────┬──────┘             └─────────────┘
          │                            │
    ┌─────▼─────┐     ┌───────────────┼───────────────┐
    │  Feature   │     │               │               │
    │Engineering │     │               │               │
    └─────┬─────┘     │               │               │
          │      ┌────▼────┐   ┌─────▼─────┐  ┌─────▼─────┐
          │      │ Strategy │   │  Genetic  │  │    AI/RL   │
          │      │Generator │   │ Optimizer │  │  Trainer   │
          │      └────┬────┘   └─────┬─────┘  └─────┬─────┘
          │           │               │               │
          │      ┌────▼────────────────▼───────────────▼────┐
          │      │           Backtesting Engine              │
          │      └────────────────┬─────────────────────────┘
          │                       │
          │      ┌────────────────▼─────────────────────────┐
          │      │            Risk Engine                    │
          │      └────────────────┬─────────────────────────┘
          │                       │
          │      ┌────────────────▼─────────────────────────┐
          │      │        Portfolio Optimizer                │
          │      └────────────────┬─────────────────────────┘
          │                       │
          │      ┌────────────────▼─────────────────────────┐
          │      │         Execution Engine                  │
          │      │       (Paper Trading / Live)              │
          │      └──────────────────────────────────────────┘
          │
    ┌─────▼──────────────────────────────────────────────────┐
    │                    Storage Layer                        │
    │            PostgreSQL  │  Redis Cache                   │
    └────────────────────────────────────────────────────────┘
```

---

## Module Reference

### 1. Data Ingestion (`backend/data_ingestion/`)

Responsible for loading market data from multiple sources.

| File | Description |
|------|-------------|
| `market_data_loader.py` | Central data loader with caching |
| `crypto_feed.py` | Cryptocurrency data via CCXT (Binance, etc.) |
| `equity_feed.py` | Equity/stock data via yfinance |
| `realtime_stream.py` | WebSocket real-time streaming |

### 2. Storage (`backend/storage/`)

Database and caching layer.

| File | Description |
|------|-------------|
| `database.py` | PostgreSQL connection via SQLAlchemy |
| `models.py` | ORM models (OHLCV, Strategy, Backtest, Trade) |
| `redis_cache.py` | Redis caching for hot data |

### 3. Feature Engineering (`backend/feature_engineering/`)

Transforms raw market data into ML-ready features.

| File | Description |
|------|-------------|
| `feature_pipeline.py` | Main pipeline orchestrator |
| `technical_features.py` | RSI, MACD, Bollinger Bands, ATR, etc. |
| `statistical_features.py` | Volatility, skewness, kurtosis, Hurst exponent |

### 4. Alpha Research (`backend/alpha_research/`)

Discovers alpha signals and factor models.

| File | Description |
|------|-------------|
| `alpha_lab.py` | Alpha research engine |
| `signal_generator.py` | Trading signal generation |
| `factor_model.py` | Multi-factor model analysis |

### 5. Strategy Generator (`backend/strategy_generator/`)

Generates and manages trading strategies.

| File | Description |
|------|-------------|
| `strategy_engine.py` | Strategy management and signal generation |
| `strategy_templates.py` | Momentum, Mean Reversion, ML, Breakout templates |

### 6. Genetic Optimizer (`backend/genetic_optimizer/`)

Evolutionary optimization for strategy parameters.

| File | Description |
|------|-------------|
| `genetic_optimizer.py` | GA with tournament selection, crossover, mutation |
| `fitness_functions.py` | Sharpe, Sortino, Calmar fitness functions |

### 7. Backtesting Engine (`backend/backtesting/`)

Vectorbt-based backtesting framework.

| File | Description |
|------|-------------|
| `backtest_engine.py` | Main backtesting engine |
| `performance_metrics.py` | Sharpe, drawdown, win rate, etc. |

### 8. Risk Engine (`backend/risk/`)

Comprehensive risk management system.

| File | Description |
|------|-------------|
| `risk_engine.py` | VaR, CVaR, drawdown monitoring, circuit breaker |

### 9. Portfolio Optimizer (`backend/portfolio_optimizer/`)

Advanced portfolio allocation methods.

| File | Description |
|------|-------------|
| `portfolio_optimizer.py` | Mean-Variance, Risk Parity, HRP, Black-Litterman |

### 10. AI Module (`backend/ai/`)

Reinforcement learning trading agents.

| File | Description |
|------|-------------|
| `rl_env.py` | Gymnasium-compatible trading environment |
| `rl_trainer.py` | Training pipeline with stable-baselines3 (PPO, SAC, TD3, A2C, DQN) |

### 11. Execution Engine (`backend/execution/`)

Order management and trade execution.

| File | Description |
|------|-------------|
| `execution_engine.py` | Order lifecycle management |
| `paper_trader.py` | Paper trading simulation |

### 12. Monitoring (`backend/monitoring/`)

System monitoring and metrics.

| File | Description |
|------|-------------|
| `dashboard_service.py` | Dashboard data aggregation |
| `metrics_collector.py` | Prometheus-compatible metrics |

---

## Trading Pipeline

The core trading loop runs continuously:

```python
while True:
    data = load_market_data()        # Step 1: Ingest data
    features = build_features(data)   # Step 2: Engineer features
    strategies = generate_strategies(features)  # Step 3: Generate strategies
    results = backtest_strategies(strategies)    # Step 4: Backtest
    best = select_best(results)       # Step 5: Select winners
    portfolio = optimize_portfolio(best)  # Step 6: Optimize allocation
    execute_paper_trades(portfolio)    # Step 7: Execute trades
```

---

## Infrastructure

| Component | Purpose |
|-----------|---------|
| Docker Compose | Local development orchestration |
| Kubernetes | Production deployment with HPA |
| Airflow | Pipeline scheduling (4h trading, weekly RL training) |
| Prometheus | Metrics collection |
| Grafana | Visualization dashboards |
| PostgreSQL | Persistent storage |
| Redis | Caching and real-time data |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/status` | System status |
| POST | `/api/v1/data/load` | Load market data |
| POST | `/api/v1/strategies/generate` | Generate strategies |
| POST | `/api/v1/backtest/run` | Run backtest |
| POST | `/api/v1/optimization/run` | Genetic optimization |
| POST | `/api/v1/ai/train` | Train RL agent |
| POST | `/api/v1/portfolio/optimize` | Optimize portfolio |
| GET | `/api/v1/risk/report` | Risk assessment |
| POST | `/api/v1/pipeline/start` | Start pipeline |
| GET | `/api/v1/dashboard/overview` | Dashboard data |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/macyb27/aether-trader-web.git
cd aether-trader-web
pip install -r requirements.txt
npm install

# Start with Docker
docker compose up -d

# Or start manually
make backend  # Terminal 1
make frontend # Terminal 2

# Run tests
make test
```
