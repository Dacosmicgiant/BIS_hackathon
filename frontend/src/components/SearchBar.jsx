import { Search, Loader2 } from 'lucide-react'

export default function SearchBar({ onSearch, loading, query, setQuery }) {

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSearch(query)
    }
  }

  return (
    <div className="relative">
      <textarea
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe your product or manufacturing process...&#10;e.g. We manufacture 33 grade ordinary Portland cement for construction use"
        rows={3}
        disabled={loading}
        className="w-full px-4 py-3 pr-14 rounded-xl border border-gray-200
                   bg-white shadow-sm text-gray-900 placeholder-gray-400
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   resize-none text-sm leading-relaxed disabled:opacity-60"
      />
      <button
        onClick={() => onSearch(query)}
        disabled={loading || !query.trim()}
        className="absolute right-3 bottom-3 w-9 h-9 rounded-lg bg-blue-600
                   flex items-center justify-center text-white
                   hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors"
      >
        {loading
          ? <Loader2 size={16} className="animate-spin" />
          : <Search size={16} />
        }
      </button>
    </div>
  )
}