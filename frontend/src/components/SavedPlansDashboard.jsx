import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = 'http://127.0.0.1:8000'

export default function SavedPlansDashboard({ onSelectPlan, onOpenAuth }) {
  const { token, user } = useAuth()
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (!token) return
    async function fetchPlans() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API_BASE}/travel-plans`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error('Failed to fetch travel plans')
        const data = await res.json()
        setPlans(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchPlans()
  }, [token])

  if (!user) {
    return (
      <div className="glass-panel p-10 rounded-3xl text-center max-w-xl mx-auto space-y-4">
        <div className="text-4xl">🔐</div>
        <h2 className="text-xl font-bold text-slate-100">Sign In to View Saved Plans</h2>
        <p className="text-xs text-slate-400">
          Your generated travel itineraries, custom budget evaluations, and shareable plans will be automatically stored here.
        </p>
        <button
          onClick={onOpenAuth}
          className="py-2.5 px-6 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 font-semibold text-white text-xs shadow-lg shadow-cyan-500/20 hover:opacity-95"
        >
          Sign In / Register Account
        </button>
      </div>
    )
  }

  const filteredPlans = plans.filter((p) =>
    p.destination.toLowerCase().includes(search.toLowerCase()) ||
    (p.origin && p.origin.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-2xl">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Saved Travel Plans</h2>
          <p className="text-xs text-slate-400">Access and refine your past AI-generated itineraries</p>
        </div>

        <div className="w-full sm:w-64">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search destination..."
            className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {loading && (
        <div className="text-center py-12 text-slate-400 text-sm animate-pulse">
          Loading your travel itineraries...
        </div>
      )}

      {error && (
        <div className="glass-panel p-4 rounded-xl border-rose-500/40 bg-rose-950/40 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {!loading && filteredPlans.length === 0 && (
        <div className="glass-panel p-10 rounded-2xl text-center space-y-2">
          <div className="text-3xl">✈️</div>
          <h3 className="text-sm font-semibold text-slate-200">No Saved Plans Found</h3>
          <p className="text-xs text-slate-400">
            {search ? 'No plans match your search query.' : 'Generate your first trip plan to see it saved here!'}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredPlans.map((plan) => (
          <div
            key={plan.run_id}
            onClick={() => onSelectPlan(plan.run_id)}
            className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/50 transition-all cursor-pointer group hover:scale-[1.01]"
          >
            <div className="flex items-start justify-between gap-2 mb-3">
              <div>
                <span className="text-xs font-medium text-cyan-400 tracking-wide uppercase">
                  {plan.origin ? `${plan.origin} ✈️ ` : ''}{plan.destination}
                </span>
                <h3 className="text-base font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  {plan.destination} Trip
                </h3>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                  plan.status === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}
              >
                {plan.status}
              </span>
            </div>

            <div className="space-y-1.5 text-xs text-slate-300 border-t border-slate-800/80 pt-3">
              <div className="flex justify-between">
                <span className="text-slate-500">Budget:</span>
                <span className="font-semibold text-slate-100">
                  {plan.currency} {Number(plan.budget || 0).toLocaleString()}
                </span>
              </div>
              {plan.start_date && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Start Date:</span>
                  <span>{plan.start_date}</span>
                </div>
              )}
              <div className="flex justify-between text-[11px] text-slate-500 pt-1">
                <span>Created:</span>
                <span>{plan.created_at ? new Date(plan.created_at).toLocaleDateString() : 'N/A'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
