"""
RL Environment - Gymnasium-compatible trading environment for RL agents.
Implements a realistic market simulation with position management.
"""

import logging
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

logger = logging.getLogger(__name__)


class TradingEnvironment(gym.Env):
    """
    Gymnasium-compatible trading environment for reinforcement learning.
    
    Observation space:
    - Market features (OHLCV + technical indicators)
    - Portfolio state (position, PnL, drawdown)
    - Time features (day of week, hour, etc.)
    
    Action space:
    - Continuous: position sizing from -1 (full short) to +1 (full long)
    - Or Discrete: {0: hold, 1: buy, 2: sell}
    
    Reward:
    - Risk-adjusted returns (Sharpe-like)
    - Penalizes excessive trading and drawdowns
    """

    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(
        self,
        df: pd.DataFrame,
        features: pd.DataFrame,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        max_position: float = 1.0,
        window_size: int = 50,
        reward_type: str = "sharpe",
        action_type: str = "continuous",
        render_mode: Optional[str] = None,
    ):
        """
        Args:
            df: OHLCV DataFrame
            features: Pre-computed feature DataFrame (aligned with df)
            initial_capital: Starting capital
            commission: Trading commission rate
            slippage: Slippage rate
            max_position: Maximum position size (fraction of capital)
            window_size: Number of past bars in observation
            reward_type: "sharpe", "pnl", "risk_adjusted"
            action_type: "continuous" or "discrete"
        """
        super().__init__()

        self.df = df.reset_index(drop=True)
        self.features = features.reset_index(drop=True)
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.max_position = max_position
        self.window_size = window_size
        self.reward_type = reward_type
        self.action_type = action_type
        self.render_mode = render_mode

        # Feature dimensions
        self.n_features = self.features.shape[1]
        self.n_portfolio_features = 5  # position, pnl, drawdown, cash_ratio, trade_count

        # Observation space: [window_size x features] + portfolio state
        obs_dim = self.window_size * self.n_features + self.n_portfolio_features
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        # Action space
        if action_type == "continuous":
            self.action_space = spaces.Box(
                low=-1.0, high=1.0, shape=(1,), dtype=np.float32
            )
        else:
            self.action_space = spaces.Discrete(3)  # hold, buy, sell

        # State variables
        self._reset_state()
        logger.info(
            f"TradingEnvironment created: {len(df)} bars, "
            f"{self.n_features} features, action={action_type}"
        )

    def _reset_state(self):
        """Reset internal state variables."""
        self.current_step = self.window_size
        self.capital = self.initial_capital
        self.position = 0.0  # Current position size (-1 to 1)
        self.position_price = 0.0
        self.portfolio_value = self.initial_capital
        self.peak_value = self.initial_capital
        self.total_trades = 0
        self.total_commission = 0.0
        self.returns_history = []
        self.equity_history = [self.initial_capital]
        self.done = False

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """Reset environment to initial state."""
        super().reset(seed=seed)
        self._reset_state()
        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(self, action: Any) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.

        Args:
            action: Trading action (position target)

        Returns:
            observation, reward, terminated, truncated, info
        """
        if self.done:
            return self._get_observation(), 0.0, True, False, self._get_info()

        # Parse action
        if self.action_type == "continuous":
            target_position = float(np.clip(action[0], -self.max_position, self.max_position))
        else:
            # Discrete: 0=hold, 1=buy, 2=sell
            if action == 1:
                target_position = self.max_position
            elif action == 2:
                target_position = -self.max_position
            else:
                target_position = self.position

        # Execute trade
        prev_value = self.portfolio_value
        self._execute_action(target_position)

        # Advance step
        self.current_step += 1

        # Update portfolio value
        self._update_portfolio_value()

        # Calculate reward
        reward = self._calculate_reward(prev_value)

        # Check termination
        terminated = self.current_step >= len(self.df) - 1
        truncated = self.portfolio_value <= self.initial_capital * 0.5  # 50% loss = stop

        if terminated or truncated:
            self.done = True

        obs = self._get_observation()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def _execute_action(self, target_position: float):
        """Execute a position change."""
        position_change = target_position - self.position

        if abs(position_change) < 0.01:
            return  # Skip tiny changes

        current_price = self.df.iloc[self.current_step]["close"]

        # Calculate trade cost
        trade_value = abs(position_change) * self.portfolio_value
        commission_cost = trade_value * self.commission
        slippage_cost = trade_value * self.slippage

        self.total_commission += commission_cost + slippage_cost
        self.capital -= commission_cost + slippage_cost

        # Update position
        self.position = target_position
        self.position_price = current_price
        self.total_trades += 1

    def _update_portfolio_value(self):
        """Update portfolio value based on current position and price."""
        if self.current_step >= len(self.df):
            return

        current_price = self.df.iloc[self.current_step]["close"]
        prev_price = self.df.iloc[self.current_step - 1]["close"]

        # PnL from position
        if self.position != 0 and prev_price > 0:
            price_return = (current_price - prev_price) / prev_price
            position_pnl = self.position * price_return * self.portfolio_value
            self.portfolio_value += position_pnl

        # Track returns
        if len(self.equity_history) > 0:
            ret = (self.portfolio_value - self.equity_history[-1]) / self.equity_history[-1]
            self.returns_history.append(ret)

        self.equity_history.append(self.portfolio_value)
        self.peak_value = max(self.peak_value, self.portfolio_value)

    def _calculate_reward(self, prev_value: float) -> float:
        """Calculate step reward."""
        if prev_value == 0:
            return 0.0

        step_return = (self.portfolio_value - prev_value) / prev_value

        if self.reward_type == "pnl":
            return step_return * 100  # Scale for learning

        elif self.reward_type == "sharpe":
            # Rolling Sharpe-like reward
            if len(self.returns_history) < 10:
                return step_return * 100

            recent_returns = np.array(self.returns_history[-20:])
            mean_ret = np.mean(recent_returns)
            std_ret = np.std(recent_returns)
            sharpe = mean_ret / std_ret if std_ret > 0 else 0
            return sharpe

        elif self.reward_type == "risk_adjusted":
            # Penalize drawdowns and excessive trading
            drawdown = (self.portfolio_value - self.peak_value) / self.peak_value
            trade_penalty = -0.001 if abs(self.position - (self.position)) > 0.01 else 0

            return step_return * 100 + drawdown * 10 + trade_penalty

        return step_return * 100

    def _get_observation(self) -> np.ndarray:
        """Construct observation vector."""
        # Market features window
        start = max(0, self.current_step - self.window_size)
        end = self.current_step

        feature_window = self.features.iloc[start:end].values
        if len(feature_window) < self.window_size:
            padding = np.zeros((self.window_size - len(feature_window), self.n_features))
            feature_window = np.vstack([padding, feature_window])

        market_obs = feature_window.flatten()

        # Portfolio state
        drawdown = (
            (self.portfolio_value - self.peak_value) / self.peak_value
            if self.peak_value > 0 else 0
        )
        pnl_pct = (
            (self.portfolio_value - self.initial_capital) / self.initial_capital
        )

        portfolio_obs = np.array([
            self.position,
            pnl_pct,
            drawdown,
            self.capital / self.portfolio_value if self.portfolio_value > 0 else 1,
            self.total_trades / max(self.current_step, 1),
        ])

        obs = np.concatenate([market_obs, portfolio_obs]).astype(np.float32)

        # Replace NaN/Inf
        obs = np.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)

        return obs

    def _get_info(self) -> Dict:
        """Get current environment info."""
        return {
            "step": self.current_step,
            "portfolio_value": self.portfolio_value,
            "position": self.position,
            "total_trades": self.total_trades,
            "total_commission": self.total_commission,
            "pnl_pct": (self.portfolio_value - self.initial_capital) / self.initial_capital,
            "max_drawdown": (self.portfolio_value - self.peak_value) / self.peak_value if self.peak_value > 0 else 0,
        }

    def render(self):
        """Render current state."""
        if self.render_mode == "human":
            info = self._get_info()
            print(
                f"Step {info['step']}: "
                f"Value=${info['portfolio_value']:,.2f} "
                f"Pos={info['position']:.2f} "
                f"PnL={info['pnl_pct']:.2%} "
                f"DD={info['max_drawdown']:.2%} "
                f"Trades={info['total_trades']}"
            )
