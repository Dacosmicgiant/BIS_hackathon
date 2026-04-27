import { useState } from 'react'
import { Sparkles, Zap, Download, Loader2 } from 'lucide-react'
import axios from 'axios'
import SearchBar from './components/SearchBar'
import StandardCard from './components/StandardCard'
import EmptyState from './components/EmptyState'
import LoadingState from './components/LoadingState'

const EXAMPLES = [
  "33 Grade Ordinary Portland Cement",
  "Hollow concrete blocks for load bearing walls",
  "Corrugated asbestos cement roofing sheets",
  "Precast concrete pipes for water mains",
]

export default function App() {
  const [query, setQuery]               = useState('')
  const [results, setResults]           = useState(null)
  const [loading, setLoading]           = useState(false)
  const [exporting, setExporting]       = useState(false)
  const [error, setError]               = useState(null)
  const [latency, setLatency]           = useState(null)
  const [message, setMessage]           = useState(null)
  const [withRationale, setWithRationale] = useState(true)

  async function handleSearch(q) {
    if (!q.trim()) return
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
  }

  function handleExample(example) {
    setQuery(example)
    handleSearch(example)
  }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">BIS</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900 leading-tight">
                BIS Copilot
              </h1>
              <p className="text-xs text-gray-500">
                AI-powered BIS standard discovery for Indian MSEs
              </p>
            </div>
          </div>

          {/* Rationale toggle */}
          <button
            onClick={() => setWithRationale(r => !r)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs
                        font-medium border transition-all cursor-pointer select-none
                        ${withRationale
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : 'bg-gray-50 text-gray-500 border-gray-200 hover:border-gray-300'
                        }`}
          >
            {withRationale
              ? <><Sparkles size={12} /> AI Rationale On</>
              : <><Zap size={12} /> Fast Mode</>
            }
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-4xl mx-auto px-4 py-10">

        {/* Hero */}
        {!results && !loading && !message && (
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              Find the right BIS standards
            </h2>
            <p className="text-gray-500 text-lg max-w-xl mx-auto">
              Describe your product or manufacturing process and get
              instant, accurate BIS standard recommendations.
            </p>
          </div>
        )}

        {/* Search */}
        <SearchBar
          onSearch={handleSearch}
          loading={loading}
          query={query}
          setQuery={setQuery}
        />

        {/* Mode hint */}
        {!results && !loading && (
          <p className="text-center text-xs text-gray-400 mt-2">
            {withRationale
              ? 'AI Rationale mode — explains why each standard applies (slower)'
              : 'Fast mode — retrieval only, no AI explanation (~50ms)'
            }
          </p>
        )}

        {/* Example chips */}
        {!results && !loading && !message && (
          <div className="mt-4 flex flex-wrap gap-2 justify-center">
            {EXAMPLES.map(example => (
              <button
                key={example}
                onClick={() => handleExample(example)}
                className="text-xs px-3 py-1.5 rounded-full bg-white border border-gray-200
                           text-gray-600 hover:border-blue-400 hover:text-blue-600
                           transition-colors cursor-pointer"
              >
                {example}
              </button>
            ))}
          </div>
        )}

        {/* Loading */}
        {loading && <LoadingState withRationale={withRationale} />}

        {/* Error */}
        {error && (
          <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-xl
                          text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Invalid query message */}
        {message && !loading && (
          <div className="mt-8 text-center py-10">
            <p className="text-gray-500 text-sm mb-6">{message}</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {EXAMPLES.map(example => (
                <button
                  key={example}
                  onClick={() => handleExample(example)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white border border-gray-200
                             text-gray-600 hover:border-blue-400 hover:text-blue-600
                             transition-colors cursor-pointer"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {results && !loading && results.length > 0 && (
          <div className="mt-8">

            {/* Results header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-gray-800">
                  {results.length} standards found
                </h3>
                {withRationale && (
                  <span className="flex items-center gap-1 text-xs text-blue-600
                                   bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                    <Sparkles size={10} /> AI rationale
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400">
                  {latency < 1
                    ? `${Math.round(latency * 1000)}ms`
                    : `${latency.toFixed(2)}s`
                  }
                </span>

                <button
                  onClick={handleExport}
                  disabled={exporting}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                             bg-blue-600 text-white text-xs font-medium
                             hover:bg-blue-700 disabled:opacity-50
                             disabled:cursor-not-allowed transition-colors"
                >
                  {exporting
                    ? <><Loader2 size={12} className="animate-spin" /> Generating...</>
                    : <><Download size={12} /> Export PDF</>
                  }
                </button>
              </div>
            </div>

            {/* Cards */}
            <div className="space-y-3">
              {results.map((standard, i) => (
                <StandardCard
                  key={standard.is_code}
                  standard={standard}
                  rank={i + 1}
                  withRationale={withRationale}
                />
              ))}
            </div>

            <button
              onClick={handleReset}
              className="mt-6 text-sm text-gray-400 hover:text-gray-600 transition-colors"
            >
              ← New search
            </button>
          </div>
        )}

        {/* Empty results */}
        {results && !loading && results.length === 0 && !message && (
          <EmptyState />
        )}

      </main>
    </div>
  )
}