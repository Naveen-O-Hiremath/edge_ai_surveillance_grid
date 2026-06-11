import { Monitor, Smartphone, Video } from 'lucide-react'
import clsx from 'clsx'

export type CameraSourceType = 'rtsp' | 'webcam' | 'mobile'

const SOURCES = [
  {
    id: 'rtsp' as const,
    label: 'CCTV / RTSP',
    desc: 'IP camera or NVR stream URL',
    icon: Video,
  },
  {
    id: 'webcam' as const,
    label: 'Laptop Webcam',
    desc: 'Use this computer\'s built-in camera',
    icon: Monitor,
  },
  {
    id: 'mobile' as const,
    label: 'Mobile Camera',
    desc: 'Stream from phone browser (QR link)',
    icon: Smartphone,
  },
]

interface Props {
  value: CameraSourceType
  onChange: (v: CameraSourceType) => void
}

export default function CameraSourcePicker({ value, onChange }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
      {SOURCES.map(({ id, label, desc, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={clsx(
            'p-3 rounded-xl border text-left transition-all',
            value === id
              ? 'border-sentinel-500/50 bg-sentinel-600/10'
              : 'border-surface-border hover:border-sentinel-500/20 bg-surface-elevated/50',
          )}
        >
          <Icon className={clsx('w-5 h-5 mb-2', value === id ? 'text-sentinel-400' : 'text-gray-500')} />
          <p className="text-sm font-medium">{label}</p>
          <p className="text-[10px] text-gray-500 mt-0.5">{desc}</p>
        </button>
      ))}
    </div>
  )
}
