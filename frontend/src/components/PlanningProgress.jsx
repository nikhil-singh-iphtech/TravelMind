import { useMemo, useState } from 'react'

const AGENT_CONFIGS = [
  { id: 'request', name: 'Request Agent', role: 'Input Parsing & Intent Structuring', icon: '📝', color: 'from-blue-500 to-cyan-500' },
  { id: 'flight', name: 'Flight Research Agent', role: 'Real Live Flight Search (Duffel API)', icon: '✈️', color: 'from-cyan-500 to-teal-500' },
  { id: 'hotel', name: 'Hotel Research Agent', role: 'Real Live Hotel Search (Live/MakCorps API)', icon: '🏨', color: 'from-purple-500 to-indigo-500' },
  { id: 'activity', name: 'Activity Agent', role: 'Interest Matching & Attractions', icon: '🎡', color: 'from-amber-500 to-orange-500' },
  { id: 'weather', name: 'Weather Agent', role: 'Forecast Analysis (Open-Meteo)', icon: '☀️', color: 'from-sky-500 to-blue-600' },
  { id: 'strategy', name: 'Strategy Agent', role: 'Selection & Optimization (Comfort/Budget)', icon: '🧠', color: 'from-indigo-500 to-purple-600' },
  { id: 'budget', name: 'Budget Evaluator Agent', role: 'Deterministic Financial Verification', icon: '💰', color: 'from-emerald-500 to-green-600' },
  { id: 'constraint', name: 'Constraint Evaluator Agent', role: 'Feasibility & Rule Validation', icon: '🛡️', color: 'from-rose-500 to-pink-600' },
  { id: 'itinerary', name: 'Itinerary Synthesizer', role: 'Final Day-by-Day Schedule Generation', icon: '📍', color: 'from-violet-500 to-fuchsia-600' },
]

export default function PlanningProgress({ events, status }) {
  const [selectedAgentTab, setSelectedAgentTab] = useState('all')

  const agentLogs = useMemo(() => {
    const logs = {}
    AGENT_CONFIGS.forEach((agent) => {
      logs[agent.id] = []
    })
    logs['general'] = []

    events.forEach((ev) => {
      const type = (ev.event_type || '').toLowerCase()
      const msg = (ev.message || '').toLowerCase()
      
      let target = 'general'
      if (type.includes('flight') || msg.includes('flight')) target = 'flight'
      else if (type.includes('hotel') || msg.includes('hotel')) target = 'hotel'
      else if (type.includes('activity') || msg.includes('activit')) target = 'activity'
      else if (type.includes('weather') || msg.includes('weather')) target = 'weather'
      else if (type.includes('budget') || msg.includes('budget')) target = 'budget'
      else if (type.includes('constraint') || msg.includes('constraint')) target = 'constraint'
      else if (type.includes('itinerary') || msg.includes('itinerary')) target = 'itinerary'
      else if (type.includes('strategy') || msg.includes('strategy')) target = 'strategy'
      else if (type.includes('request') || msg.includes('parsed') || msg.includes('starting')) target = 'request'

      if (logs[target]) {
        logs[target].push(ev)
      } else {
        logs['general'].push(ev)
      }
    })

    return logs
  }, [events])

  if (events.length === 0 && status === 'idle') return null

  const activeLogs = selectedAgentTab === 'all' 
    ? events 
    : (agentLogs[selectedAgentTab] || [])

  return (
    <div className="glass-panel p-6 rounded-2xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span className="text-purple-400">⚡</span> Live Multi-Agent Execution Monitor
          </h2>
          <p className="text-xs text-slate-400">
            Real-time step-by-step visibility into individual agent decisions & payloads
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Total Steps: {events.length}</span>
          <span className={`text-xs px-3 py-1 rounded-full font-semibold ${
            status === 'running' 
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse' 
              : status === 'done' 
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
              : 'bg-slate-800 text-slate-400'
          }`}>
            {status === 'running' ? '● Pipeline Running' : status === 'done' ? '✓ Executed Successfully' : 'Ready'}
          </span>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <button
          onClick={() => setSelectedAgentTab('all')}
          className={`p-3 rounded-xl border text-left transition-all ${
            selectedAgentTab === 'all'
              ? 'bg-gradient-to-br from-indigo-900/60 to-purple-900/60 border-indigo-400 text-white shadow-lg'
              : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <div className="text-xl mb-1">🌐</div>
          <div className="text-xs font-bold text-slate-200">All Agents Stream</div>
          <div className="text-[10px] text-slate-400 font-mono mt-1">{events.length} events</div>
        </button>

        {AGENT_CONFIGS.map((agent) => {
          const count = (agentLogs[agent.id] || []).length
          const isSelected = selectedAgentTab === agent.id
          const hasActivity = count > 0

          return (
            <button
              key={agent.id}
              onClick={() => setSelectedAgentTab(agent.id)}
              className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden ${
                isSelected
                  ? 'bg-slate-800 border-cyan-400 text-white shadow-lg ring-1 ring-cyan-400/50'
                  : hasActivity
                  ? 'bg-slate-900/80 border-slate-700/80 text-slate-200 hover:border-slate-600'
                  : 'bg-slate-900/40 border-slate-800/60 text-slate-500 hover:text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-lg">{agent.icon}</span>
                {hasActivity && (
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                )}
              </div>
              <div className="text-xs font-bold truncate mt-1">{agent.name}</div>
              <div className="text-[10px] text-slate-400 truncate">{agent.role}</div>
              <div className="mt-2 flex items-center justify-between text-[10px] font-mono">
                <span className={hasActivity ? 'text-cyan-300' : 'text-slate-600'}>
                  {count} logs
                </span>
                {hasActivity && <span className="text-emerald-400">Active</span>}
              </div>
            </button>
          )
        })}
      </div>

      {/* Terminal Live Stream Console */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/90 overflow-hidden font-mono">
        <div className="flex items-center justify-between bg-slate-900 px-4 py-2 border-b border-slate-800 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
            <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
            <span className="ml-2 font-semibold text-slate-300">
              Agent Output Stream [{selectedAgentTab.toUpperCase()}]
            </span>
          </div>
          <span className="text-[10px] text-slate-500">Live SSE Socket</span>
        </div>

        <div className="p-4 max-h-80 overflow-y-auto space-y-2 text-xs">
          {activeLogs.length === 0 ? (
            <div className="text-slate-600 italic text-center py-6">
              No specific telemetry events captured for this agent slice yet.
            </div>
          ) : (
            activeLogs.map((e, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-2 rounded-lg bg-slate-900/40 border border-slate-800/60 hover:bg-slate-800/40 transition"
              >
                <span className="text-slate-500 text-[10px] shrink-0 pt-0.5">
                  {new Date(e.timestamp).toLocaleTimeString()}
                </span>
                <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50 text-[10px] shrink-0 font-semibold">
                  {e.event_type}
                </span>
                <span className="text-slate-300 leading-relaxed break-all">
                  {e.message}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}