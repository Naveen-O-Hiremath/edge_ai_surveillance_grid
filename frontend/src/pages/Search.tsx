import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search as SearchIcon, Sparkles } from 'lucide-react'
import EventTimeline from '../components/EventTimeline'
import { api } from '../lib/api'

const SUGGESTIONS = [
  'What happened yesterday after 10 PM?',
  'Show all unknown visitors last week',
  'Show every laptop movement',
  'Show all masked person detections',
  'Show door state changes today',
]

export default function Search() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<{ answer: string; matching_events: import('../lib/api').Event[] } | null>(null)
  const [loading, setLoading] = useState(false)

  const search = async (q?: string) => {
    const searchQuery = q || query
    if (!searchQuery) return
    setLoading(true)
    try {
      const res = await api.search(searchQuery)
      setResult(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Intelligence Search</h2>
        <p className="text-gray-400 text-sm mt-1">Natural language security queries across all event logs</p>
      </div>

      <div className="glass-card p-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              className="input-field pl-11 text-base"
              placeholder="Ask anything about your security logs..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && search()}
            />
          </div>
          <button onClick={() => search()} disabled={loading} className="btn-primary px-6 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => { setQuery(s); search(s) }} className="text-xs px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:text-sentinel-300 hover:bg-sentinel-500/10 transition-colors">
              {s}
            </button>
          ))}
        </div>
      </div>

      {result && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="glass-card p-5 border-sentinel-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-sentinel-400" />
              <span className="text-sm font-medium text-sentinel-300">AI Analysis</span>
            </div>
            <p className="text-gray-200">{result.answer}</p>
          </div>
          <EventTimeline events={result.matching_events} />
        </motion.div>
      )}
    </div>
  )
}
