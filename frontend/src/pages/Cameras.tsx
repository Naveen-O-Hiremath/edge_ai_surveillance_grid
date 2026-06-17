import { useEffect, useState } from 'react'
import { Camera, Wifi, WifiOff, Monitor, Smartphone, Video } from 'lucide-react'
import { api, type Camera as CameraType } from '../lib/api'
import PublishLinkCard from '../components/PublishLinkCard'

const SOURCE_ICONS = {
  rtsp: Video,
  webcam: Monitor,
  mobile: Smartphone,
}

export default function Cameras() {
  const [cameras, setCameras] = useState<CameraType[]>([])
  const [snapshots, setSnapshots] = useState<Record<string, string>>({})

  const load = () => api.getCameras().then(setCameras).catch(console.error)

  useEffect(() => {
    load()
    const interval = setInterval(load, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const refreshSnapshots = async () => {
      for (const cam of cameras) {
        if (!cam.is_streaming) continue
        try {
          const token = localStorage.getItem('sentinel_token')
          const res = await fetch(`/api/v1/cameras/${cam.id}/snapshot?t=${Date.now()}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          })
          if (res.ok) {
            const blob = await res.blob()
            const url = URL.createObjectURL(blob)
            setSnapshots((prev) => {
              if (prev[cam.id]) URL.revokeObjectURL(prev[cam.id])
              return { ...prev, [cam.id]: url }
            })
          }
        } catch {
          /* ignore */
        }
      }
    }
    refreshSnapshots()
    const interval = setInterval(refreshSnapshots, 2000)
    return () => clearInterval(interval)
  }, [cameras])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Camera Grid</h2>
        <p className="text-gray-400 text-sm mt-1">Green = receiving frames in the last 10 seconds. Open the publisher link to go live.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cameras.map((cam) => {
          const SourceIcon = SOURCE_ICONS[cam.source_type as keyof typeof SOURCE_ICONS] || Camera
          const snapshot = cam.is_streaming ? snapshots[cam.id] : undefined
          const live = cam.is_streaming
          return (
            <div key={cam.id} className="glass-card-hover overflow-hidden">
              <div className="aspect-video bg-surface-elevated flex items-center justify-center relative">
                {snapshot ? (
                  <img src={snapshot} alt={cam.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="text-center p-4">
                    <SourceIcon className="w-12 h-12 text-gray-600 mx-auto" />
                    <p className="text-xs text-gray-500 mt-2">
                      {live ? 'Loading preview…' : 'Feed offline — open publisher'}
                    </p>
                  </div>
                )}
                <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2 py-1 rounded-full bg-black/50 text-xs">
                  <span className={`w-2 h-2 rounded-full ${live ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
                  <span className={live ? 'text-green-400' : 'text-gray-400'}>
                    {live ? 'Streaming' : 'Offline'}
                  </span>
                </div>
                <div className="absolute top-3 right-3 px-2 py-0.5 rounded bg-black/50 text-[10px] uppercase text-gray-300">
                  {cam.source_type}
                </div>
                {live && (
                  <div className="absolute bottom-3 right-3 text-xs font-mono text-gray-300">
                    Signal: {Math.round(cam.health_score ?? 0)}%
                  </div>
                )}
              </div>
              <div className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">{cam.name}</h3>
                    <p className="text-xs text-gray-500">
                      Mode: {cam.status}
                      {cam.last_heartbeat ? ` · Last frame ${new Date(cam.last_heartbeat).toLocaleTimeString()}` : ''}
                    </p>
                  </div>
                  {live ? (
                    <Wifi className="w-4 h-4 text-green-400" />
                  ) : (
                    <WifiOff className="w-4 h-4 text-gray-500" />
                  )}
                </div>
                {cam.source_type !== 'rtsp' && cam.publish_url && (
                  <PublishLinkCard camera={cam} />
                )}
              </div>
            </div>
          )
        })}
        {!cameras.length && (
          <p className="text-gray-500 col-span-full text-center py-12">
            No cameras configured. Go to Configure to add a webcam or mobile camera.
          </p>
        )}
      </div>
    </div>
  )
}
