"""
Aether Trader - Airflow DAG for Trading Pipeline Orchestration.
Schedules and orchestrates the complete trading pipeline.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "aether-trader",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}


# ============================================================
# Main Trading Pipeline DAG
# ============================================================

with DAG(
    dag_id="aether_trading_pipeline",
    default_args=default_args,
    description="Main trading pipeline - data ingestion to execution",
    schedule_interval="0 */4 * * *",  # Every 4 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["trading", "pipeline", "production"],
) as trading_dag:

    load_data = BashOperator(
        task_id="load_market_data",
        bash_command='curl -X POST http://backend:8000/api/v1/data/load -H "Content-Type: application/json" -d \'{"symbols": ["BTC/USDT", "ETH/USDT"], "timeframe": "1h"}\'',
    )

    generate_strategies = BashOperator(
        task_id="generate_strategies",
        bash_command='curl -X POST http://backend:8000/api/v1/strategies/generate -H "Content-Type: application/json" -d \'{"n_variants": 20}\'',
    )

    run_backtest = BashOperator(
        task_id="run_backtests",
        bash_command='curl -X POST http://backend:8000/api/v1/backtest/run -H "Content-Type: application/json" -d \'{"strategy_name": "auto", "symbol": "BTC/USDT"}\'',
    )

    optimize_portfolio = BashOperator(
        task_id="optimize_portfolio",
        bash_command='curl -X POST http://backend:8000/api/v1/portfolio/optimize -H "Content-Type: application/json" -d \'{"method": "max_sharpe"}\'',
    )

    check_risk = BashOperator(
        task_id="check_risk",
        bash_command="curl http://backend:8000/api/v1/risk/report",
    )

    load_data >> generate_strategies >> run_backtest >> optimize_portfolio >> check_risk


# ============================================================
# RL Training DAG
# ============================================================

with DAG(
    dag_id="aether_rl_training",
    default_args=default_args,
    description="Reinforcement learning model training pipeline",
    schedule_interval="0 2 * * 0",  # Weekly on Sunday at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ai", "training", "rl"],
) as rl_dag:

    train_rl = BashOperator(
        task_id="train_rl_agent",
        bash_command='curl -X POST http://backend:8000/api/v1/ai/train -H "Content-Type: application/json" -d \'{"algorithm": "ppo", "total_timesteps": 500000}\'',
        execution_timeout=timedelta(hours=6),
    )

    evaluate_rl = BashOperator(
        task_id="evaluate_rl_agent",
        bash_command="curl http://backend:8000/api/v1/ai/models",
    )

    train_rl >> evaluate_rl


# ============================================================
# Genetic Optimization DAG
# ============================================================

with DAG(
    dag_id="aether_genetic_optimization",
    default_args=default_args,
    description="Genetic algorithm strategy optimization",
    schedule_interval="0 3 * * 6",  # Weekly on Saturday at 3 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["optimization", "genetic"],
) as ga_dag:

    run_optimization = BashOperator(
        task_id="run_genetic_optimization",
        bash_command='curl -X POST http://backend:8000/api/v1/optimization/run -H "Content-Type: application/json" -d \'{"population_size": 200, "generations": 100}\'',
        execution_timeout=timedelta(hours=4),
    )

    check_results = BashOperator(
        task_id="check_optimization_results",
        bash_command="curl http://backend:8000/api/v1/optimization/status",
    )

    run_optimization >> check_results
