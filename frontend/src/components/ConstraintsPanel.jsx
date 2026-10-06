export default function ConstraintsPanel({ constraintResult }) {
  if (!constraintResult) return null

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h2 className="text-sm font-semibold text-slate-700 mb-2">Constraints</h2>
      {constraintResult.passed ? (
        <p className="text-sm text-emerald-700">All constraints satisfied.</p>
      ) : (
        <ul className="space-y-1 text-sm text-red-700">
          {constraintResult.violations.map((v, i) => (
            <li key={i}>
              {v.constraint}: expected {v.expected}, got {v.actual}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}