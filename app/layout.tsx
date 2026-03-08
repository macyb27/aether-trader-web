import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Aether Trader Pro - AI-Powered Trading Platform',
  description: 'Autonomous trading with paper trading, multi-agent AI system, and real-time market analysis',
  keywords: 'trading, AI, machine learning, paper trading, algorithmic trading',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <div className="min-h-screen bg-gradient-dark">
        {children}
      </div>
    </>
  )
}
