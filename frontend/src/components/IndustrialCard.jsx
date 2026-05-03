import { useState } from 'react'
import { ChevronRight, ChevronDown, Bookmark } from 'lucide-react'

export default function IndustrialCard({ standard, rank, withRationale, isSaved, onToggleSave }) {
  const [expanded, setExpanded] = useState(rank === 1)

  return (
    <div className="bg-[#151C2C] rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors overflow-hidden mb-4 p-5 shadow-sm">
      <div className="flex gap-5">
        
        {/* Timeline Column */}
        <div className="flex flex-col items-center mt-1">
          <span className="w-7 h-7 rounded-full border border-indigo-500/50 text-indigo-400 text-xs font-bold flex items-center justify-center bg-[#0B1121] shadow-[0_0_10px_rgba(99,102,241,0.2)]">
            {rank}
          </span>
          <div className="w-px h-full bg-slate-800 mt-4 rounded-full"></div>
        </div>

        {/* Content Column */}
        <div className="flex-1 min-w-0">
          
          {/* Header Row */}
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-semibold text-white text-lg tracking-wide">{standard.is_code}</span>
              <span className="bg-slate-800/80 border border-slate-700 text-slate-400 text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-medium">
                {standard.section_name}
              </span>
            </div>
            <div className="flex items-center gap-4">
              {/* Save / Bookmark Button */}
              <button 
                onClick={onToggleSave}
                className={`cursor-pointer transition-all hover:scale-110 ${isSaved ? 'text-indigo-400' : 'text-slate-500 hover:text-indigo-300'}`}
                title={isSaved ? "Remove from saved" : "Save standard"}
              >
                <Bookmark size={18} className={isSaved ? "fill-current" : ""} />
              </button>
            </div>
          </div>

          {/* Title */}
          <h3 className="text-slate-200 font-medium text-base mb-4 pr-8">
            {standard.title.toLowerCase().replace(/\b\w/g, c => c.toUpperCase())}
          </h3>

          {/* Expand Toggle */}
          <button 
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors font-medium cursor-pointer mb-2"
          >
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            Scope & Description
          </button>

          {/* Expanded Content */}
          {expanded && (
            <div className="mt-4 pt-4 border-t border-slate-800/80">
              {withRationale && standard.rationale && (
                <div className="mb-4">
                  <p className="text-xs font-semibold text-indigo-400/80 mb-1.5 uppercase tracking-wider">AI Synthesis</p>
                  <p className="text-sm text-slate-300 leading-relaxed bg-[#0B1121]/50 p-3 rounded-lg border border-slate-800">
                    {standard.rationale}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Official Scope</p>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {standard.scope}
                </p>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}