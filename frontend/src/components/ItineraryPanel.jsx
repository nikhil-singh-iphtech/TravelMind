export default function ItineraryPanel({ itinerary }) {
  if (!itinerary) return null

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 col-span-2">
      <h2 className="text-sm font-semibold text-slate-700 mb-2">Itinerary</h2>
      <p className="text-sm text-slate-700 leading-relaxed">{itinerary.summary}</p>
    </div>
  )
}