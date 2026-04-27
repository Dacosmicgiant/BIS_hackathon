import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

const SECTION_COLORS = {
  'Cement and Concrete':                      'bg-blue-50   text-blue-700   border-blue-200',
  'Building Limes':                           'bg-lime-50   text-lime-700   border-lime-200',
  'Stones':                                   'bg-stone-50  text-stone-700  border-stone-200',
  'Wood Products for Building':               'bg-amber-50  text-amber-700  border-amber-200',
  'Gypsum Building Materials':                'bg-yellow-50 text-yellow-700 border-yellow-200',
  'Timber':                                   'bg-orange-50 text-orange-700 border-orange-200',
  'Bitumen and Tar Products':                 'bg-gray-50   text-gray-700   border-gray-200',
  'Floor, Wall, Roof Coverings and Finishes': 'bg-rose-50   text-rose-700   border-rose-200',
  'Water Proofing and Damp Proofing Materials': 'bg-cyan-50  text-cyan-700   border-cyan-200',
  'Structural Steels':                        'bg-slate-50  text-slate-700  border-slate-200',
  'Glass':                                    'bg-sky-50    text-sky-700    border-sky-200',
}

const DEFAULT_COLOR = 'bg-purple-50 text-purple-700 border-purple-200'

export default function StandardCard({ standard, rank, withRationale }) {
  const [expanded, setExpanded] = useState(rank === 1)

  const sectionColor = SECTION_COLORS[standard.section_name] || DEFAULT_COLOR

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm
                    hover:shadow-md transition-shadow overflow-hidden">

      {/* Card header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full text-left px-5 py-4 flex items-start gap-4"
      >
        {/* Rank badge */}
        <span className="mt-0.5 w-6 h-6 rounded-full bg-gray-100 text-gray-500
                         text-xs font-semibold flex items-center justify-center shrink-0">
          {rank}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {/* IS Code */}
            <span className="font-mono font-semibold text-blue-700 text-sm">
              {standard.is_code}
            </span>
            {/* Year */}
            {standard.year && (
              <span className="text-xs text-gray-400">{standard.year}</span>
            )}
            {/* Section badge */}
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${sectionColor}`}>
              {standard.section_name}
            </span>
          </div>

          {/* Title */}
          <p className="text-sm font-medium text-gray-900 leading-snug">
            {standard.title
              .toLowerCase()
              .replace(/\b\w/g, c => c.toUpperCase())}
          </p>
        </div>

        {/* Expand toggle */}
        <span className="text-gray-400 shrink-0 mt-1">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-4 border-t border-gray-100">

          {/* Rationale — only when withRationale=true and text exists */}
          {withRationale && standard.rationale && (
            <div className="mt-3 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs font-semibold text-blue-600 mb-1 uppercase tracking-wide">
                Why this applies
              </p>
              <p className="text-sm text-blue-900 leading-relaxed">
                {standard.rationale}
              </p>
            </div>
          )}

          {/* Scope */}
          <div className="mt-3">
            <p className="text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wide">
              Scope
            </p>
            <p className="text-sm text-gray-600 leading-relaxed">
              {standard.scope}
            </p>
          </div>

          {/* Footer meta */}
          <div className="mt-3 flex items-center gap-3 text-xs text-gray-400">
            {standard.subcategory
              && standard.subcategory !== 'Foreword'
              && standard.subcategory !== 'Contents'
              && (
                <span>Category: {standard.subcategory}</span>
              )}
            <span>Score: {standard.rrf_score.toFixed(4)}</span>
          </div>

        </div>
      )}
    </div>
  )
}