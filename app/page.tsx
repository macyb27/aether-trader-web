'use client'

import Link from 'next/link'
import { ArrowRight, BarChart3, Brain, Zap, Shield, TrendingUp, Cpu } from 'lucide-react'

export default function Home() {
  return (
    <div className="w-full">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-slate-950/80 backdrop-blur-md border-b border-slate-800 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Cpu className="w-8 h-8 text-cyan-500" />
            <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Aether Trader Pro
            </span>
          </div>
          <div className="flex gap-4">
            <Link href="/auth/login" className="px-4 py-2 text-slate-300 hover:text-white transition">
              Login
            </Link>
            <Link href="/auth/signup" className="btn-primary text-sm">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="mb-8 inline-block">
            <span className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-cyan-300 text-sm font-medium">
              🚀 AI-Powered Trading Platform
            </span>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            Trade with{' '}
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
              Autonomous AI
            </span>
          </h1>
          
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Multi-agent system with self-learning AI, genetic algorithms, and real-time market analysis. 
            Start with paper trading, validate your strategies, then go live.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link href="/dashboard" className="btn-primary flex items-center justify-center gap-2">
              Launch Dashboard <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="btn-secondary">
              Watch Demo
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 sm:gap-8 mb-16">
            <div className="card">
              <div className="text-3xl font-bold text-cyan-400 mb-2">€10K</div>
              <div className="text-sm text-slate-400">Paper Trading Capital</div>
            </div>
            <div className="card">
              <div className="text-3xl font-bold text-cyan-400 mb-2">5</div>
              <div className="text-sm text-slate-400">AI Agents</div>
            </div>
            <div className="card">
              <div className="text-3xl font-bold text-cyan-400 mb-2">2+Y</div>
              <div className="text-sm text-slate-400">Historical Data</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">Powerful Features</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <Brain className="w-6 h-6 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold">Self-Learning AI</h3>
              </div>
              <p className="text-slate-400">
                Transfer Learning with TensorFlow.js for pattern recognition and price prediction
              </p>
            </div>

            {/* Feature 2 */}
            <div className="card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <Zap className="w-6 h-6 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold">Genetic Algorithms</h3>
              </div>
              <p className="text-slate-400">
                Automatic strategy evolution and optimization through fitness-based selection
              </p>
            </div>

            {/* Feature 3 */}
            <div className="card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold">Paper Trading</h3>
              </div>
              <p className="text-slate-400">
                Risk-free testing with €10,000 virtual capital and real market data
              </p>
            </div>

            {/* Feature 4 */}
            <div className="card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <Cpu className="w-6 h-6 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold">Multi-Agent System</h3>
              </div>
              <p className="text-slate-400">
                QA Bot, RL Developer, Market Intel, and Orchestrator working together
              </p>
            </div>

            {/* Feature 5 */}
            <div className="card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <Shield className="w-6 h-6 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold">Risk Management</h3>
              </div>
              <p className="text-slate-400">
                Strict guardrails: 1% max loss, 5% position size, Sharpe ≥1.5
              </p>
            </div>

            {/* Feature 6 */}
            <div className="card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold">Real-Time Analytics</h3>
              </div>
              <p className="text-slate-400">
                Live market data from Alpaca & Finnhub with sentiment analysis
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to Trade Smarter?</h2>
          <p className="text-xl text-slate-300 mb-8">
            Join thousands of traders using AI-powered strategies
          </p>
          <Link href="/auth/signup" className="btn-primary inline-flex items-center gap-2">
            Start Free Trial <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Features</a></li>
                <li><a href="#" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition">Documentation</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms</a></li>
                <li><a href="#" className="hover:text-white transition">Disclaimer</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Follow</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Twitter</a></li>
                <li><a href="#" className="hover:text-white transition">GitHub</a></li>
                <li><a href="#" className="hover:text-white transition">Discord</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-8 text-center text-slate-400 text-sm">
            <p>&copy; 2026 Aether Trader Pro. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
