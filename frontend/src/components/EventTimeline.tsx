import { format } from 'date-fns'

import { motion } from 'framer-motion'

import SeverityBadge from './SeverityBadge'

import type { Event } from '../lib/api'



export default function EventTimeline({ events }: { events: Event[] }) {

  if (!events.length) {

    return (

      <div className="text-center py-12 text-gray-500">

        <p>No events recorded yet</p>

        <p className="text-sm mt-1">Situational events appear here during surveillance</p>

      </div>

    )

  }



  return (

    <div className="space-y-3">

      {events.map((event, i) => (

        <motion.div

          key={event.id}

          initial={{ opacity: 0, x: -20 }}

          animate={{ opacity: 1, x: 0 }}

          transition={{ delay: i * 0.05 }}

          className="glass-card p-4 flex items-start gap-4 hover:border-sentinel-500/20 transition-colors"

        >

          <div className="flex-shrink-0 w-20 text-center">

            <p className="text-xs text-gray-500 font-mono">

              {format(new Date(event.created_at), 'HH:mm')}

            </p>

            <p className="text-[10px] text-gray-600 font-mono">

              {format(new Date(event.created_at), 'dd MMM')}

            </p>

          </div>

          <div className="flex-1 min-w-0">

            <div className="flex items-center gap-2 mb-1">

              <SeverityBadge severity={event.severity} />

            </div>

            <p className="font-medium text-sm text-gray-100">{event.title}</p>

            {event.description && event.description !== event.title && (

              <p className="text-xs text-gray-400 mt-1">{event.description}</p>

            )}

          </div>

          <div className="text-right flex-shrink-0">

            <p className="text-lg font-bold font-mono text-sentinel-400">{event.risk_score}</p>

            <p className="text-[10px] text-gray-500">RISK</p>

          </div>

        </motion.div>

      ))}

    </div>

  )

}


