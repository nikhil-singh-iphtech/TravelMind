export default function DestinationLinksPanel({ resources, destination }) {
  if (!resources || resources.length === 0) return null

  return (
    <div className="glass-panel p-6 rounded-3xl space-y-4 border border-cyan-500/30">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🗺️</span>
          <div>
            <h3 className="text-base font-bold text-slate-100">Plan Your Trip: {destination} Guides</h3>
            <p className="text-xs text-slate-400">Verified destination resources, seasonal tips & sightseeing guides</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {resources.map((res, idx) => (
          <a
            key={idx}
            href={res.url}
            target="_blank"
            rel="noopener noreferrer"
            className="glass-panel p-4 rounded-2xl border border-slate-800 hover:border-cyan-500/50 transition-all flex flex-col justify-between group hover:scale-[1.01]"
          >
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block">
                {res.source_site}
              </span>
              <h4 className="text-xs font-bold text-slate-100 group-hover:text-cyan-300 transition-colors line-clamp-2">
                {res.title}
              </h4>
              <p className="text-[11px] text-slate-400 line-clamp-3">
                {res.snippet}
              </p>
            </div>

            <div className="mt-4 text-[11px] font-semibold text-cyan-400 flex items-center gap-1">
              <span>Read Guide</span>
              <span>↗</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
