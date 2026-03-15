# Aether Trader Pro - AI Quantitative Trading Platform

**Aether Trader Pro** is a fully modular, scalable AI-powered quantitative trading research platform. It combines classical quantitative finance methods with modern machine learning and reinforcement learning to discover, optimize, and execute trading strategies.

🚀 **Live Demo**: Coming soon on Vercel  
📱 **Mobile App**: [Aether-Trader-Mobile](https://github.com/macyb27/Aether-Trader-Mobile)  
💻 **Web Platform**: This repository

---

## 🎯 Core Features

### 🧠 AI & Quantitative Research
- **Feature Engineering**: Advanced technical (RSI, MACD, Bollinger Bands) and statistical (Volatility, Skewness, Hurst exponent) indicators.
- **Alpha Research Lab**: Signal generation and multi-factor model analysis.
- **Strategy Generator**: Automated generation of Momentum, Mean Reversion, Breakout, and ML-based strategies.
- **Genetic Optimization**: Evolutionary algorithms with tournament selection, crossover, and mutation for parameter tuning.
- **Reinforcement Learning**: Gymnasium-compatible trading environments trained with stable-baselines3 (PPO, SAC, TD3, A2C, DQN).

### 📈 Trading & Execution
- **Backtesting Engine**: High-performance vectorbt-based backtesting with walk-forward analysis and Monte Carlo simulations.
- **Risk Engine**: Comprehensive risk management including VaR, CVaR, drawdown monitoring, and circuit breakers.
- **Portfolio Optimizer**: Advanced allocation methods (Mean-Variance, Risk Parity, Hierarchical Risk Parity, Black-Litterman).
- **Execution Engine**: Simulated paper trading broker with order lifecycle management.

### 💻 Web Dashboard (Next.js)
- **Portfolio Overview**: Real-time balance, invested capital, and profit/loss tracking.
- **Multi-Agent System**: Monitor 4 specialized AI agents (QA Bot, RL Developer, Market Intel, Orchestrator).
- **Trading Workflow Pipeline**: Visualizes the 5-phase process (Hypothesis → Backtest → Paper Trading → Validation → Live).

---

## 🏗️ Architecture & Tech Stack

The system is built with a modern, scalable microservices architecture.

### Backend Stack (Python)
| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI, Uvicorn |
| **Data & Analysis** | Pandas, NumPy, SciPy |
| **Trading & Backtesting** | vectorbt, CCXT, yfinance |
| **AI / ML** | stable-baselines3, Gymnasium, PyTorch |
| **Database & Cache** | PostgreSQL (SQLAlchemy/asyncpg), SQLite (Dev), Redis |

### Frontend Stack (TypeScript)
| Component | Technology |
|-----------|-----------|
| **Framework** | Next.js 14 (React 18) |
| **Styling** | Tailwind CSS 3 |
| **State Management** | Zustand, React Hooks |
| **Authentication** | NextAuth.js (JWT) |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| **Orchestration** | Docker Compose, Kubernetes (HPA, Ingress) |
| **Scheduling** | Apache Airflow (DAGs for trading & training) |
| **Monitoring** | Prometheus, Grafana |

---

## 🔄 The Trading Pipeline

The core automated trading loop runs continuously via Airflow scheduling:

```python
while True:
    data = load_market_data()                   # 1. Ingest OHLCV data (CCXT/yfinance)
    features = build_features(data)             # 2. Compute momentum, volatility, RSI, etc.
    strategies = generate_strategies(features)  # 3. Generate random & template strategies
    results = backtest_strategies(strategies)   # 4. Simulate trades & calculate Sharpe/Drawdown
    best = select_best(results)                 # 5. Score via Genetic Optimization
    portfolio = optimize_portfolio(best)        # 6. Apply Risk Parity / Mean Variance
    execute_paper_trades(portfolio)             # 7. Execute via simulated broker
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for full stack)

### Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/macyb27/aether-trader-web.git
   cd aether-trader-web
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (Alpaca, Finnhub, etc.)
   ```

3. **Start with Docker (Recommended)**
   ```bash
   make docker-up
   ```
   This starts the Backend (FastAPI), Frontend (Next.js), PostgreSQL, Redis, Prometheus, and Grafana.

4. **Manual Start (Without Docker)**
   ```bash
   # Install dependencies
   make install

   # Start both servers
   make dev
   ```

### Access Points
- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Grafana Metrics**: `http://localhost:3001`

---

## 📚 Documentation

For detailed technical documentation, please refer to:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed module breakdown and system design.
- [Makefile](./Makefile) - Available development commands.

---

## 🧪 Testing

The backend includes a comprehensive test suite covering all core modules.

```bash
# Run all tests with coverage report
make test

# Run tests quickly
make test-fast
```

---

## 👨‍💻 Author

**Cheffe** - AI Engineer  
- GitHub: [@macyb27](https://github.com/macyb27)

---

## 📄 License

MIT License - see LICENSE file for details.
