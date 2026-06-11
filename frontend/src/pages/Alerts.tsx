import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Bell, Plus, Volume2 } from 'lucide-react'
import SeverityBadge from '../components/SeverityBadge'
import { api, type AlertRule } from '../lib/api'

const EVENT_TYPES = [
  'masked_person', 'unknown_person', 'asset_removed', 'asset_moved',
  'camera_tampered', 'door_opened', 'person_loitering', 'tailgating',
]

const CHANNELS = ['push', 'desktop', 'email', 'sms', 'whatsapp', 'sound']

export default function Alerts() {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    name: '', event_type: 'masked_person', min_severity: 'high',
    channels: ['push', 'desktop'] as string[], sound_enabled: true,
  })

  useEffect(() => { api.getAlertRules().then(setRules).catch(console.error) }, [])

  const create = async () => {
    await api.createAlertRule(form)
    setShowCreate(false)
    api.getAlertRules().then(setRules)
  }

  const toggleChannel = (ch: string) => {
    setForm((f) => ({
      ...f,
      channels: f.channels.includes(ch) ? f.channels.filter((c) => c !== ch) : [...f.channels, ch],
    }))
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Threat Alert Configuration</h2>
          <p className="text-gray-400 text-sm mt-1">Configure when and how alerts are dispatched to mobile and desktop</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Rule
        </button>
      </div>

      {showCreate && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-5 space-y-4">
          <input className="input-field" placeholder="Rule name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <select className="input-field" value={form.event_type} onChange={(e) => setForm({ ...form, event_type: e.target.value })}>
              {EVENT_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select>
            <select className="input-field" value={form.min_severity} onChange={(e) => setForm({ ...form, min_severity: e.target.value })}>
              {['info', 'low', 'medium', 'high', 'critical'].map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-2">Notification Channels</p>
            <div className="flex flex-wrap gap-2">
              {CHANNELS.map((ch) => (
                <button
                  key={ch}
                  onClick={() => toggleChannel(ch)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    form.channels.includes(ch)
                      ? 'bg-sentinel-600/20 border-sentinel-500/30 text-sentinel-300'
                      : 'border-surface-border text-gray-500'
                  }`}
                >
                  {ch}
                </button>
              ))}
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" checked={form.sound_enabled} onChange={(e) => setForm({ ...form, sound_enabled: e.target.checked })} />
            <Volume2 className="w-4 h-4" /> Enable audible alarm for high-severity alerts
          </label>
          <button onClick={create} className="btn-primary">Create Alert Rule</button>
        </motion.div>
      )}

      <div className="space-y-3">
        {rules.map((rule) => (
          <motion.div key={rule.id} className="glass-card-hover p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-2 rounded-lg ${rule.is_active ? 'bg-sentinel-500/10' : 'bg-gray-700/30'}`}>
                <Bell className={`w-5 h-5 ${rule.is_active ? 'text-sentinel-400' : 'text-gray-500'}`} />
              </div>
              <div>
                <h3 className="font-medium">{rule.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {rule.event_type.replace(/_/g, ' ')} · min severity: {rule.min_severity}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <SeverityBadge severity={rule.min_severity} />
              <div className="flex gap-1">
                {rule.channels.map((ch) => (
                  <span key={ch} className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{ch}</span>
                ))}
              </div>
              {rule.sound_enabled && <Volume2 className="w-4 h-4 text-threat-medium" />}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
