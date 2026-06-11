import { useEffect, useState } from 'react'
import EventTimeline from '../components/EventTimeline'
import { api, type Event } from '../lib/api'

export default function Events() {
  const [events, setEvents] = useState<Event[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    const params: Record<string, string> = { limit: '100' }
    if (filter) params.severity = filter
    api.getEvents(params).then(setEvents).catch(console.error)
    const interval = setInterval(() => api.getEvents(params).then(setEvents).catch(console.error), 10000)
    return () => clearInterval(interval)
  }, [filter])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Event Log</h2>
          <p className="text-gray-400 text-sm mt-1">Complete audit trail of all detected events</p>
        </div>
        <select className="input-field w-48" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All severities</option>
          {['critical', 'high', 'medium', 'low', 'info'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>
      <EventTimeline events={events} />
    </div>
  )
}
