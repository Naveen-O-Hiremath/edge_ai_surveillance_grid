import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, AlertTriangle } from 'lucide-react'
import SeverityBadge from '../components/SeverityBadge'
import { useWebSocket } from '../hooks/useWebSocket'
import { api, type Incident } from '../lib/api'

export default function ThreatCenter() {
  const { alerts } = useWebSocket('/ws/live')
  const [incidents, setIncidents] = useState<Incident[]>([])

  useEffect(() => {
    api.getIncidents().then(setIncidents).catch(console.error)
    const interval = setInterval(() => api.getIncidents().then(setIncidents).catch(console.error), 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Threat Center</h2>
        <p className="text-gray-400 text-sm mt-1">Correlated incidents and live threat alerts</p>
      </div>

      {alerts.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
          <h3 className="font-semibold text-threat-critical flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Live Alerts
          </h3>
          {alerts.slice(0, 5).map((alert, i) => (
            <div key={i} className="glass-card p-4 border-threat-critical/30 animate-pulse-slow">
              <div className="flex items-center justify-between">
                <p className="font-medium">{(alert.data.title as string) || 'Alert'}</p>
                <SeverityBadge severity={(alert.data.severity as string) || 'high'} />
              </div>
              <p className="text-xs text-gray-400 mt-1">Risk: {alert.data.risk_score as number}</p>
            </div>
          ))}
        </motion.div>
      )}

      <div className="space-y-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Shield className="w-4 h-4 text-sentinel-400" /> Correlated Incidents
        </h3>
        {incidents.length ? incidents.map((inc) => (
          <motion.div key={inc.id} className="glass-card-hover p-5">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold">{inc.title}</h4>
                <p className="text-sm text-gray-400 mt-1">{inc.ai_summary || inc.title}</p>
                <p className="text-xs text-gray-500 mt-2">
                  Started: {new Date(inc.started_at).toLocaleString()} · Status: {inc.status}
                </p>
              </div>
              <div className="text-right">
                <SeverityBadge severity={inc.severity} />
                <p className="text-2xl font-bold font-mono text-threat-critical mt-2">{inc.risk_score}</p>
              </div>
            </div>
          </motion.div>
        )) : (
          <p className="text-gray-500 text-center py-12">No open incidents — all clear</p>
        )}
      </div>
    </div>
  )
}
