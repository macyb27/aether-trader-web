"use client";

import { useEffect, useState } from "react";

interface SystemStatus {
  status: string;
  modules: Record<string, string>;
  timestamp: string;
}

interface PortfolioData {
  total_value: number;
  cash: number;
  pnl: number;
  pnl_pct: number;
  total_trades: number;
}

export default function AnalyticsDashboard() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error("Failed to fetch status:", err);
    }
  };

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "portfolio", label: "Portfolio" },
    { id: "strategies", label: "Strategies" },
    { id: "backtesting", label: "Backtesting" },
    { id: "risk", label: "Risk" },
    { id: "ai", label: "AI/RL" },
    { id: "optimization", label: "Optimization" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Aether Trader</h1>
              <p className="text-xs text-gray-400">AI Quantitative Research Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${status?.status === "running" ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
              <span className="text-sm text-gray-400">
                {status?.status === "running" ? "System Online" : "Connecting..."}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="border-b border-gray-800 bg-gray-900/30">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "text-cyan-400 border-b-2 border-cyan-400"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === "overview" && <OverviewPanel status={status} />}
        {activeTab === "portfolio" && <PortfolioPanel />}
        {activeTab === "strategies" && <StrategiesPanel />}
        {activeTab === "backtesting" && <BacktestingPanel />}
        {activeTab === "risk" && <RiskPanel />}
        {activeTab === "ai" && <AIPanel />}
        {activeTab === "optimization" && <OptimizationPanel />}
      </main>
    </div>
  );
}

function MetricCard({ title, value, subtitle, trend }: {
  title: string;
  value: string;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${
        trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-white"
      }`}>
        {value}
      </p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

function OverviewPanel({ status }: { status: SystemStatus | null }) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">System Overview</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Portfolio Value" value="$100,000.00" subtitle="Initial Capital" trend="neutral" />
        <MetricCard title="Total PnL" value="$0.00" subtitle="0.00%" trend="neutral" />
        <MetricCard title="Active Strategies" value="0" subtitle="Awaiting generation" />
        <MetricCard title="Total Trades" value="0" subtitle="Paper trading" />
      </div>

      {/* Module Status */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-4">Module Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {status?.modules && Object.entries(status.modules).map(([name, state]) => (
            <div key={name} className="flex items-center gap-2 p-2 rounded-lg bg-gray-800/50">
              <div className={`w-2 h-2 rounded-full ${state === "ready" ? "bg-green-500" : "bg-yellow-500"}`} />
              <span className="text-sm text-gray-300 capitalize">{name.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-4">Platform Architecture</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="space-y-2">
            <h4 className="font-medium text-cyan-400">Data Layer</h4>
            <ul className="space-y-1 text-gray-400">
              <li>Market Data Ingestion (CCXT + yfinance)</li>
              <li>PostgreSQL Storage</li>
              <li>Redis Cache</li>
              <li>Real-time WebSocket Streams</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-cyan-400">Intelligence Layer</h4>
            <ul className="space-y-1 text-gray-400">
              <li>Feature Engineering Pipeline</li>
              <li>Alpha Research Lab</li>
              <li>Strategy Generator</li>
              <li>Genetic Optimizer</li>
              <li>RL Trading Agent (SB3)</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-cyan-400">Execution Layer</h4>
            <ul className="space-y-1 text-gray-400">
              <li>Backtesting Engine (vectorbt)</li>
              <li>Risk Management</li>
              <li>Portfolio Optimizer</li>
              <li>Paper Trading Execution</li>
              <li>Monitoring Dashboard</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function PortfolioPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Portfolio Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total Value" value="$100,000.00" trend="neutral" />
        <MetricCard title="Cash" value="$100,000.00" />
        <MetricCard title="Positions" value="0" />
        <MetricCard title="Drawdown" value="0.00%" trend="neutral" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 h-64 flex items-center justify-center">
        <p className="text-gray-500">Equity curve will appear here after pipeline execution</p>
      </div>
    </div>
  );
}

function StrategiesPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Strategy Management</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Registered Templates" value="4" subtitle="Momentum, MeanReversion, ML, Breakout" />
        <MetricCard title="Generated Variants" value="0" subtitle="Awaiting generation" />
        <MetricCard title="Active Strategies" value="0" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Strategy Templates</h3>
        <div className="space-y-2">
          {["Momentum", "Mean Reversion", "ML-Based", "Breakout"].map((name) => (
            <div key={name} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
              <span className="text-gray-300">{name}</span>
              <span className="text-xs px-2 py-1 rounded bg-cyan-900/50 text-cyan-400">Available</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BacktestingPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Backtesting Engine</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Total Backtests" value="0" />
        <MetricCard title="Best Sharpe" value="--" />
        <MetricCard title="Best Return" value="--" />
        <MetricCard title="Avg Win Rate" value="--" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <p className="text-gray-500">Run backtests via the API or pipeline to see results here.</p>
        <p className="text-sm text-gray-600 mt-2">Supports: Walk-forward analysis, Monte Carlo simulation, Multi-asset backtesting</p>
      </div>
    </div>
  );
}

function RiskPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Risk Management</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Risk Score" value="0/100" subtitle="Low risk" trend="neutral" />
        <MetricCard title="Max Position" value="10%" />
        <MetricCard title="Max Drawdown Limit" value="10%" />
        <MetricCard title="Circuit Breaker" value="Inactive" trend="neutral" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Risk Limits</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between p-2 bg-gray-800/50 rounded">
            <span className="text-gray-400">Max Position Size</span>
            <span className="text-white">10%</span>
          </div>
          <div className="flex justify-between p-2 bg-gray-800/50 rounded">
            <span className="text-gray-400">Max Leverage</span>
            <span className="text-white">1.0x</span>
          </div>
          <div className="flex justify-between p-2 bg-gray-800/50 rounded">
            <span className="text-gray-400">Max Daily Loss</span>
            <span className="text-white">2%</span>
          </div>
          <div className="flex justify-between p-2 bg-gray-800/50 rounded">
            <span className="text-gray-400">VaR 95% Limit</span>
            <span className="text-white">3%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AIPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">AI / Reinforcement Learning</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Algorithm" value="PPO" subtitle="Proximal Policy Optimization" />
        <MetricCard title="Training Runs" value="0" />
        <MetricCard title="Models Saved" value="0" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Supported Algorithms</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {["PPO", "A2C", "SAC", "TD3", "DQN"].map((algo) => (
            <div key={algo} className="text-center p-3 bg-gray-800/50 rounded-lg">
              <span className="text-cyan-400 font-mono font-bold">{algo}</span>
            </div>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-4">
          Powered by stable-baselines3 with Gymnasium-compatible trading environment.
          Supports continuous and discrete action spaces.
        </p>
      </div>
    </div>
  );
}

function OptimizationPanel() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Genetic Optimization</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Population Size" value="100" />
        <MetricCard title="Generations" value="50" />
        <MetricCard title="Mutation Rate" value="10%" />
        <MetricCard title="Crossover Rate" value="80%" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Optimization Features</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            "Tournament Selection",
            "Arithmetic Crossover",
            "Adaptive Mutation",
            "Elitism Preservation",
            "Multi-Objective (NSGA-II)",
            "Early Stopping",
            "Convergence Tracking",
            "Parameter Space Search",
          ].map((feature) => (
            <div key={feature} className="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
              <span className="text-gray-300">{feature}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
