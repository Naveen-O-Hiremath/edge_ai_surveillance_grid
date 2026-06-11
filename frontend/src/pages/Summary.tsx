import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Sparkles, Loader2 } from 'lucide-react'
import { api, type Summary } from '../lib/api'

export default function SummaryPage() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const res = await api.generateSummary()
      setSummary(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">AI Security Summary</h2>
          <p className="text-gray-400 text-sm mt-1">Intelligent daily briefing collated from all system logs</p>
        </div>
        <button onClick={generate} disabled={loading} className="btn-primary flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Generate Daily Summary
        </button>
      </div>

      {summary && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          <div className="glass-card p-6 border-sentinel-500/20">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-sentinel-400" />
              <h3 className="font-semibold">Executive Briefing</h3>
              <span className="text-xs text-gray-500 ml-auto">
                Generated {new Date(summary.generated_at).toLocaleString()}
              </span>
            </div>
            <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">{summary.narrative}</p>
          </div>

          {summary.stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(summary.stats).filter(([k]) => !k.includes('_') || k === 'avg_risk_score').slice(0, 8).map(([key, value]) => (
                typeof value === 'number' || typeof value === 'string' ? (
                  <div key={key} className="glass-card p-4 text-center">
                    <p className="text-2xl font-bold text-sentinel-400">{String(value)}</p>
                    <p className="text-xs text-gray-500 mt-1 capitalize">{key.replace(/_/g, ' ')}</p>
                  </div>
                ) : null
              ))}
            </div>
          )}
        </motion.div>
      )}

      {!summary && !loading && (
        <div className="text-center py-20 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>Click "Generate Daily Summary" to create an AI-powered security briefing</p>
        </div>
      )}
    </div>
  )
}
