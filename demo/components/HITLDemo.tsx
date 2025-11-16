'use client'

import { useState } from 'react'

type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'none'

export default function HITLDemo() {
  const [isRunning, setIsRunning] = useState(false)
  const [steps, setSteps] = useState<string[]>([])
  const [approvalStatus, setApprovalStatus] = useState<ApprovalStatus>('none')
  const [userComment, setUserComment] = useState('')
  const [showCommentBox, setShowCommentBox] = useState(false)

  const simulateWorkflow = () => {
    setIsRunning(true)
    setSteps([])
    setApprovalStatus('none')
    setUserComment('')
    setShowCommentBox(false)

    const initialSteps = [
      'wflo: Initialized workflow: database-cleanup-task',
      'wflo: Starting cleanup-agent with HITL approval gates enabled',
      'Agent: Analyzing database for records to clean up...',
      'Agent: Found 15,847 old records for deletion',
      'Agent: Preparing DELETE query: "DELETE FROM customer_records WHERE last_active < 2023-01-01"',
      '🛑 wflo: HIGH-RISK OPERATION DETECTED',
      '⏸️  wflo: Workflow PAUSED - Awaiting human approval',
      '📧 wflo: Approval notification sent to: manager@company.com',
      '💬 wflo: Slack notification sent to #ops-approvals',
    ]

    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex < initialSteps.length) {
        setSteps(prev => [...prev, initialSteps[stepIndex]])
        stepIndex++

        if (stepIndex === initialSteps.length) {
          setApprovalStatus('pending')
        }
      } else {
        clearInterval(interval)
      }
    }, 600)

    return () => clearInterval(interval)
  }

  const handleApprove = () => {
    setApprovalStatus('approved')
    setShowCommentBox(false)

    const approvalSteps = [
      `✅ wflo: Approval GRANTED by manager@company.com`,
      userComment ? `   Comment: "${userComment}"` : '',
      '▶️  wflo: Resuming workflow execution',
      'Agent: Executing DELETE query with safeguards...',
      'Agent: Successfully deleted 15,847 records',
      'wflo: Workflow completed successfully',
      '📝 wflo: Approval audit logged to database',
    ].filter(Boolean)

    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex < approvalSteps.length) {
        setSteps(prev => [...prev, approvalSteps[stepIndex]])
        stepIndex++
      } else {
        clearInterval(interval)
        setIsRunning(false)
      }
    }, 700)
  }

  const handleReject = () => {
    setApprovalStatus('rejected')
    setShowCommentBox(false)

    const rejectionSteps = [
      `❌ wflo: Approval REJECTED by manager@company.com`,
      userComment ? `   Comment: "${userComment}"` : '',
      '🛑 wflo: Workflow terminated - Operation not permitted',
      'wflo: Rollback: No changes made to database',
      '📝 wflo: Rejection audit logged to database',
      '📧 wflo: Notification sent to workflow owner',
    ].filter(Boolean)

    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex < rejectionSteps.length) {
        setSteps(prev => [...prev, rejectionSteps[stepIndex]])
        stepIndex++
      } else {
        clearInterval(interval)
        setIsRunning(false)
      }
    }, 700)
  }

  const resetDemo = () => {
    setIsRunning(false)
    setSteps([])
    setApprovalStatus('none')
    setUserComment('')
    setShowCommentBox(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-purple-400">
          With HITL: Human-in-the-Loop Approval Gates
        </h3>
        <div className="flex gap-3">
          {!isRunning && approvalStatus === 'none' && (
            <button
              onClick={simulateWorkflow}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
            >
              ▶ Run Demo
            </button>
          )}
          {(approvalStatus !== 'none' && !isRunning) && (
            <button
              onClick={resetDemo}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Approval Card - Only show when pending */}
      {approvalStatus === 'pending' && (
        <div className="bg-gradient-to-br from-yellow-900/40 to-orange-900/40 border-2 border-yellow-500 rounded-xl p-8 shadow-2xl shadow-yellow-500/20">
          <div className="flex items-start gap-4 mb-6">
            <div className="text-5xl">⚠️</div>
            <div className="flex-1">
              <h4 className="text-2xl font-bold text-yellow-300 mb-2">
                Approval Required: High-Risk Operation
              </h4>
              <p className="text-yellow-200 text-sm">
                This workflow has been paused and requires your approval to continue
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-black/40 rounded-lg p-4 border border-yellow-500/30">
              <p className="text-yellow-300 text-xs font-semibold mb-2">WHO (Agent)</p>
              <p className="text-white font-mono">cleanup-agent-001</p>
            </div>
            <div className="bg-black/40 rounded-lg p-4 border border-yellow-500/30">
              <p className="text-yellow-300 text-xs font-semibold mb-2">WORKFLOW</p>
              <p className="text-white font-mono">database-cleanup-task</p>
            </div>
          </div>

          <div className="bg-black/40 rounded-lg p-4 border border-red-500/50 mb-4">
            <p className="text-red-300 text-xs font-semibold mb-2">WHAT (Operation)</p>
            <pre className="text-white font-mono text-sm overflow-x-auto">
              DELETE FROM customer_records{'\n'}WHERE last_active {'<'} '2023-01-01'
            </pre>
            <p className="text-gray-300 text-sm mt-2">
              <span className="font-semibold">Impact:</span> 15,847 records will be permanently deleted
            </p>
          </div>

          <div className="bg-black/40 rounded-lg p-4 border border-yellow-500/30 mb-4">
            <p className="text-yellow-300 text-xs font-semibold mb-2">WHY (Reason)</p>
            <p className="text-white">Running monthly cleanup task to remove inactive customer records from 2022</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-black/40 rounded-lg p-4 border border-red-500/50">
              <p className="text-red-300 text-xs font-semibold mb-2">RISK LEVEL</p>
              <div className="flex items-center gap-2">
                <span className="inline-block px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-full">
                  HIGH
                </span>
                <span className="text-red-300 text-sm">(Destructive query)</span>
              </div>
            </div>
            <div className="bg-black/40 rounded-lg p-4 border border-blue-500/30">
              <p className="text-blue-300 text-xs font-semibold mb-2">ESTIMATED COST</p>
              <p className="text-white text-2xl font-bold">$0.02</p>
            </div>
          </div>

          {/* Comment Section */}
          {showCommentBox && (
            <div className="mb-6">
              <label className="block text-yellow-300 text-sm font-semibold mb-2">
                Optional Comment:
              </label>
              <textarea
                value={userComment}
                onChange={(e) => setUserComment(e.target.value)}
                placeholder="Add a reason for your decision (optional)"
                className="w-full px-4 py-2 bg-black/60 border border-yellow-500/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-yellow-400"
                rows={3}
              />
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => {
                if (!showCommentBox) {
                  setShowCommentBox(true)
                } else {
                  handleApprove()
                }
              }}
              className="flex-1 px-6 py-4 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold text-lg transition-all transform hover:scale-105 shadow-lg"
            >
              ✅ Approve
            </button>
            <button
              onClick={() => {
                if (!showCommentBox) {
                  setShowCommentBox(true)
                } else {
                  handleReject()
                }
              }}
              className="flex-1 px-6 py-4 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold text-lg transition-all transform hover:scale-105 shadow-lg"
            >
              ❌ Reject
            </button>
          </div>

          {!showCommentBox && (
            <p className="text-center text-yellow-300 text-sm mt-4">
              Click a button to add an optional comment
            </p>
          )}
        </div>
      )}

      {/* Success/Rejection Banners */}
      {approvalStatus === 'approved' && (
        <div className="bg-green-900/40 border-2 border-green-400 rounded-xl p-6 text-center">
          <p className="text-3xl font-bold text-green-400 mb-2">
            ✅ OPERATION APPROVED
          </p>
          <p className="text-green-300">
            Workflow resumed and completed successfully. All actions audited.
          </p>
        </div>
      )}

      {approvalStatus === 'rejected' && (
        <div className="bg-red-900/40 border-2 border-red-400 rounded-xl p-6 text-center">
          <p className="text-3xl font-bold text-red-400 mb-2">
            ❌ OPERATION REJECTED
          </p>
          <p className="text-red-300">
            Workflow terminated safely. No changes were made.
          </p>
        </div>
      )}

      {/* Workflow Steps */}
      <div className="bg-black/60 rounded-xl p-6 border border-purple-500/30 max-h-64 overflow-y-auto">
        <p className="text-purple-300 font-semibold mb-3">Workflow Execution Log:</p>
        {steps.length === 0 && (
          <p className="text-gray-500 italic">Click "Run Demo" to start the workflow with HITL approval gates...</p>
        )}
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`py-1 font-mono text-sm ${
              step.includes('🛑') || step.includes('HIGH-RISK')
                ? 'text-red-400 font-bold'
                : step.includes('⏸️') || step.includes('PAUSED')
                ? 'text-yellow-400 font-bold'
                : step.includes('✅') || step.includes('GRANTED')
                ? 'text-green-400 font-bold'
                : step.includes('❌') || step.includes('REJECTED')
                ? 'text-red-400 font-bold'
                : step.includes('wflo:')
                ? 'text-purple-300'
                : step.includes('Comment:')
                ? 'text-blue-300 italic'
                : 'text-gray-300'
            }`}
          >
            [{new Date().toLocaleTimeString()}] {step}
          </div>
        ))}
      </div>

      <div className="bg-purple-900/20 border border-purple-500/50 rounded-lg p-4">
        <p className="text-purple-300 text-sm">
          <span className="font-bold">Enterprise Governance:</span> wflo's HITL approval gates pause workflows
          for high-risk operations, notify managers via Slack/email, and provide a clean UI showing Who, What,
          Why, Risk, and Cost. All approvals/rejections are audited for compliance.
        </p>
      </div>
    </div>
  )
}
