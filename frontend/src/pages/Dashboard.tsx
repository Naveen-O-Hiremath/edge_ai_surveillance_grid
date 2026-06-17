import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Camera, Shield, Activity, Users, AlertTriangle, Box, TrendingUp,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import StatCard from '../components/StatCard'
import EventTimeline from '../components/EventTimeline'
import { api, type DashboardData, type SystemStatus } from '../lib/api'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [system, setSystem] = useState<SystemStatus | null>(null)

  useEffect(() => {
    const load = () => {
      api.getDashboard().then(setData).catch(console.error)
      api.getSystemStatus().then(setSystem).catch(console.error)
    }
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  const stats = data?.stats
  const severityData = Object.entries(data?.severity_distribution || {}).map(([name, value]) => ({
    name, value,
  }))

  const operational = system?.healthy ?? false

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Command Center</h2>
          <p className="text-gray-400 text-sm mt-1">
            {system?.message || 'Checking system status…'}
          </p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
          operational
            ? 'bg-green-500/10 border-green-500/20'
            : 'bg-threat-critical/10 border-threat-critical/30'
        }`}>
          <span className={`w-2 h-2 rounded-full ${operational ? 'bg-green-400 animate-pulse' : 'bg-threat-critical'}`} />
          <span className={`text-xs font-medium ${operational ? 'text-green-400' : 'text-threat-critical'}`}>
            {operational ? 'Feeds Active' : 'No Live Feeds'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Cameras Streaming"
          value={`${stats?.online_cameras ?? 0}/${stats?.total_cameras ?? 0}`}
          icon={Camera}
          color="blue"
          subtitle="Receiving frames in last 10s"
        />
        <StatCard title="Open Incidents" value={stats?.active_threats ?? 0} icon={Shield} color="red" subtitle="Unresolved threats" />
        <StatCard title="Events Today" value={stats?.events_today ?? 0} icon={Activity} color="purple" />
        <StatCard
          title="Incident Risk"
          value={stats?.risk_score_avg ?? 0}
          icon={TrendingUp}
          color="yellow"
          subtitle="Avg. of open incidents"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Unknown Visitors" value={stats?.unknown_visitors_today ?? 0} icon={Users} color="red" />
        <StatCard title="Asset Alerts" value={stats?.asset_alerts_today ?? 0} icon={Box} color="yellow" />
        <StatCard title="Edge AI" value={system?.edge_ai_reachable ? 'Online' : 'Offline'} icon={AlertTriangle} color={system?.edge_ai_reachable ? 'green' : 'red'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="lg:col-span-2 glass-card p-5">
          <h3 className="font-semibold mb-4">Activity Timeline</h3>
          {(data?.timeline?.length ?? 0) > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={data?.timeline || []}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0099e6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0099e6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="hour" tickFormatter={(h) => `${h}:00`} stroke="#475569" fontSize={12} />
                <YAxis stroke="#475569" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1a2234', border: '1px solid #1e293b', borderRadius: 8 }} />
                <Area type="monotone" dataKey="count" stroke="#0099e6" fill="url(#colorCount)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-sm py-16 text-center">No events today — activate surveillance with a live camera feed</p>
          )}
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-5">
          <h3 className="font-semibold mb-4">Severity Distribution</h3>
          {severityData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={severityData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" stroke="none">
                    {severityData.map((entry) => (
                      <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] || '#64748b'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1a2234', border: '1px solid #1e293b', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-2 justify-center mt-2">
                {severityData.map((s) => (
                  <span key={s.name} className="flex items-center gap-1 text-xs text-gray-400">
                    <span className="w-2 h-2 rounded-full" style={{ background: SEVERITY_COLORS[s.name] }} />
                    {s.name} ({s.value})
                  </span>
                ))}
              </div>
            </>
          ) : (
            <p className="text-gray-500 text-sm py-16 text-center">No severity data yet</p>
          )}
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-5">
        <h3 className="font-semibold mb-4">Recent High-Severity Events</h3>
        {(data?.top_threats?.length ?? 0) > 0 ? (
          <EventTimeline events={data?.top_threats || []} />
        ) : (
          <p className="text-gray-500 text-sm py-8 text-center">No high or critical events today</p>
        )}
      </motion.div>
    </div>
  )
}
