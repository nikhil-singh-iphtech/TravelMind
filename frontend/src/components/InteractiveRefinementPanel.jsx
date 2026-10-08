import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = 'http://127.0.0.1:8000'

export default function InteractiveRefinementPanel({ result, runId, onPlanUpdated }) {
  const { token } = useAuth()
  const flights = result?.flights || []
  const hotels = result?.hotels || []
  const activities = result?.activities || []
  const currentFlight = result?.selected_flight
  const currentHotel = result?.selected_hotel

  const [selectedFlightId, setSelectedFlightId] = useState(currentFlight?.id || '')
  const [selectedHotelId, setSelectedHotelId] = useState(currentHotel?.id || '')
  const [excludedActivityIds, setExcludedActivityIds] = useState([])
  const [customBudget, setCustomBudget] = useState('')
  const [updating, setUpdating] = useState(false)
  const [msg, setMsg] = useState(null)

  const toggleActivity = (actId) => {
    setExcludedActivityIds((prev) =>
      prev.includes(actId) ? prev.filter((id) => id !== actId) : [...prev, actId]
    )
  }

  const handleRefine = async () => {
    if (!runId || !token) return
    setUpdating(true)
    setMsg(null)
    try {
      const payload = {
        flight_id: selectedFlightId || undefined,
        hotel_id: selectedHotelId || undefined,
        excluded_activity_ids: excludedActivityIds,
        custom_budget: customBudget ? Number(customBudget) : undefined,
      }
      const res = await fetch(`${API_BASE}/travel-plans/${runId}/refine`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Failed to refine plan')
      const updatedPlanData = await res.json()
      setMsg({ type: 'success', text: 'Plan refined and re-evaluated successfully!' })
      if (onPlanUpdated && updatedPlanData.result) {
        onPlanUpdated(updatedPlanData.result)
      }
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className="glass-panel p-6 rounded-3xl space-y-6 border border-indigo-500/30">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🛠️</span>
          <div>
            <h3 className="text-base font-bold text-slate-100">Interactive Plan Refinement</h3>
            <p className="text-xs text-slate-400">Swap options and instantly trigger multi-agent re-evaluation</p>
          </div>
        </div>
      </div>

      {msg && (
        <div
          className={`p-3 rounded-xl text-xs ${
            msg.type === 'success'
              ? 'bg-emerald-950/60 border border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/60 border border-rose-500/40 text-rose-300'
          }`}
        >
          {msg.text}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
        {/* Flight Selection */}
        {flights.length > 0 && (
          <div className="space-y-2">
            <label className="font-semibold text-slate-200 block">✈️ Select Flight Option:</label>
            <select
              value={selectedFlightId}
              onChange={(e) => setSelectedFlightId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              {flights.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.airline} — {f.currency} {Number(f.price).toLocaleString()}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Hotel Selection */}
        {hotels.length > 0 && (
          <div className="space-y-2">
            <label className="font-semibold text-slate-200 block">🏨 Select Hotel Option:</label>
            <select
              value={selectedHotelId}
              onChange={(e) => setSelectedHotelId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              {hotels.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} — {h.currency} {Number(h.price_per_night).toLocaleString()}/night ({h.nights} nights)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Activities Selection */}
      {activities.length > 0 && (
        <div className="space-y-2">
          <label className="font-semibold text-slate-200 block">🎯 Activities (Check to exclude):</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
            {activities.map((a) => {
              const isExcluded = excludedActivityIds.includes(a.id)
              return (
                <label
                  key={a.id}
                  className={`flex items-center justify-between p-2.5 rounded-xl border transition-colors cursor-pointer text-xs ${
                    isExcluded
                      ? 'bg-rose-950/20 border-rose-800/40 text-rose-300 line-through'
                      : 'bg-slate-900/60 border-slate-800 text-slate-200'
                  }`}
                >
                  <span>{a.name} ({Number(a.price).toLocaleString()})</span>
                  <input
                    type="checkbox"
                    checked={isExcluded}
                    onChange={() => toggleActivity(a.id)}
                    className="accent-rose-500"
                  />
                </label>
              )
            })}
          </div>
        </div>
      )}

      {/* Target Budget Editor */}
      <div className="space-y-2">
        <label className="font-semibold text-slate-200 block">💰 Override Target Budget (Optional):</label>
        <input
          type="number"
          value={customBudget}
          onChange={(e) => setCustomBudget(e.target.value)}
          placeholder="Enter new budget threshold..."
          className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
      </div>

      <button
        onClick={handleRefine}
        disabled={updating || !runId}
        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 font-semibold text-white text-xs shadow-lg shadow-cyan-500/20 hover:opacity-95 transition-all disabled:opacity-50"
      >
        {updating ? 'Re-evaluating Plan...' : '🔄 Apply Changes & Re-evaluate Budget'}
      </button>
    </div>
  )
}
