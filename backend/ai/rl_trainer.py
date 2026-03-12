"""
RL Trainer - Training pipeline for reinforcement learning trading agents.
Uses stable-baselines3 for state-of-the-art RL algorithms.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RLTrainer:
    """
    Reinforcement Learning trainer for trading agents.
    
    Supported algorithms (via stable-baselines3):
    - PPO (Proximal Policy Optimization) - default, best for continuous actions
    - A2C (Advantage Actor-Critic) - fast training
    - SAC (Soft Actor-Critic) - sample efficient, continuous only
    - TD3 (Twin Delayed DDPG) - continuous actions, deterministic
    - DQN (Deep Q-Network) - discrete actions only
    
    Features:
    - Automatic hyperparameter tuning
    - Curriculum learning
    - Multi-environment training
    - Model checkpointing
    - TensorBoard logging
    - Walk-forward validation
    """

    ALGORITHM_MAP = {
        "ppo": "PPO",
        "a2c": "A2C",
        "sac": "SAC",
        "td3": "TD3",
        "dqn": "DQN",
    }

    DEFAULT_HYPERPARAMS = {
        "ppo": {
            "learning_rate": 3e-4,
            "n_steps": 2048,
            "batch_size": 64,
            "n_epochs": 10,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "clip_range": 0.2,
            "ent_coef": 0.01,
            "vf_coef": 0.5,
            "max_grad_norm": 0.5,
        },
        "a2c": {
            "learning_rate": 7e-4,
            "n_steps": 5,
            "gamma": 0.99,
            "gae_lambda": 1.0,
            "ent_coef": 0.01,
            "vf_coef": 0.25,
            "max_grad_norm": 0.5,
        },
        "sac": {
            "learning_rate": 3e-4,
            "buffer_size": 1_000_000,
            "batch_size": 256,
            "gamma": 0.99,
            "tau": 0.005,
            "ent_coef": "auto",
            "learning_starts": 1000,
        },
        "td3": {
            "learning_rate": 1e-3,
            "buffer_size": 1_000_000,
            "batch_size": 100,
            "gamma": 0.99,
            "tau": 0.005,
            "policy_delay": 2,
            "learning_starts": 1000,
        },
        "dqn": {
            "learning_rate": 1e-4,
            "buffer_size": 1_000_000,
            "batch_size": 32,
            "gamma": 0.99,
            "exploration_fraction": 0.1,
            "exploration_final_eps": 0.05,
            "learning_starts": 1000,
        },
    }

    def __init__(
        self,
        algorithm: str = "ppo",
        model_dir: str = "models/rl",
        log_dir: str = "logs/rl",
        device: str = "auto",
    ):
        self.algorithm = algorithm.lower()
        self.model_dir = Path(model_dir)
        self.log_dir = Path(log_dir)
        self.device = device
        self.model = None
        self._training_history: List[Dict] = []

        # Create directories
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"RLTrainer initialized: algorithm={algorithm}, device={device}")

    def train(
        self,
        env,
        total_timesteps: int = 100_000,
        hyperparams: Optional[Dict] = None,
        eval_env=None,
        eval_freq: int = 10_000,
        n_eval_episodes: int = 5,
        save_freq: int = 25_000,
        tb_log_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Train an RL agent.

        Args:
            env: Training environment (Gymnasium compatible)
            total_timesteps: Total training steps
            hyperparams: Algorithm hyperparameters (None = use defaults)
            eval_env: Evaluation environment
            eval_freq: Evaluation frequency
            n_eval_episodes: Number of evaluation episodes
            save_freq: Checkpoint save frequency
            tb_log_name: TensorBoard log name

        Returns:
            Training results dictionary
        """
        try:
            from stable_baselines3 import PPO, A2C, SAC, TD3, DQN
            from stable_baselines3.common.callbacks import (
                EvalCallback, CheckpointCallback, CallbackList,
            )
            from stable_baselines3.common.monitor import Monitor
        except ImportError:
            logger.error("stable-baselines3 not installed. Install with: pip install stable-baselines3")
            return {"error": "stable-baselines3 not installed"}

        # Select algorithm
        algo_map = {"ppo": PPO, "a2c": A2C, "sac": SAC, "td3": TD3, "dqn": DQN}
        algo_class = algo_map.get(self.algorithm)

        if algo_class is None:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")

        # Merge hyperparameters
        params = self.DEFAULT_HYPERPARAMS.get(self.algorithm, {}).copy()
        if hyperparams:
            params.update(hyperparams)

        # Create model
        policy = "MlpPolicy"
        self.model = algo_class(
            policy,
            env,
            verbose=1,
            tensorboard_log=str(self.log_dir),
            device=self.device,
            **params,
        )

        # Setup callbacks
        callbacks = []

        if eval_env:
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=str(self.model_dir / "best"),
                log_path=str(self.log_dir / "eval"),
                eval_freq=eval_freq,
                n_eval_episodes=n_eval_episodes,
                deterministic=True,
            )
            callbacks.append(eval_callback)

        checkpoint_callback = CheckpointCallback(
            save_freq=save_freq,
            save_path=str(self.model_dir / "checkpoints"),
            name_prefix=f"{self.algorithm}_trading",
        )
        callbacks.append(checkpoint_callback)

        # Train
        logger.info(
            f"Starting training: {self.algorithm}, "
            f"{total_timesteps} timesteps, params={params}"
        )

        start_time = datetime.utcnow()
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=CallbackList(callbacks),
            tb_log_name=tb_log_name or f"{self.algorithm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
        training_time = (datetime.utcnow() - start_time).total_seconds()

        # Save final model
        model_path = self.model_dir / f"{self.algorithm}_final"
        self.model.save(str(model_path))

        result = {
            "algorithm": self.algorithm,
            "total_timesteps": total_timesteps,
            "training_time_seconds": training_time,
            "model_path": str(model_path),
            "hyperparams": params,
        }

        self._training_history.append(result)
        logger.info(f"Training completed in {training_time:.1f}s")

        return result

    def predict(
        self,
        observation: np.ndarray,
        deterministic: bool = True,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Get action prediction from trained model."""
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")
        return self.model.predict(observation, deterministic=deterministic)

    def evaluate(
        self,
        env,
        n_episodes: int = 10,
        deterministic: bool = True,
    ) -> Dict[str, float]:
        """
        Evaluate the trained agent.

        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("No model loaded")

        episode_rewards = []
        episode_lengths = []
        episode_infos = []

        for ep in range(n_episodes):
            obs, info = env.reset()
            done = False
            total_reward = 0
            steps = 0

            while not done:
                action, _ = self.model.predict(obs, deterministic=deterministic)
                obs, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                steps += 1
                done = terminated or truncated

            episode_rewards.append(total_reward)
            episode_lengths.append(steps)
            episode_infos.append(info)

        rewards = np.array(episode_rewards)

        # Aggregate info metrics
        avg_pnl = np.mean([i.get("pnl_pct", 0) for i in episode_infos])
        avg_trades = np.mean([i.get("total_trades", 0) for i in episode_infos])
        avg_dd = np.mean([i.get("max_drawdown", 0) for i in episode_infos])

        return {
            "mean_reward": float(rewards.mean()),
            "std_reward": float(rewards.std()),
            "min_reward": float(rewards.min()),
            "max_reward": float(rewards.max()),
            "mean_episode_length": float(np.mean(episode_lengths)),
            "avg_pnl_pct": avg_pnl,
            "avg_trades": avg_trades,
            "avg_max_drawdown": avg_dd,
            "n_episodes": n_episodes,
        }

    def load_model(self, path: str) -> None:
        """Load a saved model."""
        try:
            from stable_baselines3 import PPO, A2C, SAC, TD3, DQN

            algo_map = {"ppo": PPO, "a2c": A2C, "sac": SAC, "td3": TD3, "dqn": DQN}
            algo_class = algo_map.get(self.algorithm)

            if algo_class is None:
                raise ValueError(f"Unknown algorithm: {self.algorithm}")

            self.model = algo_class.load(path, device=self.device)
            logger.info(f"Model loaded from {path}")

        except ImportError:
            logger.error("stable-baselines3 not installed")

    def hyperparameter_search(
        self,
        env_factory: Callable,
        n_trials: int = 20,
        timesteps_per_trial: int = 50_000,
    ) -> Dict[str, Any]:
        """
        Automated hyperparameter search using random search.

        Args:
            env_factory: Function that creates a new environment
            n_trials: Number of trials
            timesteps_per_trial: Training steps per trial

        Returns:
            Best hyperparameters and results
        """
        best_reward = float("-inf")
        best_params = None
        results = []

        for trial in range(n_trials):
            # Sample random hyperparameters
            params = self._sample_hyperparams()

            try:
                env = env_factory()
                eval_env = env_factory()

                # Train with sampled params
                self.train(
                    env=env,
                    total_timesteps=timesteps_per_trial,
                    hyperparams=params,
                )

                # Evaluate
                eval_result = self.evaluate(eval_env, n_episodes=5)
                mean_reward = eval_result["mean_reward"]

                results.append({
                    "trial": trial,
                    "params": params,
                    "mean_reward": mean_reward,
                    "eval_result": eval_result,
                })

                if mean_reward > best_reward:
                    best_reward = mean_reward
                    best_params = params.copy()

                logger.info(
                    f"Trial {trial}/{n_trials}: reward={mean_reward:.4f} "
                    f"(best={best_reward:.4f})"
                )

            except Exception as e:
                logger.error(f"Trial {trial} failed: {e}")

        return {
            "best_params": best_params,
            "best_reward": best_reward,
            "all_results": results,
        }

    def _sample_hyperparams(self) -> Dict:
        """Sample random hyperparameters for search."""
        if self.algorithm == "ppo":
            return {
                "learning_rate": float(10 ** np.random.uniform(-5, -3)),
                "n_steps": int(np.random.choice([256, 512, 1024, 2048, 4096])),
                "batch_size": int(np.random.choice([32, 64, 128, 256])),
                "n_epochs": int(np.random.choice([3, 5, 10, 20])),
                "gamma": float(np.random.uniform(0.95, 0.999)),
                "gae_lambda": float(np.random.uniform(0.9, 1.0)),
                "clip_range": float(np.random.uniform(0.1, 0.3)),
                "ent_coef": float(10 ** np.random.uniform(-4, -1)),
            }
        elif self.algorithm == "sac":
            return {
                "learning_rate": float(10 ** np.random.uniform(-5, -3)),
                "buffer_size": int(np.random.choice([100_000, 500_000, 1_000_000])),
                "batch_size": int(np.random.choice([64, 128, 256, 512])),
                "gamma": float(np.random.uniform(0.95, 0.999)),
                "tau": float(np.random.uniform(0.001, 0.02)),
            }
        else:
            return self.DEFAULT_HYPERPARAMS.get(self.algorithm, {})

    def get_training_history(self) -> List[Dict]:
        """Get history of all training runs."""
        return self._training_history
