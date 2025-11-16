'use client'

import { useState, useEffect } from 'react'

export default function AfterWfloDemo() {
  const [isRunning, setIsRunning] = useState(false)
  const [cost, setCost] = useState(0)
  const [llmCalls, setLlmCalls] = useState(0)
  const [steps, setSteps] = useState<string[]>([])
  const [budgetHit, setBudgetHit] = useState(false)

  const BUDGET_LIMIT = 5.0

  const simulateWorkflow = () => {
    setIsRunning(true)
    setCost(0)
    setLlmCalls(0)
    setSteps([])
    setBudgetHit(false)

    let currentCost = 0
    let currentCalls = 0
    let currentSteps: string[] = []

    const workflowSteps = [
      { step: 'wflo: Initialized workflow with $5.00 budget', cost: 0, delay: 500 },
      { step: 'wflo: Starting data-analysis-agent', cost: 0.02, delay: 700 },
      { step: 'LLM Call: Analyzing customer data...', cost: 0.45, delay: 800 },
      { step: 'wflo: Budget check - $0.47/$5.00 used (9.4%)', cost: 0, delay: 300 },
      { step: 'LLM Call: Generating insights...', cost: 0.52, delay: 700 },
      { step: 'wflo: Budget check - $0.99/$5.00 used (19.8%)', cost: 0, delay: 300 },
      { step: 'WARNING: Agent attempting to enter loop', cost: 0, delay: 400 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.48, delay: 600 },
      { step: 'wflo: Budget check - $1.47/$5.00 used (29.4%)', cost: 0, delay: 300 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.51, delay: 600 },
      { step: 'wflo: Budget check - $1.98/$5.00 used (39.6%)', cost: 0, delay: 300 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.47, delay: 500 },
      { step: 'wflo: Budget check - $2.45/$5.00 used (49.0%)', cost: 0, delay: 300 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.53, delay: 500 },
      { step: 'wflo: Budget check - $2.98/$5.00 used (59.6%)', cost: 0, delay: 300 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.49, delay: 400 },
      { step: 'wflo: Budget check - $3.47/$5.00 used (69.4%)', cost: 0, delay: 300 },
      { step: 'LLM Call: Re-generating insights...', cost: 0.52, delay: 400 },
      { step: 'wflo: Budget check - $3.99/$5.00 used (79.8%)', cost: 0, delay: 300 },
      { step: '⚠️  wflo: WARNING - 80% of budget consumed', cost: 0, delay: 500 },
      { step: 'LLM Call: Re-analyzing same data...', cost: 0.48, delay: 300 },
      { step: 'wflo: Budget check - $4.47/$5.00 used (89.4%)', cost: 0, delay: 300 },
      { step: '🛑 wflo: BUDGET LIMIT REACHED - Halting workflow', cost: 0, delay: 800 },
      { step: '✅ wflo: Workflow gracefully terminated', cost: 0, delay: 500 },
      { step: '💰 wflo: Budget saved: Prevented $45.53 in additional costs', cost: 0, delay: 500 },
    ]

    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex >= workflowSteps.length) {
        clearInterval(interval)
        setIsRunning(false)
        return
      }

      const currentStep = workflowSteps[stepIndex]
      currentSteps = [...currentSteps, currentStep.step]
      currentCost += currentStep.cost
      if (currentStep.cost > 0) currentCalls += 1

      setSteps(currentSteps)
      setCost(currentCost)
      setLlmCalls(currentCalls)

      // Check if budget hit
      if (currentStep.step.includes('BUDGET LIMIT REACHED')) {
        setBudgetHit(true)
      }

      stepIndex++
    }, 700)

    return () => clearInterval(interval)
  }

  const resetDemo = () => {
    setIsRunning(false)
    setCost(0)
    setLlmCalls(0)
    setSteps([])
    setBudgetHit(false)
  }

  const budgetPercentage = Math.min((cost / BUDGET_LIMIT) * 100, 100)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-green-400">
          With wflo: Budget-Protected Workflow
        </h3>
        <div className="flex gap-3">
          {!isRunning && !budgetHit && (
            <button
              onClick={simulateWorkflow}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors"
            >
              ▶ Run Demo
            </button>
          )}
          {(isRunning || budgetHit) && (
            <button
              onClick={resetDemo}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Budget Bar */}
      <div className="bg-green-900/30 border-2 border-green-500 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-green-300 text-sm font-semibold">COST WITH BUDGET PROTECTION</p>
            <p className={`text-5xl font-bold ${budgetHit ? 'text-yellow-400' : 'text-green-400'}`}>
              ${cost.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-green-300 text-sm font-semibold">BUDGET LIMIT</p>
            <p className="text-3xl font-bold text-green-300">${BUDGET_LIMIT.toFixed(2)}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative w-full h-8 bg-gray-800 rounded-full overflow-hidden border-2 border-green-500/50">
          <div
            className={`h-full transition-all duration-300 ${
              budgetPercentage >= 100
                ? 'bg-gradient-to-r from-yellow-500 to-red-500'
                : budgetPercentage >= 80
                ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                : 'bg-gradient-to-r from-green-500 to-emerald-400'
            }`}
            style={{ width: `${budgetPercentage}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-white font-bold text-sm drop-shadow-lg">
              {budgetPercentage.toFixed(1)}% of Budget Used
            </span>
          </div>
        </div>

        <div className="flex justify-between mt-2 text-xs text-green-300">
          <span>LLM Calls: {llmCalls}</span>
          <span>Remaining: ${(BUDGET_LIMIT - cost).toFixed(2)}</span>
        </div>
      </div>

      {budgetHit && (
        <div className="bg-green-900/40 border-2 border-green-400 rounded-xl p-6 text-center">
          <p className="text-3xl font-bold text-green-400 mb-2">
            ✅ WORKFLOW HALTED BY wflo
          </p>
          <p className="text-green-300 text-lg">
            Budget protected. Estimated $45.53 in costs prevented.
          </p>
        </div>
      )}

      {/* Workflow Steps */}
      <div className="bg-black/60 rounded-xl p-6 border border-green-500/30 max-h-64 overflow-y-auto">
        <p className="text-green-300 font-semibold mb-3">Workflow Execution Log:</p>
        {steps.length === 0 && (
          <p className="text-gray-500 italic">Click "Run Demo" to start the protected workflow...</p>
        )}
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`py-1 font-mono text-sm ${
              step.includes('wflo:')
                ? step.includes('WARNING') || step.includes('⚠️')
                  ? 'text-yellow-400 font-bold'
                  : step.includes('BUDGET LIMIT') || step.includes('🛑')
                  ? 'text-red-400 font-bold'
                  : step.includes('✅') || step.includes('💰')
                  ? 'text-green-400 font-bold'
                  : 'text-blue-300'
                : step.includes('WARNING')
                ? 'text-yellow-300'
                : 'text-gray-300'
            }`}
          >
            [{new Date().toLocaleTimeString()}] {step}
          </div>
        ))}
      </div>

      <div className="bg-green-900/20 border border-green-500/50 rounded-lg p-4">
        <p className="text-green-300 text-sm">
          <span className="font-bold">The Solution:</span> wflo enforces budget limits on every workflow.
          When the limit is reached, the workflow is gracefully halted, preventing runaway costs while
          preserving partial results.
        </p>
      </div>
    </div>
  )
}
