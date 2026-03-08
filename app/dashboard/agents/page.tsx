'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Brain, Shield, TrendingUp, Zap, ArrowLeft, Activity } from 'lucide-react'

interface Agent {
  id: string
  name: string
  role: string
  status: 'active' | 'idle' | 'training'
  performance: number
  lastUpdate: string
  icon: React.ReactNode
}

export default function AgentsPage() {
  const [agents] = useState<Agent[]>([
    {
      id: 'qa-bot',
      name: 'QA Bot',
      role: 'Risk Management',
      status: 'active',
      performance: 98,
      lastUpdate: '2 minutes ago',
      icon: <Shield className="w-6 h-6" />,
    },
    {
      id: 'rl-developer',
      name: 'RL Developer',
      role: 'Strategy Optimization',
      status: 'training',
      performance: 85,
      lastUpdate: '5 minutes ago',
      icon: <Brain className="w-6 h-6" />,
    },
    {
      id: 'market-intel',
      name: 'Market Intel',
      role: 'Sentiment Analysis',
      status: 'active',
      performance: 92,
      lastUpdate: 'Just now',
      icon: <TrendingUp className="w-6 h-6" />,
    },
    {
      id: 'orchestrator',
      name: 'Orchestrator',
      role: 'Workflow Manager',
      status: 'active',
      performance: 100,
      lastUpdate: '1 minute ago',
      icon: <Zap className="w-6 h-6" />,
    },
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/20 text-green-300'
      case 'training':
        return 'bg-yellow-500/20 text-yellow-300'
      case 'idle':
        return 'bg-slate-500/20 text-slate-300'
      default:
        return 'bg-slate-500/20 text-slate-300'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-dark">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Link href="/dashboard" className="p-2 hover:bg-slate-800 rounded-lg transition">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <h1 className="text-2xl font-bold">Multi-Agent System</h1>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview */}
        <div className="card mb-8">
          <h2 className="text-xl font-bold mb-4">System Overview</h2>
          <div className="grid md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-800/50 rounded-lg">
              <p className="text-slate-400 text-sm mb-2">Active Agents</p>
              <p className="text-3xl font-bold text-cyan-400">3/4</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg">
              <p className="text-slate-400 text-sm mb-2">Avg Performance</p>
              <p className="text-3xl font-bold text-green-400">93.75%</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg">
              <p className="text-slate-400 text-sm mb-2">Trades Executed</p>
              <p className="text-3xl font-bold text-cyan-400">12</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg">
              <p className="text-slate-400 text-sm mb-2">Strategies Active</p>
              <p className="text-3xl font-bold text-cyan-400">5</p>
            </div>
          </div>
        </div>

        {/* Agents Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {agents.map((agent) => (
            <div key={agent.id} className="card-hover cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-cyan-500/20 rounded-lg text-cyan-400">
                    {agent.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{agent.name}</h3>
                    <p className="text-sm text-slate-400">{agent.role}</p>
                  </div>
                </div>
                <span className={`badge ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </span>
              </div>

              <div className="space-y-3">
                {/* Performance */}
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-slate-400">Performance</span>
                    <span className="text-sm font-medium">{agent.performance}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${agent.performance}%` }}
                    ></div>
                  </div>
                </div>

                {/* Last Update */}
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Activity className="w-4 h-4" />
                  <span>Updated {agent.lastUpdate}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 pt-4 border-t border-slate-800">
                <button className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition">
                  View Details →
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Workflow Pipeline */}
        <div className="card">
          <h2 className="text-xl font-bold mb-6">Trading Workflow Pipeline</h2>
          <div className="space-y-4">
            {[
              { step: 1, name: 'Hypothesis', status: 'completed', description: 'AI generates trading hypothesis' },
              { step: 2, name: 'Backtest', status: 'completed', description: 'Validate on historical data' },
              { step: 3, name: 'Paper Trading', status: 'active', description: 'Test with virtual capital' },
              { step: 4, name: 'Validation', status: 'pending', description: 'Monitor performance metrics' },
              { step: 5, name: 'Live Trading', status: 'pending', description: 'Deploy with real capital' },
            ].map((phase, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  phase.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  phase.status === 'active' ? 'bg-cyan-500/20 text-cyan-400' :
                  'bg-slate-700 text-slate-400'
                }`}>
                  {phase.step}
                </div>
                <div className="flex-1">
                  <p className="font-medium">{phase.name}</p>
                  <p className="text-sm text-slate-400">{phase.description}</p>
                </div>
                <span className={`badge ${
                  phase.status === 'completed' ? 'badge-success' :
                  phase.status === 'active' ? 'badge-info' :
                  'bg-slate-700/50 text-slate-400'
                }`}>
                  {phase.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Collaboration */}
        <div className="mt-8 card">
          <h2 className="text-xl font-bold mb-6">Agent Collaboration</h2>
          <div className="space-y-4">
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="font-medium mb-2">🤖 Orchestrator → RL Developer</p>
              <p className="text-sm text-slate-400">Sends market data and requests strategy optimization</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="font-medium mb-2">🧠 RL Developer → QA Bot</p>
              <p className="text-sm text-slate-400">Submits optimized strategies for risk validation</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="font-medium mb-2">✅ QA Bot → Market Intel</p>
              <p className="text-sm text-slate-400">Approves trades and requests sentiment analysis</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="font-medium mb-2">📊 Market Intel → Orchestrator</p>
              <p className="text-sm text-slate-400">Provides sentiment scores and market insights</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
