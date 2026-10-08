import { useState } from 'react'

export default function ExportModal({ isOpen, onClose, runId, result }) {
  const [copied, setCopied] = useState(false)

  if (!isOpen || !result) return null

  const shareUrl = `${window.location.origin}/?plan=${runId}`

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg p-6 rounded-3xl border border-slate-700/80 shadow-2xl relative bg-[#0b0f19] space-y-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 text-lg p-1"
        >
          ✕
        </button>

        <div className="text-center">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-2xl mx-auto mb-3 shadow-lg shadow-cyan-500/20">
            📤
          </div>
          <h2 className="text-xl font-extrabold text-slate-100">Export & Share Itinerary</h2>
          <p className="text-xs text-slate-400 mt-1">
            Share this travel plan via link or export as printable PDF document
          </p>
        </div>

        {/* Shareable Link Section */}
        <div className="space-y-2 glass-panel p-4 rounded-2xl border border-slate-800">
          <label className="text-xs font-semibold text-slate-300 block">🔗 Public Shareable Link</label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={shareUrl}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none"
            />
            <button
              onClick={handleCopyLink}
              className="py-2 px-4 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs hover:bg-cyan-400 transition-colors shrink-0"
            >
              {copied ? 'Copied! ✓' : 'Copy Link'}
            </button>
          </div>
        </div>

        {/* Print / PDF Document Export */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-3">
          <div>
            <h4 className="text-xs font-semibold text-slate-200">📄 PDF / Printable Document</h4>
            <p className="text-[11px] text-slate-400">
              Generates a formatted layout optimized for PDF saving or printing.
            </p>
          </div>

          <button
            onClick={handlePrint}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 font-semibold text-white text-xs shadow hover:opacity-95 transition-opacity"
          >
            🖨️ Print / Save as PDF
          </button>
        </div>
      </div>
    </div>
  )
}
