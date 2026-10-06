export default function BudgetPanel({ budgetResult }) {
  if (!budgetResult) return null
  const { total, budget, passed } = budgetResult

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h2 className="text-sm font-semibold text-slate-700 mb-2">Budget</h2>
      <p className="text-2xl font-bold text-slate-900">{total}</p>
      <p className="text-sm text-slate-500">of {budget} budget</p>
      <span
        className={`inline-block mt-2 text-xs font-medium px-2 py-1 rounded-full ${
          passed ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
        }`}
      >
        {passed ? 'Within budget' : 'Over budget'}
      </span>
    </div>
  )
}