import { useState } from 'react'

const initialForm = {
  origin: 'Delhi',
  destination: 'Tokyo',
  start_date: '2026-11-01',
  travellers: 2,
  duration_days: 7,
  budget: 200000,
  currency: 'INR',
  interests: 'culture, outdoor',
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
      className="grid grid-cols-2 gap-4 bg-white p-6 rounded-xl shadow-sm border border-slate-200"
    >
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Origin
        <input name="origin" value={form.origin} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Destination
        <input name="destination" value={form.destination} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Start date
        <input type="date" name="start_date" value={form.start_date} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Travellers
        <input type="number" min="1" name="travellers" value={form.travellers} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Duration (days)
        <input type="number" min="1" name="duration_days" value={form.duration_days} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Budget (INR)
        <input type="number" min="1" name="budget" value={form.budget} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600 col-span-2">
        Interests (comma separated)
        <input name="interests" value={form.interests} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Orchestration engine
        <select name="engine" value={form.engine} onChange={handleChange} className="rounded-lg border border-slate-300 px-3 py-2">
          <option value="custom">Custom orchestrator</option>
          <option value="langgraph">LangGraph</option>
        </select>
      </label>
      <div className="col-span-2 flex justify-end">
        <button
          type="submit"
          disabled={disabled}
          className="rounded-lg bg-slate-900 text-white px-5 py-2 text-sm font-medium disabled:opacity-50"
        >
          {disabled ? 'Planning…' : 'Plan my trip'}
        </button>
      </div>
    </form>
  )
}