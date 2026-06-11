import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  color?: 'blue' | 'red' | 'green' | 'yellow' | 'purple'
}

const colorMap = {
  blue: 'from-sentinel-500/20 to-sentinel-600/5 border-sentinel-500/20 text-sentinel-400',
  red: 'from-threat-critical/20 to-threat-critical/5 border-threat-critical/20 text-threat-critical',
  green: 'from-threat-low/20 to-threat-low/5 border-threat-low/20 text-threat-low',
  yellow: 'from-threat-medium/20 to-threat-medium/5 border-threat-medium/20 text-threat-medium',
  purple: 'from-purple-500/20 to-purple-600/5 border-purple-500/20 text-purple-400',
}

export default function StatCard({ title, value, subtitle, icon: Icon, color = 'blue' }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx('glass-card-hover p-5 bg-gradient-to-br border', colorMap[color])}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 font-medium">{title}</p>
          <p className="text-3xl font-bold mt-1 tracking-tight">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className="p-2.5 rounded-lg bg-white/5">
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </motion.div>
  )
}
