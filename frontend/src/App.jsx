import { useTravelPlanStream } from './hooks/useTravelPlanStream'
import TripRequestForm from './components/TripRequestForm'
import PlanningProgress from './components/PlanningProgress'
import BudgetPanel from './components/BudgetPanel'
import ConstraintsPanel from './components/ConstraintsPanel'
import ItineraryPanel from './components/ItineraryPanel'

export default function App() {
  const { events, result, status, error, start } = useTravelPlanStream()

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">TravelMind</h1>

        <TripRequestForm onSubmit={start} disabled={status === 'running'} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-4">
            {error}
          </div>
        )}

        <PlanningProgress events={events} />

        {result && result.status === 'failed' && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-xl p-4">
            Planning failed: {result.errors[result.errors.length - 1]}
          </div>
        )}

        {result && result.status === 'completed' && (
          <div className="grid grid-cols-2 gap-6">
            <BudgetPanel budgetResult={result.budget_result} />
            <ConstraintsPanel constraintResult={result.constraint_result} />
            <ItineraryPanel itinerary={result.itinerary} />
          </div>
        )}
      </div>
    </div>
  )
}