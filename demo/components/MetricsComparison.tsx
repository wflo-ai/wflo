export default function MetricsComparison() {
  const metrics = [
    {
      label: 'Total Cost',
      without: '$47.32',
      withBudget: '$5.00',
      withHITL: '$0.02',
      saved: '$47.30',
    },
    {
      label: 'LLM Calls',
      without: '247',
      withBudget: '52',
      withHITL: '3',
      saved: '244',
    },
    {
      label: 'Status',
      without: 'FAILED ❌',
      withBudget: 'HALTED ⏹️',
      withHITL: 'APPROVED ✅',
      saved: '-',
    },
    {
      label: 'Risk',
      without: 'Unbounded',
      withBudget: 'Controlled',
      withHITL: 'Governed',
      saved: '-',
    },
  ]

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-white/20">
            <th className="px-6 py-4 text-left text-white font-bold text-lg">Metric</th>
            <th className="px-6 py-4 text-center text-red-400 font-bold text-lg">
              Without wflo
            </th>
            <th className="px-6 py-4 text-center text-green-400 font-bold text-lg">
              With Budget Control
            </th>
            <th className="px-6 py-4 text-center text-purple-400 font-bold text-lg">
              With HITL Gates
            </th>
            <th className="px-6 py-4 text-center text-blue-400 font-bold text-lg">
              Savings
            </th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric, idx) => (
            <tr
              key={idx}
              className="border-b border-white/10 hover:bg-white/5 transition-colors"
            >
              <td className="px-6 py-4 text-white font-semibold">
                {metric.label}
              </td>
              <td className="px-6 py-4 text-center">
                <span className="inline-block px-4 py-2 bg-red-900/30 text-red-300 rounded-lg font-mono">
                  {metric.without}
                </span>
              </td>
              <td className="px-6 py-4 text-center">
                <span className="inline-block px-4 py-2 bg-green-900/30 text-green-300 rounded-lg font-mono">
                  {metric.withBudget}
                </span>
              </td>
              <td className="px-6 py-4 text-center">
                <span className="inline-block px-4 py-2 bg-purple-900/30 text-purple-300 rounded-lg font-mono">
                  {metric.withHITL}
                </span>
              </td>
              <td className="px-6 py-4 text-center">
                <span className="inline-block px-4 py-2 bg-blue-900/30 text-blue-300 rounded-lg font-bold">
                  {metric.saved}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-xl p-6 text-center">
          <div className="text-4xl mb-3">💰</div>
          <div className="text-3xl font-bold text-green-400 mb-2">89%</div>
          <div className="text-green-300 font-semibold">Cost Reduction</div>
          <div className="text-green-200 text-sm mt-2">
            Budget control prevents runaway spending
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-xl p-6 text-center">
          <div className="text-4xl mb-3">🛡️</div>
          <div className="text-3xl font-bold text-purple-400 mb-2">100%</div>
          <div className="text-purple-300 font-semibold">Risk Mitigation</div>
          <div className="text-purple-200 text-sm mt-2">
            HITL gates prevent destructive operations
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-900/30 to-cyan-900/30 border border-blue-500/30 rounded-xl p-6 text-center">
          <div className="text-4xl mb-3">📊</div>
          <div className="text-3xl font-bold text-blue-400 mb-2">Full</div>
          <div className="text-blue-300 font-semibold">Audit Trail</div>
          <div className="text-blue-200 text-sm mt-2">
            Every approval logged for compliance
          </div>
        </div>
      </div>
    </div>
  )
}
