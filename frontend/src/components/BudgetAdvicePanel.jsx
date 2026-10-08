export default function BudgetAdvicePanel({ advice, currency }) {
  if (!advice || advice.status === 'within_budget') return null

  const isReducible = advice.status === 'reducible'

  return (
    <div className={`glass-panel p-6 rounded-3xl space-y-4 border ${
      isReducible ? 'border-amber-500/40 bg-amber-950/20' : 'border-rose-500/40 bg-rose-950/20'
    }`}>
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <span className="text-xl">{isReducible ? '💡' : '⚠️'}</span>
        <div>
          <h3 className="text-base font-bold text-slate-100">
            {isReducible ? 'Budget Advisory: Cost Reduction Suggestions' : 'Budget Advisory: Additional Funds Required'}
          </h3>
          <p className="text-xs text-slate-400">
            {isReducible
              ? `Your current plan exceeds target budget by ${currency} ${Number(advice.gap).toLocaleString()}. Try these suggestions:`
              : `Even lowest-cost options exceed target budget by ${currency} ${Number(advice.gap).toLocaleString()}`}
          </p>
        </div>
      </div>

      {!isReducible && (
        <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800 text-xs text-slate-200 space-y-1">
          <div className="flex justify-between font-semibold">
            <span>Minimum Budget Required:</span>
            <span>{currency} {Number(advice.cheapest_possible_total).toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-cyan-400 font-bold">
            <span>Recommended Budget (with buffer):</span>
            <span>{currency} {Number(advice.recommended_budget).toLocaleString()}</span>
          </div>
        </div>
      )}

      {advice.suggestions && advice.suggestions.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-300 block">Recommended Adjustments:</span>
          <div className="grid grid-cols-1 gap-2">
            {advice.suggestions.map((sug, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-200"
              >
                <div>
                  <span className="font-bold text-amber-300 capitalize">[{sug.component}]</span> {sug.action}
                </div>
                {sug.estimated_saving > 0 && (
                  <span className="font-semibold text-emerald-400 shrink-0 ml-3">
                    Save {currency} {Number(sug.estimated_saving).toLocaleString()}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
