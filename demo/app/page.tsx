'use client'

import { useState } from 'react'
import BeforeWfloDemo from '@/components/BeforeWfloDemo'
import AfterWfloDemo from '@/components/AfterWfloDemo'
import HITLDemo from '@/components/HITLDemo'
import MetricsComparison from '@/components/MetricsComparison'

export default function Home() {
  const [activeDemo, setActiveDemo] = useState<'before' | 'after' | 'hitl' | null>(null)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white">
                wflo
              </h1>
              <p className="text-purple-300 mt-1">
                AI Workflow Orchestration with Guardrails
              </p>
            </div>
            <a
              href="https://github.com/wflo-ai/wflo"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h2 className="text-5xl font-bold text-white mb-6">
          The Problem with Unguarded AI Workflows
        </h2>
        <p className="text-xl text-purple-200 max-w-3xl mx-auto mb-12">
          AI agents can loop infinitely, rack up costs, or perform destructive actions.
          Watch how <span className="text-purple-400 font-semibold">wflo</span> prevents disasters.
        </p>
      </section>

      {/* Demo Buttons */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8">
        <div className="flex flex-wrap gap-4 justify-center">
          <button
            onClick={() => setActiveDemo('before')}
            className={`px-8 py-4 rounded-lg font-semibold transition-all ${
              activeDemo === 'before'
                ? 'bg-red-600 text-white shadow-lg shadow-red-500/50 scale-105'
                : 'bg-red-600/20 text-red-300 hover:bg-red-600/40 border border-red-500/30'
            }`}
          >
            🔥 Without wflo
          </button>
          <button
            onClick={() => setActiveDemo('after')}
            className={`px-8 py-4 rounded-lg font-semibold transition-all ${
              activeDemo === 'after'
                ? 'bg-green-600 text-white shadow-lg shadow-green-500/50 scale-105'
                : 'bg-green-600/20 text-green-300 hover:bg-green-600/40 border border-green-500/30'
            }`}
          >
            ✅ With wflo Budget
          </button>
          <button
            onClick={() => setActiveDemo('hitl')}
            className={`px-8 py-4 rounded-lg font-semibold transition-all ${
              activeDemo === 'hitl'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50 scale-105'
                : 'bg-purple-600/20 text-purple-300 hover:bg-purple-600/40 border border-purple-500/30'
            }`}
          >
            🛡️ With HITL Approval
          </button>
        </div>
      </section>

      {/* Demo Panels */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="bg-black/40 backdrop-blur-sm rounded-2xl border border-white/10 p-8 min-h-[500px]">
          {activeDemo === null && (
            <div className="flex items-center justify-center h-[450px] text-purple-300 text-xl">
              👆 Select a demo above to see wflo in action
            </div>
          )}
          {activeDemo === 'before' && <BeforeWfloDemo />}
          {activeDemo === 'after' && <AfterWfloDemo />}
          {activeDemo === 'hitl' && <HITLDemo />}
        </div>
      </section>

      {/* Metrics Comparison */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <h3 className="text-3xl font-bold text-white text-center mb-8">
          The Impact
        </h3>
        <MetricsComparison />
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/30 rounded-2xl p-12 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Deploy AI Agents with Confidence?
          </h3>
          <p className="text-purple-200 text-lg mb-8 max-w-2xl mx-auto">
            wflo provides the guardrails enterprises need: cost control, approval gates, and resilience patterns.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <a
              href="https://github.com/wflo-ai/wflo"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
            >
              Get Started
            </a>
            <a
              href="https://wflo.ai/docs"
              className="px-8 py-4 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-lg font-semibold transition-colors"
            >
              Read the Docs
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center text-purple-300">
          <p>Built with ❤️ for safer AI agent deployments</p>
          <p className="text-sm mt-2 text-purple-400">
            Open Source • MIT License • Built on Python, Redis, PostgreSQL
          </p>
        </div>
      </footer>
    </div>
  )
}
