'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { BarChart3, TrendingUp, Wallet, Zap, LogOut, Menu } from 'lucide-react'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [portfolio] = useState({
    balance: 10000,
    invested: 2500,
    profit: 450.50,
    trades: 12,
  })
  const [loading, setLoading] = useState(true)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/auth/login')
      return
    }

    // Simulate loading user data
    setTimeout(() => {
      setUser({ name: 'Demo User', email: 'demo@aether.com' })
      setLoading(false)
    }, 500)
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-dark">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-700 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-dark">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Zap className="w-6 h-6 text-cyan-500" />
            <span className="text-lg font-bold text-cyan-400">Aether Trader</span>
          </div>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/dashboard/trading" className="text-slate-300 hover:text-white transition">
              Trading
            </Link>
            <Link href="/dashboard/agents" className="text-slate-300 hover:text-white transition">
              Agents
            </Link>
            <Link href="/dashboard/backtest" className="text-slate-300 hover:text-white transition">
              Backtest
            </Link>
            <Link href="/dashboard/settings" className="text-slate-300 hover:text-white transition">
              Settings
            </Link>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-white transition"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 hover:bg-slate-800 rounded-lg transition"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-slate-800 p-4 space-y-2">
            <Link href="/dashboard/trading" className="block px-4 py-2 text-slate-300 hover:bg-slate-800 rounded">
              Trading
            </Link>
            <Link href="/dashboard/agents" className="block px-4 py-2 text-slate-300 hover:bg-slate-800 rounded">
              Agents
            </Link>
            <Link href="/dashboard/backtest" className="block px-4 py-2 text-slate-300 hover:bg-slate-800 rounded">
              Backtest
            </Link>
            <Link href="/dashboard/settings" className="block px-4 py-2 text-slate-300 hover:bg-slate-800 rounded">
              Settings
            </Link>
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-slate-300 hover:bg-slate-800 rounded"
            >
              Logout
            </button>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Welcome, {user?.name}!</h1>
          <p className="text-slate-400">Your AI trading dashboard</p>
        </div>

        {/* Portfolio Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          {/* Balance */}
          <div className="card-hover">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 text-sm font-medium">Portfolio Balance</h3>
              <Wallet className="w-5 h-5 text-cyan-500" />
            </div>
            <div className="text-3xl font-bold mb-2">€{portfolio.balance.toFixed(2)}</div>
            <p className="text-xs text-slate-500">Paper trading capital</p>
          </div>

          {/* Invested */}
          <div className="card-hover">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 text-sm font-medium">Invested</h3>
              <BarChart3 className="w-5 h-5 text-cyan-500" />
            </div>
            <div className="text-3xl font-bold mb-2">€{portfolio.invested.toFixed(2)}</div>
            <p className="text-xs text-slate-500">In active positions</p>
          </div>

          {/* Profit */}
          <div className="card-hover">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 text-sm font-medium">Profit</h3>
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-3xl font-bold text-green-400 mb-2">+€{portfolio.profit.toFixed(2)}</div>
            <p className="text-xs text-slate-500">+4.5% return</p>
          </div>

          {/* Trades */}
          <div className="card-hover">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 text-sm font-medium">Trades</h3>
              <Zap className="w-5 h-5 text-cyan-500" />
            </div>
            <div className="text-3xl font-bold mb-2">{portfolio.trades}</div>
            <p className="text-xs text-slate-500">Total executed</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link href="/dashboard/trading" className="card-hover hover:border-cyan-500/50 cursor-pointer">
            <h3 className="text-lg font-semibold mb-2">📊 Paper Trading</h3>
            <p className="text-slate-400 text-sm mb-4">Execute trades with virtual capital</p>
            <div className="text-cyan-400 text-sm font-medium">Start Trading →</div>
          </Link>

          <Link href="/dashboard/agents" className="card-hover hover:border-cyan-500/50 cursor-pointer">
            <h3 className="text-lg font-semibold mb-2">🤖 Multi-Agent System</h3>
            <p className="text-slate-400 text-sm mb-4">Monitor AI agents and strategies</p>
            <div className="text-cyan-400 text-sm font-medium">View Agents →</div>
          </Link>

          <Link href="/dashboard/backtest" className="card-hover hover:border-cyan-500/50 cursor-pointer">
            <h3 className="text-lg font-semibold mb-2">⚡ Backtesting</h3>
            <p className="text-slate-400 text-sm mb-4">Test strategies on historical data</p>
            <div className="text-cyan-400 text-sm font-medium">Backtest →</div>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {[
              { time: '2 hours ago', action: 'Bought 10 AAPL', price: '€1,250' },
              { time: '4 hours ago', action: 'Sold 5 MSFT', price: '€850' },
              { time: '1 day ago', action: 'Strategy optimization completed', price: 'Sharpe: 1.8' },
            ].map((item, i) => (
              <div key={i} className="flex justify-between items-center py-3 border-b border-slate-800 last:border-0">
                <div>
                  <p className="text-sm font-medium">{item.action}</p>
                  <p className="text-xs text-slate-500">{item.time}</p>
                </div>
                <p className="text-cyan-400 font-medium">{item.price}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
