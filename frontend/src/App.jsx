import { useTravelPlanStream } from './hooks/useTravelPlanStream'
import TripRequestForm from './components/TripRequestForm'
import PlanningProgress from './components/PlanningProgress'
import BudgetPanel from './components/BudgetPanel'
import ConstraintsPanel from './components/ConstraintsPanel'
import ItineraryPanel from './components/ItineraryPanel'

export default function App() {
  const { events, result, status, error, start } = useTravelPlanStream()

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 py-10 px-4 sm:px-6 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-xl shadow-lg shadow-cyan-500/20">
                🧠
              </div>
              <div>
                <h1 className="text-2xl font-extrabold bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  TravelMind AI
                </h1>
                <p className="text-xs text-slate-400">Autonomous Multi-Agent Travel Planning System</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="glass-panel px-3.5 py-1.5 rounded-full flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-300 font-medium">Real Live Flight & Hotel APIs Active</span>
            </div>
          </div>
        </header>

        {/* Input Form */}
        <TripRequestForm onSubmit={start} disabled={status === 'running'} />

        {/* Error Notification */}
        {error && (
          <div className="glass-panel border-rose-500/40 bg-rose-950/40 text-rose-200 text-sm rounded-2xl p-4 flex items-center gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <div className="font-semibold">Execution Error</div>
              <div className="text-xs text-rose-300">{error}</div>
            </div>
          </div>
        )}

        {/* Live Agent Monitor */}
        <PlanningProgress events={events} status={status} />

        {/* Failure summary */}
        {result && result.status === 'failed' && (
          <div className="glass-panel border-amber-500/40 bg-amber-950/40 text-amber-200 text-sm rounded-2xl p-4 flex items-center gap-3">
            <span className="text-xl">❌</span>
            <div>
              <div className="font-semibold">Multi-Agent Planning Failed</div>
              <div className="text-xs text-amber-300">
                {result.errors[result.errors.length - 1]}
              </div>
            </div>
          </div>
        )}

        {/* Final Synthesized Results */}
        {result && result.status === 'completed' && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <span className="text-lg">🎯</span>
              <h2 className="text-lg font-bold text-slate-100">Final Evaluated Trip Plan</h2>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <BudgetPanel budgetResult={result.budget_result} />
              <ConstraintsPanel constraintResult={result.constraint_result} />
              <ItineraryPanel itinerary={result.itinerary} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}