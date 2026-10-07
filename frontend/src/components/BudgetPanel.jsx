export default function BudgetPanel({ budgetResult }) {
  if (!budgetResult) return null
  const { total, budget, passed } = budgetResult

  const formattedTotal = Number(total).toLocaleString()
  const formattedBudget = Number(budget).toLocaleString()
  const percentUsed = Math.min(100, Math.round((Number(total) / Number(budget)) * 100))

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">💰</span>
          <h2 className="text-sm font-bold text-slate-200">Financial Audit</h2>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
            passed
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
          }`}
        >
          {passed ? '✓ Within Budget' : '⚠️ Over Budget'}
        </span>
      </div>

      <div className="my-4 space-y-2">
        <div className="flex items-baseline justify-between">
          <span className="text-3xl font-extrabold text-white tracking-tight">₹{formattedTotal}</span>
          <span className="text-xs text-slate-400 font-mono">Limit: ₹{formattedBudget}</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden border border-slate-700/50">
          <div
            className={`h-full transition-all duration-500 rounded-full ${
              passed
                ? 'bg-gradient-to-r from-teal-400 to-emerald-500'
                : 'bg-gradient-to-r from-amber-500 to-rose-500'
            }`}
            style={{ width: `${percentUsed}%` }}
          />
        </div>
        <div className="flex justify-between text-[11px] text-slate-400 font-mono">
          <span>{percentUsed}% Utilized</span>
          <span>Remaining: ₹{Math.max(0, Number(budget) - Number(total)).toLocaleString()}</span>
        </div>
      </div>

      <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-800 text-xs text-slate-300">
        Budget Evaluator Agent confirmed pricing across flights, hotels & activities.
      </div>
    </div>
  )
}