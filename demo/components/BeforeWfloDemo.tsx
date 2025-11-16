'use client'

import { useState, useEffect } from 'react'

export default function BeforeWfloDemo() {
  const [isRunning, setIsRunning] = useState(false)
  const [cost, setCost] = useState(0)
  const [llmCalls, setLlmCalls] = useState(0)
  const [steps, setSteps] = useState<string[]>([])

  const simulateWorkflow = () => {
    setIsRunning(true)
    setCost(0)
    setLlmCalls(0)
    setSteps([])

    let currentCost = 0
    let currentCalls = 0
    let currentSteps: string[] = []

    const workflowSteps = [
      { step: 'Agent initialized: data-analysis-agent', cost: 0.02, delay: 500 },
      { step: 'LLM Call: Analyzing customer data...', cost: 0.45, delay: 800 },
      { step: 'LLM Call: Generating insights...', cost: 0.52, delay: 700 },
      { step: 'WARNING: Agent entered infinite loop', cost: 0, delay: 400 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.48, delay: 600 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.51, delay: 600 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.47, delay: 500 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.53, delay: 500 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.49, delay: 400 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.52, delay: 400 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.48, delay: 300 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.51, delay: 300 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.50, delay: 200 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.52, delay: 200 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.49, delay: 200 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.51, delay: 200 },
      { step: '💸 Cost spiraling out of control...', cost: 0.50, delay: 200 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.48, delay: 150 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.52, delay: 150 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.49, delay: 150 },
    ]

    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex >= workflowSteps.length) {
        // Keep incrementing cost even after steps finish to show runaway effect
        currentCost += Math.random() * 0.6 + 0.4
        currentCalls += 1
        setCost(currentCost)
        setLlmCalls(currentCalls)

        if (currentCost > 50) {
          clearInterval(interval)
          setSteps(prev => [...prev, '💥 WORKFLOW FAILED - Cost limit exceeded!'])
        }
        return
      }

      const currentStep = workflowSteps[stepIndex]
      currentSteps = [...currentSteps, currentStep.step]
      currentCost += currentStep.cost
      if (currentStep.cost > 0) currentCalls += 1

      setSteps(currentSteps)
      setCost(currentCost)
      setLlmCalls(currentCalls)

      stepIndex++
    }, 800)

    return () => clearInterval(interval)
  }

  const resetDemo = () => {
    setIsRunning(false)
    setCost(0)
    setLlmCalls(0)
    setSteps([])
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-red-400">
          Without wflo: Unguarded AI Workflow
        </h3>
        <div className="flex gap-3">
          {!isRunning && (
            <button
              onClick={simulateWorkflow}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors"
            >
              ▶ Run Demo
            </button>
          )}
          {isRunning && (
            <button
              onClick={resetDemo}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Cost Counter */}
      <div className="bg-red-900/30 border-2 border-red-500 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-red-300 text-sm font-semibold">TOTAL COST</p>
            <p className={`text-5xl font-bold text-red-400 ${cost > 5 ? 'animate-spin-cost' : ''}`}>
              ${cost.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-red-300 text-sm font-semibold">LLM CALLS</p>
            <p className="text-3xl font-bold text-red-400">{llmCalls}</p>
          </div>
        </div>
        {cost > 10 && (
          <div className="mt-4 p-3 bg-red-500/20 border border-red-400 rounded-lg">
            <p className="text-red-300 font-semibold text-center">
              ⚠️ WARNING: Cost exceeding expected budget!
            </p>
          </div>
        )}
      </div>

      {/* Workflow Steps */}
      <div className="bg-black/60 rounded-xl p-6 border border-red-500/30 max-h-64 overflow-y-auto">
        <p className="text-red-300 font-semibold mb-3">Workflow Execution Log:</p>
        {steps.length === 0 && (
          <p className="text-gray-500 italic">Click "Run Demo" to start the workflow...</p>
        )}
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`py-1 font-mono text-sm ${
              step.includes('WARNING') || step.includes('💸')
                ? 'text-yellow-400 font-bold'
                : step.includes('FAILED')
                ? 'text-red-500 font-bold text-lg'
                : 'text-gray-300'
            }`}
          >
            [{new Date().toLocaleTimeString()}] {step}
          </div>
        ))}
      </div>

      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
        <p className="text-red-300 text-sm">
          <span className="font-bold">The Problem:</span> Without wflo, AI agents can enter infinite loops,
          make redundant API calls, and rack up unbounded costs. There's no mechanism to stop runaway execution.
        </p>
      </div>
    </div>
  )
}
