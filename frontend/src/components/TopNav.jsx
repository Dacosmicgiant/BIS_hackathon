import { Search, User } from 'lucide-react'

export default function TopNav({ query, setQuery, onSearch, loading }) {
  
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSearch(query)
    }
  }

  return (
    <header className="h-20 bg-[#0B1121] border-b border-slate-800/50 flex items-center px-8 shrink-0">
      <div className="flex-1 max-w-3xl mx-auto flex items-center">
        
        {/* Sleek Search Bar */}
        <div className="relative w-full">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Search industrial standards or describe your product..."
            className="w-full bg-[#151C2C] border border-slate-700/50 text-white rounded-full py-3 pl-12 pr-4 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 placeholder-slate-500 text-sm transition-all"
          />
        </div>
      </div>

      {/* Right side profile icon */}
      <div className="flex items-center gap-4 ml-6 pl-6 border-l border-slate-800">
        <button className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors cursor-pointer">
          <User size={16} />
        </button>
      </div>
    </header>
  )
}