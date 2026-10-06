export default function PlanningProgress({ events }) {
  if (events.length === 0) return null

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h2 className="text-sm font-semibold text-slate-700 mb-3">Planning progress</h2>
      <ul className="space-y-1 font-mono text-xs text-slate-600 max-h-64 overflow-y-auto">
        {events.map((e, i) => (
          <li key={i}>
            <span className="text-slate-400">{new Date(e.timestamp).toLocaleTimeString()}</span>{' '}
            <span className="font-semibold">{e.event_type}</span> — {e.message}
          </li>
        ))}
      </ul>
    </div>
  )
}