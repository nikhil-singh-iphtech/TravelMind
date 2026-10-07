import { useState } from 'react'

const initialForm = {
  origin: 'Delhi',
  destination: 'Tokyo',
  start_date: '2026-11-01',
  travellers: 2,
  duration_days: 7,
  budget: 200000,
  currency: 'INR',
  interests: 'culture, outdoor, food',
  engine: 'custom',
}

export default function TripRequestForm({ onSubmit, disabled }) {
  const [form, setForm] = useState(initialForm)

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      trip: {
        origin: form.origin,
        destination: form.destination,
        start_date: form.start_date,
        travellers: Number(form.travellers),
        duration_days: Number(form.duration_days),
        budget: Number(form.budget),
        currency: form.currency,
        interests: form.interests.split(',').map((s) => s.trim()).filter(Boolean),
      },
      user_id: 1,
      engine: form.engine,
    })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="glass-panel p-6 rounded-2xl relative overflow-hidden space-y-6"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
            Trip Parameters & Constraints
          </h2>
          <p className="text-xs text-slate-400">Configure parameters for multi-agent autonomous planning</p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
          Agentic Mode: Active
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Origin
          </label>
          <input
            name="origin"
            value={form.origin}
            onChange={handleChange}
            placeholder="e.g. Delhi"
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Destination
          </label>
          <input
            name="destination"
            value={form.destination}
            onChange={handleChange}
            placeholder="e.g. Tokyo"
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Start Date
          </label>
          <input
            type="date"
            name="start_date"
            value={form.start_date}
            onChange={handleChange}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition color-scheme-dark"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Travellers
          </label>
          <input
            type="number"
            min="1"
            name="travellers"
            value={form.travellers}
            onChange={handleChange}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Duration (Days)
          </label>
          <input
            type="number"
            min="1"
            name="duration_days"
            value={form.duration_days}
            onChange={handleChange}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Budget ({form.currency})
          </label>
          <input
            type="number"
            min="1"
            name="budget"
            value={form.budget}
            onChange={handleChange}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Interests (comma separated)
          </label>
          <input
            name="interests"
            value={form.interests}
            onChange={handleChange}
            placeholder="culture, outdoor, food, shopping"
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Orchestration Engine
          </label>
          <select
            name="engine"
            value={form.engine}
            onChange={handleChange}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 outline-none transition text-slate-200"
          >
            <option value="custom">Custom Autonomous Orchestrator</option>
            <option value="langgraph">LangGraph Agent Engine</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={disabled}
          className="relative group overflow-hidden rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-600 p-[1px] font-medium disabled:opacity-50 transition"
        >
          <div className="px-6 py-3 rounded-[11px] bg-slate-950/90 group-hover:bg-transparent transition-all duration-300 flex items-center gap-2">
            {disabled ? (
              <>
                <svg className="animate-spin h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-sm text-cyan-200">Agents Executing Pipeline...</span>
              </>
            ) : (
              <>
                <span className="text-sm font-semibold text-white">Trigger Multi-Agent Planning</span>
                <span className="text-cyan-400 group-hover:translate-x-1 transition-transform">→</span>
              </>
            )}
          </div>
        </button>
      </div>
    </form>
  )
}