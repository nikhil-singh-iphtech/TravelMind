export default function ConstraintsPanel({ constraintResult }) {
  if (!constraintResult) return null

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🛡️</span>
          <h2 className="text-sm font-bold text-slate-200">Constraint Validation</h2>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
            constraintResult.passed
              ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
              : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
          }`}
        >
          {constraintResult.passed ? '✓ Validated' : '❌ Violations Detected'}
        </span>
      </div>

      <div className="my-4">
        {constraintResult.passed ? (
          <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-cyan-200 text-sm flex items-center gap-3">
            <span className="text-2xl">✨</span>
            <div>
              <div className="font-semibold">All Constraints Satisfied</div>
              <div className="text-xs text-cyan-300/80">
                Dates, budget limits, flight availability, and hotel requirements matched.
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-rose-400">Detected Rule Conflicts:</div>
            <ul className="space-y-1.5 text-xs text-rose-200 font-mono">
              {constraintResult.violations.map((v, i) => (
                <li key={i} className="p-2 rounded bg-rose-950/40 border border-rose-800/50">
                  <span className="font-bold">{v.constraint}:</span> expected {v.expected}, got {v.actual}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-800 text-xs text-slate-300">
        Constraint Evaluator Agent verified feasibility before output generation.
      </div>
    </div>
  )
}