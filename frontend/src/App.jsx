import { useEffect, useState } from 'react'
import { useTravelPlanStream } from './hooks/useTravelPlanStream'
import Navbar from './components/Navbar'
import AuthModal from './components/AuthModal'
import TripRequestForm from './components/TripRequestForm'
import PlanningProgress from './components/PlanningProgress'
import BudgetPanel from './components/BudgetPanel'
import ConstraintsPanel from './components/ConstraintsPanel'
import ItineraryPanel from './components/ItineraryPanel'
import SavedPlansDashboard from './components/SavedPlansDashboard'
import InteractiveRefinementPanel from './components/InteractiveRefinementPanel'
import BudgetAdvicePanel from './components/BudgetAdvicePanel'
import DestinationLinksPanel from './components/DestinationLinksPanel'
import ExportModal from './components/ExportModal'
import { useAuth } from './context/AuthContext'

const API_BASE = 'http://127.0.0.1:8000'

export default function App() {
  const { events, result, setResult, status, setStatus, error, start } = useTravelPlanStream()
  const { token } = useAuth()

  const [activeTab, setActiveTab] = useState('plan') // 'plan' | 'saved'
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [exportModalOpen, setExportModalOpen] = useState(false)
  const [activeRunId, setActiveRunId] = useState(null)
  const [sharedNotice, setSharedNotice] = useState(null)

  // Handle shared URL parameter ?plan=RUN_ID
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const planRunId = params.get('plan')
    if (planRunId) {
      setActiveRunId(planRunId)
      fetchSharedPlan(planRunId)
    }
  }, [])

  // Keep activeRunId in sync when a new plan stream completes
  useEffect(() => {
    if (result && result.run_id) {
      setActiveRunId(result.run_id)
    }
  }, [result])

  const fetchSharedPlan = async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/travel-plans/public/${runId}`)
      if (!res.ok) throw new Error('Shared travel plan not found')
      const data = await res.json()
      if (data.result) {
        setResult(data.result)
        setStatus('done')
        setActiveTab('plan')
        setSharedNotice(`Viewing shared travel plan (${data.run_id})`)
      }
    } catch (err) {
      console.error('Failed to load shared plan:', err)
    }
  }

  const handleSelectPlanFromDashboard = async (runId) => {
    setActiveRunId(runId)
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const res = await fetch(`${API_BASE}/travel-plans/${runId}`, { headers })
      if (!res.ok) throw new Error('Failed to load plan details')
      const data = await res.json()
      if (data.result) {
        setResult(data.result)
        setStatus('done')
        setActiveTab('plan')
      }
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 py-10 px-4 sm:px-6 relative overflow-hidden">
      {/* Ambient background blur */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-8 relative z-10">
        {/* Navigation Bar */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onOpenAuth={() => setAuthModalOpen(true)}
        />

        {/* Shared Notice Toast */}
        {sharedNotice && (
          <div className="glass-panel p-3.5 rounded-2xl border border-cyan-500/40 bg-cyan-950/40 text-cyan-200 text-xs flex items-center justify-between">
            <span className="flex items-center gap-2">
              <span>🔗</span>
              <span>{sharedNotice}</span>
            </span>
            <button
              onClick={() => setSharedNotice(null)}
              className="text-cyan-400 font-bold hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Main Content View */}
        {activeTab === 'saved' ? (
          <SavedPlansDashboard
            onSelectPlan={handleSelectPlanFromDashboard}
            onOpenAuth={() => setAuthModalOpen(true)}
          />
        ) : (
          <div className="space-y-8">
            {/* Input Form */}
            <TripRequestForm onSubmit={start} disabled={status === 'running'} />

            {/* Execution Errors */}
            {error && (
              <div className="glass-panel border-rose-500/40 bg-rose-950/40 text-rose-200 text-sm rounded-2xl p-4 flex items-center gap-3">
                <span className="text-xl">⚠️</span>
                <div>
                  <div className="font-semibold">Execution Error</div>
                  <div className="text-xs text-rose-300">{error}</div>
                </div>
              </div>
            )}

            {/* Live SSE Agent Monitor */}
            <PlanningProgress events={events} status={status} />

            {/* Failure Summary */}
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

            {/* Final Evaluated Results */}
            {result && (
              <div className="space-y-6 border-t border-slate-800/80 pt-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">🎯</span>
                    <h2 className="text-lg font-bold text-slate-100">Evaluated Travel Plan</h2>
                  </div>

                  <button
                    onClick={() => setExportModalOpen(true)}
                    className="py-2 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 text-white font-semibold text-xs shadow-lg shadow-cyan-500/20 hover:opacity-95 transition-opacity self-start sm:self-auto"
                  >
                    📤 Export & Share Itinerary
                  </button>
                </div>

                {/* Budget & Constraints Panels */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <BudgetPanel budgetResult={result.budget_result} />
                  <ConstraintsPanel constraintResult={result.constraint_result} />
                </div>

                {/* Phase D: Budget Advisor Recommendations */}
                <BudgetAdvicePanel
                  advice={result.budget_advice}
                  currency={result.request?.currency || 'INR'}
                />

                {/* Interactive Refinement Panel */}
                <InteractiveRefinementPanel
                  result={result}
                  runId={activeRunId}
                  onPlanUpdated={(newResult) => setResult(newResult)}
                />

                {/* Itinerary Panel */}
                <ItineraryPanel itinerary={result.itinerary} />

                {/* Phase D: Verified Destination Links */}
                <DestinationLinksPanel
                  resources={result.destination_resources}
                  destination={result.request?.destination || result.itinerary?.destination || 'Destination'}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Auth Modal */}
      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />

      {/* Export & Share Modal */}
      <ExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        runId={activeRunId}
        result={result}
      />
    </div>
  )
}