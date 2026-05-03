import { useState } from 'react'
import { Sparkles, Download, Loader2, History as HistoryIcon, Bookmark as BookmarkIcon } from 'lucide-react'
import axios from 'axios'

import Sidebar from './components/Sidebar'
import TopNav from './components/TopNav'
import IndustrialCard from './components/IndustrialCard'

const EXAMPLES = [
  "33 Grade Ordinary Portland Cement",
  "Hollow concrete blocks for load bearing walls",
  "Corrugated asbestos cement roofing sheets",
  "Precast concrete pipes for water mains",
]

export default function App() {
  const [query, setQuery]                 = useState('')
  const [results, setResults]             = useState(null)
  const [loading, setLoading]             = useState(false)
  const [exporting, setExporting]         = useState(false)
  const [error, setError]                 = useState(null)
  const [latency, setLatency]             = useState(null)
  const [message, setMessage]             = useState(null)
  
  // Navigation & Memory States
  const [activeView, setActiveView]       = useState('search') // 'search', 'history', or 'saved'
  const [history, setHistory]             = useState([])
  const [savedStandards, setSavedStandards] = useState([]) // NEW: Stores saved standard objects
  const [withRationale, setWithRationale] = useState(true)

  // Toggle standard in/out of the saved array
  function toggleSaveStandard(standard) {
    setSavedStandards(prev => {
      const isSaved = prev.some(s => s.is_code === standard.is_code)
      if (isSaved) {
        return prev.filter(s => s.is_code !== standard.is_code) // Remove it
      } else {
        return [...prev, standard] // Add it
      }
    })
  }

  async function handleSearch(q) {
    if (!q.trim()) return
    
    setActiveView('search')
    
    setHistory(prev => {
      if (prev[0] === q.trim()) return prev;
      return [q.trim(), ...prev];
    })

    setLoading(true)
    setError(null)
    setResults(null)
    setMessage(null)

    try {
      const res = await axios.post('/recommend', {
        query:          q.trim(),
        top_n:          5,
        with_rationale: withRationale,
      })
      setResults(res.data.standards)
      setLatency(res.data.latency_seconds)
      setMessage(res.data.message || null)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    if (!results || !query) return
    setExporting(true)
    try {
      const res = await axios.post('/export', {
        query:          query.trim(),
        top_n:          5,
        with_rationale: withRationale,
      }, { responseType: 'blob' })

      const url  = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href  = url
      link.setAttribute('download', 'BIS_Compliance_Report.pdf')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      setError('Failed to generate PDF report.')
    } finally {
      setExporting(false)
    }
  }

  function handleReset() {
    setResults(null)
    setQuery('')
    setMessage(null)
    setError(null)
    setActiveView('search')
  }

  return (
    <div className="flex h-screen bg-[#0B1121] text-slate-200 font-sans overflow-hidden">
      
      <Sidebar 
        onNewSearch={handleReset} 
        activeView={activeView} 
        setActiveView={setActiveView} 
      />

      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <TopNav 
          query={query} 
          setQuery={setQuery} 
          onSearch={handleSearch} 
          loading={loading} 
        />

        <main className="flex-1 overflow-y-auto px-8 py-10">
          <div className="max-w-4xl mx-auto">

            {/* --- SAVED STANDARDS VIEW --- */}
            {activeView === 'saved' && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h2 className="text-2xl font-semibold text-white tracking-tight mb-2">Saved Standards</h2>
                <p className="text-sm text-slate-500 mb-8">Access your bookmarked BIS regulations.</p>
                
                {savedStandards.length === 0 ? (
                  <div className="text-center py-16 bg-[#151C2C] border border-slate-800 rounded-xl">
                    <BookmarkIcon className="mx-auto text-slate-600 mb-3" size={32} />
                    <p className="text-slate-400">You haven't saved any standards yet.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {savedStandards.map((standard, i) => (
                      <IndustrialCard
                        key={standard.is_code}
                        standard={standard}
                        rank={i + 1}
                        withRationale={withRationale}
                        isSaved={true}
                        onToggleSave={() => toggleSaveStandard(standard)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* --- HISTORY VIEW --- */}
            {activeView === 'history' && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h2 className="text-2xl font-semibold text-white tracking-tight mb-2">Search History</h2>
                <p className="text-sm text-slate-500 mb-8">View and re-run your previous standard queries.</p>
                
                {history.length === 0 ? (
                  <div className="text-center py-16 bg-[#151C2C] border border-slate-800 rounded-xl">
                    <HistoryIcon className="mx-auto text-slate-600 mb-3" size={32} />
                    <p className="text-slate-400">Your search history is empty.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {history.map((histQuery, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setQuery(histQuery)
                          handleSearch(histQuery)
                        }}
                        className="w-full text-left bg-[#151C2C] border border-slate-800 p-5 rounded-xl hover:border-indigo-500/50 hover:bg-[#1A2333] transition-all flex items-center gap-4 group cursor-pointer"
                      >
                        <div className="w-8 h-8 rounded-full bg-slate-800/50 flex items-center justify-center group-hover:bg-indigo-500/20 transition-colors">
                          <HistoryIcon size={16} className="text-slate-500 group-hover:text-indigo-400" />
                        </div>
                        <span className="text-slate-300 group-hover:text-white font-medium">{histQuery}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* --- SEARCH VIEW --- */}
            {activeView === 'search' && (
              <>
                {/* EMPTY STATE */}
                {!results && !loading && !message && (
                  <div className="flex flex-col items-center justify-center mt-20 text-center">
                    <div className="w-16 h-16 bg-slate-800/50 rounded-2xl flex items-center justify-center mb-6 border border-slate-700/50">
                      <Sparkles className="text-indigo-400" size={28} />
                    </div>
                    <h2 className="text-3xl font-semibold text-white mb-3">
                      Find the right BIS standards
                    </h2>
                    <p className="text-slate-400 text-lg max-w-xl mx-auto mb-10">
                      Describe your product or manufacturing process and get instant, accurate BIS standard recommendations.
                    </p>
                    <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
                      {EXAMPLES.map(example => (
                        <button
                          key={example}
                          onClick={() => { setQuery(example); handleSearch(example) }}
                          className="text-sm px-4 py-2.5 rounded-full bg-[#151C2C] border border-slate-700/80 text-slate-300 hover:text-white hover:border-slate-500 transition-colors cursor-pointer"
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* LOADING STATE */}
                {loading && (
                  <div className="mt-12 space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="bg-[#151C2C] rounded-xl border border-slate-800 p-6 animate-pulse">
                        <div className="flex gap-5">
                          <div className="w-7 h-7 rounded-full bg-slate-800 shrink-0" />
                          <div className="flex-1 space-y-4 py-1">
                            <div className="h-4 bg-slate-800 rounded w-1/4" />
                            <div className="space-y-2">
                              <div className="h-3 bg-slate-800/50 rounded" />
                              <div className="h-3 bg-slate-800/50 rounded w-5/6" />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* ERROR STATE */}
                {error && (
                  <div className="mt-8 p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-400 text-sm">
                    {error}
                  </div>
                )}

                {/* MESSAGE STATE */}
                {message && !loading && (
                  <div className="mt-12 text-center py-10 bg-[#151C2C] border border-slate-800 rounded-xl">
                    <p className="text-slate-400 text-sm mb-6">{message}</p>
                    <button onClick={handleReset} className="text-sm text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer">
                      Try another search
                    </button>
                  </div>
                )}

                {/* RESULTS STATE */}
                {results && !loading && results.length > 0 && (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 mt-8">
                    <div className="flex items-end justify-between mb-8">
                      <div>
                        <h2 className="text-2xl font-semibold text-white tracking-tight">{results.length} standards found</h2>
                        <p className="text-sm text-slate-500 mt-1">Showing highly relevant industrial regulations for your query.</p>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <span className="text-xs font-mono text-slate-500 bg-[#151C2C] px-3 py-1.5 rounded-lg border border-slate-800">
                          {latency < 1 ? `${Math.round(latency * 1000)}ms` : `${latency.toFixed(2)}s`}
                        </span>
                        <button
                          onClick={handleExport}
                          disabled={exporting}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700/50 text-white text-sm font-semibold border border-slate-600/50 hover:bg-slate-600 transition-colors disabled:opacity-50 cursor-pointer"
                        >
                          {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                          Export PDF
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      {results.map((standard, i) => (
                        <IndustrialCard
                          key={standard.is_code}
                          standard={standard}
                          rank={i + 1}
                          withRationale={withRationale}
                          // Pass down the isSaved boolean and the toggle function
                          isSaved={savedStandards.some(s => s.is_code === standard.is_code)}
                          onToggleSave={() => toggleSaveStandard(standard)}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

          </div>
        </main>
      </div>
    </div>
  )
}